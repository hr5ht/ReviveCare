from django.contrib import admin

from .models import AuditLog, ClinicalNote, DoctorProfile


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'specialty', 'phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialty')


@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ('patient', 'author', 'created_at')
    search_fields = ('patient__name', 'text')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Read-only: an audit trail nobody can edit or delete from the admin."""
    list_display = ('created_at', 'user', 'action', 'patient', 'detail', 'ip')
    list_filter = ('action', 'user')
    search_fields = ('patient__name', 'patient__email', 'user__username', 'detail')
    date_hierarchy = 'created_at'
    list_select_related = ('user', 'patient')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
