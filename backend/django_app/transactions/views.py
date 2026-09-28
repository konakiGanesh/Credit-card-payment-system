import hmac
import uuid
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import IntegrityError, transaction
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from cards.models import Card
from .models import Transaction
from .serializers import TransactionSerializer, filtered_transactions


class TransactionListView(generics.ListAPIView):
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return filtered_transactions(Transaction.objects.filter(user=self.request.user), self.request.query_params)


class TransactionDetailView(generics.RetrieveAPIView):
    serializer_class = TransactionSerializer
    lookup_field = "pk"

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class InternalPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        key = request.headers.get("X-Service-Key", "")
        return bool(key) and hmac.compare_digest(key, settings.SERVICE_API_KEY)


class InternalPaymentView(APIView):
    authentication_classes = []
    permission_classes = [InternalPermission]
    throttle_classes = []

    def post(self, request):
        if not isinstance(request.data, dict) or set(request.data) != {"user_id", "card_id", "amount", "currency", "idempotency_key"}:
            return Response({"detail": "Invalid payment fields."}, status=400)
        try:
            user_id, card_id = int(request.data["user_id"]), int(request.data["card_id"])
            amount = Decimal(str(request.data["amount"]))
            key, currency = request.data["idempotency_key"], request.data["currency"]
            if user_id <= 0 or card_id <= 0 or not amount.is_finite() or amount <= 0 or amount > Decimal("9999999999.99") or amount.as_tuple().exponent < -2:
                raise ValueError
            if not isinstance(key, str) or not 1 <= len(key) <= 100 or not isinstance(currency, str) or currency != "USD":
                raise ValueError
        except (ValueError, TypeError, InvalidOperation):
            return Response({"detail": "Invalid payment request."}, status=400)
        # Check an existing key before the card: retries remain safe after card deletion.
        existing = Transaction.objects.filter(user_id=user_id, idempotency_key=key, user__is_active=True).first()
        if existing:
            if existing.original_card_id != card_id or existing.amount != amount or existing.currency != currency:
                return Response({"detail": "Idempotency key already used for a different payment."}, status=409)
            return Response(TransactionSerializer(existing).data)
        card = Card.objects.filter(pk=card_id, user_id=user_id, user__is_active=True).first()
        if not card:
            return Response({"detail": "Card not found."}, status=404)
        try:
            with transaction.atomic():
                payment, created = Transaction.objects.get_or_create(
                    user_id=user_id, idempotency_key=key,
                    defaults={"card": card, "original_card_id": card.pk, "card_last_four": card.last_four,
                              "amount": amount, "currency": currency},
                )
        except IntegrityError:
            payment = Transaction.objects.get(user_id=user_id, idempotency_key=key)
            created = False
        if payment.original_card_id != card_id or payment.amount != amount or payment.currency != currency:
            return Response({"detail": "Idempotency key already used for a different payment."}, status=409)
        return Response(TransactionSerializer(payment).data, status=201 if created else 200)


class InternalPaymentFinalizeView(APIView):
    authentication_classes = []
    permission_classes = [InternalPermission]
    throttle_classes = []

    def post(self, request, reference: uuid.UUID):
        if not isinstance(request.data, dict) or set(request.data) != {"user_id", "status"} or request.data.get("status") not in ("SUCCESS", "FAILED"):
            return Response({"detail": "Invalid result."}, status=400)
        try:
            user_id = int(request.data["user_id"])
        except (ValueError, TypeError):
            return Response({"detail": "Invalid user."}, status=400)
        with transaction.atomic():
            payment = Transaction.objects.select_for_update().filter(reference=reference, user_id=user_id).first()
            if not payment:
                return Response({"detail": "Payment not found."}, status=404)
            if payment.status == Transaction.Status.PENDING:
                payment.status = request.data["status"]
                payment.failure_reason = "Simulation declined" if payment.status == Transaction.Status.FAILED else ""
                payment.save(update_fields=["status", "failure_reason", "updated_at"])
            elif payment.status != request.data["status"]:
                return Response({"detail": "Payment already finalized."}, status=409)
        return Response(TransactionSerializer(payment).data)