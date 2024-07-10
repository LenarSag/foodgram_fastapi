from typing import Sequence
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.ingredient_repository import ingredients_exists
from crud.tag_repository import tags_exists
from models.recipes import Tag


async def check_ingredients(
    session: AsyncSession, ingredients: list[dict[str, int]]
) -> list[dict[str, int]]:
    ingredients_ids = [int(ingredient.get("id")) for ingredient in ingredients]
    existing_ingredients = await ingredients_exists(session, ingredients_ids)
    missing_ingredients = set(ingredients_ids) - set(existing_ingredients)
    if missing_ingredients:
        raise HTTPException(
            detail=f"Ingredients {missing_ingredients} don't exist",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    return ingredients


async def check_tags(session: AsyncSession, tags: list) -> Sequence[Tag]:
    existing_tags = await tags_exists(session, tags)
    existing_tags_ids = [tag.id for tag in existing_tags]
    missing_tags = set(tags) - set(existing_tags_ids)
    if missing_tags:
        raise HTTPException(
            detail=f"Tags {missing_tags} don't exist",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    return existing_tags
