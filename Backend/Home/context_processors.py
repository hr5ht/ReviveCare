from Patients.models import Notification


def patient(request):
    """Unread notification count for the patient header bell."""
    patient_id = request.session.get('patient_id') if hasattr(request, 'session') else None
    if not patient_id:
        return {}
    return {'unread_notifications': Notification.objects.filter(patient_id=patient_id, read_at=None).count()}
