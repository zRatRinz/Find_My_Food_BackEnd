from sqlmodel import SQLModel, Field
from datetime import datetime
from app.core import datetimezone

class TrnFeedbackModel(SQLModel, table=True):
    __tablename__ = "trn_feedback"
    feedback_id: int | None = Field(default=None, primary_key=True)
    user_id: int
    title: str
    detail: str
    create_date: datetime = Field(default_factory=datetimezone.get_thai_now)