from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from sqlalchemy.orm import Session

from app.auth_service import read_access_token
from app.database import get_db
from app.models import User


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme,
    ),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login is required.",
        )

    try:
        token_data = read_access_token(credentials.credentials)
        user_id = UUID(token_data["user_id"])
    except (ValueError, TypeError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired login token.",
        ) from error

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account was not found.",
        )

    return user


def require_engineer(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "engineer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Engineer access is required.",
        )

    return current_user