from pydantic import BaseModel, Field
from datetime import date, datetime
from app.enums.types import StorageTypeEnum

class StockInfoDTO(BaseModel):
    # item_name: str
    quantity: float
    unit_name: str

class AddUserStockDTO(BaseModel):
    ingredient_id: int
    item_name: str
    quantity: float
    unit_id: int
    expire_date: date | None = None
    storage_location: StorageTypeEnum

class UpdateItemInUserStockDTO(BaseModel):
    quantity: float = Field(gt=0, description="จำนวนต้องมากกว่า 0")
    unit_id: int
    expire_date: date | None = None
    storage_location: StorageTypeEnum

class UserStockDTO(BaseModel):
    stock_id: int
    ingredient_id: int
    item_name: str
    quantity: float
    unit_id: int
    unit_name: str
    expire_date: date | None = None
    storage_location: str
    create_date: datetime
    update_date: datetime | None = None