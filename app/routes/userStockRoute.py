from fastapi import APIRouter, Depends
from typing import Annotated
from sqlmodel import Session
from app.dependencies import get_current_active_user
from app.db import database
from app.enums.types import StorageTypeEnum
from app.models.userModel import MasUserModel
from app.schemas.userStockDTO import AddUserStockDTO, UpdateItemInUserStockDTO, UserStockDTO, ItemExpirationDTO
from app.schemas.response import StandardResponse
from app.services import userStockService

router = APIRouter(prefix="/userStock", tags=["userStock"])

STORAGE_LABELS = {
    StorageTypeEnum.PANTRY: "อุณหภูมิห้อง",
    StorageTypeEnum.FRIDGE: "ช่องแช่เย็น",
    StorageTypeEnum.FREEZER: "ช่องแช่แข็ง",
}

@router.post("/addUserStock")
def add_user_stock(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                   request_body: AddUserStockDTO,
                   db: Session = Depends(database.get_db)):
    response = userStockService.add_user_stock(db, current_user.user_id, request_body)
    return StandardResponse.success(data=response)

@router.patch("/updateItemInUserStock/{stock_id}")
def update_item_in_user_stock(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                              stock_id: int,
                              request_body: UpdateItemInUserStockDTO,
                              db: Session = Depends(database.get_db)):
    response = userStockService.update_item_in_user_stock(db, current_user.user_id, stock_id, request_body)
    return StandardResponse.success()

@router.delete("/deleteItemInUserStock/{stock_id}")
def delete_item_in_user_stock(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                              stock_id: int,
                              db: Session = Depends(database.get_db)):
    response = userStockService.delete_item_in_user_stock(db, current_user.user_id, stock_id)
    return StandardResponse.success()

@router.get("/getUserStockFromStorage/{storage_location}", response_model=StandardResponse[list[UserStockDTO]])
def get_user_stock_from_storage(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                             storage_location: StorageTypeEnum,
                             db: Session = Depends(database.get_db)):
    response = userStockService.get_user_stock_from_storage(db, current_user.user_id, storage_location)
    return StandardResponse.success(data=response)

@router.get("/getStorageLocation")
def get_storage_location(current_user: Annotated[MasUserModel, Depends(get_current_active_user)]):
    storage_location = [
        {
            "storage_location": location,
            "storage_label": STORAGE_LABELS[location]
        }
        for location in StorageTypeEnum
    ]
    return StandardResponse.success(data=storage_location)

@router.get("/getItemExpireDate/{storage_location}/{item_id}", response_model=StandardResponse[ItemExpirationDTO])
def get_item_expire_date(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                         storage_location: StorageTypeEnum,
                         item_id: int,
                         db: Session = Depends(database.get_db)):
    response = userStockService.get_item_expire_date(db, storage_location, item_id)
    return StandardResponse.success(data=ItemExpirationDTO(expire_date=response))