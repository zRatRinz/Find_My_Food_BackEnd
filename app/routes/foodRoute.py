# from fastapi import APIRouter, Depends, File, UploadFile, Form
# from typing import Annotated
# from sqlmodel import Session
# from app.dependencies import get_current_user
# from app.db import database
# from app.services import foodService
# from app.models.userModel import MasUserModel
# from app.schemas.foodDTO import FoodDTO, FoodWithIngredientDTO, CreateNewFoodDTO
# from app.schemas.response import StandardResponse

# router = APIRouter(prefix="/foods", tags=["foods"])

# @router.get("/")
# def root():
#     return {"message":"555"}
#     # return {
#     #     "message":datetime.now(ZoneInfo("Asia/Bangkok")),
#     #     "now":datetime.now()
#     #     }


# @router.get("/getAllFood", response_model=StandardResponse[list[FoodDTO]])
# def get_all_food_async(db:Session = Depends(database.get_db)):
#     try:
#         response = foodService.get_all_food(db)
#         return StandardResponse.success(data=response)
#     except Exception as ex:
#         return StandardResponse.fail(message=str(ex))
    
# @router.get("/getFoodByName/{food}",response_model=StandardResponse[list[FoodDTO]])
# def get_food_by_name(food:str, db: Session = Depends(database.get_db)):
#     try:
#         response = foodService.get_food_by_name(db, food)
        
#         if not response:
#             return StandardResponse.fail(message="Not Found")
#         return StandardResponse.success(data=response)
#     except Exception as ex:
#         return StandardResponse.fail(message=str(ex))
    
# @router.get("/getFoodIngredientById/{food_id}", response_model=StandardResponse[FoodWithIngredientDTO])
# def get_food_ingredient_by_id_async(food_id:int ,db:Session = Depends(database.get_db)):
#     try:
#         response = foodService.get_food_ingredient_by_id(db, food_id)

#         if not response:
#             return StandardResponse.fail(message="Not Found")
#         return StandardResponse.success(data=response)
#     except Exception as ex:
#         return StandardResponse.fail(message=str(ex))
    
# @router.post("/createNewFood")
# def create_new_food(food:str = Form(...), is_public: bool = Form(True), is_active: bool = Form(True), file: UploadFile = File(...), db:Session = Depends(database.get_db)):
#     try:

#         request = CreateNewFoodDTO(
#             food=food,
#             is_public=is_public,
#             is_active=is_active,
#         )
#         response = foodService.create_new_food(db, request, file)
#         if not response:
#             return StandardResponse.fail(message="บันทึกไม่สำเร็จ")
#         return StandardResponse.success()
#     except Exception as ex:
#         return StandardResponse.fail(message=str(ex))
    

