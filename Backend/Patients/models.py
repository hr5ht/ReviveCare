# patient/models.py
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
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
    chat_since = models.DateTimeField(null=True, blank=True)  # start of the current chatbot conversation

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
        ('front', 'Front arm raise (wrists rise toward shoulder height)'),
        ('squat', 'Squat (knee angle closes on both legs)'),
        ('knee_ext', 'Seated knee extension (either knee straightens)'),
        ('hip_abd', 'Standing hip abduction (either leg swings out)'),
        ('heel', 'Heel raise (hips rise; thresholds are % of leg length)'),
        ('jack', 'Jumping jack (arms and legs open together)'),
    ]
    COLORS = [(c, c.title()) for c in ('emerald', 'blue', 'purple', 'orange')]
    DIFFICULTIES = [('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')]

    slug = models.SlugField(unique=True)  # also the workout URL: /patient/exercise/<slug>/
    name = models.CharField(max_length=80)
    description = models.CharField(max_length=200)
    instructions = models.TextField(blank=True, help_text='One step per line')
    icon = models.CharField(max_length=40, default='activity', help_text='lucide icon name')
    color = models.CharField(max_length=20, choices=COLORS, default='emerald')
    target_reps = models.PositiveSmallIntegerField(default=10)
    difficulty = models.CharField(max_length=12, choices=DIFFICULTIES, default='beginner')
    sets = models.PositiveSmallIntegerField(default=2)
    rest_seconds = models.PositiveSmallIntegerField(default=30, help_text='Rest between sets')
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

    @property
    def steps(self):
        return [line.strip() for line in self.instructions.splitlines() if line.strip()]

    def to_dict(self, plan=None):
        """Shape the exercise templates and the tracker JS expect; a patient's plan overrides reps and sets."""
        data = {'id': self.slug, 'name': self.name, 'description': self.description, 'icon': self.icon,
                'color': self.color, 'targetReps': self.target_reps, 'videoUrl': self.video_url,
                'rule': self.rule, 'upAngle': self.up_angle, 'downAngle': self.down_angle, 'steps': self.steps,
                'difficulty': self.difficulty, 'difficultyLabel': self.get_difficulty_display(),
                'sets': self.sets, 'restSeconds': self.rest_seconds}
        if plan:
            data.update(targetReps=plan.reps, sets=plan.total_sets)
        return data


class ExercisePlan(models.Model):
    """An exercise a doctor has assigned to a patient, with optional per-patient targets."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='plan')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='plans')
    target_reps = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Blank = the exercise's default")
    sets = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Blank = the exercise's default")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['exercise__order', 'exercise__name']
        constraints = [models.UniqueConstraint(fields=['patient', 'exercise'], name='one_plan_entry_per_exercise')]

    def __str__(self):
        return f"{self.patient.name}: {self.exercise.name}"

    @property
    def reps(self):
        return self.target_reps or self.exercise.target_reps

    @property
    def total_sets(self):
        return self.sets or self.exercise.sets


class RecoveryGoal(models.Model):
    """A measurable target a doctor sets for a patient; progress is computed from workouts."""
    KINDS = [
        ('sessions', 'Complete workout sessions'),
        ('total_reps', 'Reach total reps'),
        ('streak', 'Exercise days in a row'),
        ('range', 'Reach a range-of-motion angle'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='goals')
    kind = models.CharField(max_length=12, choices=KINDS)
    target = models.PositiveIntegerField(help_text='Sessions, reps, days, or degrees depending on the kind')
    exercise = models.ForeignKey(Exercise, null=True, blank=True, on_delete=models.SET_NULL,
                                 help_text='Required for range goals; optional filter for reps/sessions')
    due_date = models.DateField(null=True, blank=True)
    achieved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['achieved_at', 'due_date', '-created_at']

    def __str__(self):
        return f"{self.patient.name}: {self.describe()}"

    def describe(self):
        where = f" ({self.exercise.name})" if self.exercise else ''
        unit = {'sessions': 'workout sessions', 'total_reps': 'reps', 'streak': 'days in a row', 'range': '°'}[self.kind]
        if self.kind == 'range':
            return f"Reach {self.target}{unit}{where}"
        return f"{self.target} {unit}{where}"


class Alert(models.Model):
    """A chat message the chatbot scored as serious, waiting for the doctor to review it."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='alerts')
    message = models.TextField()
    response = models.TextField(blank=True)
    seriousness = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.patient.name} · {self.seriousness:.2f} · {self.created_at:%d %b %H:%M}"


class ChatMessage(models.Model):
    """One turn of a patient's conversation with the chatbot."""
    ROLES = [('user', 'Patient'), ('assistant', 'Assistant')]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='chat_messages')
    role = models.CharField(max_length=10, choices=ROLES)
    content = models.TextField()
    seriousness = models.FloatField(null=True, blank=True)  # assistant replies only
    helpful = models.BooleanField(null=True, blank=True)  # patient's thumbs up/down on an assistant reply
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at', 'id']
        indexes = [models.Index(fields=['patient', 'created_at'])]

    def __str__(self):
        return f"{self.patient.name} · {self.role} · {self.created_at:%d %b %H:%M}"


class DiaryEntry(models.Model):
    """A patient's own note on how they feel: pain 0-10 plus any symptoms."""
    SYMPTOMS = [
        ('swelling', 'Swelling'), ('stiffness', 'Stiffness'), ('redness', 'Redness or warmth'), ('fever', 'Fever'),
        ('numbness', 'Numbness or tingling'), ('nausea', 'Nausea'), ('fatigue', 'Tiredness'), ('poor_sleep', 'Poor sleep'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='diary')
    pain = models.PositiveSmallIntegerField()  # 0 (none) to 10 (worst imaginable)
    symptoms = models.JSONField(default=list, blank=True)  # keys from SYMPTOMS
    notes = models.TextField(max_length=1000, blank=True)
    context = models.CharField(max_length=10, default='diary',
                               choices=[('diary', 'Diary'), ('before', 'Before a workout'), ('after', 'After a workout')])
    exercise = models.CharField(max_length=40, blank=True)  # exercise slug for before/after checks
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'diary entries'

    def __str__(self):
        return f"{self.patient.name} · pain {self.pain} · {self.created_at:%d %b %H:%M}"

    def symptom_labels(self):
        names = dict(self.SYMPTOMS)
        return [names.get(s, s) for s in self.symptoms]


class Vitals(models.Model):
    """Readings a patient takes at home; any of them can be left out."""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='vitals')
    systolic = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(60), MaxValueValidator(250)])
    diastolic = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(30), MaxValueValidator(150)])
    heart_rate = models.PositiveSmallIntegerField(null=True, blank=True, validators=[MinValueValidator(30), MaxValueValidator(220)])
    temperature = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True,  # °F, as home thermometers in India read
                                      validators=[MinValueValidator(90), MaxValueValidator(110)])
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'vitals'

    def __str__(self):
        return f"{self.patient.name} · {self.created_at:%d %b %H:%M}"

    @property
    def blood_pressure(self):
        return f"{self.systolic}/{self.diastolic}" if self.systolic and self.diastolic else None
