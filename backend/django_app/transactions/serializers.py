from rest_framework import serializers

from .models import Transaction


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ("id", "reference", "card", "card_last_four", "amount", "currency", "status",
                  "failure_reason", "created_at", "updated_at")
        read_only_fields = fields


class TransactionFilterSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Transaction.Status.choices, required=False)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    amount_min = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False)
    amount_max = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0, required=False)

    def validate(self, attrs):
        if attrs.get("date_from") and attrs.get("date_to") and attrs["date_from"] > attrs["date_to"]:
            raise serializers.ValidationError("date_from must not exceed date_to.")
        if attrs.get("amount_min") is not None and attrs.get("amount_max") is not None and attrs["amount_min"] > attrs["amount_max"]:
            raise serializers.ValidationError("amount_min must not exceed amount_max.")
        return attrs


def filtered_transactions(queryset, params):
    serializer = TransactionFilterSerializer(data=params)
    serializer.is_valid(raise_exception=True)
    for key, value in serializer.validated_data.items():
        lookup = {"date_from": "created_at__date__gte", "date_to": "created_at__date__lte",
                  "amount_min": "amount__gte", "amount_max": "amount__lte"}.get(key, key)
        queryset = queryset.filter(**{lookup: value})
    return queryset.order_by("-created_at", "-id")