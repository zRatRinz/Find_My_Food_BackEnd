from fastapi import APIRouter, Depends
from typing import Annotated
from sqlmodel import Session
from app.dependencies import get_current_active_user
from app.db import database
from app.models.userModel import MasUserModel
from app.schemas.userStockDTO import AddUserStockDTO
from app.schemas.response import StandardResponse
from app.services import userStockService

router = APIRouter(prefix="/userStock", tags=["userStock"])

@router.post("/addUserStock")
def add_user_stock(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                   request_body: AddUserStockDTO,
                   db: Session = Depends(database.get_db)):
    response = userStockService.add_user_stock(db, current_user.user_id, request_body)
    return StandardResponse.success(data=response)