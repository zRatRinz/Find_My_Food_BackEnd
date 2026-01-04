from sqlmodel import Session, select,text
from sqlalchemy.orm import selectinload
from app.models.foodModel import FoodModel
from app.schemas.foodDTO import CreateNewFoodModel

def get_all_food(db: Session):
    # sql = text("select * from mas_food")
    sql = select(FoodModel)
    result = db.exec(sql).all()
    # result = db.exec(sql)
    return result
    # return [dict(row) for row in result.mappings()]

def get_food_by_name(db: Session, food:str):
    sql = select(FoodModel).where(FoodModel.food.contains(food))
    result = db.exec(sql).all()
    return result
# def getFoodIngredientById(db:Session, food_id:int):
#     sql = select(Food.food).where(Food.food_id == food_id).options(selectinload(Food.ingredients))
#     result = db.exec(sql).first()
#     return result

def get_food_ingredient_by_id(db:Session, food_id:int):
    sql = select(FoodModel).where(FoodModel.food_id == food_id).options(selectinload(FoodModel.ingredients))
    result = db.exec(sql).first()
    return result

def create_new_food(db:Session, request:CreateNewFoodModel):
    try:
        new_food = FoodModel(
            food = request.food,
            image_url = request.image_url,
            is_public = request.is_public,
            is_active = request.is_active
        )

        db.add(new_food)
        db.commit()
        return True
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return False