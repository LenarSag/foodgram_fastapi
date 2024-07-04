from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession


from schemas.user_schema import UserBase, UserCreate
from db.database import get_session
from crud.user_repository import (
    check_username_and_email,
    create_user
)
from security.pwd_crypt import get_hashed_password


usersrouter = APIRouter()


@usersrouter.post("/", response_model=UserBase)
async def signup_and_get_confirmation_code(
    new_user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    user = await check_username_and_email(
        session, new_user_data.username, new_user_data.email
    )
    if user:
        if user.username == new_user_data.username:
            raise HTTPException(
                detail="Username already taken",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if user.email == new_user_data.email:
            raise HTTPException(
                detail="Email already registered",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    hashed_password = get_hashed_password(new_user_data.password)
    new_user_data.password = hashed_password

    new_user = await create_user(session, new_user_data) #, hashed_password)
    return new_user