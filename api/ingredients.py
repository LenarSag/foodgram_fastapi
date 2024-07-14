from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from crud.ingredient_repository import (
    get_all_ingredients, get_ingredient_by_id
)
from db.database import get_session
from schemas.ingredient_schema import IngredientDB


ingredientsrouter = APIRouter()


@ingredientsrouter.get("/", response_model=list[IngredientDB])
async def get_ingredients(
    name: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    ingredients = await get_all_ingredients(session, name)
    return ingredients


@ingredientsrouter.get("/{ingredient_id}", response_model=IngredientDB)
async def get_ingredient(
    ingredient_id: int, session: AsyncSession = Depends(get_session)
):
    ingredient = await get_ingredient_by_id(session, ingredient_id)
    if not ingredient:
        raise HTTPException(
            detail="Ingredient not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return ingredient
