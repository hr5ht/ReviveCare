from django.contrib import admin

from .models import ClinicalNote, DoctorProfile


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'specialty', 'phone')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'specialty')


@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ('patient', 'author', 'created_at')
    search_fields = ('patient__name', 'text')
