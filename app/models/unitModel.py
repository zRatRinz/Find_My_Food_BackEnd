from sqlmodel import SQLModel, Field

class UnitModel(SQLModel, table=True):
    __tablename__ = "mas_unit"
    unit_id: int | None = Field(default=None, primary_key=True)
    unit_name: str
    unit_symbol: str | None = None
    is_active: bool = Field(default=True)