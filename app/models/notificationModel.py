from sqlmodel import SQLModel, Field
from datetime import datetime
from app.core import datetimezone

class TrnNotificationModel(SQLModel, table=True):
    __tablename__ = "trn_notification"
    notification_id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="mas_user.user_id")
    title: str
    body: str
    create_date: datetime = Field(default_factory=datetimezone.get_thai_now)
    read_date: datetime | None = None
    is_read: bool = Field(default=False)