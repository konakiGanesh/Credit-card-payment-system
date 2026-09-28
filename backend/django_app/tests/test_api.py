from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from admin_panel.models import AdminLog
from cards.models import Card
from transactions.models import Transaction

User = get_user_model()
pytestmark = pytest.mark.django_db
TEST_NUMBER = "4242424242424242"


@pytest.fixture
def user():
    return User.objects.create_user(username="alice", email="alice@example.test", password="Long-Passphrase-485!")


@pytest.fixture
def other():
    return User.objects.create_user(username="bob", email="bob@example.test", password="Long-Passphrase-485!")


@pytest.fixture
def admin():
    return User.objects.create_superuser(username="root", email="root@example.test", password="Long-Passphrase-485!")


@pytest.fixture
def client(user):
    api = APIClient()
    api.force_authenticate(user=user)
    return api


@pytest.fixture
def card(user):
    return Card.objects.create(user=user, card_type="credit", cardholder_name="Alice", card_brand="Visa",
                               last_four="4242", expiry_month=12, expiry_year=date.today().year + 2)


def test_register_and_password_hash():
    response = APIClient().post("/api/auth/register/", {"username": "new_user", "email": "new@example.test",
                                    "password": "Long-Passphrase-485!"})
    assert response.status_code == 201
    assert "password" not in response.data
    assert User.objects.get(username="new_user").check_password("Long-Passphrase-485!")
    assert not User.objects.get(username="new_user").is_staff


def test_login_refresh_logout_and_protected_route(user):
    anon = APIClient()
    assert anon.get("/api/cards/").status_code == 401
    assert anon.post("/api/auth/login/", {"username": "alice", "password": "wrong"}).status_code == 401
    tokens = anon.post("/api/auth/login/", {"username": "alice", "password": "Long-Passphrase-485!"}).data
    anon.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert anon.get("/api/auth/me/").data["role"] == "user"
    assert anon.post("/api/auth/token/refresh/", {"refresh": tokens["refresh"]}).status_code == 200
    assert anon.post("/api/auth/logout/", {"refresh": tokens["refresh"]}).status_code == 400  # rotated token blacklisted


def test_card_masking_secrecy_and_deletion(client, user):
    payload = {"number": TEST_NUMBER, "cardholder_name": "Alice", "card_type": "credit",
               "expiry_month": 12, "expiry_year": date.today().year + 2}
    assert client.post("/api/cards/", {**payload, "cvv": "123"}).status_code == 400
    response = client.post("/api/cards/", payload)
    assert response.status_code == 201
    assert response.data["masked_number"] == "**** **** **** 4242"
    assert TEST_NUMBER not in str(response.data)
    saved = Card.objects.get(user=user)
    assert not hasattr(saved, "number") and not hasattr(saved, "cvv")
    assert TEST_NUMBER not in str(saved.__dict__)
    assert client.get("/api/cards/").data["count"] == 1
    assert client.delete(f"/api/cards/{saved.pk}/").status_code == 204
    assert client.get("/api/cards/").data["count"] == 0


def test_card_isolation(client, other, card):
    foreign = Card.objects.create(user=other, card_type="debit", cardholder_name="Bob",
                                  card_brand="Visa", last_four="0002", expiry_month=12, expiry_year=2030)
    assert client.get("/api/cards/").data["count"] == 1
    assert client.delete(f"/api/cards/{foreign.pk}/").status_code == 404
    assert Card.objects.filter(pk=foreign.pk).exists()


def test_history_filters_isolation_and_detail(client, user, other, card):
    own = Transaction.objects.create(user=user, card=card, original_card_id=card.pk, card_last_four="4242", amount=Decimal("25.00"),
                                     status="SUCCESS", idempotency_key="one")
    Transaction.objects.create(user=other, card=None, original_card_id=999, card_last_four="0002", amount=Decimal("9.00"),
                               status="FAILED", idempotency_key="two")
    today = date.today().isoformat()
    response = client.get("/api/transactions/", {"status": "SUCCESS", "date_from": today,
                                                  "date_to": today, "amount_min": 20, "amount_max": 30})
    assert response.status_code == 200 and response.data["count"] == 1
    assert client.get("/api/transactions/", {"status": "FAILED"}).data["count"] == 0
    detail = client.get(f"/api/transactions/{own.pk}/")
    assert detail.status_code == 200 and detail.data["id"] == own.pk
    assert client.get("/api/transactions/", {"amount_min": "bogus"}).status_code == 400
    assert client.get("/api/transactions/", {"date_from": "2030-01-01", "date_to": "2020-01-01"}).status_code == 400


def test_internal_payment_pending_success_retry_and_conflict(client, user, card):
    service = APIClient(HTTP_X_SERVICE_KEY="test-service-key-at-least-16")
    payload = {"user_id": user.id, "card_id": card.id, "amount": "12.50", "currency": "USD", "idempotency_key": "abc"}
    assert APIClient().post("/internal/payments/", payload, format="json").status_code == 403
    first = service.post("/internal/payments/", payload, format="json")
    assert first.status_code == 201 and first.data["status"] == "PENDING"
    assert service.post("/internal/payments/", payload, format="json").status_code == 200
    assert service.post("/internal/payments/", {**payload, "amount": "13.00"}, format="json").status_code == 409
    path = f"/internal/payments/{first.data['reference']}/"
    assert service.post(path, {"user_id": user.id, "status": "SUCCESS"}, format="json").data["status"] == "SUCCESS"
    assert service.post(path, {"user_id": user.id, "status": "FAILED"}, format="json").status_code == 409
    card.delete()
    assert service.post("/internal/payments/", payload, format="json").data["status"] == "SUCCESS"
    assert Transaction.objects.count() == 1


def test_internal_rejects_invalid_card_amount_and_failure(other, user, card):
    service = APIClient(HTTP_X_SERVICE_KEY="test-service-key-at-least-16")
    base = {"user_id": other.id, "card_id": card.id, "amount": "1.00", "currency": "USD", "idempotency_key": "x"}
    assert service.post("/internal/payments/", base, format="json").status_code == 404
    assert service.post("/internal/payments/", [{"user_id": user.id}], format="json").status_code == 400
    for amount in ["0", "-1", "0.001", "NaN"]:
        assert service.post("/internal/payments/", {**base, "user_id": user.id, "amount": amount}, format="json").status_code == 400
    created = service.post("/internal/payments/", {**base, "user_id": user.id, "amount": "1001.00"}, format="json")
    assert created.data["status"] == "PENDING"
    final = service.post(f"/internal/payments/{created.data['reference']}/",
                         {"user_id": user.id, "status": "FAILED"}, format="json")
    assert final.data["status"] == "FAILED" and final.data["failure_reason"] == "Simulation declined"


def test_admin_permissions_export_logs_and_summary(client, admin, other, card):
    for path in ["users/", "cards/", "transactions/", "summary/", "logs/", "transactions/export/"]:
        assert client.get(f"/api/admin/{path}").status_code == 403
    api = APIClient()
    api.force_authenticate(user=admin)
    assert api.get("/api/admin/users/").data["count"] == 3
    assert api.get("/api/admin/cards/").data["count"] == 1
    assert api.get("/api/admin/summary/").data["cards"] == 1
    assert api.patch(f"/api/admin/users/{other.pk}/", {"is_active": False}).status_code == 200
    assert not User.objects.get(pk=other.pk).is_active
    assert api.get("/api/admin/transactions/export/").status_code == 200
    assert AdminLog.objects.count() == 2
    assert api.get("/api/admin/logs/").data["count"] == 2


def test_only_superuser_can_promote_staff(client, user, other, admin):
    user.is_staff = True
    user.save()
    assert client.patch(f"/api/admin/users/{other.pk}/", {"is_staff": True}).status_code == 400
    api = APIClient()
    api.force_authenticate(user=admin)
    assert api.patch(f"/api/admin/users/{other.pk}/", {"is_staff": True}).status_code == 200