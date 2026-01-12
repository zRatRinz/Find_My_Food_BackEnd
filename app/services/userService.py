from fastapi import UploadFile
from sqlmodel import Session, select, or_
from datetime import datetime
from app.models.userModel import MasUserModel
from app.schemas.userDTO import UserLoginDTO, UserRegisterDTO
from app.core import datetimezone, security, cloudinary


def create_user_account(request: UserRegisterDTO, db:Session):
    try:
        existing_user_email_sql = select(MasUserModel).where(MasUserModel.email == request.email)
        existing_user_email_result = db.exec(existing_user_email_sql).first()
        if existing_user_email_result:
            return None, "Email นี้มีคนใช้งานแล้ว"
        
        existing_user_username_sql = select(MasUserModel).where(MasUserModel.username == request.username)
        existing_user_username_result = db.exec(existing_user_username_sql).first()
        if existing_user_username_result:
            return None, "Username นี้มีคนใช้งานแล้ว"

        hashed_password =  security.create_hash_password(request.password)
        new_user_profile = MasUserModel(
            email = request.email,
            password = hashed_password,
            username = request.username,
            first_name = request.first_name,
            last_name = request.last_name,
            gender = request.gender,
            age = request.age
        )

        db.add(new_user_profile)
        db.commit()
        db.refresh(new_user_profile)
        return new_user_profile.user_id, None
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return None, "เกิดข้อผิดพลาด"
    
def create_user_account_with_google(request: MasUserModel, db:Session):
    try:
        existing_user_email_sql = select(MasUserModel).where(MasUserModel.email == request.email)
        existing_user_email_result = db.exec(existing_user_email_sql).first()
        if existing_user_email_result:
            return None, "Email นี้มีคนใช้งานแล้ว"
        
        existing_user_username_sql = select(MasUserModel).where(MasUserModel.username == request.username)
        existing_user_username_result = db.exec(existing_user_username_sql).first()
        if existing_user_username_result:
            return None, "Username นี้มีคนใช้งานแล้ว"

        new_user_profile = MasUserModel(
            email = request.email,
            username = request.username,
            first_name = request.first_name,
            last_name = request.last_name,
            gender = request.gender,
            age = request.age,
            provider = request.provider
        )

        db.add(new_user_profile)
        db.commit()
        db.refresh(new_user_profile)
        return new_user_profile, None
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return None, "เกิดข้อผิดพลาด"
    
# def login(db: Session):
#     sql = select(UserAccountModel)
#     username_result = db.exec(sql).all()
#     if not username_result:
#         return username_result
    
#     return username_result

def authenticate_user(username:str, password:str, db:Session):
    user_result = get_user_by_username(username, db)
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
        return False

def get_user_by_username(username:str, db: Session):
    sql = select(MasUserModel).where(or_(MasUserModel.email == username, MasUserModel.username == username))
    user_result = db.exec(sql).first()
    return user_result

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
    if not image_url:
        return ("fail", "Upload รูปภาพไม่สำเร็จ")

    try:
        current_user.image_url = image_url
        db.add(current_user)
        db.commit()
        return ("success", None)
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return ("fail","เกิดข้อผิดพลาด")
