from datetime import datetime

from sqlalchemy import (
    Column,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    DateTime,
    Table,
    func,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config import (
    MAX_COOKING_TIME,
    MAX_FIELD_LENGTH,
    MAX_INGREDIENT_AMOUNT,
    MAX_SLUG_LENGTH,
    MAX_UNIT_LENGTH,
    MIN_COOKING_TIME,
    MIN_INGREDIENT_AMOUNT
)
from models.base import Base
from utils.short_url import get_hashed_short_url


recipe_tag = Table(
    "recipe_tag",
    Base.metadata,
    Column("recipe_id", ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)


favorite = Table(
    "favorite",
    Base.metadata,
    Column("user_id", ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("recipe_id", ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True),
)

cart = Table(
    "cart",
    Base.metadata,
    Column("user_id", ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
    Column("recipe_id", ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(MAX_FIELD_LENGTH), nullable=False)
    slug: Mapped[str] = mapped_column(String(MAX_SLUG_LENGTH), unique=True)

    recipes: Mapped[list["Recipe"]] = relationship(
        "Recipe", secondary=recipe_tag, back_populates="tags"
    )

    __table_args__ = (
        UniqueConstraint("name", "slug", name="tag_name_slug"),
    )


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredient"

    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recipe.id", ondelete="CASCADE"), primary_key=True
    )
    ingredient_id: Mapped[int] = mapped_column(
        ForeignKey("ingredient.id", ondelete="CASCADE"), primary_key=True
    )
    amount: Mapped[int] = mapped_column(
        SmallInteger,
        CheckConstraint(
            f"amount >= {MIN_INGREDIENT_AMOUNT} "
            f"AND amount <= {MAX_INGREDIENT_AMOUNT}"
            ),
        nullable=False
    )

    ingredient: Mapped["Ingredient"] = relationship(
        back_populates="recipe_associations"
    )
    recipe: Mapped["Recipe"] = relationship(
        back_populates="ingredient_associations"
    )


class Ingredient(Base):
    __tablename__ = "ingredient"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(MAX_FIELD_LENGTH))
    measurement_unit: Mapped[str] = mapped_column(String(MAX_UNIT_LENGTH))

    recipes: Mapped[list["Recipe"]] = relationship(
        secondary="recipe_ingredient", back_populates="ingredients"
    )
    recipe_associations: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="ingredient"
    )

    __table_args__ = (
        UniqueConstraint(
            "name", "measurement_unit", name="ingredient_name_unit"
        ),
    )


class Recipe(Base):
    __tablename__ = "recipe"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    name: Mapped[str] = mapped_column(String(MAX_FIELD_LENGTH), nullable=False)
    image: Mapped[str] = mapped_column(String, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    cooking_time: Mapped[int] = mapped_column(
        SmallInteger,
        CheckConstraint(
            f"cooking_time >= {MIN_COOKING_TIME} "
            f"AND cooking_time <= {MAX_COOKING_TIME}"
        ),
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    author = relationship("User", back_populates="recipes")
    tags: Mapped[list["Tag"]] = relationship(
        "Tag", secondary=recipe_tag, back_populates="recipes"
    )
    ingredients: Mapped[list["Ingredient"]] = relationship(
        secondary="recipe_ingredient", back_populates="recipes"
    )
    ingredient_associations: Mapped[list["RecipeIngredient"]] = relationship(
        back_populates="recipe"
    )
    user_favorite = relationship(
        "User", secondary=favorite, back_populates="favorite_recipes"
    )
    user_on_cart = relationship(
        "User", secondary=cart, back_populates="on_cart_recipes"
    )

    __table_args__ = (
        UniqueConstraint("author_id", "name", name="uix_author_recipe_name"),
    )

    def __str__(self):
        return f"{self.name}. Автор: {self.author.username}"

    @property
    def get_short_url(self):
        short_url = get_hashed_short_url(self.id)
        return short_url
