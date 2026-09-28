from django.contrib import admin

from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ("reference", "user", "amount", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("reference", "user__username")
    readonly_fields = [field.name for field in Transaction._meta.fields]