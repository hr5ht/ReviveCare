import logging
from functools import wraps

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils import timezone
from Patients.models import Exercise, Patient

from .forms import PatientContactForm

logger = logging.getLogger(__name__)


def patient_page(view):
    """Send patients still on a temporary password to the change-password page first."""
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if Patient.objects.filter(id=request.session.get('patient_id'), must_change_password=True).exists():
            return redirect('change_password')
        return view(request, *args, **kwargs)
    return wrapper


def _initials(name):
    return ''.join(n[0] for n in name.split())


def home(request):
    return render(request, 'home.html', {
        'features': [
            {'icon': 'clock', 'title': 'Real-Time Monitoring', 'description': 'Track patient recovery progress with continuous health data monitoring and automated alerts.'},
            {'icon': 'heart', 'title': 'Personalized Care Plans', 'description': "Customized recovery protocols tailored to each patient's specific medical needs and conditions."},
            {'icon': 'shield', 'title': 'HIPAA Compliant', 'description': 'Enterprise-grade security ensuring patient data privacy and regulatory compliance.'},
            {'icon': 'trending-up', 'title': 'Analytics Dashboard', 'description': 'Comprehensive insights into recovery trends, medication adherence, and health outcomes.'},
        ],
        'benefits': [
            'Reduce hospital readmission rates',
            'Improve patient satisfaction scores',
            'Streamline post-discharge communication',
            'Enable proactive intervention',
            'Comprehensive medication management',
            'Integrated telehealth consultations',
        ],
    })


def patient_login(request):
    return render(request, 'patient_login.html')


def days_in_recovery(patient):
    """Days since surgery/discharge, or a dash when the doctor hasn't set the date."""
    if not patient.surgery_date:
        return '—'
    return str(max(0, (timezone.localdate() - patient.surgery_date).days))


@patient_page
def patient_dashboard(request):
    patient = Patient.objects.filter(id=request.session.get('patient_id')).first()
    if not patient:
        return render(request, 'patient_dashboard.html', {'patient': None})
    return render(request, 'patient_dashboard.html', {
        'patient': patient,
        'initials': _initials(patient.name or 'Patient'),
        # Mock data until the backend provides it
        'tasks': [
            {'task': 'Morning stretching routine', 'completed': True, 'time': '8:00 AM'},
            {'task': 'Take prescribed medication', 'completed': True, 'time': '9:00 AM'},
            {'task': 'Afternoon breathing exercises', 'completed': False, 'time': '2:00 PM'},
            {'task': 'Evening walk (15 minutes)', 'completed': False, 'time': '5:00 PM'},
        ],
        'tasks_done': 2,
        'recovery_stats': [
            {'label': 'Days in Recovery', 'value': days_in_recovery(patient), 'icon': 'calendar', 'cls': 'bg-emerald-100 text-emerald-600'},
            {'label': 'Progress Score', 'value': '87%', 'icon': 'trending-up', 'cls': 'bg-blue-100 text-blue-600'},
            {'label': 'Goals Achieved', 'value': '8/10', 'icon': 'target', 'cls': 'bg-purple-100 text-purple-600'},
        ],
    })


def _logged_in_patient(request):
    return Patient.objects.filter(id=request.session.get('patient_id')).first()


@patient_page
def patient_profile(request):
    patient = _logged_in_patient(request)
    if not patient:
        return redirect('patient_login')
    fields = ['phone', 'emergency_contact_name', 'emergency_contact_phone']
    if request.method == 'POST':
        form = PatientContactForm(request.POST)
        if form.is_valid():
            for f in fields:
                setattr(patient, f, form.cleaned_data[f])
            patient.save(update_fields=fields)
            messages.success(request, 'Contact details saved.')
            return redirect('patient_profile')
    else:
        form = PatientContactForm(initial={f: getattr(patient, f) for f in fields})
    return render(request, 'patient_profile.html', {'patient': patient, 'initials': _initials(patient.name), 'form': form})


def change_password(request):
    patient = Patient.objects.filter(id=request.session.get('patient_id')).first()
    if not patient:
        return redirect('patient_login')
    return render(request, 'change_password.html', {'patient': patient, 'fields': [
        ('current', 'Current Password', 'Enter your current password'),
        ('new_password', 'New Password', 'At least 8 characters'),
        ('confirm', 'Confirm New Password', 'Re-enter the new password'),
    ]})


def exercises_for(request):
    """(exercise, plan) pairs a patient should see: their active plan, or the whole library if they have none."""
    patient = _logged_in_patient(request)
    plan = list(patient.plan.filter(is_active=True, exercise__is_active=True).select_related('exercise')) if patient else []
    if plan:
        return [(p.exercise, p) for p in plan]
    return [(e, None) for e in Exercise.objects.filter(is_active=True)]


def _find_exercise(request, slug):
    return next(((e, p) for e, p in exercises_for(request) if e.slug == slug), (None, None))


@patient_page
def exercises(request):
    return render(request, 'exercises.html', {'exercises': [e.to_dict(p) for e, p in exercises_for(request)]})


@patient_page
def exercise_detail(request, slug):
    exercise, plan = _find_exercise(request, slug)
    if not exercise:
        return redirect('exercises')
    return render(request, 'exercise_detail.html', {'exercise': exercise.to_dict(plan)})


@patient_page
def exercise_workout(request, exercise_id):
    exercise, plan = _find_exercise(request, exercise_id)
    if not exercise:
        return redirect('exercises')
    return render(request, 'exercise_workout.html', {'exercise': exercise.to_dict(plan)})


@patient_page
def chat(request):
    return render(request, 'chat.html')


RESET_SALT = 'patient-password-reset'
RESET_MAX_AGE = 24 * 60 * 60  # seconds


def _reset_token(patient):
    # Includes a slice of the current password hash, so the link stops working once the password changes
    return signing.dumps({'id': patient.id, 'h': patient.password[-16:]}, salt=RESET_SALT)


def _patient_from_token(token):
    try:
        data = signing.loads(token, salt=RESET_SALT, max_age=RESET_MAX_AGE)
    except signing.BadSignature:
        return None
    patient = Patient.objects.filter(id=data.get('id')).first()
    return patient if patient and patient.password[-16:] == data.get('h') else None


def patient_forgot_password(request):
    sent = False
    if request.method == 'POST':
        patient = Patient.objects.filter(email=request.POST.get('email', '').strip().lower(), is_active=True).first()
        if patient:
            link = request.build_absolute_uri(f'/patient/reset-password/{_reset_token(patient)}/')
            try:
                send_mail('Reset your ReViveCare password',
                          f"Hi {patient.name},\n\nChoose a new ReViveCare password here (the link expires in 24 hours):\n\n"
                          f"{link}\n\nIf you didn't ask for this, you can ignore this email.\n\n— The ReViveCare team",
                          None, [patient.email])
            except Exception:
                logger.exception('Patient reset email failed for %s', patient.id)
        sent = True  # same response either way, so the page doesn't reveal which emails exist
    return render(request, 'patient_forgot_password.html', {'sent': sent})


def patient_reset_password(request, token):
    patient = _patient_from_token(token)
    error = None
    if patient and request.method == 'POST':
        new, confirm = request.POST.get('new_password', ''), request.POST.get('confirm', '')
        try:
            if new != confirm:
                raise ValidationError("The passwords don't match.")
            validate_password(new)
        except ValidationError as e:
            error = ' '.join(e.messages)
        else:
            patient.password = make_password(new)
            patient.must_change_password = False
            patient.failed_login_count, patient.locked_until = 0, None
            patient.save(update_fields=['password', 'must_change_password', 'failed_login_count', 'locked_until'])
            return render(request, 'patient_reset_password.html', {'done': True})
    return render(request, 'patient_reset_password.html', {'valid': bool(patient), 'error': error})
