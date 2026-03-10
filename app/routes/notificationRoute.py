from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import Annotated
from app.db import database
from app.dependencies import get_current_active_user
from app.services import notificationService
from app.models.userModel import MasUserModel
from app.schemas.notificationDTO import NotificationDTO
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/notification", tags=["notification"])

@router.patch("/readNotification")
def read_notification(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], 
                      db: Session = Depends(database.get_db)):
    response = notificationService.read_notification(current_user.user_id, db)
    return StandardResponse.success(data=response)

@router.get("/sendExpirePushNotification")
async def send_expire_push_notification(db: Session = Depends(database.get_db)):
    response = notificationService.send_expire_push_notification_process(db)
    return StandardResponse.success(data=response)

@router.get("/getUnreadNotificationCount")
def get_unread_notification_count(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], 
                                  db: Session = Depends(database.get_db)):
    response = notificationService.get_unread_notification_count(current_user.user_id, db)
    return StandardResponse.success(data={"notification_count": response})

@router.get("/getAllNotification", response_model=StandardResponse[list[NotificationDTO]])
def get_all_notification(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                         db: Session = Depends(database.get_db)):
    response = notificationService.get_all_notifications(current_user.user_id, db)
    return StandardResponse.success(data=response)