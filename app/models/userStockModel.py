from sqlmodel import SQLModel, Field, Relationship
from datetime import date, datetime
from app.core import datetimezone
from app.models.unitModel import UnitModel

class TrnUserStockModel(SQLModel, table=True):
    __tablename__ = "trn_user_stock"
    stock_id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="mas_user.user_id", index=True)
    ingredient_id: int = Field(foreign_key="mas_ingredient.ingredient_id", index=True)
    item_name: str
    quantity: float
    unit_id: int = Field(foreign_key="mas_unit.unit_id")
    expire_date: date | None = None
    storage_location: str
    create_date: datetime = Field(default_factory=datetimezone.get_thai_now)
    update_date: datetime | None = None

    unit: "UnitModel" = Relationship()
