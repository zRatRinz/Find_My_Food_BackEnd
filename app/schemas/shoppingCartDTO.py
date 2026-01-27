from pydantic import BaseModel, ConfigDict
from datetime import datetime

class AddShoppingItemInNewShoppingListDTO(BaseModel):
    item_name: str
    quantity: float
    unit_id: int
    note: str | None = None

class CreateNewShoppingListDTO(BaseModel):
    shopping_type: str
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