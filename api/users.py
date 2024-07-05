from fastapi import APIRouter, HTTPException, Query, Depends, Request, status
from fastapi.responses import JSONResponse
# from fastapi_pagination import Page, add_pagination, paginate
from sqlalchemy.ext.asyncio import AsyncSession

from config import DEFAULT_PAGE_NUMBER, MAX_OBJ_PER_PAGE, MIN_PAGE_NUM, OBJ_PER_PAGE
from schemas.pagination_schema import PaginatedSubscriptionUsers, PaginatedUsers
from schemas.user_schema import UserAuth, UserCreate, UserCreated, UserDB, UserSubscription

from db.database import get_session
from crud.user_repository import (
    add_subscription,
    check_username_and_email,
    count_following_users,
    count_users,
    create_user,
    get_all_users,
    get_following_users,
    get_user_by_id,
    get_user_by_id_with_recipes,
    subscription_exists
)
from security.pwd_crypt import get_hashed_password
from security.security import get_user_from_token


usersrouter = APIRouter()


@usersrouter.get("/", response_model=PaginatedUsers)
async def get_users(
    request: Request,
    session: AsyncSession = Depends(get_session),
    page: int = Query(DEFAULT_PAGE_NUMBER, ge=MIN_PAGE_NUM),
    size: int = Query(OBJ_PER_PAGE, le=MAX_OBJ_PER_PAGE)
):
    total = await count_users(session)
    users = await get_all_users(session, skip=(page-1)*size, limit=size)

    base_url = str(request.url).split("?")[0]
    next_url = (
        f"{base_url}?page={page + 1}&size={size}"
        if (page * size) < total else None
    )
    previous_url = (
        f"{base_url}?page={page - 1}&size={size}"
        if page > 1 else None
    )
    results = [
        UserDB(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_subscribed=False,
            avatar=user.avatar
        )
        for user in users
    ]

    return PaginatedUsers(
        count=total,
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


@usersrouter.get("/me/", response_model=UserDB)
async def get_myself(
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token),
):
    user = await get_user_by_id(session, current_user.id)
    return user


@usersrouter.get("/subscriptions/", response_model=PaginatedSubscriptionUsers)
async def get_my_subscriptions(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: UserAuth = Depends(get_user_from_token),
    page: int = Query(DEFAULT_PAGE_NUMBER, ge=MIN_PAGE_NUM),
    size: int = Query(OBJ_PER_PAGE, le=MAX_OBJ_PER_PAGE)
):
    total = await count_following_users(session, current_user.id)
    users = await get_following_users(session, current_user.id)

    base_url = str(request.url).split("?")[0]
    next_url = (
        f"{base_url}?page={page + 1}&size={size}"
        if (page * size) < total else None
    )
    previous_url = (
        f"{base_url}?page={page - 1}&size={size}"
        if page > 1 else None
    )
    results = [
        UserSubscription(
            id=user.id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_subscribed=True,
            avatar=user.avatar,
            recipes=user.recipes,
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


@usersrouter.get("/{user_id}/", response_model=UserDB)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            detail="User not found.",
            status_code=status.HTTP_404_NOT_FOUND
        )
    return user