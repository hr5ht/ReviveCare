from django.conf import settings
from django.db import models


class DoctorProfile(models.Model):
    """Extra details for a doctor account (doctors log in as Django users)."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.username}"

    @classmethod
    def for_user(cls, user):
        return cls.objects.get_or_create(user=user)[0]


class ClinicalNote(models.Model):
    """A dated note a doctor writes on a patient's chart."""
    patient = models.ForeignKey('Patients.Patient', on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    text = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient} · {self.created_at:%d %b %Y}"
