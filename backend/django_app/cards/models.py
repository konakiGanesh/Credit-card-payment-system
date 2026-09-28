from django.conf import settings
from django.db import models


class Card(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cards")
    card_type = models.CharField(max_length=6, choices=[("credit", "Credit"), ("debit", "Debit")])
    cardholder_name = models.CharField(max_length=100)
    card_brand = models.CharField(max_length=20)
    last_four = models.CharField(max_length=4)
    expiry_month = models.PositiveSmallIntegerField()
    expiry_year = models.PositiveSmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def masked_number(self) -> str:
        return f"**** **** **** {self.last_four}"

    def __str__(self) -> str:
        return f"{self.card_brand} {self.masked_number}"