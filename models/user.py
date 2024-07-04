import re

from sqlalchemy import Integer, ForeignKey, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship, backref
from sqlalchemy.orm import validates

from models.base import Base
from config import MAX_USERNAME_LENGTH, MAX_EMAIL_LENGTH


subscription = Table(
    "subscription",
    Base.metadata,
    Column(
        "following_id",
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "follower_id",
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(MAX_USERNAME_LENGTH), unique=True, nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(
        String(MAX_EMAIL_LENGTH), unique=True, nullable=False, index=True
    )
    first_name: Mapped[str] = mapped_column(String(MAX_USERNAME_LENGTH))
    last_name: Mapped[str] = mapped_column(String(MAX_USERNAME_LENGTH))
    password: Mapped[str] = mapped_column(String, nullable=False)
    avatar: Mapped[str] = mapped_column(String(200), nullable=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    follower: Mapped[list["User"]] = relationship(
        secondary=subscription,
        primaryjoin=id == subscription.c.follower_id,
        secondaryjoin=id == subscription.c.following_id,
        backref=backref("following_subscriptions", cascade="all, delete"),
    )

    following: Mapped[list["User"]] = relationship(
        secondary=subscription,
        primaryjoin=id == subscription.c.following_id,
        secondaryjoin=id == subscription.c.follower_id,
        backref=backref("follower_subscriptions", cascade="all, delete"),
    )

    recipes = relationship(
        "Recipe", back_populates="author", cascade="all, delete-orphan"
    )

    favorite_recipes = relationship(
        "Recipe", secondary="favorite", back_populates="user_favorite"
    )
    on_cart_recipes = relationship(
        "Recipe", secondary="cart", back_populates="user_on_cart"
    )

    @validates("username")
    def validate_username(self, key, value):
        username_regex = r"^[\w.@+-]+$"
        if not re.match(username_regex, value):
            raise ValueError("Username is invalid")
        return value

    @validates("email")
    def validate_email(self, key, value):
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, value):
            raise ValueError("Invalid email format")
        return value

    def __str__(self) -> str:
        return self.username

    @property
    def is_admin(self):
        return self.is_superuser
