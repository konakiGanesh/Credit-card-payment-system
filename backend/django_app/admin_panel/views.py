import csv
from datetime import timedelta

from django.db.models import Count, Sum
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import generics, permissions
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework.response import Response
from rest_framework.views import APIView

from cards.models import Card
from cards.serializers import CardSerializer
from transactions.models import Transaction
from transactions.serializers import TransactionSerializer, filtered_transactions
from users.models import User
from users.serializers import UserManageSerializer, UserSerializer
from .models import AdminLog


class StaffOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class UserListView(generics.ListAPIView):
    permission_classes = [StaffOnly]
    serializer_class = UserSerializer
    queryset = User.objects.order_by("id")


class UserManageView(generics.UpdateAPIView):
    permission_classes = [StaffOnly]
    serializer_class = UserManageSerializer
    queryset = User.objects.all()
    http_method_names = ["patch", "options"]

    def perform_update(self, serializer):
        user = serializer.save()
        AdminLog.objects.create(admin_user=self.request.user, action="update_user", target_type="user",
                                target_id=str(user.pk), metadata={"changed_fields": list(serializer.validated_data)})


class AdminCardListView(generics.ListAPIView):
    permission_classes = [StaffOnly]
    serializer_class = CardSerializer
    queryset = Card.objects.select_related("user").order_by("-created_at")


class AdminTransactionListView(generics.ListAPIView):
    permission_classes = [StaffOnly]
    serializer_class = TransactionSerializer

    def get_queryset(self):
        return filtered_transactions(Transaction.objects.all(), self.request.query_params)


class SummaryView(APIView):
    permission_classes = [StaffOnly]

    @extend_schema(responses=inline_serializer(name="AdminSummary", fields={
        "users": serializers.IntegerField(), "cards": serializers.IntegerField(),
        "transactions": serializers.IntegerField(), "statuses": serializers.ListField(),
        "successful_total": serializers.DecimalField(max_digits=12, decimal_places=2),
        "daily": serializers.ListField(),
    }))
    def get(self, request):
        successful = Transaction.objects.filter(status=Transaction.Status.SUCCESS)
        daily = list(successful.filter(created_at__gte=timezone.now() - timedelta(days=30))
                     .annotate(day=TruncDate("created_at")).values("day")
                     .annotate(count=Count("id"), total=Sum("amount")).order_by("day"))
        return Response({"users": User.objects.count(), "cards": Card.objects.count(),
                         "transactions": Transaction.objects.count(),
                         "statuses": list(Transaction.objects.values("status").annotate(count=Count("id")).order_by("status")),
                         "successful_total": successful.aggregate(total=Sum("amount"))["total"] or 0,
                         "daily": daily})


class ExportView(APIView):
    permission_classes = [StaffOnly]

    @extend_schema(responses={(200, "text/csv"): bytes})
    def get(self, request):
        queryset = filtered_transactions(Transaction.objects.select_related("user"), request.query_params)
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="transactions.csv"'
        writer = csv.writer(response)
        writer.writerow(["reference", "user_id", "card_last_four", "amount", "currency", "status", "created_at"])
        for payment in queryset.iterator():
            writer.writerow([payment.reference, payment.user_id, payment.card_last_four, payment.amount,
                             payment.currency, payment.status, payment.created_at.isoformat()])
        AdminLog.objects.create(admin_user=request.user, action="export_transactions", target_type="transaction",
                                target_id="all", metadata={"filter_fields": [k for k in request.query_params if k in
                                                {"status", "date_from", "date_to", "amount_min", "amount_max"}]})
        return response


class AdminLogListView(generics.ListAPIView):
    permission_classes = [StaffOnly]
    queryset = AdminLog.objects.order_by("-timestamp")
    class LogSerializer(serializers.ModelSerializer):
        class Meta:
            model = AdminLog
            fields = ("id", "admin_user_id", "action", "target_type", "target_id", "metadata", "timestamp")

    serializer_class = LogSerializer