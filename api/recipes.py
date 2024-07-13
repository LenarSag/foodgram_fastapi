from typing import Optional

from fastapi import (
    APIRouter, HTTPException, Request, Response, Query, status, Depends
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import (
    DEFAULT_PAGE_NUMBER,
    MAX_OBJ_PER_PAGE,
    MIN_PAGE_NUM,
    OBJ_PER_PAGE,
    RECIPE_DIRECTORY
)
from crud.ingredient_repository import get_ingredients_details
from crud.recipes_repository import (
    count_recipes_with_filters,
    create_recipe,
    delete_recipe_model,
    get_recipe_by_id,
    get_recipe_by_id_with_author_tags,
    get_recipe_by_id_with_author_tags_ingredients,
    get_recipe_by_user_id_and_name,
    get_recipes_with_filters,
    update_recipe_model
)
from crud.user_repository import get_user_with_followers_cart_favorites
from db.database import get_session
from schemas.ingredient_schema import IngredientInRecipe
from schemas.pagination_schema import PaginatedRecipes
from schemas.recipe_schema import RecipeBase, RecipeCreate, RecipeDB
from schemas.user_schema import UserAuth, UserDB
from security.security import get_user_from_token, get_user_from_token_custom
from utils.custom_pagination import get_prev_and_next_page
from utils.save_base64 import save_image_from_base64
from utils.validators import check_tags, check_ingredients


recipesrouter = APIRouter()


@recipesrouter.get("/")
async def get_recipes(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[UserAuth] = Depends(get_user_from_token_custom),
    is_favorited: Optional[int] = Query(None),
    is_in_shopping_cart: Optional[int] = Query(None),
    author_id: Optional[int] = Query(None),
    tags: Optional[list[str]] = Query(None),
    page: int = Query(DEFAULT_PAGE_NUMBER, ge=MIN_PAGE_NUM),
    size: int = Query(OBJ_PER_PAGE, le=MAX_OBJ_PER_PAGE)
):
    is_favorited = bool(is_favorited)
    is_in_shopping_cart = bool(is_in_shopping_cart)
    current_user_id = None

    if not current_user and (is_favorited or is_in_shopping_cart):
        return []
    if current_user:
        current_user_id = current_user.id
        current_user_model = await get_user_with_followers_cart_favorites(
            session, current_user.id
        )

    filtered = True if (
        is_favorited or is_in_shopping_cart or author_id or tags
    ) else False

    total_recipes = await count_recipes_with_filters(
        session,
        is_favorited,
        is_in_shopping_cart,
        author_id,
        tags,
        current_user_id,
        filtered=filtered
    )

    previous_url, next_url = get_prev_and_next_page(request, page, size, total_recipes)

    recipes = await get_recipes_with_filters(
        session,
        is_favorited,
        is_in_shopping_cart,
        author_id,
        tags,
        current_user_id,
        skip=(page-1)*size,
        limit=size,
        filtered=filtered
    )

    results = [
        RecipeDB(
            id=recipe.id,
            tags=recipe.tags,
            author=UserDB(
                email=recipe.author.email,
                id=recipe.author.id,
                username=recipe.author.username,
                first_name=recipe.author.first_name,
                last_name=recipe.author.last_name,
                is_subscribed=(
                    recipe.author in current_user_model.follower
                    if current_user else False
                ),
                avatar=recipe.author.avatar
            ),
            ingredients=[
                IngredientInRecipe(
                    id=ingr.id,
                    name=ingr.name,
                    measurement_unit=ingr.measurement_unit,
                    amount=ingr_recipe.amount
                )
                for ingr_recipe, ingr in zip(recipe.ingredient_associations, recipe.ingredients)
            ],
            is_favorited=(
                recipe in current_user_model.favorite_recipes
                if current_user else False
            ),
            is_in_shopping_cart=(
                recipe in current_user_model.on_cart_recipes
                if current_user else False
            ),
            name=recipe.name,
            image=recipe.image,
            text=recipe.text,
            cooking_time=recipe.cooking_time
        )
        for recipe in recipes
    ]

    return PaginatedRecipes(
        count=total_recipes,
        next=next_url,
        previous=previous_url,
        results=results
    )


@recipesrouter.post("/", response_class=JSONResponse)
async def create_new_recipe(
    request: Request,
    recipe_data: RecipeCreate,
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token)
):
    recipe = await get_recipe_by_user_id_and_name(
        session, recipe_data.name, current_user.id
    )
    if recipe:
        raise HTTPException(
            detail="You can't create recipes with the same name",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    if recipe_data.image.startswith("data:image/png;base64,"):
        base64_str = recipe_data.image.split(",", 1)[1]
    else:
        raise HTTPException(
            detail="Field image should be Base64",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    recipe_data_dict = recipe_data.model_dump()

    ingredients = recipe_data_dict.pop("ingredients")
    validated_ingredients = await check_ingredients(session, ingredients)

    tags = recipe_data_dict.pop("tags")
    validated_tags = await check_tags(session, tags)

    file_path = save_image_from_base64(base64_str, RECIPE_DIRECTORY)
    base_url = str(request.url.scheme) + "://" + str(request.url.netloc)
    recipe_data_dict["image"] = base_url + "/" + file_path
    recipe_data_dict["author_id"] = current_user.id

    new_recipe = await create_recipe(
        session, recipe_data_dict, validated_tags, validated_ingredients
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


@recipesrouter.get("/{recipe_id}", response_model=RecipeDB)
async def get_recipe(
    recipe_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[UserAuth] = Depends(get_user_from_token_custom)
):
    recipe = await get_recipe_by_id_with_author_tags(session, recipe_id)
    if not recipe:
        raise HTTPException(
            detail="Recpe not fount",
            status_code=status.HTTP_404_NOT_FOUND
        )
    recipe_ingredients = await get_ingredients_details(session, recipe_id)

    if current_user:
        current_user_model = await get_user_with_followers_cart_favorites(
            session, current_user.id
        )

    serialized_recipe = RecipeDB(
        id=recipe.id,
        tags=recipe.tags,
        author=UserDB(
            username=recipe.author.username,
            id=recipe.author.id,
            email=recipe.author.email,
            first_name=recipe.author.first_name,
            last_name=recipe.author.last_name,
            is_subscribed=(
                recipe.author in current_user_model.follower
                if current_user else False
            ),
            avatar=recipe.author.avatar
        ),
        ingredients=recipe_ingredients,
        is_favorited=(
                recipe in current_user_model.favorite_recipes
                if current_user else False
            ),
        is_in_shopping_cart=(
                recipe in current_user_model.on_cart_recipes
                if current_user else False
            ),
        name=recipe.name,
        image=recipe.image,
        text=recipe.text,
        cooking_time=recipe.cooking_time
    )

    return serialized_recipe


@recipesrouter.patch("/{recipe_id}", response_model=RecipeDB)
async def update_recipe(
    request: Request,
    recipe_id: int,
    recipe_data: RecipeBase,
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token)
):
    recipe = await get_recipe_by_id_with_author_tags_ingredients(session, recipe_id)
    if not recipe:
        raise HTTPException(
            detail="Recipe not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    if recipe.author_id != current_user.id:
        raise HTTPException(
            detail="You can only edit your recipe",
            status_code=status.HTTP_403_FORBIDDEN
        )

    recipe_with_name = await get_recipe_by_user_id_and_name(
        session, recipe_data.name, current_user.id
    )
    if recipe_with_name and recipe_with_name.id != recipe_id:
        raise HTTPException(
            detail="You already have recipe with same name",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    recipe_data_dict = recipe_data.model_dump()

    ingredients = recipe_data_dict.pop("ingredients")
    validated_ingredients = await check_ingredients(session, ingredients)

    tags = recipe_data_dict.pop("tags")
    validated_tags = await check_tags(session, tags)

    if recipe_data.image:
        if recipe_data.image.startswith("data:image/png;base64,"):
            base64_str = recipe_data.image.split(",", 1)[1]
            file_path = save_image_from_base64(base64_str, RECIPE_DIRECTORY)
            base_url = str(request.url.scheme) + "://" + str(request.url.netloc)
            recipe_data_dict["image"] = base_url + "/" + file_path
            recipe_data_dict["author_id"] = current_user.id
        else:
            raise HTTPException(
                detail="Field image should be Base64",
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
    current_user_model = await get_user_with_followers_cart_favorites(
            session, current_user.id
        )

    updated_recipe = await update_recipe_model(
        session, recipe,
        recipe_data_dict,
        validated_tags,
        validated_ingredients
    )

    ingredients_list_with_amount = await get_ingredients_details(
        session, updated_recipe.id
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
        id=updated_recipe.id,
        tags=updated_recipe.tags,
        author=UserDB(
            email=updated_recipe.author.email,
            id=updated_recipe.author.id,
            username=updated_recipe.author.username,
            first_name=updated_recipe.author.first_name,
            last_name=updated_recipe.author.last_name,
            is_subscribed=False,
            avatar=updated_recipe.author.avatar,

        ),
        ingredients=serialized_ingredients,
        is_favorited=(
                True if
                updated_recipe in current_user_model.favorite_recipes
                else False
            ),
        is_in_shopping_cart=(
                True if
                updated_recipe in current_user_model.on_cart_recipes
                else False
            ),
        name=updated_recipe.name,
        image=updated_recipe.image,
        text=updated_recipe.text,
        cooking_time=updated_recipe.cooking_time
    )

    return serialized_recipe


@recipesrouter.delete("/{recipe_id}", response_model=RecipeDB)
async def delete_recipe(
    recipe_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token)
):
    recipe_to_delete = await get_recipe_by_id(session, recipe_id)
    if not recipe_to_delete:
        raise HTTPException(
            detail="Recipe not found",
            status_code=status.HTTP_404_NOT_FOUND
        )
    if recipe_to_delete.author_id != current_user.id:
        raise HTTPException(
            detail="You can only delete your recipe",
            status_code=status.HTTP_403_FORBIDDEN
        )

    await delete_recipe_model(session, recipe_to_delete)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
