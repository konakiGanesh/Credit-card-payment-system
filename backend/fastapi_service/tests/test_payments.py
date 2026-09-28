import os
from datetime import timedelta
from decimal import Decimal

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("JWT_SIGNING_KEY", "test-jwt-signing-key-at-least-16")
os.environ.setdefault("JWT_ISSUER", "credit-card-django")
os.environ.setdefault("JWT_AUDIENCE", "credit-card-services")
os.environ.setdefault("SERVICE_API_KEY", "test-service-key-at-least-16")

from app.main import app
from app.services import payments


def access(user_id=42, token_type="access"):
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    return jwt.encode({"user_id": user_id, "token_type": token_type, "iat": now,
                       "exp": now + timedelta(minutes=15), "jti": "test", "iss": "credit-card-django",
                       "aud": "credit-card-services"}, os.environ["JWT_SIGNING_KEY"], algorithm="HS256")


def test_missing_bad_refresh_and_valid_jwt():
    client = TestClient(app)
    assert client.post("/payments", json={"card_id": 1, "amount": "1.00"}).status_code == 401
    for token in ["bad", access(token_type="refresh")]:
        assert client.post("/payments", headers={"Authorization": f"Bearer {token}"},
                           json={"card_id": 1, "amount": "1.00"}).status_code == 401


def test_reject_amounts_and_malformed():
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {access()}"}
    for payload in [{"card_id": 1, "amount": 0}, {"card_id": 1, "amount": -1},
                    {"card_id": 0, "amount": 1}, {"card_id": 1, "amount": "1.001"},
                    {"card_id": 1, "amount": 1, "cvv": "123"}]:
        assert client.post("/payments", headers=headers, json=payload).status_code == 422


def test_simulation_rule():
    assert payments.simulate(Decimal("1000.00")) == "SUCCESS"
    assert payments.simulate(Decimal("1000.01")) == "FAILED"


def test_success_failure_idempotent_and_unauthorized(monkeypatch):
    seen = []

    async def fake_call(config, path, payload):
        seen.append((path, payload))
        if path == "/internal/payments/":
            if payload["card_id"] == 99:
                from fastapi import HTTPException
                raise HTTPException(status_code=404, detail="Card not found.")
            return {"status": "PENDING", "reference": "abc", "amount": payload["amount"]}, 201
        return {"status": payload["status"], "reference": "abc"}, 200

    monkeypatch.setattr(payments, "call_django", fake_call)
    from app.core.config import Settings
    from app.schemas.payments import PaymentRequest
    import asyncio
    config = Settings()
    for amount, expected in [("2.00", "SUCCESS"), ("1001.00", "FAILED")]:
        result, status = asyncio.run(payments.process_payment(config, 42, PaymentRequest(card_id=1, amount=amount), "key"))
        assert result["status"] == expected and status == 201
        assert seen[-1][1]["user_id"] == 42
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        asyncio.run(payments.process_payment(config, 42, PaymentRequest(card_id=99, amount=1), "key"))
    assert exc.value.status_code == 404


def test_private_service_failure_is_sanitized(monkeypatch):
    async def unavailable(self, *args, **kwargs):
        raise httpx.ConnectError("database-secret")

    monkeypatch.setattr(httpx.AsyncClient, "post", unavailable)
    import asyncio
    from fastapi import HTTPException
    from app.core.config import Settings
    with pytest.raises(HTTPException) as exc:
        asyncio.run(payments.call_django(Settings(), "/internal/payments/", {}))
    assert exc.value.status_code == 503
    assert "database-secret" not in exc.value.detail