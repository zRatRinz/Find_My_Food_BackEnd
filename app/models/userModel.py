from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING
from datetime import date, datetime
from app.core import datetimezone
# from app.models.recipeModel import TrnRecipeModel

if TYPE_CHECKING:
    from app.models.recipeModel import TrnRecipeModel 

class MasUserModel(SQLModel, table=True):
    __tablename__ = "mas_user"
    user_id: int = Field(primary_key=True)
    email: str = Field(unique=True)
    username: str | None = Field(unique=True)
    password: str | None = None
    gender: str | None = None
    birth_date: date | None = None
    image_url: str | None = None
    provider: str = Field(default="local")
    create_date: datetime = Field(default_factory=datetimezone.get_thai_now)
    update_date: datetime | None = None
    last_login: datetime | None = None
    is_active: bool = True

    recipes: list["TrnRecipeModel"] = Relationship(back_populates="user")
