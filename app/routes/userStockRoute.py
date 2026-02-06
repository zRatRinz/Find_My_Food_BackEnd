from fastapi import APIRouter, Depends, HTTPException, Response, status
from typing import Annotated
from sqlmodel import Session
from app.dependencies import get_current_active_user
from app.db import database
from app.models.userModel import MasUserModel
from app.schemas.userStockDTO import AddUserStockDTO
from app.schemas.response import StandardResponse
from app.enums.errorCodeEnum import ErrorCodeEnum
from app.services import userStockService

router = APIRouter(prefix="/userStock", tags=["userStock"])

@router.post("/addUserStock")
def add_user_stock(response_obj: Response,
                   current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                   request_body: AddUserStockDTO,
                   db: Session = Depends(database.get_db)):
    response = userStockService.add_user_stock(db, current_user.user_id, request_body)
    if not response:
        response_obj.status_code = status.HTTP_400_BAD_REQUEST
        return StandardResponse.fail(message="เกิดข้อผิดพลาดในการบันทึกข้อมูล")
    return StandardResponse.success(data=response)