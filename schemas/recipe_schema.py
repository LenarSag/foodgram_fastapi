from typing import Optional
from pydantic import BaseModel, Field, field_validator
from typing_extensions import Annotated

from config import (
    MAX_COOKING_TIME,
    MAX_FIELD_LENGTH,
    MIN_COOKING_TIME,
)
from schemas.ingredient_schema import IngredientInRecipe, IngredientsRecipeCreate
from schemas.tag_schema import TagDB
from schemas.user_schema import UserDB


class RecipeBase(BaseModel):
    ingredients: list[IngredientsRecipeCreate]
    tags: list[Annotated[int, Field(ge=1)]]
    text: str
    image: Optional[str] = None
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


class RecipeCreate(RecipeBase):
    image: str


class RecipeShort(BaseModel):
    id: int
    name: str
    image: str
    cooking_time: int


class RecipeDB(BaseModel):
    id: int
    tags: list[TagDB]
    author: UserDB
    ingredients: list[IngredientInRecipe]
    is_favorited: bool = False
    is_in_shopping_cart: bool = False
    name: str
    image: str
    text: str
    cooking_time: int
