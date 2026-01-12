from sqlmodel import Session, select, and_, delete
from sqlalchemy.orm import selectinload
from app.core import cloudinary, datetimezone
from app.models.recipeModel import TrnRecipeModel, DtlRecipeIngredientModel, DtlRecipeStepModel
from app.schemas.recipeDTO import CreateNewRecipeDTO, UpdateRecipeHeaderDTO, UpdateRecipeIngredientListDTO, UpdateRecipeStepListDTO

def create_new_recipe(db: Session, request: CreateNewRecipeDTO, user_id: int):
    try:
        recipe_data = request.model_dump(exclude={"ingredients", "steps"})
        new_recipe = TrnRecipeModel(**recipe_data)
        new_recipe.user_id = user_id
        # db.flush()

        # ingredients = [ingredient.model_dump() for ingredient in request.ingredients]
        # steps = [step.model_dump() for step in request.steps]

        new_recipe.ingredients = [DtlRecipeIngredientModel(**ingredient.model_dump()) for ingredient in request.ingredients]
        # db.add_all(new_recipe.ingredients)
        new_recipe.steps = [DtlRecipeStepModel(**step.model_dump()) for step in request.steps]
        # db.add_all(new_recipe.steps)

        db.add(new_recipe)
        db.flush()
        if new_recipe.image_url and "temp-img" in new_recipe.image_url:
            try:
                new_image_url = cloudinary.move_temp_image_to_food_folder(new_recipe.recipe_id, new_recipe.image_url)
                if new_image_url:
                    new_recipe.image_url = new_image_url
            except Exception as cloudinary_ex:
                print(f"Cloudinary Move Failed: {cloudinary_ex}")
                raise cloudinary_ex

        db.commit()
        return True

    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return False
    
def update_recipe_header_by_recipe_id(db: Session, user_id: int, recipe_id: int, request_body: UpdateRecipeHeaderDTO):
    try:
        recipe = db.get(TrnRecipeModel, recipe_id)
        if not recipe:
            print(f"Error: Recipe ID {recipe_id} not found.")
            return None,"ไม่พบรายการอาหารที่ต้องการแก้ไข"
        
        if recipe.user_id != user_id:
            print(f"Error: Not authorized to update recipe with ID {recipe_id}.")
            return None,"ไม่พบรายการอาหารที่ต้องการแก้ไข"
        
        for field, value in request_body.model_dump().items():
            setattr(recipe, field, value)

        recipe.update_date = datetimezone.get_thai_now()
        db.commit()
        # db.refresh(recipe)
        return True, None
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return None, "เกิดข้อผิดพลาดในการแก้ไขรายการอาหาร"
    
def update_recipe_ingredient_by_recipe_id(db: Session, user_id: int, recipe_id: int, request_body: UpdateRecipeIngredientListDTO):
    try:
        recipe = db.get(TrnRecipeModel, recipe_id)
        if not recipe:
            print(f"Error: Recipe ID {recipe_id} not found.")
            return None, "ไม่พบรายการอาหารที่ต้องการแก้ไข"

        if recipe.user_id != user_id:
            print(f"Error: Not authorized to update recipe with ID {recipe_id}.")
            return None ,"ไม่พบรายการอาหารที่ต้องการแก้ไข"
        
        db.exec(delete(DtlRecipeIngredientModel).where(DtlRecipeIngredientModel.recipe_id == recipe_id))
        ingredients = [DtlRecipeIngredientModel(**ingredient.model_dump(), recipe_id=recipe_id) for ingredient in request_body.ingredients]

        db.add_all(ingredients)
        db.commit()
        # for ingredient in ingredients:
        #     db.refresh(ingredient)
        return True, None
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return None, "เกิดข้อผิดพลาดในการแก้ไขวัตถุดิบ"
    
def update_recipe_step_by_recipe_id(db: Session, user_id: int, recipe_id: int, request_body: UpdateRecipeStepListDTO):
    try:
        recipe = db.get(TrnRecipeModel, recipe_id)
        if not recipe:
            print(f"Error: Recipe ID {recipe_id} not found.")
            return None, "ไม่พบรายการอาหารที่ต้องการแก้ไข"
        
        if recipe.user_id != user_id:
            print(f"Error: Not authorized to update recipe with ID {recipe_id}.")
            return None, "ไม่พบรายการอาหารที่ต้องการแก้ไข"
        
        db.exec(delete(DtlRecipeStepModel).where(DtlRecipeStepModel.recipe_id == recipe_id))
        steps = [DtlRecipeStepModel(**step.model_dump(), recipe_id=recipe_id) for step in request_body.steps]

        db.add_all(steps)
        db.commit()
        # for step in steps:
        #     db.refresh(step)
        return True, None
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return None, "เกิดข้อผิดพลาดในการแก้ไขขั้นตอนการทำ"
    
def get_all_recipe(db: Session):
    sql = select(TrnRecipeModel).where(TrnRecipeModel.is_active == True).options(
        selectinload(TrnRecipeModel.user)
    )
    result = db.exec(sql).all()
    return result

def get_recipe_by_name(db: Session, recipe_name: str):
    sql = select(TrnRecipeModel).where(and_(TrnRecipeModel.recipe_name.contains(recipe_name), TrnRecipeModel.is_active == True)).options(
        selectinload(TrnRecipeModel.user)
    )
    result = db.exec(sql).all()
    return result

def get_recipe_detail_by_recipe_id(db: Session, request: int):
    sql = select(TrnRecipeModel).where(TrnRecipeModel.recipe_id == request).options(
        selectinload(TrnRecipeModel.user),
        selectinload(TrnRecipeModel.ingredients).options(
            selectinload(DtlRecipeIngredientModel.ingredient),
            selectinload(DtlRecipeIngredientModel.unit)
        ),
        selectinload(TrnRecipeModel.steps)
    )
    result = db.exec(sql).first()
    return result

def get_my_create_recipe(db: Session, user_id: int):
    sql = select(TrnRecipeModel).where(TrnRecipeModel.user_id == user_id).options(
        selectinload(TrnRecipeModel.user)
    )
    result = db.exec(sql).all()
    return result