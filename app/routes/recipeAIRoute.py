from fastapi import APIRouter, File, UploadFile
from app.services import recipeAIService 
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/recipeAI", tags=["recipeAI"])

@router.post("/")
async def predict_food_image(file: UploadFile = File(...)):
    image_bytes = await file.read()
    result = recipeAIService.predict_food_image(image_bytes)
    return StandardResponse.success(data=result)