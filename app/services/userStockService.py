from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from sqlalchemy import delete
from datetime import timedelta
from app.core.exceptions import NotFoundException
from app.core import datetimezone
from app.enums.types import StorageTypeEnum
from app.models.userStockModel import TrnUserStockModel
from app.models.recipeModel import MasIngredientModel
from app.models.userModel import MasUserModel
from app.schemas.userStockDTO import AddUserStockDTO, UpdateItemInUserStockDTO

def add_user_stock(db: Session, user_id: int, request_body: AddUserStockDTO):
    try:
        new_stock_item = TrnUserStockModel(**request_body.model_dump(), user_id=user_id)
        db.add(new_stock_item)
        db.commit()
        db.refresh(new_stock_item)
        return new_stock_item
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        raise

def update_item_in_user_stock(db: Session, user_id: int, stock_id: int, request_body: UpdateItemInUserStockDTO):
    item = db.get(TrnUserStockModel, stock_id)
    if not item:
        raise NotFoundException("ไม่พบรายการที่ต้องการแก้ไข")
    
    if request_body.quantity is not None:
        item.quantity = request_body.quantity

    if request_body.unit_id is not None:
        item.unit_id = request_body.unit_id

    if request_body.expire_date is not None:
        item.expire_date = request_body.expire_date

    if request_body.storage_location is not None:
        item.storage_location = request_body.storage_location

    try:
        item.update_date = datetimezone.get_thai_now()
        db.commit()
        db.refresh(item)
        return item
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        raise

def delete_item_in_user_stock(db: Session, user_id: int, stock_id: int):
    try:
        result = db.exec(
            delete(TrnUserStockModel).where(
                TrnUserStockModel.stock_id == stock_id,
                TrnUserStockModel.user_id == user_id
            )
        )

        if result.rowcount == 0:
            raise NotFoundException("ไม่พบรายการที่ต้องการลบ")
        db.commit()
        return True
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        raise

def get_user_stock_from_storage(db: Session, user_id: int, storage_location: StorageTypeEnum):
    result = db.exec(select(TrnUserStockModel).where(
        TrnUserStockModel.user_id == user_id, 
        TrnUserStockModel.storage_location == storage_location
        ).options(joinedload(TrnUserStockModel.unit))
    ).all()
    return result

def get_item_expire_date(db: Session, storage_location: StorageTypeEnum, item_id: int, ):
    item = db.exec(select(MasIngredientModel).where(MasIngredientModel.ingredient_id == item_id)).first()
    if not item:
        raise NotFoundException("ไม่พบรายการที่ต้องการแก้ไข")
    
    if storage_location == StorageTypeEnum.PANTRY:
        days = item.pantry_days
    elif storage_location == StorageTypeEnum.FRIDGE:
        days = item.fridge_days
    elif storage_location == StorageTypeEnum.FREEZER:
        days = item.freezer_days
    else:
        days = None

    if days is None:
        return None
    
    expire_date = datetimezone.get_thai_now().date() + timedelta(days=days)
    return expire_date

def check_item_expire_date(db: Session):
    date_now = datetimezone.get_thai_now().date()
    expire_result = db.exec(
        select(MasUserModel.user_id, MasUserModel.username, MasUserModel.fcm_token)
        .join(TrnUserStockModel, MasUserModel.user_id == TrnUserStockModel.user_id)
        .where(
            TrnUserStockModel.expire_date < date_now + timedelta(days=1),
            MasUserModel.fcm_token != None    
        ).distinct()
    ).all()

    return [
        {
            "user_id": user.user_id,
            "username": user.username,
            "fcm_token": user.fcm_token
        }
        for user in expire_result
    ]