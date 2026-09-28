from functools import lru_cache
from uuid import uuid4

import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import Settings
from app.schemas.payments import PaymentRequest, PaymentResponse
from app.services.payments import process_payment


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
app = FastAPI(title="Simulated Payment Processing API", version="1.0.0",
              description="Demo only: no real payment networks, credentials, CVV or PIN.")
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key"])
bearer = HTTPBearer()


def authenticated_user(credentials: HTTPAuthorizationCredentials = Depends(bearer),
                       config: Settings = Depends(get_settings)) -> int:
    try:
        claims = jwt.decode(credentials.credentials, config.jwt_signing_key, algorithms=["HS256"],
                            audience=config.jwt_audience, issuer=config.jwt_issuer,
                            options={"require": ["exp", "iat", "jti", "token_type", "user_id", "iss", "aud"]})
        raw_id = claims.get("user_id")
        if claims.get("token_type") != "access" or isinstance(raw_id, bool) or not isinstance(raw_id, (int, str)) or not str(raw_id).isdecimal() or int(raw_id) <= 0:
            raise ValueError
        return int(raw_id)
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired access token.") from None


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/payments", response_model=PaymentResponse, responses={401: {"description": "Invalid access token"},
           404: {"description": "Card not owned by user"}, 409: {"description": "Conflicting idempotency key"}}, tags=["payments"])
async def create_payment(payment: PaymentRequest, user_id: int = Depends(authenticated_user),
                         idempotency_key: str | None = Header(default=None, max_length=100),
                         config: Settings = Depends(get_settings)):
    if idempotency_key is not None and (not idempotency_key.strip() or len(idempotency_key) > 100):
        raise HTTPException(status_code=400, detail="Invalid Idempotency-Key.")
    result, response_status = await process_payment(config, user_id, payment, idempotency_key or str(uuid4()))
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=response_status, content=result)