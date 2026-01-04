from sqlmodel import SQLModel, Field, Column, DateTime, func
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class FoodDTO(SQLModel):
    __tablename__ = "mas_food"
    food_id: Optional[int] = Field(default=None,primary_key=True)
    food:str
    image_url: Optional[str] = None
    # create_date: datetime = Field(sa_column=Column(DateTime(timezone=True),server_default=func.now()))
    # update_date: datetime = Field(sa_column=Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now()))
    owner_id: Optional[int] = None
    is_public: bool
    is_active: bool

class IngredientDTO(SQLModel):
    ingredient_id: int
    ingredient: str

class FoodWithIngredientDTO(SQLModel):
    food_id: int
    food: str
    image_url: Optional[str] = None
    ingredients: list[IngredientDTO] = []

class CreateNewFoodModel(BaseModel):
    food: str
    image_url: Optional[str] = None
    is_public: bool
    is_active: bool = True