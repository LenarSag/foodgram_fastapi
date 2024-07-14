from typing import Optional

from fastapi import (
    APIRouter, HTTPException, Query, Depends, Request, Response, status
)
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from config import (
    DEFAULT_PAGE_NUMBER,
    MAX_OBJ_PER_PAGE,
    MIN_PAGE_NUM,
    OBJ_PER_PAGE,
    USER_DIRECTORY
)
from models.user import User
from schemas.pagination_schema import (
    PaginatedSubscriptionUsers,
    PaginatedUsers
)
from schemas.user_schema import (
    UserAuth,
    UserAvatar,
    UserChangePassword,
    UserCreate,
    UserCreated,
    UserDB,
    UserSubscription
)
from schemas.recipe_schema import RecipeShort
from db.database import get_session
from crud.user_repository import (
    add_avatar_to_field,
    add_subscription,
    change_password,
    check_username_and_email,
    count_following_users,
    count_users,
    create_user,
    delete_avatar_field,
    get_all_users,
    get_all_users_with_followers,
    get_following_users,
    get_user_by_id,
    get_user_by_id_with_followers,
    get_user_by_id_with_recipes,
    subscription_exists,
    delete_subscription
)
from security.pwd_crypt import get_hashed_password, verify_password
from security.security import get_user_from_token, get_user_from_token_custom
from utils.custom_pagination import get_prev_and_next_page
from utils.save_base64 import save_image_from_base64


usersrouter = APIRouter()


def get_limited_recipes(
    user: User, recipe_limits: Optional[int] = None
) -> list[RecipeShort]:
    recipes = [
        RecipeShort(
            id=recipe.id,
            name=recipe.name,
            image=recipe.image,
            cooking_time=recipe.cooking_time
        ) for recipe in user.recipes
    ]

    if recipe_limits is not None:
        recipes = recipes[:recipe_limits]

    return recipes


@usersrouter.get("/", response_model=PaginatedUsers)
async def get_users(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[UserAuth] = Depends(get_user_from_token_custom),
    page: int = Query(DEFAULT_PAGE_NUMBER, ge=MIN_PAGE_NUM),
    size: int = Query(OBJ_PER_PAGE, le=MAX_OBJ_PER_PAGE)
):
    total_users = await count_users(session)
    if current_user:
        current_user_model = await get_user_by_id(session, current_user.id)
        users = await get_all_users_with_followers(session, skip=(page-1)*size, limit=size)
    else:
        users = await get_all_users(session, skip=(page-1)*size, limit=size)

    previous_url, next_url = get_prev_and_next_page(
        request, page, size, total_users
    )

    results = [
        UserDB(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_subscribed=(
                current_user_model in user.following
                if current_user else False
            ),
            avatar=user.avatar
        )
        for user in users
    ]

    return PaginatedUsers(
        count=total_users,
        next=next_url,
        previous=previous_url,
        results=results
    )


@usersrouter.post("/", response_class=JSONResponse)
async def create_new_user(
    new_user_data: UserCreate,
    session: AsyncSession = Depends(get_session),
):
    user = await check_username_and_email(
        session, new_user_data.username, new_user_data.email
    )
    if user:
        if user.username == new_user_data.username:
            raise HTTPException(
                detail="Username already taken",
                status_code=status.HTTP_400_BAD_REQUEST
            )
        if user.email == new_user_data.email:
            raise HTTPException(
                detail="Email already registered",
                status_code=status.HTTP_400_BAD_REQUEST
            )

    hashed_password = get_hashed_password(new_user_data.password)
    new_user_data.password = hashed_password

    new_user = await create_user(session, new_user_data)
    serialized_user = UserCreated.model_validate(new_user)

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=serialized_user.model_dump()
    )


@usersrouter.put("/me/avatar/", response_model=UserAvatar)
async def add_avatar(
    avatar_data: UserAvatar,
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token),
):
    if avatar_data.avatar.startswith("data:image/png;base64,"):
        base64_str = avatar_data.avatar.split(",", 1)[1]
    else:
        raise HTTPException(
            detail="Field avatar can't be empty",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    file_path = save_image_from_base64(base64_str, USER_DIRECTORY)

    await add_avatar_to_field(session, current_user.id, file_path)

    base_url = str(request.url.scheme) + "://" + str(request.url.netloc)
    serialized_user = UserAvatar(
        avatar=base_url + "/" + file_path
    )
    return serialized_user


@usersrouter.delete("/me/avatar/", response_model=UserDB)
async def delete_avatar(
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token),
):
    avatar_deleted = await delete_avatar_field(
        session, current_user.id
    )
    if avatar_deleted:
        return Response(status_code=status.HTTP_204_NO_CONTENT)


@usersrouter.get("/me/", response_model=UserDB)
async def get_myself(
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token),
):
    user = await get_user_by_id(session, current_user.id)
    return user


@usersrouter.post("/set_password/", response_class=Response)
async def set_password(
    password_data: UserChangePassword,
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token),
):
    user = await get_user_by_id(session, current_user.id)
    is_correct_password = verify_password(
        password_data.current_password, user.password
    )
    if not is_correct_password:
        raise HTTPException(
            detail="Current assword is incorrect", 
            status_code=status.HTTP_400_BAD_REQUEST
        )
    hashed_password = get_hashed_password(password_data.new_password)
    await change_password(session, user, hashed_password)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@usersrouter.get("/subscriptions/", response_model=PaginatedSubscriptionUsers)
async def get_my_subscriptions(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token),
    page: int = Query(DEFAULT_PAGE_NUMBER, ge=MIN_PAGE_NUM),
    size: int = Query(OBJ_PER_PAGE, le=MAX_OBJ_PER_PAGE),
    recipe_limits: Optional[int] = Query(None)
):
    total = await count_following_users(session, current_user.id)
    users = await get_following_users(session, current_user.id)

    previous_url, next_url = get_prev_and_next_page(request, page, size, total)

    results = [
        UserSubscription(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_subscribed=True,
            avatar=user.avatar,
            recipes=get_limited_recipes(user, recipe_limits),
            recipes_count=len(user.recipes)
        )
        for user in users
    ]

    return PaginatedSubscriptionUsers(
        count=total,
        next=next_url,
        previous=previous_url,
        results=results
    )


@usersrouter.post("/{user_id}/subscribe/", response_class=JSONResponse)
async def subscribe(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token),
):
    user_to_follow = await get_user_by_id_with_recipes(session, user_id)
    if not user_to_follow:
        raise HTTPException(
            detail="User not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )
    if user_to_follow.id == current_user.id:
        raise HTTPException(
            detail="You can't follow yourself",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    subscription = await subscription_exists(
        session, user_to_follow.id, current_user.id
    )
    if subscription:
        raise HTTPException(
            detail="You already following this user",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    new_subscription = await add_subscription(
        session, user_to_follow.id, current_user.id
    )
    if new_subscription:
        serialized_user = UserSubscription(
            id=user_to_follow.id,
            username=user_to_follow.username,
            email=user_to_follow.email,
            first_name=user_to_follow.first_name,
            last_name=user_to_follow.last_name,
            is_subscribed=True,
            avatar=user_to_follow.avatar,
            recipes=user_to_follow.recipes,
            recipes_count=len(user_to_follow.recipes)
        )

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content=serialized_user.model_dump()
        )


@usersrouter.delete("/{user_id}/subscribe/", response_class=JSONResponse)
async def delete_subscribe(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token),
):
    user_to_unfollow = await get_user_by_id(session, user_id)
    if not user_to_unfollow:
        raise HTTPException(
            detail="User not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )
    subscription = await subscription_exists(session, user_id, current_user.id)
    if not subscription:
        raise HTTPException(
            detail="You are not subscribed to this user.",
            status_code=status.HTTP_400_BAD_REQUEST
        )

    await delete_subscription(session, user_id, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@usersrouter.get("/{user_id}/", response_model=UserDB)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: Optional[UserAuth] = Depends(get_user_from_token_custom),
):
    user = await get_user_by_id_with_followers(session, user_id)
    if not user:
        raise HTTPException(
            detail="User not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )
    if current_user:
        is_subscribed = any(
            current_user.id == following_user.id
            for following_user in user.following
        )
    else:
        is_subscribed = False

    serialized_user = UserDB(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_subscribed=is_subscribed,
            avatar=user.avatar
        )
    return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=serialized_user.model_dump()
        )
