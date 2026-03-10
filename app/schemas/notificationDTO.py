from pydantic import BaseModel
from datetime import datetime

class NotificationDTO(BaseModel):
    notification_id: int
    title: str
    body: str
    create_date: datetime
    is_read: bool