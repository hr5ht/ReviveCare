from django.contrib import admin

from .models import ArmRaise, BicepCurl, JumpingJack, Patient, SLS


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_active', 'must_change_password', 'locked_until', 'created_at')
    list_filter = ('is_active', 'must_change_password')
    search_fields = ('name', 'email')
    readonly_fields = ('password', 'failed_login_count', 'locked_until', 'created_at', 'updated_at')


@admin.register(SLS, BicepCurl, JumpingJack, ArmRaise)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('patient', 'date', 'total_reps', 'target_reps', 'completed')
    list_filter = ('completed', 'date')
    search_fields = ('patient__name', 'patient__email')
    exclude = ('angles_data',)
