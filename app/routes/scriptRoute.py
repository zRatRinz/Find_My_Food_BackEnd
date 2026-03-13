from fastapi import APIRouter, HTTPException
from app.scripts.build_recipe_vectors import run as build_recipe
from app.scripts.build_user_vectors import run as build_user
from app.core.config import CRON_SECRET_TOKEN

router = APIRouter(prefix="/script", tags=["script"])

@router.get("/runRecommendationScript")
def update_vectors(token: str):
    if token != CRON_SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid Token")
    
    try:
        # 2. สั่งรันเรียงตามลำดับ (Recipe ต้องเสร็จก่อน User)
        print("Starting Cronjob: Building Vectors...")
        build_recipe() 
        build_user()
        print("Cronjob Completed Successfully!")
        
        return {"status": "success", "message": "Vectors updated successfully"}
    except Exception as e:
        print(f"Cronjob Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))