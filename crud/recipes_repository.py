from typing import Any, Sequence

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.recipes import Recipe, RecipeIngredient, Tag


async def get_all_recipes(session: AsyncSession) -> Sequence[Recipe]:
    query = select(Recipe)
    result = await session.execute(query)
    return result.scalars().all()


async def create_recipe(
    session: AsyncSession,
    recipe_data: dict[str, Any],
    tag_models: Sequence[Tag],
    ingredients_list: list[dict[str, int]]
) -> Recipe:
    recipe = Recipe(**recipe_data)
    session.add(recipe)
    recipe.tags.extend(tag_models)
    await session.flush()

    recipe_ingredient = [
        RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient.get("id"),
            amount=ingredient.get("amount")
        )
        for ingredient in ingredients_list
    ]
    session.add_all(recipe_ingredient)
    await session.commit()
    await session.refresh(recipe, attribute_names=["tags", "author"])

    return recipe


async def check_recipe_exists(
    session: AsyncSession, recipe_name: str, user_id: int
) -> bool:
    query = select(Recipe).where(
        Recipe.author_id == user_id, Recipe.name == recipe_name
    )
    result = await session.execute(query)
    recipe = result.scalars().first()
    return recipe is not None
