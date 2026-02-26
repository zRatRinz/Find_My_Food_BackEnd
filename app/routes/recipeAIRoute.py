from fastapi import APIRouter, File, UploadFile, Depends, Response, status
from typing import Annotated
from sqlmodel import Session
from app.dependencies import get_current_active_user
from app.db import database
from app.enums.errorCodeEnum import ErrorCodeEnum
from app.models.userModel import MasUserModel
from app.schemas.response import StandardResponse
from app.services import recipeAIService 

router = APIRouter(prefix="/recipeAI", tags=["recipeAI"])

@router.post("/")
async def analyze_food_image(response_obj: Response, current_user: Annotated[MasUserModel, Depends(get_current_active_user)], 
                             file: UploadFile = File(...),
                             db: Session = Depends(database.get_db)):
    image_bytes = await file.read()
    response, error_code = recipeAIService.analyze_food_image(current_user.user_id, image_bytes, db)
    if response is None:
        if error_code == ErrorCodeEnum.NOT_FOUND:
            return StandardResponse.fail(message="รูปภาพนี้ไม่ใช่อาหาร กรุณาเลือกรูปภาพอาหาร")
        response_obj.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return StandardResponse.fail(message="เกิดข้อผิดพลาดในการวิเคราะห์รูปภาพอาหาร")

    return StandardResponse.success(data=response)