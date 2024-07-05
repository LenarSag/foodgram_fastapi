import re
from typing import Optional

from fastapi.exceptions import ValidationException
from pydantic import BaseModel, EmailStr, Field, field_validator

from config import MAX_USERNAME_LENGTH, MAX_EMAIL_LENGTH


class UserAuth(BaseModel):
    id: int


class UserBase(BaseModel):
    username: str = Field(
        max_length=MAX_USERNAME_LENGTH, pattern=r"^[\w.@+-]+$"
    )
    email: EmailStr = Field(max_length=MAX_EMAIL_LENGTH)
    first_name: str = Field(max_length=MAX_USERNAME_LENGTH)
    last_name: str = Field(max_length=MAX_USERNAME_LENGTH)

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        password_regex = re.compile(
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        )
        if not password_regex.match(value):
            raise ValidationException(
                "Password must be at least 8 characters long, include an "
                "uppercase letter, a lowercase letter, a number, "
                "and a special character."
            )
        return value


class UserCreated(UserBase, UserAuth):
    avatar: Optional[str] = None


class UserDB(UserCreated):
    is_subscribed: bool = False


class UserGetToken(BaseModel):
    email: EmailStr = Field(max_length=MAX_EMAIL_LENGTH)
    password: str

    class Config:
        from_attributes = True
