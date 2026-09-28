import re
from datetime import date

from rest_framework import serializers

from .models import Card


def luhn_valid(number: str) -> bool:
    digits = [int(char) for char in number]
    checksum = 0
    for index, digit in enumerate(reversed(digits)):
        if index % 2:
            digit *= 2
            if digit > 9:
                digit -= 9
        checksum += digit
    return checksum % 10 == 0


class CardSerializer(serializers.ModelSerializer):
    number = serializers.CharField(write_only=True, trim_whitespace=False, style={"input_type": "password"})
    masked_number = serializers.CharField(read_only=True)

    class Meta:
        model = Card
        fields = ("id", "card_type", "cardholder_name", "card_brand", "last_four", "masked_number",
                  "expiry_month", "expiry_year", "created_at", "number")
        read_only_fields = ("id", "card_brand", "last_four", "masked_number", "created_at")

    def validate_cardholder_name(self, value):
        if not re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", value):
            raise serializers.ValidationError("Use letters and punctuation only for the cardholder name.")
        return value

    def validate(self, attrs):
        if self.instance is None and set(self.initial_data) - {"card_type", "cardholder_name", "expiry_month", "expiry_year", "number"}:
            raise serializers.ValidationError("Unsupported card field.")
        number = attrs.get("number", "")
        if not re.fullmatch(r"[0-9]{13,19}", number) or not luhn_valid(number):
            raise serializers.ValidationError({"number": "Invalid test card number."})
        today = date.today()
        month, year = attrs["expiry_month"], attrs["expiry_year"]
        if not 1 <= month <= 12 or not today.year <= year <= today.year + 20 or (year, month) < (today.year, today.month):
            raise serializers.ValidationError({"expiry_month": "Expiry must be a valid future month."})
        return attrs

    def create(self, validated_data):
        number = validated_data.pop("number")
        validated_data["last_four"] = number[-4:]
        validated_data["card_brand"] = "Visa" if number.startswith("4") else "Mastercard" if number.startswith(("51", "52", "53", "54", "55")) else "Other"
        return Card.objects.create(user=self.context["request"].user, **validated_data)