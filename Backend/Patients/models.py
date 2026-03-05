# patient/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone

class Patient(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                               related_name='patients')
    password = models.CharField(max_length=128, default='1234321')  # Added password field
    must_change_password = models.BooleanField(default=False)  # set while the password is a temporary one
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    info = models.TextField(max_length=3000)
    condition = models.CharField(max_length=150, blank=True)  # e.g. "Total knee replacement"
    surgery_date = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    @classmethod
    def for_doctor(cls, user):
        """Patients a doctor may see: their own (superusers see everyone)."""
        return cls.objects.all() if user.is_superuser else cls.objects.filter(doctor=user)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'


class Workout(models.Model):
    """One exercise session for one patient per day (replaces the per-exercise models)."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='workouts')
    exercise = models.CharField(max_length=40, db_index=True)  # exercise slug, e.g. 'bicep-curl'
    date = models.DateField(default=timezone.localdate)

    total_reps = models.IntegerField(default=0)
    target_reps = models.IntegerField(default=10)
    excellent_reps = models.IntegerField(default=0)
    good_reps = models.IntegerField(default=0)
    partial_reps = models.IntegerField(default=0)

    duration_seconds = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    angles_data = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['patient', 'date'])]

    def __str__(self):
        return f"{self.patient.name} - {self.exercise} - {self.date}"

    @property
    def completion_percentage(self):
        return int(self.total_reps / self.target_reps * 100) if self.target_reps else 0

    @property
    def quality_score(self):
        if not self.total_reps:
            return 0
        return round((self.excellent_reps * 100 + self.good_reps * 70 + self.partial_reps * 40) / self.total_reps, 1)


class Exercise(models.Model):
    """A rehab exercise the browser tracker knows how to count."""
    RULES = [
        ('curl', 'Elbow curl (angle closes below the "up" threshold)'),
        ('raise', 'Arm raise (shoulder angle opens above the "up" threshold)'),
        ('jack', 'Jumping jack (arms and legs open together)'),
    ]
    COLORS = [(c, c.title()) for c in ('emerald', 'blue', 'purple', 'orange')]

    slug = models.SlugField(unique=True)  # also the workout URL: /patient/exercise/<slug>/
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200)
    icon = models.CharField(max_length=40, default='activity', help_text='lucide icon name')
    color = models.CharField(max_length=20, choices=COLORS, default='emerald')
    target_reps = models.PositiveSmallIntegerField(default=10)
    video_url = models.CharField(max_length=200, blank=True, help_text='Reference video, e.g. /static/Patients/videos/bc.mp4')
    rule = models.CharField(max_length=10, choices=RULES)
    up_angle = models.PositiveSmallIntegerField(help_text='Angle (degrees) that counts as the top of a rep')
    down_angle = models.PositiveSmallIntegerField(help_text='Angle (degrees) that resets for the next rep')
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def to_dict(self):
        """Shape the exercise templates and the tracker JS expect."""
        return {'id': self.slug, 'name': self.name, 'description': self.description, 'icon': self.icon,
                'color': self.color, 'targetReps': self.target_reps, 'videoUrl': self.video_url,
                'rule': self.rule, 'upAngle': self.up_angle, 'downAngle': self.down_angle}
