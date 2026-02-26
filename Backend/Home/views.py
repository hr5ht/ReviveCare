from functools import wraps

from django.shortcuts import render, redirect
from Patients.models import Patient


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


# Shared by the exercise list and workout pages
EXERCISES = [
    {'id': 'bicep-curl', 'name': 'Bicep Curl', 'description': 'Strengthen your biceps with controlled arm movements',
     'icon': 'dumbbell', 'color': 'emerald', 'targetReps': 12, 'videoUrl': '/static/Patients/videos/bc.mp4'},
    {'id': 'shoulder-extension', 'name': 'Lateral Raise', 'description': 'Improve shoulder mobility and strength',
     'icon': 'activity', 'color': 'blue', 'targetReps': 10, 'videoUrl': '/static/Patients/videos/sl.mp4'},
    {'id': 'jumping-jacks', 'name': 'Jumping Jacks', 'description': 'Full-body cardio warmup exercise',
     'icon': 'zap', 'color': 'purple', 'targetReps': 20, 'videoUrl': '/static/Patients/videos/jj.mp4'},
    {'id': 'arm-raises', 'name': 'Arm Raises', 'description': 'Build shoulder endurance and stability',
     'icon': 'target', 'color': 'orange', 'targetReps': 15, 'videoUrl': '/static/Patients/videos/ar.mp4'},
]


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
            {'label': 'Days in Recovery', 'value': '12', 'icon': 'calendar', 'cls': 'bg-emerald-100 text-emerald-600'},
            {'label': 'Progress Score', 'value': '87%', 'icon': 'trending-up', 'cls': 'bg-blue-100 text-blue-600'},
            {'label': 'Goals Achieved', 'value': '8/10', 'icon': 'target', 'cls': 'bg-purple-100 text-purple-600'},
        ],
    })


def change_password(request):
    patient = Patient.objects.filter(id=request.session.get('patient_id')).first()
    if not patient:
        return redirect('patient_login')
    return render(request, 'change_password.html', {'patient': patient, 'fields': [
        ('current', 'Current Password', 'Enter your current password'),
        ('new_password', 'New Password', 'At least 8 characters'),
        ('confirm', 'Confirm New Password', 'Re-enter the new password'),
    ]})


@patient_page
def exercises(request):
    return render(request, 'exercises.html', {'exercises': EXERCISES})


@patient_page
def exercise_workout(request, exercise_id):
    exercise = next((e for e in EXERCISES if e['id'] == exercise_id), None)
    if not exercise:
        return redirect('exercises')
    return render(request, 'exercise_workout.html', {'exercise': exercise})


@patient_page
def chat(request):
    return render(request, 'chat.html')
