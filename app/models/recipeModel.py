from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
from datetime import datetime
from app.core import datetimezone
from app.models.unitModel import UnitModel

if TYPE_CHECKING:
    from app.models.userModel import MasUserModel

# class RecipeModel(SQLModel, table=True):
#     __tablename__ = "trn_recipe"
#     recipe_id: int | None = Field(default=None, primary_key=True)
#     recipe_name: str
#     create_date: datetime = Field(default_factory=datetimezone.get_thai_now)
#     update_date: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

class MasIngredientModel(SQLModel, table=True):
    __tablename__ = "mas_ingredient"
    ingredient_id: int | None = Field(default=None,primary_key=True)
    ingredient_name:str
    image_url: str | None = None
    create_date: datetime = Field(default_factory=datetimezone.get_thai_now)
    update_date: datetime | None = None

class TrnRecipeModel(SQLModel, table=True):
    __tablename__ = "trn_recipe"
    recipe_id: int = Field(default=None, primary_key=True)
    recipe_name: str
    description: str | None = None
    cooking_time_min: int | None = None
    image_url: str | None = None
    user_id: int | None = Field(foreign_key="mas_user.user_id")
    is_public: bool = Field(default=True)
    is_active: bool = Field(default=True)
    create_date: datetime = Field(default_factory=datetimezone.get_thai_now)
    update_date: datetime | None = None

    user: "MasUserModel" = Relationship(back_populates="recipes")
    ingredients: list["DtlRecipeIngredientModel"] = Relationship(back_populates="recipe")
    steps: list["DtlRecipeStepModel"] = Relationship(back_populates="recipe")

    @property
    def username(self) -> str | None:
        return self.user.username if self.user else None

class DtlRecipeIngredientModel(SQLModel, table=True):
    __tablename__ = "dtl_recipe_ingredient"
    recipe_ingredient_id: int = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="trn_recipe.recipe_id")
    ingredient_id: int = Field(foreign_key="mas_ingredient.ingredient_id")
    quantity: float
    unit_id: int = Field(foreign_key="mas_unit.unit_id")

    recipe: "TrnRecipeModel" = Relationship(back_populates="ingredients")
    ingredient: "MasIngredientModel" = Relationship()
    unit: "UnitModel" = Relationship()

    @property
    def ingredient_name(self) -> str | None:
        return self.ingredient.ingredient_name
    @property
    def unit_name(self) -> str | None:
        return self.unit.unit_name

class DtlRecipeStepModel(SQLModel, table=True):
    __tablename__ = "dtl_recipe_step"
    recipe_step_id: int = Field(default=None, primary_key=True)
    recipe_id: int = Field(foreign_key="trn_recipe.recipe_id")
    step_no: int
    instruction: str

    recipe: "TrnRecipeModel" = Relationship(back_populates="steps")

class MapRecipeLikeModel(SQLModel, table=True):
    __tablename__ = "map_recipe_like"
    recipe_id: int = Field(foreign_key="trn_recipe.recipe_id", primary_key=True)
    user_id: int = Field(foreign_key="mas_user.user_id", primary_key=True)
    create_date: datetime = Field(default_factory=datetimezone.get_thai_now)