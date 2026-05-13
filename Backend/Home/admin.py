from django.contrib import admin

from .models import DemoRequest


@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'email', 'created_at', 'contacted')
    list_filter = ('contacted',)
    list_editable = ('contacted',)
    search_fields = ('name', 'organization', 'email')
