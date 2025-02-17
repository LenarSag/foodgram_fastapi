from typing import Optional, Sequence

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.recipes import Tag


async def get_all_tags(session: AsyncSession) -> Sequence[Tag]:
    query = select(Tag)
    result = await session.execute(query)
    return result.scalars().all()


async def get_tag_by_id(
    session: AsyncSession, tag_id: int
) -> Optional[Tag]:
    query = select(Tag).filter_by(id=tag_id)
    result = await session.execute(query)
    return result.scalars().first()


async def tags_exists(
    session: AsyncSession, tags: list[int]
) -> Sequence[Tag]:
    query = select(Tag).filter(Tag.id.in_(tags))
    result = await session.execute(query)
    existing_tags = result.scalars().all()
    return existing_tags
