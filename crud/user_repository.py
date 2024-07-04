from typing import Optional, Union, Sequence

from pydantic import EmailStr
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import or_

from models.user import User
from schemas.user_schema import UserCreate, UserBase


async def create_user(
    session: AsyncSession,
    user_data: UserCreate
) -> User:
    db_user = User(**user_data.model_dump())  #, password=hashed_password)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_user_by_id(session: AsyncSession, id: int) -> Optional[User]:
    query = select(User).filter_by(id=id)
    result = await session.execute(query)
    return result.scalars().first()


async def get_user_by_email(
        session: AsyncSession, email: EmailStr
) -> Optional[User]:
    query = select(User).filter_by(email=email)
    result = await session.execute(query)
    return result.scalars().first()


async def check_username_and_email(
        session: AsyncSession, username: str, email: EmailStr
) -> Optional[User]:
    query = select(User).where(or_(User.username == username, User.email == email))
    result = await session.execute(query)
    return result.scalars().first()

    # subquery = select(
    #     exists().where(or_(User.username == username, User.email == email))
    # )
    # result = await session.execute(subquery)
    # return result.scalar()
