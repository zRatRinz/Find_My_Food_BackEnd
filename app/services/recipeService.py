from sqlmodel import Session, select, delete, func
from sqlalchemy.orm import selectinload, joinedload
from app.core import cloudinary, datetimezone
from app.models.recipeModel import TrnRecipeModel, DtlRecipeIngredientModel, DtlRecipeStepModel, MapRecipeLikeModel, MasIngredientModel
from app.schemas.recipeDTO import (
    CreateNewRecipeDTO, UpdateRecipeHeaderDTO, UpdateRecipeIngredientListDTO, UpdateRecipeStepListDTO, 
    RecipeResponseDTO, RecipeIngredientResponseDTO, RecipeStepResponseDTO, RecipeDetailResponseDTO, LikeRecipeResponseDTO
)
from app.enums.errorCodeEnum import ErrorCodeEnum

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
    
def like_recipe(db: Session, user_id: int, recipe_id: int):
    try:
        recipe = db.get(TrnRecipeModel, recipe_id)
        if not recipe:
            print(f"Error: Recipe ID {recipe_id} not found.")
            return None, ErrorCodeEnum.NOT_FOUND
        like_exist_sql = select(MapRecipeLikeModel).where(MapRecipeLikeModel.user_id == user_id, MapRecipeLikeModel.recipe_id == recipe_id)
        like_exist = db.exec(like_exist_sql).first()
        if like_exist:
            return None, ErrorCodeEnum.BAD_REQUEST
        
        like = MapRecipeLikeModel(user_id=user_id, recipe_id=recipe_id)
        db.add(like)
        db.commit()
        new_count = db.scalar(
            select(func.count(MapRecipeLikeModel.user_id))
            .where(MapRecipeLikeModel.recipe_id == recipe_id)
        )
        is_liked = True
        return LikeRecipeResponseDTO(like_count=new_count, is_liked=is_liked), None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, ErrorCodeEnum.INTERNAL_ERROR
    
def unlike_recipe(db: Session, user_id: int, recipe_id: int):
    try:
        recipe = db.get(TrnRecipeModel, recipe_id)
        if not recipe:
            print(f"Error: Recipe ID {recipe_id} not found.")
            return None, ErrorCodeEnum.NOT_FOUND
        like_exist_sql = select(MapRecipeLikeModel).where(MapRecipeLikeModel.user_id == user_id, MapRecipeLikeModel.recipe_id == recipe_id)
        like_exist = db.exec(like_exist_sql).first()
        if not like_exist:
            return None, ErrorCodeEnum.BAD_REQUEST
        
        db.delete(like_exist)
        db.commit()
        new_count = db.scalar(
            select(func.count(MapRecipeLikeModel.user_id))
            .where(MapRecipeLikeModel.recipe_id == recipe_id)
        )
        is_liked = False
        return LikeRecipeResponseDTO(like_count=new_count, is_liked=is_liked), None
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None, ErrorCodeEnum.INTERNAL_ERROR
    
def get_all_recipe(db: Session):
    sql = select(
        TrnRecipeModel, func.count(MapRecipeLikeModel.user_id).label("like_count")
        ).outerjoin(
            MapRecipeLikeModel,
            MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
        ).where(
            TrnRecipeModel.is_active == True
        ).group_by(
            TrnRecipeModel.recipe_id
        ).options(
            selectinload(TrnRecipeModel.user)
        )
    
    result = db.exec(sql).all()
    return [ RecipeResponseDTO.model_validate(
        recipe, from_attributes=True
    ).model_copy(
        update={"like_count": like_count}
    ) for recipe, like_count in result]

def get_recipe_by_name(db: Session, recipe_name: str):
    try:
        sql = select(
            TrnRecipeModel, func.count(MapRecipeLikeModel.user_id).label("like_count")
            ).outerjoin(
                MapRecipeLikeModel,
                MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
            ).where(
                TrnRecipeModel.recipe_name.contains(recipe_name), TrnRecipeModel.is_active.is_(True)
            ).group_by(
                TrnRecipeModel.recipe_id
            ).options(
            selectinload(TrnRecipeModel.user)
        )
        result = db.exec(sql).all()
        return [ RecipeResponseDTO.model_validate(
            recipe, from_attributes=True
        ).model_copy(
            update={"like_count": like_count}
        ) for recipe, like_count in result]
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        return None

def get_recipe_detail_by_recipe_id(db: Session, recipe_id: int, user_id: int | None = None):
    try:
        recipe = db.get(TrnRecipeModel, recipe_id)
        if not recipe:
            print(f"Error: Recipe ID {recipe_id} not found.")
            return None, ErrorCodeEnum.NOT_FOUND
        # ingredients = db.exec(select(DtlRecipeIngredientModel).where(DtlRecipeIngredientModel.recipe_id == recipe_id)).all()
        ingredients = db.exec(
            select(DtlRecipeIngredientModel)
            .where(DtlRecipeIngredientModel.recipe_id == recipe_id)
            .options(
                joinedload(DtlRecipeIngredientModel.ingredient),
                joinedload(DtlRecipeIngredientModel.unit)
            )
        ).all()
        steps = db.exec(select(DtlRecipeStepModel).where(DtlRecipeStepModel.recipe_id == recipe_id).order_by(DtlRecipeStepModel.step_no)).all()
        like_count = db.scalar(select(func.count(MapRecipeLikeModel.user_id)).where(MapRecipeLikeModel.recipe_id == recipe_id))
        
        is_liked = False
        if user_id:
            like_exist_sql = select(func.count()).where(MapRecipeLikeModel.user_id == user_id, MapRecipeLikeModel.recipe_id == recipe_id)
            like_exist = db.scalar(like_exist_sql)
            is_liked = like_exist > 0

        return RecipeDetailResponseDTO(
            recipe = RecipeResponseDTO.model_validate(recipe).model_copy(update={"like_count": like_count}),
            ingredients = [RecipeIngredientResponseDTO.model_validate(ingredient) for ingredient in ingredients],
            steps = [RecipeStepResponseDTO.model_validate(step) for step in steps],
            is_liked = is_liked
        ), None
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return None, ErrorCodeEnum.INTERNAL_ERROR

def get_my_create_recipe(db: Session, user_id: int):
    sql = select(TrnRecipeModel).where(TrnRecipeModel.user_id == user_id).options(
        selectinload(TrnRecipeModel.user)
    )
    result = db.exec(sql).all()
    return result

def get_ingredient_by_name(db: Session, ingredient_name: str):
    sql = select(MasIngredientModel).where(MasIngredientModel.ingredient_name.ilike(f"%{ingredient_name}%"))
    result = db.exec(sql).all()
    return result