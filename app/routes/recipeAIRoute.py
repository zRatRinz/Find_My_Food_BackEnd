from fastapi import APIRouter, File, UploadFile, Depends
from typing import Annotated
from sqlmodel import Session
from app.dependencies import get_current_active_user
from app.db import database
from app.models.userModel import MasUserModel
from app.schemas.recipeDTO import RecipeResponseDTO, RecipePromptContentDTO
from app.schemas.response import StandardResponse
from app.services import recipeAIService 

router = APIRouter(prefix="/recipeAI", tags=["recipeAI"])

@router.post("/analyzeFoodImage",response_model=StandardResponse[list[RecipeResponseDTO]])
async def analyze_food_image(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], 
                             file: UploadFile = File(...),
                             db: Session = Depends(database.get_db)):
    image_bytes = await file.read()
    response = recipeAIService.analyze_food_image(current_user.user_id, image_bytes, db)
    return StandardResponse.success(data=response)

@router.post("/generateRecipeImage")
async def generate_recipe_image(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                                request_body: RecipePromptContentDTO,):
    response = recipeAIService.generate_recipe_image(request_body.recipe_name, request_body.ingredients)
    return StandardResponse.success(data=response)

@router.post("/analyzeIngredientImage", response_model=StandardResponse[list[RecipeResponseDTO]])
async def analyze_ingredient_image(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                                   file: UploadFile = File(...),
                                   db: Session = Depends(database.get_db)):
    image_bytes = await file.read()
    response = recipeAIService.analize_ingredient_image(current_user.user_id, image_bytes, db)
    return StandardResponse.success(data=response)