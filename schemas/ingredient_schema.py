from typing import Annotated

from pydantic import BaseModel, Field

from config import (
    MIN_INGREDIENT_AMOUNT,
    MAX_INGREDIENT_AMOUNT
)


class IngredientDB(BaseModel):
    id: int
    name: str
    measurement_unit: str

    class Config:
        from_attributes = True


class IngredientsRecipeCreate(BaseModel):
    id: Annotated[int, Field(ge=1)]
    amount: Annotated[
        int, Field(ge=MIN_INGREDIENT_AMOUNT, le=MAX_INGREDIENT_AMOUNT)
    ]

    class Config:
        extra = "allow"


class IngredientInRecipe(IngredientDB):
    amount: int
