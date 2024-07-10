from typing import Optional
from fastapi import APIRouter, HTTPException, Request, Query, status, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import DEFAULT_PAGE_NUMBER, MAX_OBJ_PER_PAGE, MIN_PAGE_NUM, OBJ_PER_PAGE, RECIPE_DIRECTORY
from crud.ingredient_repository import get_ingredients_details, ingredients_exists
from crud.recipes_repository import check_recipe_exists, create_recipe, get_all_recipes
from crud.tag_repository import tags_exists
from crud.user_repository import get_user_by_id
from db.database import get_session


from schemas.ingredient_schema import IngredientInRecipe
from schemas.recipe_schema import RecipeCreate, RecipeDB
from schemas.user_schema import UserAuth
from security.security import get_user_from_token, get_user_from_token_custom
from utils.save_base64 import save_image_from_base64
from utils.validators import check_tags, check_ingredients


recipesrouter = APIRouter()


@recipesrouter.get("/")
async def get_recipes(
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token_custom),
    page: int = Query(DEFAULT_PAGE_NUMBER, ge=MIN_PAGE_NUM),
    size: int = Query(OBJ_PER_PAGE, le=MAX_OBJ_PER_PAGE),
    is_favorited: Optional[int] = Query(None),
    is_in_shopping_cart: Optional[int] = Query(None),
    author_id: Optional[int] = Query(None),
    tags: Optional[list[str]] = Query(None)

):
    pass


@recipesrouter.post("/", response_class=JSONResponse)
async def create_new_recipe(
    request: Request,
    new_recipe: RecipeCreate,
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token)
):
    recipe_exists = await check_recipe_exists(
        session, new_recipe.name, current_user.id
    )
    if recipe_exists:
        raise HTTPException(
            detail="You can't create recipes with the same name",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    if new_recipe.image.startswith("data:image/png;base64,"):
        base64_str = new_recipe.image.split(",", 1)[1]
    else:
        raise HTTPException(
            detail="Field image can't be empty",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    file_path = save_image_from_base64(base64_str, RECIPE_DIRECTORY)
    base_url = str(request.url.scheme) + "://" + str(request.url.netloc)

    recipe_data = new_recipe.model_dump()
    recipe_data["author_id"] = current_user.id
    recipe_data["image"] = base_url + "/" + file_path

    ingredients = recipe_data.pop("ingredients")
    validated_ingredients = await check_ingredients(session, ingredients)

    tags = recipe_data.pop("tags")
    validated_tags = await check_tags(session, tags)

    new_recipe = await create_recipe(
        session, recipe_data, validated_tags, validated_ingredients
    )

    ingredients_list_with_amount = await get_ingredients_details(
        session, new_recipe.id
    )
    serialized_ingredients = [
        IngredientInRecipe(
            id=ingredient.id,
            name=ingredient.name,
            measurement_unit=ingredient.measurement_unit,
            amount=ingredient.amount
        )
        for ingredient in ingredients_list_with_amount
    ]

    serialized_recipe = RecipeDB(
        id=new_recipe.id,
        tags=new_recipe.tags,
        author=new_recipe.author,
        ingredients=serialized_ingredients,
        is_favorited=False,
        is_in_shopping_cart=False,
        name=new_recipe.name,
        image=new_recipe.image,
        text=new_recipe.text,
        cooking_time=new_recipe.cooking_time
    )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=serialized_recipe.model_dump()
    )
