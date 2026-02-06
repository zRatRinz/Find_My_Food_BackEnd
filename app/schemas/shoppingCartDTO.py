from pydantic import BaseModel, ConfigDict
from datetime import datetime
from app.schemas.userStockDTO import StockInfoDTO
from app.enums.types import ShoppingTypeEnum

class AddShoppingItemInNewShoppingListDTO(BaseModel):
    item_name: str
    quantity: float
    unit_id: int
    note: str | None = None

class CreateNewShoppingListDTO(BaseModel):
    shopping_type: ShoppingTypeEnum
    list_name: str
    items: list[AddShoppingItemInNewShoppingListDTO]

class AddShoppingItemToShoppingListDTO(AddShoppingItemInNewShoppingListDTO):
    shopping_list_id: int

class UpdateShoppingItemStatusDTO(BaseModel):
    # shopping_item_id: int
    is_check: bool

class UpdateShoppingItemQuantityDTO(BaseModel):
    quantity: float
    
class UpdateShoppingItemUnitDTO(BaseModel):
    unit_id: int

class UpdateShoppingItemResponseDTO(BaseModel):
    shopping_item_id: int
    item_name: str
    quantity: float
    unit_id: int
    unit_name: str
    is_check: bool
    note: str | None = None

# class UpdateShoppingItemStatusListDTO(BaseModel):
#     items: list[UpdateShoppingItemStatusDTO]
    
class ShoppingItemResponseDTO(BaseModel):
    shopping_item_id: int
    item_name: str
    quantity: float
    unit_name: str
    is_check: bool
    note: str | None = None

    model_config = ConfigDict(from_attributes=True)
    
class ShoppingListResponseDTO(BaseModel):
    shopping_list_id: int
    list_name: str | None
    status: str | None
    create_date: datetime
    items: list[ShoppingItemResponseDTO] = [] 

    model_config = ConfigDict(from_attributes=True)

class ShoppingPreviewDTO(BaseModel):
    ingredient_id: int
    item_name: str
    recipe_quantity: float
    recipe_unit_name: str
    user_stock: StockInfoDTO | None = None

class RecipeIngredientDTO(BaseModel):
    ingredient_id: int
    item_name: str
    quantity: float
    unit_id: int

class AddRecipeIngredientToShoppingListDTO(BaseModel):
    recipe_id: int
    items: list[RecipeIngredientDTO]