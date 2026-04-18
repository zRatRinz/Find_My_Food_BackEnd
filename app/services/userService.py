from fastapi import UploadFile
from sqlmodel import Session, select, or_, func
from sqlalchemy.orm import selectinload
from datetime import datetime
from app.core import datetimezone, security, cloudinary
from app.core.exceptions import BadRequestException, NotFoundException
from app.models.userModel import MasUserModel
from app.models.recipeModel import MapRecipeLikeModel, TrnRecipeModel
from app.schemas.userDTO import UserLoginDTO, UserRegisterDTO, ChangePasswordDTO, UpdateUsernameDTO, SimpleUserInfoDTO, UserLikeRecipeDTO

def create_user_account(request: UserRegisterDTO, db:Session):
    try:
        existing_user_email_sql = select(MasUserModel).where(MasUserModel.email == request.email)
        existing_user_email_result = db.exec(existing_user_email_sql).first()
        if existing_user_email_result:
            raise BadRequestException("Email นี้มีคนใช้งานแล้ว")
        
        existing_user_username_sql = select(MasUserModel).where(MasUserModel.username == request.username)
        existing_user_username_result = db.exec(existing_user_username_sql).first()
        if existing_user_username_result:
            raise BadRequestException("Username นี้มีคนใช้งานแล้ว")

        hashed_password =  security.create_hash_password(request.password)
        new_user_profile = MasUserModel(
            email = request.email,
            password = hashed_password,
            username = request.username,
            gender = request.gender,
            birth_date = request.birth_date
        )

        db.add(new_user_profile)
        db.commit()
        db.refresh(new_user_profile)
        return new_user_profile.user_id
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise

def create_user_account_with_google(request: MasUserModel, db:Session):
    existing_user_email_sql = select(MasUserModel).where(MasUserModel.email == request.email)
    existing_user_email_result = db.exec(existing_user_email_sql).first()
    if existing_user_email_result:
        # return None, "Email นี้มีคนใช้งานแล้ว"
        raise BadRequestException("Email นี้มีคนใช้งานแล้ว")
        
    existing_user_username_sql = select(MasUserModel).where(MasUserModel.username == request.username)
    existing_user_username_result = db.exec(existing_user_username_sql).first()
    if existing_user_username_result:
        # return None, "Username นี้มีคนใช้งานแล้ว"
        raise BadRequestException("Username นี้มีคนใช้งานแล้ว")

    try:
        new_user_profile = MasUserModel(
            email = request.email,
            username = request.username,
            gender = request.gender,
            birth_date = request.birth_date,
            provider = request.provider
        )

        db.add(new_user_profile)
        db.commit()
        db.refresh(new_user_profile)
        return new_user_profile
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise
    
# def login(db: Session):
#     sql = select(UserAccountModel)
#     username_result = db.exec(sql).all()
#     if not username_result:
#         return username_result
    
#     return username_result

def authenticate_user(username:str, password:str, db:Session):
    user_result = get_user_by_username_or_email(username, db)
    if not user_result:
        return False
    
    password_result = security.verify_password(password,user_result.password)
    if not password_result:
        return False    
    return user_result

def update_login_time(user: MasUserModel, db: Session):
    try:
        user.last_login = datetimezone.get_thai_now()
        db.add(user)
        db.commit()
        return True
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise

def get_user_by_username_or_email(request:str, db: Session):
    sql = select(MasUserModel).where(or_(MasUserModel.email == request, MasUserModel.username == request))
    user_result = db.exec(sql).first()
    return user_result

def get_user_by_email(email:str, db: Session):
    sql = select(MasUserModel.email).where(MasUserModel.email == email)
    email_result = db.exec(sql).first()
    return email_result

def get_user_by_user_id(user_id: int, db: Session):
    sql = select(MasUserModel).where(MasUserModel.user_id == user_id)
    user_result = db.exec(sql).first()
    return user_result

def get_user_info_by_id(user_id: int, db: Session):
    sql = select(MasUserModel).where(MasUserModel.user_id == user_id)
    result = db.exec(sql).first()
    return result

def update_user_image(current_user: MasUserModel, file: UploadFile, db: Session):
    image_url = cloudinary.upload_user_image_to_cloudinary(current_user.user_id, file)
    # if not image_url:
    #     return ("fail", "Upload รูปภาพไม่สำเร็จ")

    try:
        current_user.image_url = image_url
        db.add(current_user)
        db.commit()
        return True
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise

def update_user_username(current_user: MasUserModel, request_body: UpdateUsernameDTO, db: Session):
    if current_user.username == request_body.username:
        raise BadRequestException("Username ใหม่ต้องไม่ซ้ํากับ Username ปัจจุบัน")
        
    existing_user_username_sql = select(MasUserModel).where(MasUserModel.username == request_body.username)
    existing_user_username_result = db.exec(existing_user_username_sql).first()
    if existing_user_username_result:
        raise BadRequestException("Username นี้มีคนใช้งานแล้ว")

    try:
        current_user.username = request_body.username
        current_user.update_date = datetimezone.get_thai_now()
        db.commit()
        return True
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise

def change_user_password(current_user: MasUserModel, request_body: ChangePasswordDTO, db: Session):
    if not security.verify_password(request_body.current_password, current_user.password):
        raise BadRequestException("รหัสผ่านปัจจุบันไม่ถูกต้อง")

    if request_body.new_password != request_body.confirm_password:
        raise BadRequestException("รหัสผ่านไม่ตรงกัน")

    if security.verify_password(request_body.new_password, current_user.password):
        raise BadRequestException("รหัสผ่านใหม่ต้องไม่ซ้ำกับรหัสผ่านปัจจุบัน")

    try:
        current_user.password = security.create_hash_password(request_body.new_password)
        current_user.update_date = datetimezone.get_thai_now()
        db.commit()
        return True
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        raise

def get_simple_user_info(user_id: int, db: Session):
    sql = select(MasUserModel.username, MasUserModel.email, MasUserModel.gender, MasUserModel.birth_date, MasUserModel.image_url).where(MasUserModel.user_id == user_id)
    result = db.exec(sql).first()
    if not result:
        raise NotFoundException("ไม่พบผู้ใช้งาน")
    
    return SimpleUserInfoDTO(
        user_id = user_id,
        email = result.email,
        username = result.username,
        gender=result.gender,
        birth_date=result.birth_date,
        image_url = result.image_url
    )

def get_user_like_recipe(user_id: int, db: Session):
    liked_recipe_ids = select(MapRecipeLikeModel.recipe_id).where(MapRecipeLikeModel.user_id == user_id)

    main_sql = select(
        TrnRecipeModel, 
        func.count(MapRecipeLikeModel.user_id).label("like_count")
    ).outerjoin(
        MapRecipeLikeModel,
        MapRecipeLikeModel.recipe_id == TrnRecipeModel.recipe_id
    ).where(
        TrnRecipeModel.is_active == True,
        TrnRecipeModel.recipe_id.in_(liked_recipe_ids)
    ).group_by(
        TrnRecipeModel.recipe_id
    ).options(
        selectinload(TrnRecipeModel.user)
    )

    result = db.exec(main_sql).all()
    return [ UserLikeRecipeDTO.model_validate(
        recipe, from_attributes=True
    ).model_copy(
        update={"like_count": like_count, "is_liked": True}
    ) for recipe, like_count in result]
    
