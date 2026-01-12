from pydantic import BaseModel

class UnitResponseDTO(BaseModel):
    unit_id: int
    unit_name: str
    unit_symbol: str | None = None