from typing import Any, Optional, Sequence

from sqlalchemy import func, insert, delete, Exists
from sqlalchemy.orm import selectinload
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.recipes import (
    Ingredient, Recipe, RecipeIngredient, Tag, favorite, cart
)


def set_ingredients(
    ingredients_list: list[dict[str, int]], recipe_id: int
) -> list[RecipeIngredient]:
    recipe_ingredient = [
        RecipeIngredient(
            recipe_id=recipe_id,
            ingredient_id=ingredient.get("id"),
            amount=ingredient.get("amount")
        )
        for ingredient in ingredients_list
    ]

    return recipe_ingredient


def get_favorite_recipes_query(user_id) -> Exists:
    query = select(favorite).filter(
        favorite.c.user_id == user_id,
        favorite.c.recipe_id == Recipe.id
    ).exists()
    return query


def get_on_cart_recipes_query(user_id) -> Exists:
    query = select(favorite).filter(
        cart.c.user_id == user_id,
        cart.c.recipe_id == Recipe.id
    ).exists()
    return query


async def get_recipes_with_filters(
        session: AsyncSession,
        is_favorited: bool,
        is_in_shopping_cart: bool,
        author_id: Optional[int],
        tags: Optional[list[str]],
        current_user_id: Optional[int],
        skip: int = 0,
        limit: int = 10,
        filtered: bool = False
) -> Sequence[Recipe]:
    query = select(Recipe).options(
        selectinload(Recipe.tags),
        selectinload(Recipe.author),
        selectinload(Recipe.ingredient_associations),
        selectinload(Recipe.ingredients),
        selectinload(Recipe.user_favorite),
        selectinload(Recipe.user_in_cart)
        ).offset(skip).limit(limit)

    if filtered:
        if is_favorited:
            query = query.filter(get_favorite_recipes_query(current_user_id))

        if is_in_shopping_cart:
            query = query.filter(get_on_cart_recipes_query(current_user_id))

        if author_id:
            query = query.filter(Recipe.author_id == author_id)

        if tags:
            query = query.join(Recipe.tags).filter(Tag.slug.in_(tags))

    result = await session.execute(query)
    return result.scalars().all()


async def count_recipes_with_filters(
        session: AsyncSession,
        is_favorited: bool,
        is_in_shopping_cart: bool,
        author_id: Optional[int],
        tags: Optional[list[str]],
        current_user_id: Optional[int],
        filtered: bool = False
) -> int:
    query = select(func.count(Recipe.id))

    if filtered:
        if is_favorited:
            query = query.filter(get_favorite_recipes_query(current_user_id))

        if is_in_shopping_cart:
            query = query.filter(get_on_cart_recipes_query(current_user_id))

        if author_id:
            query = query.filter(Recipe.author_id == author_id)

        if tags:
            query = query.join(Recipe.tags).filter(Tag.slug.in_(tags))

    result = await session.execute(query)
    return result.scalar_one()


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

    recipe_ingredient_data = set_ingredients(ingredients_list, recipe.id)
    session.add_all(recipe_ingredient_data)

    await session.commit()
    await session.refresh(recipe, attribute_names=["tags", "author"])

    return recipe


async def update_recipe_model(
    session: AsyncSession,
    recipe_model: Recipe,
    recipe_data: dict[str, Any],
    tag_models: Sequence[Tag],
    ingredients_list: list[dict[str, int]]
) -> Recipe:
    recipe_model.text = recipe_data.get("text")
    recipe_model.name = recipe_data.get("name")
    recipe_model.cooking_time = recipe_data.get("cooking_time")
    if recipe_data.get("image"):
        recipe_model.image = recipe_data.get("image")

    recipe_model.tags.clear()
    recipe_model.tags.extend(tag_models)
    await session.flush()

    recipe_model.ingredient_associations.clear()
    recipe_ingredient_data = set_ingredients(ingredients_list, recipe_model.id)
    session.add_all(recipe_ingredient_data)

    await session.commit()
    await session.refresh(
        recipe_model, attribute_names=[
            "tags", "author"
            ]
    )

    return recipe_model


async def delete_recipe_model(session: AsyncSession, recipe_model: Recipe):
    await session.delete(recipe_model)
    await session.commit()
    return True


async def get_recipe_by_user_id_and_name(
    session: AsyncSession, recipe_name: str, user_id: int
) -> Optional[Recipe]:
    query = select(Recipe).where(
        Recipe.author_id == user_id, Recipe.name == recipe_name
    )
    result = await session.execute(query)
    return result.scalars().first()


async def get_recipe_by_id(
        session: AsyncSession, recipe_id: int
) -> Optional[Recipe]:
    query = select(Recipe).filter_by(id=recipe_id)
    result = await session.execute(query)
    return result.scalars().first()


async def get_recipe_by_id_with_author_tags(
        session: AsyncSession, recipe_id: int
) -> Optional[Recipe]:
    query = select(Recipe).filter_by(id=recipe_id).options(
        selectinload(Recipe.author),
        selectinload(Recipe.tags)
    )
    result = await session.execute(query)
    return result.scalars().first()


async def get_recipe_by_id_with_author_tags_ingredients(
        session: AsyncSession, recipe_id: int
) -> Optional[Recipe]:
    query = select(Recipe).filter_by(id=recipe_id).options(
        selectinload(Recipe.author),
        selectinload(Recipe.tags),
        selectinload(Recipe.ingredient_associations)
    )
    result = await session.execute(query)
    return result.scalars().first()


async def recipe_exists_in_favorites(
        session: AsyncSession, recipe_id: int, user_id: int
) -> bool:
    query = select(favorite).where(
        favorite.c.recipe_id == recipe_id,
        favorite.c.user_id == user_id
    )
    result = await session.execute(query)
    subscription_row = result.fetchone()
    return subscription_row is not None


async def add_recipe_to_favorite(
        session: AsyncSession, recipe_id: int, user_id: int
) -> bool:
    stmt = insert(favorite).values(
        recipe_id=recipe_id, user_id=user_id
    )
    await session.execute(stmt)
    await session.commit()
    return True


async def delete_recipe_from_favorite(
        session: AsyncSession, recipe_id: int, user_id: int
) -> bool:
    stmt = delete(favorite).where(
        favorite.c.recipe_id == recipe_id,
        favorite.c.user_id == user_id
    )
    await session.execute(stmt)
    await session.commit()
    return True


async def recipe_exists_in_cart(
        session: AsyncSession, recipe_id: int, user_id: int
) -> bool:
    query = select(cart).where(
        cart.c.recipe_id == recipe_id,
        cart.c.user_id == user_id
    )
    result = await session.execute(query)
    subscription_row = result.fetchone()
    return subscription_row is not None


async def add_recipe_to_cart(
        session: AsyncSession, recipe_id: int, user_id: int
) -> bool:
    stmt = insert(cart).values(
        recipe_id=recipe_id, user_id=user_id
    )
    await session.execute(stmt)
    await session.commit()
    return True


async def delete_recipe_from_cart(
        session: AsyncSession, recipe_id: int, user_id: int
) -> bool:
    stmt = delete(cart).where(
        cart.c.recipe_id == recipe_id,
        cart.c.user_id == user_id
    )
    await session.execute(stmt)
    await session.commit()
    return True


async def get_ingredients_in_user_cart(
    session: AsyncSession, user_id: int
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Ingredient.name,
            Ingredient.measurement_unit,
            func.sum(RecipeIngredient.amount).label("total_amount")
        )
        .join(
            RecipeIngredient, Ingredient.id == RecipeIngredient.ingredient_id
        )
        .join(cart, cart.c.recipe_id == RecipeIngredient.recipe_id)
        .where(cart.c.user_id == user_id)
        .group_by(Ingredient.name, Ingredient.measurement_unit)
    )

    result = await session.execute(stmt)
    ingredients = result.all()

    return [
        {
            "name": name,
            "measurement_unit": measurement_unit,
            "amount": total_amount
        }
        for name, measurement_unit, total_amount in ingredients
    ]
