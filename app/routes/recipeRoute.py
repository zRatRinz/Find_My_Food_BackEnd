from fastapi import APIRouter, Depends, File, UploadFile
from typing import Annotated
from sqlmodel import Session
from app.core import cloudinary
from app.db import database
from app.dependencies import get_current_active_user
from app.models.userModel import MasUserModel
from app.schemas.recipeDTO import (
    CreateNewRecipeDTO, UpdateRecipeHeaderDTO, UpdateRecipeIngredientListDTO, UpdateRecipeStepListDTO, RecipeResponseDTO,
    RecipeDetailResponseDTO, RecipeIngredientResponseDTO, IngredientResponseDTO
)
from app.schemas.response import StandardResponse
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
def like_recipe(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, db:Session = Depends(database.get_db)):
    response, message = recipeService.like_recipe(db, current_user.user_id, recipe_id)
    if not response:
        return StandardResponse.fail(message=message)
    return StandardResponse.success()

@router.delete("/unlikeRecipe/{recipe_id}")
def unlike_recipe(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, db:Session = Depends(database.get_db)):
    response, message = recipeService.unlike_recipe(db, current_user.user_id, recipe_id)
    if not response:
        return StandardResponse.fail(message=message)
    return StandardResponse.success()

    
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
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.get("getRecipeByName/{request}", response_model=StandardResponse[list[RecipeResponseDTO]])
def get_recipe_by_name(request:str, db:Session = Depends(database.get_db)):
    try:
        response = recipeService.get_recipe_by_name(db, request)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
@router.get("/getRecipeDetailById/{request}", response_model=StandardResponse[RecipeDetailResponseDTO])
def get_recipe_detail_by_recipe_id(request:int, db:Session = Depends(database.get_db)):
    try:
        response = recipeService.get_recipe_detail_by_recipe_id(db, request)
        return StandardResponse.success(data=response)
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
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