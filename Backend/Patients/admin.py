from django.contrib import admin
from django.utils.html import format_html

from .models import Exercise, ExercisePlan, Patient, RecoveryGoal, Workout


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


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'rule', 'difficulty', 'target_reps', 'up_angle', 'down_angle', 'order', 'is_active')
    list_editable = ('target_reps', 'order', 'is_active')
    list_filter = ('rule', 'difficulty', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('video_preview',)
    fieldsets = [
        (None, {'fields': ('name', 'slug', 'description', 'instructions', 'icon', 'color', 'order', 'is_active')}),
        ('Tracking', {'fields': ('rule', 'up_angle', 'down_angle', 'target_reps', 'sets', 'rest_seconds', 'difficulty')}),
        ('Reference video', {'fields': ('video_url', 'video_preview')}),
    ]

    @admin.display(description='Preview')
    def video_preview(self, obj):
        if not obj.video_url:
            return '—'
        return format_html('<video src="{}" controls muted style="max-width:360px;border-radius:8px"></video>', obj.video_url)


@admin.register(ExercisePlan)
class ExercisePlanAdmin(admin.ModelAdmin):
    list_display = ('patient', 'exercise', 'target_reps', 'sets', 'is_active', 'assigned_by')
    list_filter = ('is_active', 'exercise')
    search_fields = ('patient__name', 'patient__email')


@admin.register(RecoveryGoal)
class RecoveryGoalAdmin(admin.ModelAdmin):
    list_display = ('patient', 'kind', 'target', 'exercise', 'due_date', 'achieved_at')
    list_filter = ('kind',)
    search_fields = ('patient__name',)
