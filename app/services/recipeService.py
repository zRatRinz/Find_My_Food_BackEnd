from sqlmodel import Session, select, delete, func, desc, or_, distinct
from sqlalchemy.orm import selectinload, joinedload
from sklearn.metrics.pairwise import cosine_similarity
from app.core import cloudinary, datetimezone
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.recipeModel import (
    TrnRecipeModel, DtlRecipeIngredientModel, DtlRecipeStepModel, MapRecipeLikeModel, MasIngredientModel, 
    MasTagModel, MapRecipeTagModel
)
from app.models.userStockModel import TrnUserStockModel
from app.schemas.recipeDTO import (
    CreateNewRecipeDTO, UpdateRecipeHeaderDTO, UpdateRecipeIngredientListDTO, UpdateRecipeStepListDTO, RecipeResponseDTO, 
    RecipeHeaderResponseDTO, RecipeIngredientResponseDTO, RecipeStepResponseDTO, RecipeDetailResponseDTO, LikeRecipeResponseDTO
)
from app.services import vectorStoreService

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
    
def update_recipe_header_by_recipe_id(db: Session, user_id: int, recipe_id: int, request_body: UpdateRecipeHeaderDTO):
    recipe = db.get(TrnRecipeModel, recipe_id)
    if not recipe:
        print(f"Error: Recipe ID {recipe_id} not found.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")
        
    if recipe.user_id != user_id:
        print(f"Error: Not authorized to update recipe with ID {recipe_id}.")
        raise NotFoundException("ไม่พบสูตรอาหารที่ต้องการแก้ไข")
        
    try:
        update_data = request_body.model_dump(exclude={"categories", "tags"}, exclude_unset=True)
        for field, value in update_data.items():
            setattr(recipe, field, value)

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
        user_vector = vectorStoreService.get_user_vector(db, user_id)
        if user_vector is None:
            return []
        
        recipe_vectors = vectorStoreService.get_recipe_vectors(db)

        scores = []
        for recipe_id, vec in recipe_vectors.items():
            score = cosine_similarity([user_vector], [vec])[0][0]
            scores.append((recipe_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        print(f"\n=== คะแนนความคล้าย (User ID: {user_id}) ===")
        for r_id, s in scores[:15]:
            print(f"Recipe ID: {r_id:2} | Score: {s:.4f}")
        print("==========================================\n")

        top_ids = [recipe_id for recipe_id, _ in scores[:15]]

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
                TrnRecipeModel.is_active == True,
                TrnRecipeModel.recipe_name.contains(recipe_name), 
                visibility_condition
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

def get_recipe_by_ai_recipe_name(user_id: int, recipe_name: list[str], db: Session):
    if not recipe_name:
        return []

    visibility_condition = or_(
        TrnRecipeModel.is_public == True,
        TrnRecipeModel.user_id == user_id
    )

    name_condition = or_(*[TrnRecipeModel.recipe_name.contains(name) for name in recipe_name])

    query = select(
        TrnRecipeModel, func.count(MapRecipeLikeModel.user_id).label("like_count")
    ).outerjoin(
        MapRecipeLikeModel,
        MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
    ).where(
        TrnRecipeModel.is_active == True,
        name_condition, 
        visibility_condition
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
        update={"like_count": like_count}
    ) for recipe, like_count in result]

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
    sql = select(TrnRecipeModel).where(TrnRecipeModel.user_id == user_id).options(
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

    ingredient_condition = or_(*[MasIngredientModel.ingredient_name.contains(name) for name in ingredient_name])
    match_count = func.count(distinct(MasIngredientModel.ingredient_id)).label("match_count")
    like_count_col = func.count(distinct(MapRecipeLikeModel.user_id)).label("like_count")
    
    query = select(
        TrnRecipeModel, func.count(MapRecipeLikeModel.user_id).label("like_count")
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
        )
    
    result = db.exec(query).all()
    return [ RecipeResponseDTO.model_validate(
        recipe, from_attributes=True
    ).model_copy(
        update={"like_count": like_count, "is_liked": is_liked > 0}
    ) for recipe, like_count, is_liked in result]