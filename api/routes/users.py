from fastapi import APIRouter, Depends, HTTPException

from api.deps import require_admin
from api.schemas import UserCreateRequest, UserResponse
from core.auth import hash_password
from core.db import create_user, delete_user, get_user, list_users

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def get_users(admin: dict = Depends(require_admin)):
    return list_users()


@router.post("", response_model=UserResponse)
def add_user(payload: UserCreateRequest, admin: dict = Depends(require_admin)):
    if get_user(payload.username) is not None:
        raise HTTPException(status_code=409, detail="Cet utilisateur existe déjà")
    create_user(payload.username, hash_password(payload.password), is_admin=payload.is_admin)
    return get_user(payload.username)


@router.delete("/{username}")
def remove_user(username: str, admin: dict = Depends(require_admin)):
    if username == admin["username"]:
        raise HTTPException(status_code=400, detail="Impossible de se supprimer soi-même")
    if not delete_user(username):
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return {"status": "deleted", "username": username}
