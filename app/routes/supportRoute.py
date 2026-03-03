from fastapi import APIRouter, Depends
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
def submit_feedback(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                    request_body: FeedBackDTO,
                    db: Session = Depends(database.get_db)):
    response = supportService.create_feedback(current_user.user_id, request_body, db)
    return StandardResponse.success()