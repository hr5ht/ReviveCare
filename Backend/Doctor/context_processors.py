from Patients.models import Alert, Message, Patient

from .models import DoctorProfile


def doctor(request):
    """Name, initials, specialty and unread alert/message counts of the logged-in doctor for the navbar."""
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {}
    name = user.get_full_name() or user.username
    profile = DoctorProfile.objects.filter(user=user).first()
    return {
        'doctor_name': f'Dr. {name}',
        'doctor_initials': ''.join(w[0] for w in name.split()[:2]).upper(),
        'doctor_specialty': (profile and profile.specialty) or 'Doctor',
        'unread_alerts': Alert.objects.filter(patient__in=Patient.for_doctor(user), acknowledged_at=None).count(),
        'unread_messages': Message.objects.filter(patient__in=Patient.for_doctor(user), from_patient=True, read_at=None).count(),
    }
