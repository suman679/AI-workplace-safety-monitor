import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db
from app.models.user import Role, User

bearer = HTTPBearer(auto_error=False)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer), db: Session = Depends(get_db)
) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication expired or invalid")
    if creds is None:
        raise unauthorized
    try:
        payload = decode_token(creds.credentials, "access")
        user_id = uuid.UUID(payload["sub"])
    except (jwt.PyJWTError, ValueError, KeyError):
        raise unauthorized
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise unauthorized
    return user


def require_roles(*roles: Role):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles and user.role != Role.SUPER_ADMIN:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission for this action")
        return user

    return checker


def company_id_of(user: User) -> uuid.UUID:
    if user.company_id is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Your account is not linked to a company")
    return user.company_id


def get_owned(db: Session, model, obj_id: uuid.UUID, company_id: uuid.UUID):
    """Fetch a company-scoped row; another company's rows look like they don't exist."""
    obj = db.get(model, obj_id)
    if obj is None or obj.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__} not found")
    return obj


WRITERS = (Role.COMPANY_ADMIN, Role.SAFETY_MANAGER)
ADMINS = (Role.COMPANY_ADMIN,)
