from functools import wraps

from django.contrib.auth.decorators import login_required
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


@login_required
def medical_dashboard(request):
    appointments = [
        {'patient': 'Sarah Mitchell', 'time': '09:00 AM', 'type': 'Consultation', 'status': 'confirmed'},
        {'patient': 'James Wilson', 'time': '10:30 AM', 'type': 'Follow-up', 'status': 'confirmed'},
        {'patient': 'Emily Davis', 'time': '11:15 AM', 'type': 'Check-up', 'status': 'pending'},
        {'patient': 'Michael Chen', 'time': '02:00 PM', 'type': 'Consultation', 'status': 'confirmed'},
        {'patient': 'Lisa Anderson', 'time': '03:30 PM', 'type': 'Lab Review', 'status': 'pending'},
    ]
    for a in appointments:
        a['initials'] = _initials(a['patient'])
    return render(request, 'medical_dashboard.html', {
        'stats': [
            {'icon': 'users', 'label': 'Total Patients', 'value': '1,429', 'change': '+12%', 'trend': 'up', 'cls': 'bg-emerald-50 text-emerald-600'},
            {'icon': 'calendar', 'label': 'Appointments Today', 'value': '24', 'change': '3 pending', 'trend': 'neutral', 'cls': 'bg-blue-50 text-blue-600'},
            {'icon': 'activity', 'label': 'Active Cases', 'value': '89', 'change': '-5% from last week', 'trend': 'neutral', 'cls': 'bg-purple-50 text-purple-600'},
            {'icon': 'heart', 'label': 'Critical Alerts', 'value': '3', 'change': 'Require attention', 'trend': 'alert', 'cls': 'bg-rose-50 text-rose-600'},
        ],
        'appointments': appointments,
        'activity': [
            {'action': 'Lab results uploaded', 'patient': 'John Thompson', 'time': '15 min ago', 'icon': 'file-text'},
            {'action': 'New prescription added', 'patient': 'Maria Garcia', 'time': '32 min ago', 'icon': 'pill'},
            {'action': 'Appointment rescheduled', 'patient': 'Robert Lee', 'time': '1 hour ago', 'icon': 'calendar'},
            {'action': 'Vital signs updated', 'patient': 'Anna Smith', 'time': '2 hours ago', 'icon': 'activity'},
        ],
        'alerts': [
            {'message': 'Patient Sarah Mitchell - Blood pressure spike detected', 'severity': 'high', 'time': '5 min ago'},
            {'message': 'Lab results require immediate review - John Thompson', 'severity': 'medium', 'time': '23 min ago'},
            {'message': 'Medication refill needed - Emily Davis', 'severity': 'low', 'time': '1 hour ago'},
        ],
    })


@login_required
def doctor_dashboard(request):
    patients = [
        {'name': 'Sarah Mitchell', 'condition': 'Post-Surgery Recovery', 'status': 'improving', 'lastUpdate': '2 hours ago'},
        {'name': 'James Wilson', 'condition': 'Cardiac Rehabilitation', 'status': 'stable', 'lastUpdate': '5 hours ago'},
        {'name': 'Emily Davis', 'condition': 'Physical Therapy', 'status': 'critical', 'lastUpdate': '30 min ago'},
        {'name': 'Michael Chen', 'condition': 'Medication Management', 'status': 'improving', 'lastUpdate': '1 day ago'},
    ]
    for p in patients:
        p['initials'] = _initials(p['name'])
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
        'patients': patients,
    })


@login_required
def add_patient(request):
    return render(request, 'add_patient.html')


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
