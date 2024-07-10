from pydantic import BaseModel, Field, field_validator
from typing_extensions import Annotated

from config import (
    MAX_COOKING_TIME,
    MAX_FIELD_LENGTH,
    MAX_INGREDIENT_AMOUNT,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT
)


class Ingredients(BaseModel):
    id: Annotated[int, Field(ge=1)]
    amount: Annotated[
        int, Field(ge=MIN_INGREDIENT_AMOUNT, le=MAX_INGREDIENT_AMOUNT)
    ]

    class Config:
        extra = "allow"


class RecipeCreate(BaseModel):
    ingredients: list[Ingredients]
    tags: list[Annotated[int, Field(ge=1)]]
    text: str
    image: str
    name: Annotated[str, Field(max_length=MAX_FIELD_LENGTH)]
    cooking_time: Annotated[
        int, Field(ge=MIN_COOKING_TIME, le=MAX_COOKING_TIME)
    ]

    @field_validator("tags")
    @classmethod
    def check_tags(cls, value):
        if not value:
            raise ValueError("Tags can't be empty")
        return value

    @field_validator("ingredients")
    @classmethod
    def check_ingredients(cls, value):
        if not value:
            raise ValueError("Ingredients can't be empty")
        return value
