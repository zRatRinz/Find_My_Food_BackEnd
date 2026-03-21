from sqlmodel import Session, select, delete, func, desc, or_, distinct, intersect, literal
from sqlalchemy.orm import selectinload, joinedload
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import json
import scipy.sparse as sp
from sklearn.feature_extraction.text import TfidfVectorizer
from collections import Counter

from app.core import cloudinary, datetimezone, aiConfig
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.recipeModel import (
    TrnRecipeModel, DtlRecipeIngredientModel, DtlRecipeStepModel, MapRecipeLikeModel, MasIngredientModel, 
    MasTagModel, MapRecipeTagModel, MapRecipeImageVectorModel
)
from app.models.userStockModel import TrnUserStockModel
from app.models.systemModel import SysModelVocabularyModel, MapRecipeVectorModel
from app.schemas.recipeDTO import (
    CreateNewRecipeDTO, UpdateRecipeHeaderDTO, UpdateRecipeIngredientListDTO, UpdateRecipeStepListDTO, RecipeResponseDTO, 
    RecipeHeaderResponseDTO, RecipeIngredientResponseDTO, RecipeStepResponseDTO, RecipeDetailResponseDTO, LikeRecipeResponseDTO,
    RecipeWithHighLikeResponseDTO
)
from app.services import vectorStoreService
from app.scripts.build_recipe_vectors import thai_tokenizer
import time

MIN_SCORE_THRESHOLD = 0.8
BONUS_SCORE = 0.2
EXACT_MATCH_BONUS = 2.0
MOBILENET_AGREE_BONUS = 0.15

NORMALIZE_MAP = {
    "เส้นหมี่": "หมี่",
    "บะหมี่": "หมี่"
}

LOW_WEIGHT_WORDS = {"ข้าว", "เส้น", "หมี่", "บะหมี่", "น้ำ", "แห้ง", "ราด", "หน้า", "อาหาร", "จาน", "เมนู", "สูตร"}
MEDIUM_WEIGHT_WORDS = {"หมู", "ไก่", "เนื้อ", "ปลา", "กุ้ง", "หมึก", "ทะเล", "หอย", "ปู", "ไข่", "เต้าหู้", "ปลากระป๋อง"}
HIGH_VALUE_WORDS = {
    "มัสมั่น", "กะเพรา", "ต้มยำ", "ผัดไทย", "ขี้เมา", "เขียวหวาน", 
    "ส้มตำ", "ราดหน้า", "สุกี้", "ซีอิ๊ว", "หมูแดง", "หมูกรอบ", "สามชั้น", 
    "ผงกะหรี่", "ผัดฉ่า", "ยำ", "แซ่บ", "แกงส้ม", "แกงเหลือง", "ข้าวซอย", "อเมริกัน",
    "กระเทียม", "พริกแกง", "คะน้า", "ไข่เจียว", "ลาบ", "น้ำตก", "ข้าวมันไก่", "ข้าวหมก"
}

def get_token_weight(token, db_token_freq=None):
    if token in HIGH_VALUE_WORDS:
        return 3.0
    elif token in MEDIUM_WEIGHT_WORDS:
        return 1.0 
    elif token in LOW_WEIGHT_WORDS:
        return 0.5

    if db_token_freq:
        freq = db_token_freq.get(token, 1)

        if freq > 50:
            return 0.5
        elif freq > 10:
            return 1.0
        else:
            return 2.0

    return 1.0

def token_match(token, db_recipe_name, db_tokens):
    if token in db_tokens:
        return True
    
    if len(token) >= 3 and token in db_recipe_name:
        return True

    if len(token) > 3:
        for i in range(1, len(token)):
            left = token[:i]
            right = token[i:]
            if left in db_tokens and right in db_tokens:
                return True

    return False

def tokenize_and_normalize(text):
    tokens = thai_tokenizer(text)
    return [NORMALIZE_MAP.get(t, t) for t in tokens]

def create_new_recipe(db: Session, request_body: CreateNewRecipeDTO, user_id: int):
    try:
        recipe_data = request_body.model_dump(exclude={"categories", "tags", "ingredients", "steps"})
        new_recipe = TrnRecipeModel(**recipe_data)
        new_recipe.user_id = user_id

        new_recipe.ingredients = [DtlRecipeIngredientModel(**ingredient.model_dump()) for ingredient in request_body.ingredients]
        new_recipe.steps = [DtlRecipeStepModel(**step.model_dump()) for step in request_body.steps]

        tags_list = request_body.tags or []
        all_tags = list(set(request_body.categories + tags_list))
        valid_tags = db.exec(
                select(MasTagModel).where(MasTagModel.tag_id.in_(all_tags))
        ).all()
        tag_dict = {tag.tag_id: tag for tag in valid_tags}
        if not request_body.categories:
            raise BadRequestException("สูตรอาหารต้องมีหมวดหมู่หลัก (Category) อย่างน้อย 1 แท็ก")
        
        for tag_id in request_body.categories:
            if tag_id not in tag_dict:
                raise NotFoundException(f"ไม่พบหมวดหมู่หลัก (Category ID: {tag_id}) ในระบบ")
            
            if tag_dict[tag_id].tag_type != "category":
                raise NotFoundException(f"ไม่พบหมวดหมู่หลัก (Category ID: {tag_id}) ในระบบ")

        if tags_list:
            for tag_id in tags_list:
                if tag_id not in tag_dict:
                    raise NotFoundException(f"ไม่พบแท็ก (Tag ID: {tag_id}) ในระบบ")
                
                if tag_dict[tag_id].tag_type == "category":
                    raise NotFoundException(f"ไม่พบแท็ก (Tag ID: {tag_id}) ในระบบ")
        
        new_recipe.recipe_tags = [MapRecipeTagModel(tag_id=tag_id) for tag_id in all_tags]

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
        raise

def update_recipe_image(recipe_id: int, image_url: str, db: Session):
    if "food-img/" not in image_url:
        try:
            response = cloudinary.move_temp_image_to_food_folder(recipe_id, image_url)
            if response:
                image_url = response
        except Exception as cloudinary_ex:
            print(f"Cloudinary Move Failed: {cloudinary_ex}")
            raise cloudinary_ex
    
    try:
        recipe = db.get(TrnRecipeModel, recipe_id)
        if recipe.image_url == image_url:
            return True
        recipe.image_url = image_url
        recipe.update_date = datetimezone.get_thai_now()
        db.commit()
        return True
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise
    
def update_recipe_header_by_recipe_id(db: Session, user_id: int, recipe_id: int, request_body: UpdateRecipeHeaderDTO):
    recipe = db.get(TrnRecipeModel, recipe_id)
    if not recipe:
        print(f"Error: Recipe ID {recipe_id} not found.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")
        
    if recipe.user_id != user_id:
        print(f"Error: Not authorized to update recipe with ID {recipe_id}.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")
        
    try:
        update_data = request_body.model_dump(exclude={"categories", "tags", "is_created_by_ai"}, exclude_unset=True)
        for field, value in update_data.items():
            setattr(recipe, field, value)

        if recipe.is_created_by_ai:
            recipe.is_active = True

        recipe.update_date = datetimezone.get_thai_now()

        db.exec(
            delete(MapRecipeTagModel).where(MapRecipeTagModel.recipe_id == recipe_id)
        )

        tags_list = request_body.tags or []
        all_tags = list(set(request_body.categories + tags_list))
        valid_tags = db.exec(
                select(MasTagModel).where(MasTagModel.tag_id.in_(all_tags))
        ).all()
        tag_dict = {tag.tag_id: tag for tag in valid_tags}
        
        if not request_body.categories:
            raise BadRequestException("สูตรอาหารต้องมีหมวดหมู่หลัก (Category) อย่างน้อย 1 แท็ก")
        
        for tag_id in request_body.categories:
            if tag_id not in tag_dict:
                raise NotFoundException(f"ไม่พบหมวดหมู่หลัก (Category ID: {tag_id}) ในระบบ")
            
            if tag_dict[tag_id].tag_type != "category":
                raise NotFoundException(f"ไม่พบหมวดหมู่หลัก (Category ID: {tag_id}) ในระบบ")

        if tags_list:
            for tag_id in tags_list:
                if tag_id not in tag_dict:
                    raise NotFoundException(f"ไม่พบแท็ก (Tag ID: {tag_id}) ในระบบ")
                
                if tag_dict[tag_id].tag_type == "category":
                    raise NotFoundException(f"ไม่พบแท็ก (Tag ID: {tag_id}) ในระบบ")

        tags = [MapRecipeTagModel(recipe_id=recipe_id, tag_id=tag_id) for tag_id in all_tags]
        db.add_all(tags)

        db.commit()
        # db.refresh(recipe)
        return True
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise
    
def update_recipe_ingredient_by_recipe_id(db: Session, user_id: int, recipe_id: int, request_body: UpdateRecipeIngredientListDTO):
    recipe = db.get(TrnRecipeModel, recipe_id)
    if not recipe:
        print(f"Error: Recipe ID {recipe_id} not found.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")

    if recipe.user_id != user_id:
        print(f"Error: Not authorized to update recipe with ID {recipe_id}.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")
        
    try:
        db.exec(delete(DtlRecipeIngredientModel).where(DtlRecipeIngredientModel.recipe_id == recipe_id))
        ingredients = [DtlRecipeIngredientModel(**ingredient.model_dump(), recipe_id=recipe_id) for ingredient in request_body.ingredients]

        db.add_all(ingredients)
        db.commit()
        # for ingredient in ingredients:
        #     db.refresh(ingredient)
        return True
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise
    
def update_recipe_step_by_recipe_id(db: Session, user_id: int, recipe_id: int, request_body: UpdateRecipeStepListDTO):
    recipe = db.get(TrnRecipeModel, recipe_id)
    if not recipe:
        print(f"Error: Recipe ID {recipe_id} not found.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")
        
    if recipe.user_id != user_id:
        print(f"Error: Not authorized to update recipe with ID {recipe_id}.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")
        
    try:
        db.exec(delete(DtlRecipeStepModel).where(DtlRecipeStepModel.recipe_id == recipe_id))
        steps = [DtlRecipeStepModel(**step.model_dump(), recipe_id=recipe_id) for step in request_body.steps]

        db.add_all(steps)
        db.commit()
        # for step in steps:
        #     db.refresh(step)
        return True
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise
    
def like_recipe(db: Session, user_id: int, recipe_id: int):
    try:
        recipe = db.get(TrnRecipeModel, recipe_id)
        if not recipe:
            print(f"Error: Recipe ID {recipe_id} not found.")
            raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")

        like_exist_sql = select(MapRecipeLikeModel).where(MapRecipeLikeModel.user_id == user_id, MapRecipeLikeModel.recipe_id == recipe_id)
        like_exist = db.exec(like_exist_sql).first()
        if like_exist:
            raise BadRequestException("คุณ like สูตรอาหารนี้ไปแล้ว")
        
        like = MapRecipeLikeModel(user_id=user_id, recipe_id=recipe_id)
        db.add(like)
        db.commit()
        new_count = db.scalar(
            select(func.count(MapRecipeLikeModel.user_id))
            .where(MapRecipeLikeModel.recipe_id == recipe_id)
        )
        is_liked = True
        return LikeRecipeResponseDTO(like_count=new_count, is_liked=is_liked)
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        raise
    
def unlike_recipe(db: Session, user_id: int, recipe_id: int):
    recipe = db.get(TrnRecipeModel, recipe_id)
    if not recipe:
        print(f"Error: Recipe ID {recipe_id} not found.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")
        
    like_exist_sql = select(MapRecipeLikeModel).where(MapRecipeLikeModel.user_id == user_id, MapRecipeLikeModel.recipe_id == recipe_id)
    like_exist = db.exec(like_exist_sql).first()
    if not like_exist:
        raise BadRequestException("คุณยังไม่ได้ like รายการนี้")
        
    try:    
        db.delete(like_exist)
        db.commit()
        new_count = db.scalar(
            select(func.count(MapRecipeLikeModel.user_id))
            .where(MapRecipeLikeModel.recipe_id == recipe_id)
        )
        is_liked = False
        return LikeRecipeResponseDTO(like_count=new_count, is_liked=is_liked)
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        raise

def delete_my_recipe_by_recipe_id(user_id: int, recipe_id: int, db: Session):
    recipe = db.get(TrnRecipeModel, recipe_id)
    if not recipe:
        print(f"Error: Recipe ID {recipe_id} not found.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")
        
    if recipe.user_id != user_id:
        print(f"Error: Not authorized to delete recipe with ID {recipe_id}.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")
        
    try:
        recipe.is_active = False
        recipe.update_date = datetimezone.get_thai_now()
        db.commit()
        return True
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        raise

def get_all_recipe(user_id: int | None, db: Session):
    if user_id:
        visibility_condition = or_(
            TrnRecipeModel.is_public == True,
            TrnRecipeModel.user_id == user_id
        )

    else:
        visibility_condition = TrnRecipeModel.is_public == True
    
    query = select(
        TrnRecipeModel, 
        func.count(MapRecipeLikeModel.user_id).label("like_count"),
        func.count(MapRecipeLikeModel.user_id).filter(MapRecipeLikeModel.user_id == user_id).label("is_liked")
    ).outerjoin(
        MapRecipeLikeModel,
        MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
    ).where(
        TrnRecipeModel.is_active == True, visibility_condition
    ).group_by(
        TrnRecipeModel.recipe_id
    ).options(
        selectinload(TrnRecipeModel.user),
        selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
    )
    
    result = db.exec(query).all()

    # gen_z_recipes = []
    # all_recipes = []

    # for recipe, like_count, is_liked in result:
    #     dto = RecipeResponseDTO.model_validate(
    #         recipe, from_attributes=True
    #     ).model_copy(
    #         update={"like_count": like_count, "is_liked": is_liked > 0}
    #     )

    #     all_recipes.append(dto)

    #     if "Gen Z" in dto.tags and like_count > 0:
    #         gen_z_recipes.append(dto)

    # gen_z_recipes.sort(key=lambda x: x.like_count, reverse=True)
    # top5_gen_z_recipes = gen_z_recipes[:5]

    # return RecipeWithHighLikeResponseDTO(
    #     gen_z_recipes=top5_gen_z_recipes,
    #     recipes=all_recipes
    # )
    return [ RecipeResponseDTO.model_validate(
        recipe, from_attributes=True
    ).model_copy(
        update={"like_count": like_count, "is_liked": is_liked > 0}
    ) for recipe, like_count, is_liked in result]

def get_recommend_recipe_from_stock(db: Session, user_id: int):
    try:
        user_stock = db.exec(select(TrnUserStockModel.ingredient_id, TrnUserStockModel.item_name).where(TrnUserStockModel.user_id == user_id)).all()
        if not user_stock:
            return []
        
        visibility_condition = or_(
            TrnRecipeModel.is_public == True,
            TrnRecipeModel.user_id == user_id
        )
        
        ingredient_ids = [ingredient.ingredient_id for ingredient in user_stock if ingredient.ingredient_id]
        item_names = [ingredient.item_name for ingredient in user_stock if ingredient.item_name]

        match_count = func.count(DtlRecipeIngredientModel.ingredient_id)

        total_count = (
            select(func.count(DtlRecipeIngredientModel.ingredient_id))
            .where(DtlRecipeIngredientModel.recipe_id == TrnRecipeModel.recipe_id)
            .correlate(TrnRecipeModel)
            .scalar_subquery()
        )

        match_percentage = (match_count * 100.0 / total_count).label("match_percentage")

        main_sql = (
            select(
                TrnRecipeModel,
                func.count(MapRecipeLikeModel.user_id).label("like_count"),
                func.count(MapRecipeLikeModel.user_id).filter(MapRecipeLikeModel.user_id == user_id).label("is_liked"),
                match_percentage
            )
            .join(
                DtlRecipeIngredientModel,
                DtlRecipeIngredientModel.recipe_id == TrnRecipeModel.recipe_id
            )
            .join(
                MasIngredientModel,
                MasIngredientModel.ingredient_id == DtlRecipeIngredientModel.ingredient_id
            )
            .outerjoin(
                MapRecipeLikeModel,
                MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
            )
            .where(
                TrnRecipeModel.is_active == True,
                visibility_condition,
                or_(
                    DtlRecipeIngredientModel.ingredient_id.in_(ingredient_ids),
                    MasIngredientModel.ingredient_name.in_(item_names)
                )
            )
            .group_by(
                TrnRecipeModel.recipe_id
            )
            .having(
                match_percentage > 15
            )
            .options(
                selectinload(TrnRecipeModel.user),
                selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
            )
            .order_by(
                desc(match_percentage)
            )
            .limit(15)
        )   

        result = db.exec(main_sql).all()
        return [
            RecipeResponseDTO.model_validate(
                recipe, from_attributes=True
            ).model_copy(
                update={"like_count": like_count, "is_liked": is_liked > 0}
            ) 
            for recipe, like_count, is_liked, _ in result
        ]
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        raise
    
def get_recommend_recipe_for_you(db: Session, user_id: int):
    try:
        t1_start = time.perf_counter()
        user_vector = vectorStoreService.get_user_vector(db, user_id)
        if user_vector is None:
            return []
        
        recipe_vectors = vectorStoreService.get_recipe_vectors(db)

        recipe_ids = list(recipe_vectors.keys())
        recipe_matrix = np.array(list(recipe_vectors.values()))
        user_vec_array = np.array([user_vector])

        sim_scores = cosine_similarity(user_vec_array, recipe_matrix)[0]

        stock_match_dict = {}
        user_stock = db.exec(
            select(
                TrnUserStockModel.ingredient_id,
                TrnUserStockModel.item_name
            ).where(
            TrnUserStockModel.user_id == user_id
            )
        ).all()

        if user_stock:
            ingredient_ids = [ingredient.ingredient_id for ingredient in user_stock if ingredient.ingredient_id]
            item_names = [ingredient.item_name.strip() for ingredient in user_stock if ingredient.item_name]
            if ingredient_ids or item_names:
                total_count = func.nullif(
                    select(func.count(DtlRecipeIngredientModel.ingredient_id))
                    .where(DtlRecipeIngredientModel.recipe_id == TrnRecipeModel.recipe_id)
                    .correlate(TrnRecipeModel)
                    .scalar_subquery(),
                    0
                )
                match_percentage = (func.count(DtlRecipeIngredientModel.ingredient_id) * 100.0 / total_count).label("match_percentage")

                match_conditions = []
                if ingredient_ids:
                    match_conditions.append(DtlRecipeIngredientModel.ingredient_id.in_(ingredient_ids))
                if item_names:
                    match_conditions.append(MasIngredientModel.ingredient_name.in_(item_names))

                stock_sql = (
                    select(TrnRecipeModel.recipe_id, match_percentage)
                    .join(DtlRecipeIngredientModel, DtlRecipeIngredientModel.recipe_id == TrnRecipeModel.recipe_id)
                    .join(MasIngredientModel, MasIngredientModel.ingredient_id == DtlRecipeIngredientModel.ingredient_id)
                    .where(
                        TrnRecipeModel.is_active == True,
                        or_(
                            *match_conditions
                        )
                    )
                    .group_by(TrnRecipeModel.recipe_id)
                )
                
                stock_results = db.exec(stock_sql).all()
                stock_match_dict = {r_id: match for r_id, match in stock_results if match is not None}

        scores = []
        for i, recipe_id in enumerate(recipe_ids):
            content_score = sim_scores[i]
            stock_match_percent = stock_match_dict.get(recipe_id, 0.0)
            stock_score = float(stock_match_percent) / 100.0
            hybrid_score = (content_score * 0.7) + (stock_score * 0.3)
            scores.append((recipe_id, hybrid_score, content_score, stock_score))

        scores.sort(key=lambda x: x[1], reverse=True)

        print(f"\n=== Hybrid Recommendation (User ID: {user_id}) ===")
        for r_id, h_score, a_score, s_score in scores[:15]:
            print(f"Recipe: {r_id:2} | Final: {h_score:.3f} (AI: {a_score:.3f}, Stock: {s_score:.3f})")
        print("==================================================\n")

        top_ids = [s[0] for s in scores[:15]]

        if not top_ids:
            return []

        visibility_condition = or_(
                TrnRecipeModel.is_public == True,
                TrnRecipeModel.user_id == user_id
        )
        
        main_sql = select(
                TrnRecipeModel,
                func.count(MapRecipeLikeModel.user_id).label("like_count"),
                func.count(MapRecipeLikeModel.user_id).filter(MapRecipeLikeModel.user_id == user_id).label("is_liked")
            ).outerjoin(
                MapRecipeLikeModel, MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
            ).where(
                TrnRecipeModel.recipe_id.in_(top_ids),
                TrnRecipeModel.is_active == True,
                visibility_condition
            ).group_by(
                TrnRecipeModel.recipe_id
            ).options(
                selectinload(TrnRecipeModel.user),
                selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
            )
        recipes = db.exec(main_sql).all()

        recipe_dict = {recipe.recipe_id: (recipe, like_count, is_liked) for recipe, like_count, is_liked in recipes}
        sorted_recipes = [recipe_dict[recipe_id] for recipe_id in top_ids if recipe_id in recipe_dict]
        
        t1_end = time.perf_counter()
        print(f"t1: {t1_end - t1_start}")

        return [ RecipeResponseDTO.model_validate(
            recipe, from_attributes=True
        ).model_copy(
            update={"like_count": like_count, "is_liked": is_liked > 0}
        ) for recipe, like_count, is_liked in sorted_recipes]
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        raise


def get_recipe_by_name(user_id: int | None, recipe_name: str, db: Session):
    try:
        ingredients_list = [ing.strip() for ing in recipe_name.split(",") if ing.strip()]
        if not ingredients_list:
            return []

        if user_id:
            visibility_condition = or_(
                TrnRecipeModel.is_public == True,
                TrnRecipeModel.user_id == user_id
            )

        else:
            visibility_condition = TrnRecipeModel.is_public == True

        subqueries = []
        for ing in ingredients_list:
            sq = (
                select(DtlRecipeIngredientModel.recipe_id)
                .join(MasIngredientModel, MasIngredientModel.ingredient_id == DtlRecipeIngredientModel.ingredient_id)
                .where(
                    or_(
                        MasIngredientModel.ingredient_name.contains(ing),
                        literal(ing).contains(MasIngredientModel.ingredient_group)
                    )
                )
            )
            subqueries.append(sq)
        
        ingredient_subquery = intersect(*subqueries)

        query = select(
            TrnRecipeModel,
            func.count(MapRecipeLikeModel.user_id).label("like_count"),
            func.count(MapRecipeLikeModel.user_id).filter(MapRecipeLikeModel.user_id == user_id).label("is_liked")
            ).outerjoin(
                MapRecipeLikeModel,
                MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
            ).where(
                TrnRecipeModel.is_active == True,
                # TrnRecipeModel.recipe_name.contains(recipe_name), 
                visibility_condition,
                or_(
                    TrnRecipeModel.recipe_name.contains(recipe_name), 
                    TrnRecipeModel.recipe_id.in_(ingredient_subquery)
                )
            ).group_by(
                TrnRecipeModel.recipe_id
            ).options(
                selectinload(TrnRecipeModel.user),
                selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
        )
        result = db.exec(query).all()
        return [ RecipeResponseDTO.model_validate(
            recipe, from_attributes=True
        ).model_copy(
            update={"like_count": like_count, "is_liked": is_liked > 0}
        ) for recipe, like_count, is_liked in result]
    except Exception as ex:
        db.rollback()
        print(f"error: {ex}")
        raise

# def get_recipe_by_ai_recipe_name(user_id: int, mobilenet_class: str, recipe_name: list[str], db: Session):
#     if not recipe_name:
#         return []
    
#     vocab_record = db.get(SysModelVocabularyModel, "recipe_vocab")
#     if not vocab_record or not vocab_record.idf:
#         print("ไม่พบ Vocabulary หรือ IDF ในระบบ กรุณารัน Cronjob ก่อน")
#         return []
    
#     vocab_dict = vocab_record.vocabulary if isinstance(vocab_record.vocabulary, dict) else json.loads(vocab_record.vocabulary)
#     idf_list = vocab_record.idf if isinstance(vocab_record.idf, list) else json.loads(vocab_record.idf)
#     idf_array = np.array(idf_list, dtype=np.float64)

#     search_vectorizer = TfidfVectorizer(
#         tokenizer=thai_tokenizer,
#         token_pattern=None,
#         lowercase=False,
#         vocabulary=vocab_dict
#     )

#     search_vectorizer.idf_ = idf_array
#     search_vectorizer._tfidf._idf_diag = sp.diags(idf_array)

#     raw_query = " ".join(recipe_name)
#     search_vector = search_vectorizer.transform([raw_query]).toarray()
#     search_vector = np.array(search_vector, dtype=np.float32)
#     # tokens = thai_tokenizer(raw_query)
#     # unique_tokens = list(dict.fromkeys(tokens))
#     # search_query = " ".join(unique_tokens)

#     recipe_records = db.exec(select(MapRecipeVectorModel)).all()
#     if not recipe_records:
#         return []
    
#     recipe_ids = []
#     recipe_matrix = []
#     for r in recipe_records:
#         recipe_ids.append(r.recipe_id)
#         vec = json.loads(r.vector_data) if isinstance(r.vector_data, str) else r.vector_data
#         recipe_matrix.append(vec)
            
#     recipe_matrix = np.array(recipe_matrix, dtype=np.float32)
#     sim_scores = cosine_similarity(search_vector, recipe_matrix)[0]

#     recipe_details = db.exec(
#         select(TrnRecipeModel.recipe_id, TrnRecipeModel.recipe_name)
#         .where(TrnRecipeModel.recipe_id.in_(recipe_ids))
#     ).all()
#     recipe_name_map = {r.recipe_id: r.recipe_name for r in recipe_details}

#     ai_token_map = {
#         ai_name: set([t for t in tokenize_and_normalize(ai_name) if len(t) > 1])
#         for ai_name in recipe_name
#     }

#     db_token_map = {
#         r_id: set([t for t in tokenize_and_normalize(recipe_name_map.get(r_id, "")) if len(t) > 1])
#         for r_id in recipe_ids
#     }

#     is_agreed_by_gemini = False
#     if mobilenet_class and mobilenet_class != "non_food":
#         for g_name in recipe_name:
#             if mobilenet_class in g_name:
#                 is_agreed_by_gemini = True
#                 break
    
#     if not is_agreed_by_gemini and mobilenet_class != "non_food":
#         print(f"[Warning] MobileNet ทายว่า '{mobilenet_class}' แต่ Gemini ไม่เห็นด้วยเลย")

#     scored_recipes = []

#     for i in range(len(recipe_ids)):
#         r_id = recipe_ids[i]
#         base_score = sim_scores[i]
#         db_recipe_name = recipe_name_map.get(r_id, "")
#         db_tokens = db_token_map[r_id]
#         final_score = base_score

#         if is_agreed_by_gemini and mobilenet_class in db_recipe_name:
#             final_score += MOBILENET_AGREE_BONUS

#         for ai_name in recipe_name:
#             if db_recipe_name in ai_name or ai_name in db_recipe_name:
#                 final_score += EXACT_MATCH_BONUS
#                 break

#             ai_tokens = ai_token_map[ai_name]
#             common_tokens = db_tokens.intersection(ai_tokens)

#             if len(db_tokens) > 0:
#                 overlap_ratio = len(common_tokens) / len(db_tokens)
#                 if overlap_ratio >= 0.5:
#                     final_score += BONUS_SCORE
#                     break

#         scored_recipes.append((r_id, final_score))

#     # scored_recipes = [(recipe_ids[i], sim_scores[i]) for i in range(len(recipe_ids))]
#     scored_recipes.sort(key=lambda x: x[1], reverse=True)

#     print(f"\n[Vector Search] ผลลัพธ์การจับคู่กับรูปภาพ:")
#     for r_id, score in scored_recipes[:10]:
#         print(f"Recipe ID: {r_id:2} | ความแม่นยำ: {score:.4f} | {recipe_name_map.get(r_id, '')}")

#     top_recipe_ids = [r_id for r_id, score in scored_recipes[:10] if score >= MIN_SCORE_THRESHOLD]
#     if not top_recipe_ids:
#         print("AI เดาชื่อมา แต่หาใน DB ไม่เจอสิ่งที่คล้ายกันเลย")
#         return []

#     visibility_condition = or_(
#         TrnRecipeModel.is_public == True,
#         TrnRecipeModel.user_id == user_id
#     )

#     # name_condition = or_(*[TrnRecipeModel.recipe_name.contains(name) for name in recipe_name])

#     query = select(
#         TrnRecipeModel, func.count(MapRecipeLikeModel.user_id).label("like_count")
#     ).outerjoin(
#         MapRecipeLikeModel,
#         MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
#     ).where(
#         TrnRecipeModel.is_active == True,
#         # name_condition, 
#         TrnRecipeModel.recipe_id.in_(top_recipe_ids),
#         visibility_condition
#     ).group_by(
#         TrnRecipeModel.recipe_id
#     ).options(
#         selectinload(TrnRecipeModel.user),
#         selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
#     )

#     result = db.exec(query).all()
#     recipe_dict = {recipe.recipe_id: (recipe, like_count) for recipe, like_count in result}
#     sorted_recipes = [recipe_dict[r_id] for r_id in top_recipe_ids if r_id in recipe_dict]

#     return [ RecipeResponseDTO.model_validate(
#         recipe, from_attributes=True
#     ).model_copy(
#         update={"like_count": like_count}
#     ) for recipe, like_count in sorted_recipes]

def get_recipe_by_ai_recipe_name(user_id: int, mobilenet_class: str, recipe_name: list[str], uploaded_img_vector: list[float], db: Session):
    if not recipe_name:
        return []
    
    raw_query = " ".join(recipe_name)
    search_vector = aiConfig.embed_model.encode([raw_query])

    recipe_records = db.exec(select(MapRecipeVectorModel)).all()
    if not recipe_records:
        return []
    
    img_records = db.exec(select(MapRecipeImageVectorModel)).all()
    db_img_vectors = {r.recipe_id: (json.loads(r.image_vector) if isinstance(r.image_vector, str) else r.image_vector) for r in img_records}
    upload_img_vec_np = np.array([uploaded_img_vector], dtype=np.float32)
    
    recipe_ids = []
    recipe_matrix = []
    for r in recipe_records:
        recipe_ids.append(r.recipe_id)
        vec = json.loads(r.vector_data) if isinstance(r.vector_data, str) else r.vector_data
        recipe_matrix.append(vec)
            
    recipe_matrix = np.array(recipe_matrix, dtype=np.float32)
    text_sim_scores = cosine_similarity(search_vector, recipe_matrix)[0]

    recipe_details = db.exec(
        select(TrnRecipeModel)
        .where(TrnRecipeModel.recipe_id.in_(recipe_ids))
        .options(selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag))
    ).all()
    
    recipe_name_map = {}
    recipe_full_text_map = {}
    
    for r in recipe_details:
        title = r.recipe_name
        recipe_name_map[r.recipe_id] = title 
        
        tags_str = " ".join([t.tag.tag_name for t in r.recipe_tags]) if r.recipe_tags else ""
        recipe_full_text_map[r.recipe_id] = f"{title} {tags_str}".strip()

    ai_token_map = {
        ai_name: set([t for t in tokenize_and_normalize(ai_name) if len(t) > 1])
        for ai_name in recipe_name
    }

    db_token_map = {
        r_id: set([t for t in tokenize_and_normalize(recipe_full_text_map.get(r_id, "")) if len(t) > 1])
        for r_id in recipe_ids
    }

    db_token_freq = Counter()
    for tokens in db_token_map.values():
        db_token_freq.update(tokens)

    ai_doc_freq = Counter()
    for tokens in ai_token_map.values():
        for t in tokens:
            ai_doc_freq[t] += 1
    
    STOPWORDS = {"แกง", "ผัด", "ต้ม", "ทอด", "นึ่ง", "ย่าง", "สด", "น้ำ"}

    ai_strict_tokens = [
        t for t in ai_doc_freq.keys()
        if get_token_weight(t, db_token_freq) >= 2.0
        and t not in STOPWORDS
    ]

    majority_count = (len(recipe_name) // 2) + 1 if len(recipe_name) > 1 else 1
    
    IGNORE_ANCHORS = {"ข้าว", "น้ำ", "เส้น", "อาหาร", "จาน", "เมนู", "สูตร"}

    agreed_tokens = [
        t for t, freq in ai_doc_freq.items()
        if freq >= majority_count and t not in IGNORE_ANCHORS
    ]

    if agreed_tokens:
        ai_anchor_tokens = agreed_tokens
    else:
        ai_anchor_tokens = ai_strict_tokens if ai_strict_tokens else list(ai_doc_freq.keys())

    GENERIC_ANCHORS = {"หมู", "ไก่", "เนื้อ", "ปลา", "กุ้ง", "ไข่"}

    # ai_anchor_tokens = [
    #     t for t in ai_anchor_tokens
    #     if t not in GENERIC_ANCHORS
    # ]

    # if not ai_anchor_tokens:
    #     ai_anchor_tokens = [
    #         t for t in (agreed_tokens or ai_strict_tokens)
    #         if t not in GENERIC_ANCHORS
    #     ]

    filtered_anchors = [t for t in ai_anchor_tokens if t not in GENERIC_ANCHORS]
    if filtered_anchors:
        ai_anchor_tokens = filtered_anchors
    else:
        ai_anchor_tokens = agreed_tokens or ai_strict_tokens or list(ai_doc_freq.keys())
        
    ai_anchor_set = set(ai_anchor_tokens)
        
    print("All AI Tokens:", list(ai_doc_freq.keys()))
    print("Strict Tokens (ตัวประกอบให้โบนัส):", ai_strict_tokens)
    print("🎯 Anchor Tokens (พระเอกตัวจริง):", ai_anchor_tokens)

    is_agreed_by_gemini = False
    if mobilenet_class and mobilenet_class != "non_food":
        for g_name in recipe_name:
            if mobilenet_class in g_name:
                is_agreed_by_gemini = True
                break
    
    if not is_agreed_by_gemini and mobilenet_class != "non_food":
        print(f"[Warning] MobileNet ทายว่า '{mobilenet_class}' แต่ Gemini ไม่เห็นด้วยเลย")

    scored_recipes = []
    debug_score_details = {}

    for i in range(len(recipe_ids)):
        r_id = recipe_ids[i]
        text_score = float(text_sim_scores[i])
        
        img_score = 0.0
        if r_id in db_img_vectors:
            db_vec_np = np.array([db_img_vectors[r_id]], dtype=np.float32)
            img_score = float(cosine_similarity(upload_img_vec_np, db_vec_np)[0][0])
            
            if img_score > 0.70:
                base_score = (text_score * 0.5) + (img_score * 0.5)
            else:
                base_score = (text_score * 0.8) + (img_score * 0.2)
        else:
            base_score = text_score

        if base_score < 0.35:
            continue

        db_recipe_name = recipe_name_map.get(r_id, "")
        db_tokens = db_token_map[r_id]
        final_score = base_score

        is_exact_match = False
        exactness_bonus = 0.0
        
        for ai_name in recipe_name:
            if db_recipe_name in ai_name or ai_name in db_recipe_name:
                is_exact_match = True
                
                length_diff = abs(len(db_recipe_name) - len(ai_name))
                
                exactness_bonus = max(0, 1.0 - (length_diff * 0.05)) 
                break

        if base_score < 0.5 and not is_exact_match:
            final_score *= 0.2

        ai_anchor_set = set(ai_anchor_tokens)
        if ai_anchor_set and not is_exact_match:
            has_anchor = len(ai_anchor_set.intersection(db_tokens)) > 0
            if not has_anchor:
                if img_score < 0.85: 
                    continue
                
        if is_agreed_by_gemini and mobilenet_class in db_recipe_name:
            final_score += MOBILENET_AGREE_BONUS

        has_any_overlap = is_exact_match

        if is_exact_match:
            final_score += EXACT_MATCH_BONUS + (exactness_bonus * 1.0)
        if img_score >= 0.90:
            final_score += 2.0

        all_ai_tokens_combined = set()
        for ai_tokens in ai_token_map.values():
            all_ai_tokens_combined.update(ai_tokens)
            
        common_tokens = all_ai_tokens_combined.intersection(db_tokens)
        if common_tokens:
            has_any_overlap = True
            weighted_overlap = sum(get_token_weight(t, db_token_freq) for t in common_tokens)
            db_total_weight = sum(get_token_weight(t, db_token_freq) for t in db_tokens)

            if db_total_weight > 0:
                overlap_ratio = weighted_overlap / db_total_weight
                if overlap_ratio >= 0.5:
                    final_score += BONUS_SCORE

        if not has_any_overlap:
            final_score *= 0.2

        important_overlap = len(ai_anchor_set.intersection(db_tokens)) > 0
        if not important_overlap and not is_exact_match:
            if img_score < 0.85: 
                continue

        ai_strict_set = set(ai_strict_tokens)
        high_match = len(ai_strict_set.intersection(db_tokens))
        final_score += high_match * 0.3
        
        scored_recipes.append((r_id, final_score))
        debug_score_details[r_id] = {
            "text": text_score,
            "image": img_score,
            "base": base_score
        }

    scored_recipes.sort(key=lambda x: x[1], reverse=True)

    print(f"\n[{'='*40}]")
    print(f"[Hybrid Search] ผลลัพธ์ 10 อันดับแรก:")
    print(f"[{'='*40}]")
    for r_id, score in scored_recipes[:10]:
        name = recipe_name_map.get(r_id, '')
        details = debug_score_details.get(r_id, {})
        txt_s = details.get('text', 0)
        img_s = details.get('image', 0)
        base_s = details.get('base', 0)
        
        print(f"🥘 ID: {r_id:2} | เมนู: {name}")
        print(f"   ┣ ความหมาย (Text Score): {txt_s:.4f}")
        print(f"   ┣ หน้าตา (Image Score) : {img_s:.4f}")
        print(f"   ┣ ผสมแล้ว (Base Score)  : {base_s:.4f}")
        print(f"   ┗ รวมโบนัส (Final Score): {score:.4f}\n")

    top_recipe_ids = [r_id for r_id, score in scored_recipes[:10] if score >= MIN_SCORE_THRESHOLD]
    
    if not top_recipe_ids:
        print("AI เดาชื่อมา แต่หาใน DB ไม่เจอสิ่งที่คล้ายกันเลย (ไม่ผ่าน Threshold)")
        return []

    visibility_condition = or_(
        TrnRecipeModel.is_public == True,
        TrnRecipeModel.user_id == user_id
    )

    query = select(
        TrnRecipeModel, func.count(MapRecipeLikeModel.user_id).label("like_count")
    ).outerjoin(
        MapRecipeLikeModel, MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
    ).where(
        TrnRecipeModel.is_active == True,
        TrnRecipeModel.recipe_id.in_(top_recipe_ids),
        visibility_condition
    ).group_by(
        TrnRecipeModel.recipe_id
    ).options(
        selectinload(TrnRecipeModel.user),
        selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
    )

    result = db.exec(query).all()
    recipe_dict = {recipe.recipe_id: (recipe, like_count) for recipe, like_count in result}
    sorted_recipes = [recipe_dict[r_id] for r_id in top_recipe_ids if r_id in recipe_dict]

    return [ RecipeResponseDTO.model_validate(recipe, from_attributes=True).model_copy(
        update={"like_count": like_count}
    ) for recipe, like_count in sorted_recipes]


def get_recipe_detail_by_recipe_id(db: Session, recipe_id: int, user_id: int | None = None):
    recipe = db.exec(
        select(TrnRecipeModel)
        .where(TrnRecipeModel.recipe_id == recipe_id)
        .options(
            selectinload(TrnRecipeModel.user),
            selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
        )
    ).first()
    if not recipe:
        print(f"Error: Recipe ID {recipe_id} not found.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการ")
    
    try:
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
            recipe = RecipeHeaderResponseDTO.model_validate(recipe).model_copy(update={"like_count": like_count}),
            ingredients = [RecipeIngredientResponseDTO.model_validate(ingredient) for ingredient in ingredients],
            steps = [RecipeStepResponseDTO.model_validate(step) for step in steps],
            is_liked = is_liked
        )
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise

def get_my_create_recipe(db: Session, user_id: int):
    sql = select(TrnRecipeModel).where(TrnRecipeModel.user_id == user_id, TrnRecipeModel.is_active == True).options(
        selectinload(TrnRecipeModel.user),
        selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
    )
    result = db.exec(sql).all()
    return result

def get_ingredient_by_name(db: Session, ingredient_name: str):
    sql = select(MasIngredientModel).where(MasIngredientModel.ingredient_name.ilike(f"%{ingredient_name}%"))
    result = db.exec(sql).all()
    return result

def get_recipe_by_ai_ingredient_name(user_id: int, ingredient_name: list[str], db: Session):
    if not ingredient_name:
        return []

    visibility_condition = or_(
        TrnRecipeModel.is_public == True,
        TrnRecipeModel.user_id == user_id
    )

    ingredient_condition = or_(
        *[
            or_(
                MasIngredientModel.ingredient_name.contains(name),
                MasIngredientModel.ingredient_group.contains(name),
                literal(name).contains(MasIngredientModel.ingredient_group)
            )
             for name in ingredient_name
        ]
    )
    match_count = func.count(distinct(MasIngredientModel.ingredient_id))
    like_count_col = func.count(distinct(MapRecipeLikeModel.user_id)).label("like_count")
    
    query = select(
        TrnRecipeModel, like_count_col
    ).outerjoin(
        MapRecipeLikeModel,
        MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
    ).join(
        DtlRecipeIngredientModel, 
        DtlRecipeIngredientModel.recipe_id == TrnRecipeModel.recipe_id
    ).join(
        MasIngredientModel, 
        MasIngredientModel.ingredient_id == DtlRecipeIngredientModel.ingredient_id
    ).where(
        TrnRecipeModel.is_active == True,
        DtlRecipeIngredientModel.is_main_ingredient == True,
        ingredient_condition, 
        visibility_condition
    ).group_by(
        TrnRecipeModel.recipe_id
    ).order_by(
        match_count.desc(),
        like_count_col.desc()
    ).options(
        selectinload(TrnRecipeModel.user),
        selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
    )
    result = db.exec(query).all()
    return [ RecipeResponseDTO.model_validate(
        recipe, from_attributes=True
    ).model_copy(
        update={"like_count": like_count}
    ) for recipe, like_count in result]

def get_recipe_category(db: Session):
    categories = db.exec(select(MasTagModel.tag_id, MasTagModel.tag_name).where(MasTagModel.tag_type == "category")).all()
    return [
        {
            "category_id": category_id, 
            "category_name": category_name
        }
        for category_id, category_name in categories
    ]

def get_recipe_tag(db: Session):
    tags = db.exec(select(MasTagModel.tag_id, MasTagModel.tag_name).where(MasTagModel.tag_type != "category")).all()
    return [
        {
            "tag_id": tag_id, 
            "tag_name": tag_name
        }
        for tag_id, tag_name in tags
    ]

def get_recipe_by_category(user_id: int | None, category_id: int, db: Session):
    if user_id:
        visibility_condition = or_(
            TrnRecipeModel.is_public == True,
            TrnRecipeModel.user_id == user_id
        )

    else:
        visibility_condition = TrnRecipeModel.is_public == True
    
    query = select(
        TrnRecipeModel, 
        func.count(MapRecipeLikeModel.user_id).label("like_count"),
        func.count(MapRecipeLikeModel.user_id).filter(MapRecipeLikeModel.user_id == user_id).label("is_liked")
    ).outerjoin(
        MapRecipeLikeModel,
        MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
    ).join(
        MapRecipeTagModel,
        MapRecipeTagModel.recipe_id == TrnRecipeModel.recipe_id
    ).where(
        TrnRecipeModel.is_active == True,
        visibility_condition,
        MapRecipeTagModel.tag_id == category_id
    ).group_by(
        TrnRecipeModel.recipe_id
    ).options(
        selectinload(TrnRecipeModel.user),
        selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
    )
    
    result = db.exec(query).all()
    return [ RecipeResponseDTO.model_validate(
        recipe, from_attributes=True
    ).model_copy(
        update={"like_count": like_count, "is_liked": is_liked > 0}
    ) for recipe, like_count, is_liked in result]

def get_recipe_filter_option(db: Session):
    result = db.exec(
        select(MasTagModel)
    ).all()

    categories = [
        {
            "category_id": tag.tag_id,
            "category_name": tag.tag_name
        } 
        for tag in result if tag.tag_type == "category"
    ]
    tags = [
        {
            "tag_id": tag.tag_id,
            "tag_name": tag.tag_name
        } 
        for tag in result if tag.tag_type != "category"
    ]
    
    return {"categories": categories, "tags": tags}

def get_search_recipe_filter_option(user_id: int | None, categories: list[int], tags: list[int], db: Session):
    if user_id:
        visibility_condition = or_(
            TrnRecipeModel.is_public == True,
            TrnRecipeModel.user_id == user_id
        )

    else:
        visibility_condition = TrnRecipeModel.is_public == True

    filter_options = categories + tags
    if filter_options:
        valid_tags = db.exec(
                select(MasTagModel).where(MasTagModel.tag_id.in_(filter_options))
        ).all()
        tag_dict = {tag.tag_id: tag for tag in valid_tags}
            
        for tag_id in categories:
            if tag_id not in tag_dict:
                raise NotFoundException(f"ไม่พบหมวดหมู่หลัก (Category ID: {tag_id}) ในระบบ")
            
            if tag_dict[tag_id].tag_type != "category":
                raise NotFoundException(f"ไม่พบหมวดหมู่หลัก (Category ID: {tag_id}) ในระบบ")

        if tags:
            for tag_id in tags:
                if tag_id not in tag_dict:
                    raise NotFoundException(f"ไม่พบแท็ก (Tag ID: {tag_id}) ในระบบ")
                
                if tag_dict[tag_id].tag_type == "category":
                    raise NotFoundException(f"ไม่พบแท็ก (Tag ID: {tag_id}) ในระบบ")
    
    query = select(
        TrnRecipeModel, 
        func.count(MapRecipeLikeModel.user_id).label("like_count"),
        func.count(MapRecipeLikeModel.user_id).filter(MapRecipeLikeModel.user_id == user_id).label("is_liked")
    ).outerjoin(
        MapRecipeLikeModel,
        MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
    ).where(
        TrnRecipeModel.is_active == True,
        visibility_condition
    ).group_by(
        TrnRecipeModel.recipe_id
    ).options(
        selectinload(TrnRecipeModel.user),
        selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
    )

    if filter_options:
        query = query.join(
            MapRecipeTagModel,
            MapRecipeTagModel.recipe_id == TrnRecipeModel.recipe_id
        ).where(
            MapRecipeTagModel.tag_id.in_(filter_options)
        ).having(
            func.count(func.distinct(MapRecipeTagModel.tag_id)) == len(filter_options)
        )
    
    result = db.exec(query).all()
    return [ RecipeResponseDTO.model_validate(
        recipe, from_attributes=True
    ).model_copy(
        update={"like_count": like_count, "is_liked": is_liked > 0}
    ) for recipe, like_count, is_liked in result]

def get_recipe_by_ingredient_name(user_id: int | None, ingredient_list: list[str], tag_list: list[int], db: Session):
    if not ingredient_list:
        return []
    
    if user_id:
        visibility_condition = or_(
            TrnRecipeModel.is_public == True,
            TrnRecipeModel.user_id == user_id
        )

    else:
        visibility_condition = TrnRecipeModel.is_public == True

    like_count_col = func.count(distinct(MapRecipeLikeModel.user_id)).label("like_count")
    query = select(
        TrnRecipeModel, like_count_col
    ).outerjoin(
        MapRecipeLikeModel,
        MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
    )

    where_clauses = [
        TrnRecipeModel.is_active == True,
        visibility_condition
    ]
    order_by_clause = []

    if ingredient_list:
        ingredient_condition = or_(
            *[
                or_(
                    MasIngredientModel.ingredient_name.contains(name),
                    MasIngredientModel.ingredient_group.contains(name),
                    literal(name).contains(MasIngredientModel.ingredient_group)
                )
                for name in ingredient_list
            ]
        )

        query = query.join(
            DtlRecipeIngredientModel, 
            DtlRecipeIngredientModel.recipe_id == TrnRecipeModel.recipe_id
        ).join(
            MasIngredientModel,
            MasIngredientModel.ingredient_id == DtlRecipeIngredientModel.ingredient_id
        )

        where_clauses.extend(
            [
                DtlRecipeIngredientModel.is_main_ingredient == True,
                ingredient_condition
            ]
        )

        match_count = func.count(distinct(MasIngredientModel.ingredient_id))
        order_by_clause.append(match_count.desc())

    if tag_list:
        query = query.join(
            MapRecipeTagModel,
            MapRecipeTagModel.recipe_id == TrnRecipeModel.recipe_id
        )

        where_clauses.append(MapRecipeTagModel.tag_id.in_(tag_list))

    order_by_clause.append(like_count_col.desc())
    
    query = query.where(
        *where_clauses
    ).group_by(
        TrnRecipeModel.recipe_id
    ).order_by(
        *order_by_clause
    ).options(
        selectinload(TrnRecipeModel.user),
        selectinload(TrnRecipeModel.recipe_tags).joinedload(MapRecipeTagModel.tag)
    )
    result = db.exec(query).all()
    return [ RecipeResponseDTO.model_validate(
        recipe, from_attributes=True
    ).model_copy(
        update={"like_count": like_count}
    ) for recipe, like_count in result]
