# patient/models.py
from django.db import models
from django.utils import timezone

class Patient(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, default='1234321')  # Added password field
    info = models.TextField(max_length=3000)
    created_at = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Patient'
        verbose_name_plural = 'Patients'


# Add this model below Patient
class SLS(models.Model):
    """Side Lateral Raise workout tracking"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='sls_workouts')
    date = models.DateField(default=timezone.now)
    
    # Workout metrics
    total_reps = models.IntegerField(default=0)
    target_reps = models.IntegerField(default=10)
    excellent_reps = models.IntegerField(default=0)
    good_reps = models.IntegerField(default=0)
    partial_reps = models.IntegerField(default=0)
    
    # Session details
    duration_seconds = models.IntegerField(default=0, help_text="Workout duration in seconds")
    completed = models.BooleanField(default=False)
    
    # Detail data for analysis
    angles_data = models.JSONField(default=list, blank=True, help_text="Stored angles for each frame/rep")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient.name} - SLS - {self.date}"
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage"""
        if self.target_reps == 0:
            return 0
        return int((self.total_reps / self.target_reps) * 100)
    
    @property
    def quality_score(self):
        """Calculate quality score based on rep quality"""
        if self.total_reps == 0:
            return 0
        quality = (self.excellent_reps * 100 + self.good_reps * 70 + self.partial_reps * 40) / self.total_reps
        return round(quality, 1)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'SLS Workout'
        verbose_name_plural = 'SLS Workouts'


class BicepCurl(models.Model):
    """Bicep Curl workout tracking"""
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bicep_curl_workouts')
    date = models.DateField(default=timezone.now)
    
    # Workout metrics
    total_reps = models.IntegerField(default=0)
    target_reps = models.IntegerField(default=10)
    excellent_reps = models.IntegerField(default=0)  # Full range of motion
    good_reps = models.IntegerField(default=0)
    partial_reps = models.IntegerField(default=0)
    
    # Session details
    duration_seconds = models.IntegerField(default=0, help_text="Workout duration in seconds")
    completed = models.BooleanField(default=False)
    
    # Detail data for analysis
    angles_data = models.JSONField(default=list, blank=True, help_text="Stored angles for each frame/rep")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.patient.name} - Bicep Curl - {self.date}"
    
    @property
    def completion_percentage(self):
        if self.target_reps == 0:
            return 0
        return int((self.total_reps / self.target_reps) * 100)
        
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Bicep Curl Workout'
        verbose_name_plural = 'Bicep Curl Workouts'

class JumpingJack(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='jj_workouts')
    date = models.DateField(default=timezone.now)
    total_reps = models.IntegerField(default=0)
    target_reps = models.IntegerField(default=10)
    excellent_reps = models.IntegerField(default=0)
    good_reps = models.IntegerField(default=0)
    partial_reps = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    angles_data = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

class ArmRaise(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='ar_workouts')
    date = models.DateField(default=timezone.now)
    total_reps = models.IntegerField(default=0)
    target_reps = models.IntegerField(default=10)
    excellent_reps = models.IntegerField(default=0)
    good_reps = models.IntegerField(default=0)
    partial_reps = models.IntegerField(default=0)
    completed = models.BooleanField(default=False)
    angles_data = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']