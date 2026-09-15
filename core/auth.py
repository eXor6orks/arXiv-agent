import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY n'est pas défini. Ajoute-le dans ton .env "
        "(ex: JWT_SECRET_KEY=une-longue-chaine-aleatoire)."
    )

ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 12


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Retourne le username si le token est valide, lève jwt.PyJWTError sinon."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload["sub"]
