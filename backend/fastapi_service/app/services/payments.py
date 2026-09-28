from decimal import Decimal

import httpx
from fastapi import HTTPException

from app.core.config import Settings
from app.schemas.payments import PaymentRequest


def simulate(amount: Decimal) -> str:
    """Documented, deterministic demo rule: amounts above USD 1000 decline."""
    return "FAILED" if amount > Decimal("1000.00") else "SUCCESS"


async def call_django(settings: Settings, path: str, payload: dict) -> tuple[dict, int]:
    try:
        async with httpx.AsyncClient(base_url=settings.django_internal_url, timeout=8.0, trust_env=False) as client:
            response = await client.post(path, json=payload, headers={"X-Service-Key": settings.service_api_key})
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Payment database unavailable.") from None
    if response.status_code not in (200, 201):
        if response.status_code in (400, 404, 409):
            # Internal endpoints return fixed, non-sensitive messages.
            raise HTTPException(status_code=response.status_code, detail=response.json().get("detail", "Payment rejected."))
        raise HTTPException(status_code=503, detail="Payment database unavailable.")
    return response.json(), response.status_code


async def process_payment(settings: Settings, user_id: int, payment: PaymentRequest, key: str) -> tuple[dict, int]:
    pending, created_status = await call_django(settings, "/internal/payments/", {
        "user_id": user_id, "card_id": payment.card_id, "amount": str(payment.amount),
        "currency": payment.currency, "idempotency_key": key,
    })
    if pending["status"] != "PENDING":
        return pending, 200
    final, _ = await call_django(settings, f"/internal/payments/{pending['reference']}/", {
        "user_id": user_id, "status": simulate(payment.amount),
    })
    return final, created_status