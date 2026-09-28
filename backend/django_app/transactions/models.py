import uuid

from django.conf import settings
from django.db import models


class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"

    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transactions")
    card = models.ForeignKey("cards.Card", on_delete=models.SET_NULL, null=True, related_name="transactions")
    original_card_id = models.BigIntegerField()
    card_last_four = models.CharField(max_length=4)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default="USD")
    status = models.CharField(max_length=7, choices=Status.choices, default=Status.PENDING, db_index=True)
    idempotency_key = models.CharField(max_length=100)
    failure_reason = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "idempotency_key"], name="unique_user_payment_key")]
        indexes = [models.Index(fields=["user", "-created_at"]), models.Index(fields=["status", "created_at"])]