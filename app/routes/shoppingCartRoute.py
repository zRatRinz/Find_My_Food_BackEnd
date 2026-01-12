from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import Annotated
from app.dependencies import get_current_user
from app.db import database
from app.services import shoppingCartService
from app.models.userModel import MasUserModel
from app.schemas.shoppingCartDTO import (
    CreateNewShoppingListDTO, AddShoppingItemToShoppingListDTO, UpdateShoppingItemStatusDTO, UpdateShoppingItemQuantityDTO, UpdateShoppingItemUnitDTO,
    UpdateShoppingItemResponseDTO, ShoppingListResponseDTO
)
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/shoppingCart", tags=["shoppingCart"])

@router.post("/createNewShoppingList")
def create_new_shopping_list(request: CreateNewShoppingListDTO, current_user: Annotated[MasUserModel, Depends(get_current_user)], db:Session = Depends(database.get_db)):
    try:
        response = shoppingCartService.create_new_shopping_list(db, request, current_user.user_id)
        if not response:
            return StandardResponse.fail(message="บันทึกไม่สำเร็จ")
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.post("/addItemToShoppingList")
def add_item_to_shopping_list(current_user: Annotated[MasUserModel, Depends(get_current_user)], request_body: AddShoppingItemToShoppingListDTO, db:Session = Depends(database.get_db)):
    try:
        response, message = shoppingCartService.add_item_to_shopping_list(db, current_user.user_id, request_body)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

@router.patch("/updateShoppingItemStatus/{item_id}", response_model=StandardResponse[UpdateShoppingItemResponseDTO])
def update_shopping_item_status_by_shopping_list_id(current_user: Annotated[MasUserModel, Depends(get_current_user)], item_id: int, request_body: UpdateShoppingItemStatusDTO, db:Session = Depends(database.get_db)):
    try:
        response, message = shoppingCartService.update_shopping_item_status_by_shopping_item_id(db, current_user.user_id, item_id, request_body)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.patch("/updateShoppingItemQuantity/{item_id}", response_model=StandardResponse[UpdateShoppingItemResponseDTO])
def update_shopping_item_quantity_by_item_id(current_user: Annotated[MasUserModel, Depends(get_current_user)], item_id: int, request_body: UpdateShoppingItemQuantityDTO, db:Session = Depends(database.get_db)):
    try:
        response, message = shoppingCartService.update_shopping_item_quantity_by_item_id(db, current_user.user_id, item_id, request_body)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

@router.patch("updateShoppingItemUnit/{item_id}", response_model=StandardResponse[UpdateShoppingItemResponseDTO])
def update_shopping_item_unit_by_item_id(current_user: Annotated[MasUserModel, Depends(get_current_user)], item_id: int, request_body: UpdateShoppingItemUnitDTO, db:Session = Depends(database.get_db)):
    try:
        response, message = shoppingCartService.update_shopping_item_unit_by_item_id(db, current_user.user_id, item_id, request_body)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

@router.get("/getShoppingList")
def get_shopping_list(current_user: Annotated[MasUserModel, Depends(get_current_user)], db:Session = Depends(database.get_db)):
    try:
        response = shoppingCartService.get_shopping_list_by_user_id(db, current_user.user_id)
        response_dto = [
            ShoppingListResponseDTO.model_validate(item) for item in response
        ]
        return StandardResponse.success(data=response_dto)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    