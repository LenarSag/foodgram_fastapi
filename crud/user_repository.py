from typing import Optional, Sequence

from pydantic import EmailStr
from sqlalchemy import func
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import or_

from models.user import User, subscription
from schemas.user_schema import UserCreate


async def create_user(
    session: AsyncSession,
    user_data: UserCreate
) -> User:
    db_user = User(**user_data.model_dump())
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
    query = select(User).where(or_(
        User.username == username, User.email == email
    ))
    result = await session.execute(query)
    return result.scalars().first()


async def get_all_users(
        session: AsyncSession, skip: int = 0, limit: int = 10
) -> Sequence[User]:
    query = select(User).offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def count_users(session: AsyncSession) -> int:
    query = select(func.count()).select_from(User)
    result = await session.execute(query)
    return result.scalar_one()


async def count_following_users(
        session: AsyncSession, current_user_id: int
) -> int:
    query = (
        select(func.count())
        .select_from(subscription)
        .filter(subscription.c.follower_id == current_user_id)
    )
    result = await session.execute(query)
    return result.scalar_one()


async def get_following_users(
        session: AsyncSession, current_user_id: int
) -> Sequence[User]:
    query = (
        select(User)
        .join(subscription, User.id == subscription.c.following_id)
        .filter(subscription.c.follower_id == current_user_id)
    )
    result = await session.execute(query)
    following_users = result.scalars().all()
    return following_users
