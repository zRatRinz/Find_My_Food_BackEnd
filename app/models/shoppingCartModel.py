from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from app.core import datetimezone
from app.models.unitModel import UnitModel

class ShoppingListModel(SQLModel, table=True):
    __tablename__ = "trn_shopping_list"
    shopping_list_id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="mas_user.user_id")
    list_name: str | None = None
    status: str | None = None
    create_date: datetime = Field(default_factory=datetimezone.get_thai_now)
    update_date: datetime | None = None

    items: list["ShoppingItemModel"] = Relationship(back_populates="shopping_list")

class ShoppingItemModel(SQLModel, table=True):
    __tablename__ = "dtl_shopping_item"
    shopping_item_id: int = Field(default=None, primary_key=True)
    shopping_list_id: int = Field(foreign_key="trn_shopping_list.shopping_list_id")
    item_name: str
    quantity: int
    unit_id: int = Field(foreign_key="mas_unit.unit_id")
    is_check: bool = Field(default=False)
    note: str
    create_date: datetime = Field(default_factory=datetimezone.get_thai_now)
    update_date: datetime | None = None

    shopping_list: "ShoppingListModel" = Relationship(back_populates="items")
    unit: "UnitModel" = Relationship()
    
    @property
    def unit_name(self) -> str:
        return self.unit.unit_name