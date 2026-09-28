from django.contrib import admin

from .models import Card


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "card_brand", "last_four", "card_type", "created_at")
    readonly_fields = ("user", "card_brand", "last_four", "card_type", "cardholder_name", "expiry_month", "expiry_year")