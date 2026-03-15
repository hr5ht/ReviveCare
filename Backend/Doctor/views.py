from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from Home.views import _initials

from django.db.models import Max, Q
from django.utils import timezone

from Patients.models import Exercise, ExercisePlan, Patient, RecoveryGoal, Workout

from .forms import DoctorProfileForm, RecoveryGoalForm
from .models import DoctorProfile


STATUSES = ['active', 'inactive', 'new']


def patient_rows(patients):
    """Patients with their latest workout and a status: active (worked out in the last 3 days), inactive or new."""
    last = dict(Workout.objects.filter(patient__in=patients, total_reps__gt=0).values('patient')
                .annotate(latest=Max('date')).values_list('patient', 'latest'))
    today = timezone.localdate()
    rows = []
    for p in patients:
        latest = last.get(p.id)
        status = 'new' if not latest else 'active' if (today - latest).days <= 3 else 'inactive'
        rows.append({'id': p.id, 'name': p.name, 'initials': _initials(p.name), 'condition': p.condition or 'No condition recorded',
                     'status': status, 'last_workout': latest})
    rows.sort(key=lambda r: r['last_workout'] or today.replace(year=1), reverse=True)
    return rows


@login_required
def doctor_dashboard(request):
    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '')
    patients = Patient.for_doctor(request.user).filter(is_active=True)
    if q:
        patients = patients.filter(Q(name__icontains=q) | Q(email__icontains=q) | Q(condition__icontains=q))
    patients = patient_rows(patients)
    if status in STATUSES:
        patients = [p for p in patients if p['status'] == status]
    return render(request, 'doctor_dashboard.html', {
        'stats': [
            {'icon': 'users', 'label': 'Active Patients', 'value': '127', 'cls': 'bg-emerald-50 text-emerald-600'},
            {'icon': 'bell', 'label': 'New Alerts', 'value': '8', 'cls': 'bg-rose-50 text-rose-600'},
            {'icon': 'trending-up', 'label': 'Avg Progress Rate', 'value': '92%', 'cls': 'bg-blue-50 text-blue-600'},
            {'icon': 'file-text', 'label': 'Pending Reviews', 'value': '15', 'cls': 'bg-amber-50 text-amber-600'},
        ],
        'quick_actions': [
            {'icon': 'calendar', 'label': 'Schedule Appointment', 'cls': 'bg-purple-50 text-purple-600 hover:bg-purple-100'},
            {'icon': 'activity', 'label': 'Monitor Vitals', 'cls': 'bg-rose-50 text-rose-600 hover:bg-rose-100'},
            {'icon': 'pill', 'label': 'Prescribe Medication', 'cls': 'bg-emerald-50 text-emerald-600 hover:bg-emerald-100'},
            {'icon': 'video', 'label': 'Start Telehealth', 'cls': 'bg-blue-50 text-blue-600 hover:bg-blue-100'},
        ],
        'patients': patients[:10],
        'patient_count': len(patients),
        'q': q, 'status': status if status in STATUSES else '', 'statuses': STATUSES,
    })


@login_required
def add_patient(request):
    return render(request, 'add_patient.html')


@login_required
def doctor_profile(request):
    user, profile = request.user, DoctorProfile.for_user(request.user)
    if request.method == 'POST':
        form = DoctorProfileForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            user.first_name, user.last_name, user.email = d['first_name'], d['last_name'], d['email']
            user.save(update_fields=['first_name', 'last_name', 'email'])
            profile.specialty, profile.phone = d['specialty'], d['phone']
            profile.save()
            messages.success(request, 'Profile saved.')
            return redirect('doctor_profile')
    else:
        form = DoctorProfileForm(initial={'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email,
                                          'specialty': profile.specialty, 'phone': profile.phone})
    return render(request, 'doctor_profile.html', {'form': form})


def _bounded(value, low, high):
    """An int within [low, high], or None (use the exercise default) for blank/invalid input."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None
    return number if low <= number <= high else None


@login_required
def patient_plan(request, patient_id):
    """Choose which exercises a patient should do."""
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    exercises = Exercise.objects.filter(is_active=True)
    if request.method == 'POST':
        chosen = set(request.POST.getlist('exercise'))
        for exercise in exercises:
            if str(exercise.id) in chosen:
                ExercisePlan.objects.update_or_create(patient=patient, exercise=exercise, defaults={
                    'is_active': True, 'assigned_by': request.user,
                    'target_reps': _bounded(request.POST.get(f'reps_{exercise.id}'), 1, 100),
                    'sets': _bounded(request.POST.get(f'sets_{exercise.id}'), 1, 10),
                })
            else:
                ExercisePlan.objects.filter(patient=patient, exercise=exercise).update(is_active=False)
        messages.success(request, f"Exercise plan saved for {patient.name}.")
        return redirect('patient_plan', patient_id=patient.id)
    assigned = {p.exercise_id: p for p in patient.plan.filter(is_active=True)}
    rows = [{'exercise': e, 'plan': assigned.get(e.id)} for e in exercises]
    return render(request, 'doctor_patient_plan.html', {'patient': patient, 'rows': rows})


@login_required
def patient_goals(request, patient_id):
    """Set measurable recovery goals for a patient."""
    patient = get_object_or_404(Patient.for_doctor(request.user), id=patient_id)
    if request.method == 'POST' and 'delete' in request.POST:
        patient.goals.filter(id=request.POST['delete']).delete()
        messages.success(request, 'Goal removed.')
        return redirect('patient_goals', patient_id=patient.id)
    form = RecoveryGoalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        RecoveryGoal.objects.create(patient=patient, created_by=request.user, **form.cleaned_data)
        messages.success(request, 'Goal added.')
        return redirect('patient_goals', patient_id=patient.id)
    return render(request, 'doctor_patient_goals.html', {'patient': patient, 'form': form, 'goals': patient.goals.all()})
