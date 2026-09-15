from fastapi import APIRouter, HTTPException, status

from api.schemas import LoginRequest, TokenResponse
from core.auth import create_access_token, verify_password
from core.db import get_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = get_user(payload.username)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
        )
    token = create_access_token(user["username"])
    return TokenResponse(access_token=token)
