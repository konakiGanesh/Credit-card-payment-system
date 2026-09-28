import asyncio
import os
from datetime import date

import httpx
import pytest
from django.contrib.auth import get_user_model
from django.db import connections
from fastapi.testclient import TestClient
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

os.environ.setdefault("JWT_SIGNING_KEY", "test-jwt-signing-key-at-least-16")
os.environ.setdefault("JWT_ISSUER", "credit-card-django")
os.environ.setdefault("JWT_AUDIENCE", "credit-card-services")
os.environ.setdefault("SERVICE_API_KEY", "test-service-key-at-least-16")

from app.main import app
from app.services import payments
from cards.models import Card
from transactions.models import Transaction


@pytest.mark.django_db(transaction=True)
def test_fastapi_to_django_pending_success_failure_and_owner(monkeypatch):
    user = get_user_model().objects.create_user(username="payer", email="payer@example.test", password="Long-Passphrase-485!")
    other = get_user_model().objects.create_user(username="outsider", email="outsider@example.test", password="Long-Passphrase-485!")
    card = Card.objects.create(user=user, card_type="credit", cardholder_name="Payer", card_brand="Visa",
                               last_four="4242", expiry_month=12, expiry_year=date.today().year + 1)
    original = httpx.AsyncClient
    observations = []

    async def handler(request):
        def django_request():
            try:
                client = APIClient(HTTP_X_SERVICE_KEY=request.headers["X-Service-Key"])
                response = client.generic("POST", request.url.path, data=request.content, content_type="application/json")
                return response.status_code, response.content
            finally:
                connections.close_all()

        code, body = await asyncio.to_thread(django_request)
        observations.append((request.url.path, code))
        return httpx.Response(code, content=body, headers={"content-type": "application/json"})

    def mock_client(*args, **kwargs):
        return original(*args, transport=httpx.MockTransport(handler), **kwargs)

    monkeypatch.setattr(payments.httpx, "AsyncClient", mock_client)
    client = TestClient(app)
    token = str(RefreshToken.for_user(user).access_token)
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "payment-1"}
    first = client.post("/payments", headers=headers, json={"card_id": card.pk, "amount": "25.00"})
    assert first.status_code == 201 and first.json()["status"] == "SUCCESS"
    assert [row["status"] for row in Transaction.objects.values("status")] == ["SUCCESS"]
    assert observations[:2] == [("/internal/payments/", 201), (f"/internal/payments/{first.json()['reference']}/", 200)]
    assert client.post("/payments", headers=headers, json={"card_id": card.pk, "amount": "25.00"}).status_code == 200
    assert Transaction.objects.count() == 1
    failed = client.post("/payments", headers={**headers, "Idempotency-Key": "payment-2"},
                         json={"card_id": card.pk, "amount": "1001.00"})
    assert failed.status_code == 201 and failed.json()["status"] == "FAILED"
    foreign = client.post("/payments", headers={"Authorization": f"Bearer {RefreshToken.for_user(other).access_token}"},
                          json={"card_id": card.pk, "amount": "1.00"})
    assert foreign.status_code == 404
    assert Transaction.objects.count() == 2