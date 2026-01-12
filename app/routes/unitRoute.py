from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.db import database
from app.services import unitService
from app.schemas.unitDTO import UnitResponseDTO
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/unit", tags=["unit"])

@router.get("/", response_model=StandardResponse[list[UnitResponseDTO]])
def get_all_unit(db: Session = Depends(database.get_db)):
    try:
        response = unitService.get_all_unit(db)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))