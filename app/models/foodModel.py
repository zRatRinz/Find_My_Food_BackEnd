from sqlmodel import SQLModel, Field, Column, DateTime, func, Relationship
from typing import Optional
from datetime import datetime

class FoodWithIngredientModel(SQLModel, table=True):
    __tablename__ = "map_foodingredient"
    foodingredient_id:int = Field(default=None,primary_key=True)
    food_id: int = Field(foreign_key="mas_food.food_id")
    ingredient_id:int = Field(foreign_key="mas_ingredient.ingredient_id")

class FoodModel(SQLModel, table=True):
    __tablename__ = "mas_food"
    food_id: Optional[int] = Field(default=None,primary_key=True)
    food:str
    image_url: Optional[str] = None
    create_date: datetime = Field(sa_column=Column(DateTime(timezone=True),server_default=func.now()))
    update_date: datetime = Field(sa_column=Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now()))
    owner_id: Optional[int] = None
    is_public: bool
    is_active: bool

    ingredients: list[IngredientModel] = Relationship(
        back_populates="foods", 
        link_model=FoodWithIngredientModel
    )
    
class IngredientModel(SQLModel, table=True):
    __tablename__ = "mas_ingredient"
    ingredient_id: Optional[int] = Field(default=None,primary_key=True)
    ingredient:str
    image_url: Optional[str] = None
    create_date: datetime = Field(sa_column=Column(DateTime(timezone=True),server_default=func.now()))
    update_date: datetime = Field(sa_column=Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now()))

    foods: list["FoodModel"] = Relationship(
        back_populates="ingredients", 
        link_model=FoodWithIngredientModel
    )

# class FoodPublic(SQLModel):
#     __tablename__ = "mas_food"
#     food_id: Optional[int] = Field(default=None,primary_key=True)
#     food:str
#     image_url: Optional[str] = None
#     create_date: datetime = Field(sa_column=Column(DateTime(timezone=True),server_default=func.now()))
#     update_date: datetime = Field(sa_column=Column(DateTime(timezone=True),server_default=func.now(),onupdate=func.now()))



