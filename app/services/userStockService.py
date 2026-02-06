from sqlmodel import Session
from app.core import datetimezone
from app.models.userStockModel import TrnUserStockModel
from app.schemas.userStockDTO import AddUserStockDTO
from app.enums.errorCodeEnum import ErrorCodeEnum

def add_user_stock(db: Session, user_id: int, request_body: AddUserStockDTO):
    try:
        new_stock_item = TrnUserStockModel(**request_body.model_dump(), user_id=user_id)
        db.add(new_stock_item)
        db.commit()
        db.refresh(new_stock_item)
        return new_stock_item, None

    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, ErrorCodeEnum.INTERNAL_ERROR
