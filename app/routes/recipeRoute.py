from fastapi import APIRouter, Depends, File, UploadFile, Query
from typing import Annotated
from sqlmodel import Session
from app.core import cloudinary
from app.db import database
from app.dependencies import get_current_active_user, get_current_user_optional
from app.models.userModel import MasUserModel
from app.schemas.recipeDTO import (
    CreateNewRecipeDTO, UpdateRecipeHeaderDTO, UpdateRecipeIngredientListDTO, UpdateRecipeStepListDTO, RecipeResponseDTO,
    RecipeDetailResponseDTO, IngredientResponseDTO, CategoryResponseDTO, RecipeFilterOptionResponseDTO, TagResponseDTO,
    UpdateRecipeImageDTO, RecipeWithHighLikeResponseDTO
)
from app.schemas.response import StandardResponse
from app.services import recipeService

router = APIRouter(prefix="/recipe", tags=["recipe"])

@router.post("/uploadNewRecipeImage")
async def upload_new_recipe_image(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], file: UploadFile = File(...)):
    response = cloudinary.upload_temp_image_to_cloudinary(file)
    if not response:
        return StandardResponse.fail(message="อัพโหลดรูปภาพไม่สําเร็จ")
    return StandardResponse.success(data=response)

@router.post("/updateRecipeImage")
async def update_recipe_image(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe: UpdateRecipeImageDTO, db:Session = Depends(database.get_db)):
    response = recipeService.update_recipe_image(recipe.recipe_id, recipe.image_url, db)
    return StandardResponse.success()

@router.post("/createNewRecipe")
def create_new_recipe(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], request_body: CreateNewRecipeDTO, db:Session = Depends(database.get_db)):
        response = recipeService.create_new_recipe(db, request_body, current_user.user_id)
        if not response:
            return StandardResponse.fail(message="บันทึกไม่สำเร็จ")
        return StandardResponse.success()
    
@router.post("/likeRecipe/{recipe_id}")
def like_recipe(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, db:Session = Depends(database.get_db)):
    response = recipeService.like_recipe(db, current_user.user_id, recipe_id)
    return StandardResponse.success(response)

@router.delete("/unlikeRecipe/{recipe_id}")
def unlike_recipe(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, db:Session = Depends(database.get_db)):
    response = recipeService.unlike_recipe(db, current_user.user_id, recipe_id)
    return StandardResponse.success(response)
    
@router.delete("/deleteMyRecipeByRecipeId/{recipe_id}")
def delete_my_recipe_by_recipe_id(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, db:Session = Depends(database.get_db)):
    response = recipeService.delete_my_recipe_by_recipe_id(current_user.user_id, recipe_id, db)
    return StandardResponse.success()

@router.put("/updateRecipeHeaderById/{recipe_id}")
def update_recipe_header_by_recipe_id(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, request_body: UpdateRecipeHeaderDTO, db:Session = Depends(database.get_db)):
    response = recipeService.update_recipe_header_by_recipe_id(db, current_user.user_id, recipe_id, request_body)
    return StandardResponse.success()
    
@router.put("/updateRecipeIngredientById/{recipe_id}")
def update_recipe_ingredient_by_recipe_id(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, request_body: UpdateRecipeIngredientListDTO, db:Session = Depends(database.get_db)):
    response = recipeService.update_recipe_ingredient_by_recipe_id(db, current_user.user_id, recipe_id, request_body)
    return StandardResponse.success()
    
@router.put("/updateRecipeStepById/{recipe_id}")
def update_recipe_step_by_recipe_id(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], recipe_id:int, request_body: UpdateRecipeStepListDTO, db:Session = Depends(database.get_db)):
    response = recipeService.update_recipe_step_by_recipe_id(db, current_user.user_id, recipe_id, request_body)
    return StandardResponse.success(data=response)
    
@router.get("/getAllRecipe", response_model=StandardResponse[list[RecipeResponseDTO]])
def get_all_recipe(current_user: MasUserModel | None = Depends(get_current_user_optional), db:Session = Depends(database.get_db)):
    user_id = current_user.user_id if current_user else None
    response = recipeService.get_all_recipe(user_id, db)
    return StandardResponse.success(data=response)

@router.get("/getRecommendRecipeFromStock", response_model=StandardResponse[list[RecipeResponseDTO]])
def get_recommend_recipe_from_stock(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], db:Session = Depends(database.get_db)):  
    response = recipeService.get_recommend_recipe_from_stock(db, current_user.user_id)
    return StandardResponse.success(data=response)

@router.get("/getRecommendRecipeForYou", response_model=StandardResponse[list[RecipeResponseDTO]])
def get_recommend_recipe_for_you(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], db:Session = Depends(database.get_db)):  
    response = recipeService.get_recommend_recipe_for_you(db, current_user.user_id)
    return StandardResponse.success(data=response)

@router.get("getRecipeByName/{recipe_name}", response_model=StandardResponse[list[RecipeResponseDTO]])
def get_recipe_by_name(recipe_name:str,
                       current_user: MasUserModel | None = Depends(get_current_user_optional),
                       db:Session = Depends(database.get_db)):
    user_id = current_user.user_id if current_user else None
    response = recipeService.get_recipe_by_name(user_id, recipe_name, db)
    return StandardResponse.success(data=response)
    
@router.get("/getRecipeDetailById/{recipe_id}", response_model=StandardResponse[RecipeDetailResponseDTO])
def get_recipe_detail_by_recipe_id(recipe_id:int, current_user: MasUserModel | None = Depends(get_current_user_optional), db:Session = Depends(database.get_db)):
    user_id = current_user.user_id if current_user else None
    response = recipeService.get_recipe_detail_by_recipe_id(db, recipe_id, user_id)
    return StandardResponse.success(data=response)
    
@router.get("/getMyCreateRecipe", response_model=StandardResponse[list[RecipeResponseDTO]])
def get_my_create_recipe(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], db:Session = Depends(database.get_db)):
    response = recipeService.get_my_create_recipe(db, current_user.user_id)
    return StandardResponse.success(data=response)
    
@router.get("/getIngredientByName/{ingredient_name}", response_model=StandardResponse[list[IngredientResponseDTO]])
def get_ingredient_by_name(ingredient_name:str, db:Session = Depends(database.get_db)):
    response = recipeService.get_ingredient_by_name(db, ingredient_name)
    return StandardResponse.success(data=response)

@router.get("/getRecipeCategory", response_model=StandardResponse[list[CategoryResponseDTO]])
def get_recipe_category(db:Session = Depends(database.get_db)):
    response = recipeService.get_recipe_category(db)
    return StandardResponse.success(data=response)

@router.get("/getRecipeTag", response_model=StandardResponse[list[TagResponseDTO]])
def get_recipe_tag(db:Session = Depends(database.get_db)):
    response = recipeService.get_recipe_tag(db)
    return StandardResponse.success(data=response)

@router.get("/getRecipeByCategory/{category_id}")
def get_recipe_by_category(category_id:int,
                           current_user: MasUserModel | None = Depends(get_current_user_optional),
                           db:Session = Depends(database.get_db)):
    user_id = current_user.user_id if current_user else None
    response = recipeService.get_recipe_by_category(user_id, category_id, db)
    return StandardResponse.success(data=response)

@router.get("/getRecipeFilterOption", response_model=StandardResponse[RecipeFilterOptionResponseDTO])
def get_recipe_filter_option(db:Session = Depends(database.get_db)):
    response = recipeService.get_recipe_filter_option(db)
    return StandardResponse.success(data=response)

@router.get("/getSearchRecipeFilterOption", response_model=StandardResponse[RecipeWithHighLikeResponseDTO])
def get_search_recipe_filter_option(categories: list[int] = Query(default=[]), 
                                    tags: list[int] = Query(default=[]),
                                    current_user: MasUserModel | None = Depends(get_current_user_optional), 
                                    db:Session = Depends(database.get_db)):
    user_id = current_user.user_id if current_user else None
    response = recipeService.get_search_recipe_filter_option(user_id, categories, tags, db)
    return StandardResponse.success(data=response)

@router.get("/getRecipeByIngredientAndTag")
def get_recipe_by_ingredient_and_tag(ingredient_list: list[str] = Query(default=[]),
                                     tag_list: list[int] = Query(default=[]),
                                     current_user: MasUserModel | None = Depends(get_current_user_optional), 
                                     db: Session = Depends(database.get_db)):
    user_id = current_user.user_id if current_user else None
    response = recipeService.get_recipe_by_ingredient_name(user_id, ingredient_list, tag_list, db)
    return StandardResponse.success(data=response)