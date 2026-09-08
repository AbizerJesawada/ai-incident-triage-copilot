import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash


JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()


def get_jwt_secret_key() -> str:
    secret_key = os.getenv("JWT_SECRET_KEY")

    if not secret_key:
        raise RuntimeError(
            "JWT_SECRET_KEY must be configured.",
        )

    return secret_key


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    password_hash_value: str,
) -> bool:
    return password_hash.verify(
        password,
        password_hash_value,
    )


def create_access_token(
    user_id: UUID,
    role: str,
) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES,
    )

    return jwt.encode(
        {
            "sub": str(user_id),
            "role": role,
            "exp": expires_at,
        },
        get_jwt_secret_key(),
        algorithm=JWT_ALGORITHM,
    )


def read_access_token(token: str) -> dict[str, str]:
    try:
        payload = jwt.decode(
            token,
            get_jwt_secret_key(),
            algorithms=[JWT_ALGORITHM],
        )
    except InvalidTokenError as error:
        raise ValueError("Invalid or expired login token.") from error

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id or role not in {"user", "engineer"}:
        raise ValueError("Invalid login token data.")

    return {
        "user_id": str(user_id),
        "role": role,
    }