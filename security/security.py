from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi.security import OAuth2PasswordBearer
from fastapi import HTTPException, status, Depends
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

import config as config
from crud.user_repository import get_user_by_email
from models.user import User
from schemas.user_schema import UserAuth
from security.pwd_crypt import verify_password


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def authenticate_user(
    session: AsyncSession, email: EmailStr, plain_password: str
) -> Optional[User]:
    user = await get_user_by_email(session, email)
    if not user or not verify_password(plain_password, user.password):
        return None
    return user


def create_access_token(user: User) -> str:
    to_encode = {"sub": user.id}
    expire = datetime.now() + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm=config.ALGORITHM)
    return encoded_jwt


def get_user_from_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
        return UserAuth(
            id=int(payload.get("sub")),
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
