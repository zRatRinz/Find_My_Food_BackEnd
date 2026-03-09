from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.db import database
from app.services import notificationService
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/notification", tags=["notification"])

@router.get("/sendExpirePushNotification")
async def send_expire_push_notification(db: Session = Depends(database.get_db)):
    response = notificationService.send_expire_push_notification_process(db)
    return StandardResponse.success(data=response)