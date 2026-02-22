from sqlmodel import Session
from app.core import datetimezone
from app.models.supportModel import TrnFeedbackModel
from app.schemas.supportDTO import FeedBackDTO

def create_feedback(user_id:int, request_body: FeedBackDTO, db: Session):
    try:
        new_feedback = TrnFeedbackModel(
            user_id=user_id,
            title=request_body.title,
            detail=request_body.detail,
            create_date=datetimezone.get_thai_now()
        )

        db.add(new_feedback)
        db.commit()
        db.refresh(new_feedback)
        return new_feedback
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return None