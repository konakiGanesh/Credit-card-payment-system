from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PaymentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    card_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    currency: Literal["USD"] = "USD"


class PaymentResponse(BaseModel):
    reference: UUID
    card: int | None
    card_last_four: str
    amount: Decimal
    currency: str
    status: Literal["PENDING", "SUCCESS", "FAILED"]
    failure_reason: str
    created_at: datetime
    updated_at: datetime