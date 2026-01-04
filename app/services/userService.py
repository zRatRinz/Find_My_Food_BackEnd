from fastapi import UploadFile
from sqlmodel import Session,select

from app.models.userModel import LoginAccountModel, UserInfoModel
from app.schemas.userDTO import UserLoginDTO, UserRegisterDTO
from app.core import security, cloudinary


def create_login_user(request: UserRegisterDTO, db:Session):
    try:
        existing_user_sql = select(LoginAccountModel).where(LoginAccountModel.username == request.username)
        existing_user_result = db.exec(existing_user_sql).first()
        if existing_user_result:
            return ("fail","ชื่อผู้ใช้งานนี้มีคนใช้งานแล้ว")

        hashed_password =  security.create_hash_password(request.password)
        new_login_user = LoginAccountModel(
            username=request.username,
            password=hashed_password
        )

        db.add(new_login_user)
        db.flush()
        db.refresh(new_login_user)

        new_user_profile = UserInfoModel(
            user_id = new_login_user.user_id,
            first_name = request.first_name,
            last_name = request.last_name,
            age = request.age,
            gender = request.gender,
            email = request.email
        )

        db.add(new_user_profile)
        db.commit()
        return ("success",None)
    except Exception as ex:
        print(f"error: {ex}")
        db.rollback()
        return ("fail","เกิดข้อผิดพลาด")

def login(db: Session):
    sql = select(LoginAccountModel)
    username_result = db.exec(sql).all()
    if not username_result:
        return username_result
    
    return username_result

def authenticate_user(username:str, password:str, db:Session):
    user_result = get_user_by_username(username, db)
    if not user_result:
        return False
    
    password_result = security.verify_password(password,user_result.password)
    if not password_result:
        return False
    
    return user_result

def get_user_by_username(username:str, db: Session):
    sql = select(LoginAccountModel).where(LoginAccountModel.username == username)
    user_result = db.exec(sql).first()
    return user_result

def get_user_by_user_id(user_id: int, db: Session):
    sql = select(UserInfoModel).where(UserInfoModel.user_id == user_id)
    user_result = db.exec(sql).first()
    return user_result

def get_user_info(user_id: int, db: Session):
    sql = select(UserInfoModel).where(UserInfoModel.user_id == user_id)
    result = db.exec(sql).first()
    return result

def update_user_image(current_user: UserInfoModel, file: UploadFile, db: Session):
    image_url = cloudinary.upload_image_to_cloudinary(current_user.user_id, file)
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
