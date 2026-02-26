from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from Home.views import _initials


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
