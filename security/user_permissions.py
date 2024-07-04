from typing import Union

from fastapi import HTTPException, status

from models.review import Review, Comment
from models.user import User


def is_admin(user: User) -> bool:
    if user.is_admin:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Only for admins!"
    )


def is_admin_moderator_or_author(user: User, obj: Union[Review, Comment]) -> bool:
    if user.is_admin or user.is_moderator or user.id == obj.author_id:
        return True
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Not enough rights!"
    )
