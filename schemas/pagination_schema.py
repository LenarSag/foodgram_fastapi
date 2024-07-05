from typing import Optional
from pydantic import BaseModel

from schemas.user_schema import UserDB, UserSubscription


class PaginationBase(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]


class PaginatedUsers(PaginationBase):
    results: list[UserDB]


class PaginatedSubscriptionUsers(PaginationBase):
    results: list[UserSubscription]
