from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session
from uuid import UUID
from typing import Annotated
from app.dependencies import get_current_user, get_current_user_optional
from app.db import database
from app.services import shoppingCartService
from app.models.userModel import MasUserModel
from app.schemas.shoppingCartDTO import (
    CreateNewShoppingListDTO, AddShoppingItemToShoppingListDTO, UpdateShoppingItemStatusDTO, UpdateShoppingItemQuantityDTO, UpdateShoppingItemUnitDTO,
    UpdateShoppingItemResponseDTO, ShoppingListResponseDTO
)
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/shoppingCart", tags=["shoppingCart"])

@router.post("/createNewShoppingList", response_model=StandardResponse[ShoppingListResponseDTO])
def create_new_shopping_list(request_body: CreateNewShoppingListDTO,
                             guest_token: UUID | None = Header(default=None, alias="X-Guest-Token"),  
                             current_user: MasUserModel | None = Depends(get_current_user_optional), 
                             db:Session = Depends(database.get_db)):
    try:
        user_id = current_user.user_id if current_user else None
        if not user_id and not guest_token:
            raise HTTPException(
                status_code=401,
                detail="ต้อง login หรือเป็น guest ก่อน"
            )
        response, message = shoppingCartService.create_new_shopping_list(db, request_body, user_id, guest_token)
        if not response:
            return StandardResponse.fail(message="บันทึกไม่สำเร็จ")
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.post("/addItemToShoppingList")
def add_item_to_shopping_list(request_body: AddShoppingItemToShoppingListDTO,
                              guest_token: UUID | None = Header(default=None, alias="X-Guest-Token"), 
                              current_user: MasUserModel | None = Depends(get_current_user_optional), 
                              db:Session = Depends(database.get_db)):
    try:
        user_id = current_user.user_id if current_user else None
        if not user_id and not guest_token:
            raise HTTPException(
                status_code=401,
                detail="ต้อง login หรือเป็น guest ก่อน"
            )
        response, message = shoppingCartService.add_item_to_shopping_list(db, request_body, user_id, guest_token)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

@router.patch("/updateShoppingItemStatus/{item_id}", response_model=StandardResponse[UpdateShoppingItemResponseDTO])
def update_shopping_item_status_by_shopping_list_id(item_id: int,
                                                    request_body: UpdateShoppingItemStatusDTO, 
                                                    guest_token: UUID | None = Header(default=None, alias="X-Guest-Token"),
                                                    current_user: MasUserModel | None = Depends(get_current_user_optional), 
                                                    db:Session = Depends(database.get_db)):
    try:
        user_id = current_user.user_id if current_user else None
        if not user_id and not guest_token:
            raise HTTPException(
                status_code=401,
                detail="ต้อง login หรือเป็น guest ก่อน"
            )
        response, message = shoppingCartService.update_shopping_item_status_by_shopping_item_id(db, item_id, request_body, user_id, guest_token)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.patch("/updateShoppingItemQuantity/{item_id}", response_model=StandardResponse[UpdateShoppingItemResponseDTO])
def update_shopping_item_quantity_by_item_id(item_id: int,
                                             request_body: UpdateShoppingItemQuantityDTO,
                                             guest_token: UUID | None = Header(default=None, alias="X-Guest-Token"),
                                             current_user: MasUserModel | None = Depends(get_current_user_optional),
                                             db:Session = Depends(database.get_db)):
    try:
        user_id = current_user.user_id if current_user else None
        if not user_id and not guest_token:
            raise HTTPException(
                status_code=401,
                detail="ต้อง login หรือเป็น guest ก่อน"
            )
        response, message = shoppingCartService.update_shopping_item_quantity_by_item_id(db, item_id, request_body, user_id, guest_token)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

@router.patch("updateShoppingItemUnit/{item_id}", response_model=StandardResponse[UpdateShoppingItemResponseDTO])
def update_shopping_item_unit_by_item_id(item_id: int, 
                                         request_body: UpdateShoppingItemUnitDTO,
                                         guest_token: UUID | None = Header(default=None, alias="X-Guest-Token"),
                                         current_user: MasUserModel | None = Depends(get_current_user_optional),
                                         db:Session = Depends(database.get_db)):
    try:
        user_id = current_user.user_id if current_user else None
        if not user_id and not guest_token:
            raise HTTPException(
                status_code=401,
                detail="ต้อง login หรือเป็น guest ก่อน"
            )
        response, message = shoppingCartService.update_shopping_item_unit_by_item_id(db, item_id, request_body, user_id, guest_token)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.delete("/deleteShoppingList/{list_id}")
def delete_shopping_list(list_id: int,
                         guest_token: UUID | None = Header(default=None, alias="X-Guest-Token"),
                         current_user: MasUserModel | None = Depends(get_current_user_optional),
                         db:Session = Depends(database.get_db)):
    try:
        user_id = current_user.user_id if current_user else None
        if not user_id and not guest_token:
            raise HTTPException(
                status_code=401,
                detail="ต้อง login หรือเป็น guest ก่อน"
            )
        response, message = shoppingCartService.delete_shopping_list_by_shopping_list_id(db, list_id, user_id, guest_token)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

@router.delete("/deleteItemFromShoppingList/{item_id}")
def delete_item_from_shopping_list(item_id: int,
                                   guest_token: UUID | None = Header(default=None, alias="X-Guest-Token"),
                                   current_user: MasUserModel | None = Depends(get_current_user_optional),
                                   db:Session = Depends(database.get_db)):
    try:
        user_id = current_user.user_id if current_user else None
        if not user_id and not guest_token:
            raise HTTPException(
                status_code=401,
                detail="ต้อง login หรือเป็น guest ก่อน"
            )
        response, message = shoppingCartService.delete_shopping_item_by_item_id(db, item_id, user_id, guest_token)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

@router.get("/getShoppingList")
def get_shopping_list(guest_token: UUID | None = Header(default=None, alias="X-Guest-Token"),
                      current_user: MasUserModel | None = Depends(get_current_user_optional),
                      db:Session = Depends(database.get_db)):
    try:
        user_id = current_user.user_id if current_user else None
        if not user_id and not guest_token:
            raise HTTPException(
                status_code=401,
                detail="ต้อง login หรือเป็น guest ก่อน"
            )
        response = shoppingCartService.get_shopping_list_by_user_id(db, user_id, guest_token)
        response_dto = [
            ShoppingListResponseDTO.model_validate(item) for item in response
        ]
        return StandardResponse.success(data=response_dto)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    