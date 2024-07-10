from typing import Optional, Sequence

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.recipes import Ingredient


async def get_all_ingredients(session: AsyncSession) -> Sequence[Ingredient]:
    query = select(Ingredient)
    result = await session.execute(query)
    return result.scalars().all()


async def get_ingredient_by_id(
    session: AsyncSession, ingredient_id: int
) -> Optional[Ingredient]:
    query = select(Ingredient).filter_by(id=ingredient_id)
    result = await session.execute(query)
    return result.scalars().first()


async def ingredients_exists(
    session: AsyncSession, ingredients: list[int]
) -> Sequence[int]:
    query = select(Ingredient.id).filter(Ingredient.id.in_(ingredients))
    result = await session.execute(query)
    existing_ingredients = result.scalars().all()
    return existing_ingredients