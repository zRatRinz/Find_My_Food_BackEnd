from pydantic import BaseModel
from datetime import date
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