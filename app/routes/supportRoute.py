from fastapi import APIRouter, Depends, Response, status
from typing import Annotated
from sqlmodel import Session
from app.dependencies import get_current_active_user
from app.db import database
from app.models.userModel import MasUserModel
from app.schemas.supportDTO import FeedBackDTO
from app.schemas.response import StandardResponse
from app.services import supportService

router = APIRouter(prefix="/support", tags=["support"])

@router.post("/feedback/submit")
def submit_feedback(response_obj: Response,
                    current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                    request_body: FeedBackDTO,
                    db: Session = Depends(database.get_db)):
    response = supportService.create_feedback(current_user.user_id, request_body, db)
    if not response:
        response_obj.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return StandardResponse.fail(message="เกิดข้อผิดพลาดในการบันทึกข้อมูล")
    return StandardResponse.success()