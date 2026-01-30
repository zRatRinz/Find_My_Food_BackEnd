from fastapi import APIRouter, Depends, File, UploadFile, Response, status
from typing import Annotated
from sqlmodel import Session
from app.core import cloudinary
from app.db import database
from app.dependencies import get_current_active_user, get_current_user_optional
from app.models.userModel import MasUserModel
from app.schemas.recipeDTO import (
    CreateNewRecipeDTO, UpdateRecipeHeaderDTO, UpdateRecipeIngredientListDTO, UpdateRecipeStepListDTO, RecipeResponseDTO,
    RecipeDetailResponseDTO, RecipeIngredientResponseDTO, IngredientResponseDTO
)
from app.schemas.response import StandardResponse
from app.enums.errorCodeEnum import ErrorCodeEnum
from app.services import recipeService

router = APIRouter(prefix="/recipe", tags=["recipe"])

@router.post("/uploadNewRecipeImage")
async def upload_new_recipe_image(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], file: UploadFile = File(...)):
    try:
        response = cloudinary.upload_temp_image_to_cloudinary(file)
        if not response:
            return StandardResponse.fail(message="อัพโหลดรูปภาพไม่สําเร็จ")
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

@router.post("/createNewRecipe")
def create_new_recipe(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], request: CreateNewRecipeDTO, db:Session = Depends(database.get_db)):
    try:
        response = recipeService.create_new_recipe(db, request, current_user.user_id)
        if not response:
            return StandardResponse.fail(message="บันทึกไม่สำเร็จ")
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.post("/likeRecipe/{recipe_id}")
def like_recipe(response_obj:Response, current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, db:Session = Depends(database.get_db)):
    response, error_code = recipeService.like_recipe(db, current_user.user_id, recipe_id)
    if not response:
        if error_code == ErrorCodeEnum.NOT_FOUND:
            response_obj.status_code = status.HTTP_404_NOT_FOUND
            return StandardResponse.fail(message="ไม่พบรายการอาหารที่ต้องการแก้ไข")
        elif error_code == ErrorCodeEnum.BAD_REQUEST:
            response_obj.status_code = status.HTTP_400_BAD_REQUEST
            return StandardResponse.fail(message="คุณ like รายการนี้ไปแล้ว")
        
        response_obj.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return StandardResponse.fail(message="เกิดข้อผิดพลาดในการด like สูตรอาหาร")
    return StandardResponse.success(response)

@router.delete("/unlikeRecipe/{recipe_id}")
def unlike_recipe(response_obj:Response, current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, db:Session = Depends(database.get_db)):
    response, error_code = recipeService.unlike_recipe(db, current_user.user_id, recipe_id)
    if not response:
        if error_code == ErrorCodeEnum.NOT_FOUND:
            response_obj.status_code = status.HTTP_404_NOT_FOUND
            return StandardResponse.fail(message="ไม่พบรายการอาหารที่ต้องการแก้ไข")
        elif error_code == ErrorCodeEnum.BAD_REQUEST:
            response_obj.status_code = status.HTTP_400_BAD_REQUEST
            return StandardResponse.fail(message="คุณยังไม่ได้ like รายการนี้")
        response_obj.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return StandardResponse.fail(message="เกิดข้อผิดพลาดในการด unlike สูตรอาหาร")
    return StandardResponse.success(response)

    
@router.put("/updateRecipeHeaderById/{recipe_id}")
def update_recipe_header_by_recipe_id(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, request_body: UpdateRecipeHeaderDTO, db:Session = Depends(database.get_db)):
    try:
        response, message = recipeService.update_recipe_header_by_recipe_id(db, current_user.user_id, recipe_id, request_body)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.put("/updateRecipeIngredientById/{recipe_id}")
def update_recipe_ingredient_by_recipe_id(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, request_body: UpdateRecipeIngredientListDTO, db:Session = Depends(database.get_db)):
    try:
        response, message = recipeService.update_recipe_ingredient_by_recipe_id(db, current_user.user_id, recipe_id, request_body)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.put("/updateRecipeStepById/{recipe_id}")
def update_recipe_step_by_recipe_id(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, request_body: UpdateRecipeStepListDTO, db:Session = Depends(database.get_db)):
    try:
        response, message = recipeService.update_recipe_step_by_recipe_id(db, current_user.user_id, recipe_id, request_body)
        if not response:
            return StandardResponse.fail(message=message)
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.get("/getAllRecipe", response_model=StandardResponse[list[RecipeResponseDTO]])
def get_all_recipe(db:Session = Depends(database.get_db)):
    try:
        response = recipeService.get_all_recipe(db)
        # response = [RecipeResponseDTO(
        #     **recipe.model_dump(),
        #     like_count=like_count
        # ) for recipe, like_count in result]
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.get("getRecipeByName/{request}", response_model=StandardResponse[list[RecipeResponseDTO]])
def get_recipe_by_name(request:str, response_obj:Response, db:Session = Depends(database.get_db)):
    response = recipeService.get_recipe_by_name(db, request)
    if response is None:
        response_obj.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return StandardResponse.fail(message="เกิดข้อผิดพลาดในการดึงรายการสูตรอาหาร")
    return StandardResponse.success(data=response)
    
@router.get("/getRecipeDetailById/{recipe_id}", response_model=StandardResponse[RecipeDetailResponseDTO])
def get_recipe_detail_by_recipe_id(response_obj:Response, recipe_id:int, current_user: MasUserModel | None = Depends(get_current_user_optional), db:Session = Depends(database.get_db)):
    user_id = current_user.user_id if current_user else None
    response, error_code = recipeService.get_recipe_detail_by_recipe_id(db, recipe_id, user_id)
    if not response:
        if error_code == ErrorCodeEnum.NOT_FOUND:
            response_obj.status_code = status.HTTP_404_NOT_FOUND
            return StandardResponse.fail(message="ไม่พบรายการอาหารที่ต้องการ")
        
        response_obj.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return StandardResponse.fail(message="เกิดข้อผิดพลาดในการดึงสูตรอาหาร")
    return StandardResponse.success(data=response)
    
@router.get("/getMyCreateRecipe", response_model=StandardResponse[list[RecipeResponseDTO]])
def get_my_create_recipe(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], db:Session = Depends(database.get_db)):
    try:
        response = recipeService.get_my_create_recipe(db, current_user.user_id)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.get("/getIngredientByName/{ingredient_name}", response_model=StandardResponse[list[IngredientResponseDTO]])
def get_ingredient_by_name(ingredient_name:str, db:Session = Depends(database.get_db)):
    try:
        response = recipeService.get_ingredient_by_name(db, ingredient_name)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))