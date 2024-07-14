from typing import Optional, Sequence

from pydantic import EmailStr
from sqlalchemy import func, insert, delete
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


async def get_user_by_id_with_followers(
        session: AsyncSession, id: int
) -> Optional[User]:
    query = select(User).filter_by(id=id).options(selectinload(User.following))
    result = await session.execute(query)
    return result.scalars().first()


async def get_user_by_id_with_recipes(
    session: AsyncSession, id: int
) -> Optional[User]:
    query = select(User).filter_by(id=id).options(selectinload(User.recipes))
    result = await session.execute(query)
    return result.scalars().first()


async def get_user_with_followers_cart_favorites(
    session: AsyncSession, id: int
) -> Optional[User]:
    query = select(User).filter_by(id=id).options(
        selectinload(User.follower),
        selectinload(User.in_cart_recipes),
        selectinload(User.favorite_recipes)
        )
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


async def get_all_users_with_followers(
        session: AsyncSession, skip: int = 0, limit: int = 10
) -> Sequence[User]:
    query = (
        select(User).offset(skip).
        limit(limit).options(selectinload(User.following))
    )
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
        .options(selectinload(User.recipes))
    )
    result = await session.execute(query)
    following_users = result.scalars().all()
    return following_users


async def subscription_exists(
        session: AsyncSession, following_id: int, follower_id: int
) -> bool:
    query = select(subscription).where(
        subscription.c.following_id == following_id,
        subscription.c.follower_id == follower_id
    )
    result = await session.execute(query)
    subscription_row = result.fetchone()
    return subscription_row is not None


async def add_subscription(
        session: AsyncSession, following_id: int, follower_id: int
) -> bool:
    stmt = insert(subscription).values(
        following_id=following_id, follower_id=follower_id
    )
    await session.execute(stmt)
    await session.commit()
    return True


async def delete_subscription(
        session: AsyncSession, following_id: int, follower_id: int
) -> bool:
    stmt = delete(subscription).where(
        subscription.c.following_id == following_id,
        subscription.c.follower_id == follower_id
    )
    await session.execute(stmt)
    await session.commit()
    return True


async def add_avatar_to_field(
        session: AsyncSession, user_id: int, file_path: str
) -> Optional[User]:
    query = select(User).filter_by(id=user_id)
    result = await session.execute(query)
    user_model = result.scalars().first()
    user_model.avatar = file_path
    await session.commit()
    await session.refresh(user_model)
    return user_model


async def delete_avatar_field(session: AsyncSession, user_id: int) -> bool:
    query = select(User).filter_by(id=user_id)
    result = await session.execute(query)
    user_model = result.scalars().first()
    user_model.avatar = None
    await session.commit()
    return True


async def change_password(
        session: AsyncSession, user: User, new_password
) -> bool:
    user.password = new_password
    await session.commit()
    return True
