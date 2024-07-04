from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession


from schemas.user_schema import UserBase, UserCreate, UserGetToken
from db.database import get_session
from crud.user_repository import (
    check_username_and_email,
    create_user,

    get_user_by_email,

)

from security.security import authenticate_user, create_access_token



loginroute = APIRouter()


@loginroute.post("/login/")
async def login_for_access_token(
    user_data: UserGetToken,
    session: AsyncSession = Depends(get_session),
):
    email = user_data.email
    password = user_data.password

    user = await authenticate_user(session, email, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user)
    return {"access_token": access_token, "token_type": "bearer"}
