from django.contrib import admin

from .models import Patient, Workout


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'condition', 'surgery_date', 'doctor', 'is_active', 'must_change_password', 'locked_until', 'created_at')
    list_filter = ('is_active', 'must_change_password', 'doctor')
    search_fields = ('name', 'email', 'condition')
    readonly_fields = ('password', 'failed_login_count', 'locked_until', 'created_at', 'updated_at')


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('patient', 'exercise', 'date', 'total_reps', 'target_reps', 'completed')
    list_filter = ('exercise', 'completed', 'date')
    search_fields = ('patient__name', 'patient__email')
    exclude = ('angles_data',)
