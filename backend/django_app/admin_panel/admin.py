from django.contrib import admin

from .models import AdminLog


@admin.register(AdminLog)
class AdminLogAdmin(admin.ModelAdmin):
    list_display = ("admin_user", "action", "target_type", "target_id", "timestamp")
    readonly_fields = [field.name for field in AdminLog._meta.fields]