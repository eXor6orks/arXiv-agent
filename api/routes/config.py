from fastapi import APIRouter, Depends, HTTPException

from api.deps import require_admin
from api.schemas import ConfigUpdateRequest
from config.config import DEFAULTS
from core.db import get_all_config, set_config_value

router = APIRouter(prefix="/config", tags=["config"])


@router.get("")
def read_config(user: dict = Depends(require_admin)):
    return get_all_config()


@router.put("/{key}")
def update_config(key: str, payload: ConfigUpdateRequest, user: dict = Depends(require_admin)):
    if key not in DEFAULTS:
        raise HTTPException(status_code=404, detail=f"Clé de config inconnue: {key}")
    set_config_value(key, payload.value)
    return {"key": key, "value": payload.value}
