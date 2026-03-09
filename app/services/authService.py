from sqlmodel import Session, select
from datetime import timedelta
from google.oauth2 import id_token
from google.auth.transport import requests
import jwt
from app.core import security, datetimezone
from app.core.config import ACCESS_TOKEN_EXPIRE_MIN, GOOGLE_ANDROID_CLIENT_ID, SECRET_KEY, ALGORITHM
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.userModel import MasUserModel
from app.models.systemModel import SysResetOTPModel
from app.schemas.userDTO import UserAccountDTO, GoogleRegisterDTO
from app.schemas.response import TokenResponse
from app.services import userService, emailService

def login_process(username: str, password: str, db: Session):
    user = userService.authenticate_user(username, password, db)
    if not user:
        raise BadRequestException("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        
    access_token_exprires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
    access_token = security.create_access_token(
        data={"sub":str(user.user_id)},
        expires_delta=access_token_exprires
    )
        
    login_time = userService.update_login_time(user, db)
        
    try:
        user_info_data = UserAccountDTO(
            username = user.username,
            birth_date = user.birth_date,
            gender = user.gender,
            email = user.email
        )
        return TokenResponse(
            access_token = access_token,
            token_type = "bearer",
            data = user_info_data
        )
    except Exception as ex:
        print(f"error: {str(ex)}")
        raise

def google_login_process(request_id_token: str, db: Session):
    try:
        id_info = id_token.verify_oauth2_token(request_id_token, requests.Request(), GOOGLE_ANDROID_CLIENT_ID)
    except ValueError:
        print("Invalid token")
        raise BadRequestException("Invalid token")
    
    email = id_info["email"]
    google_id = id_info["sub"]
    user = userService.get_user_by_username_or_email(email, db)
    if user:
        if user.provider != "google":
            raise BadRequestException("บัญชีนี้ไม่ได้สมัครด้วย Google")
        
        login_time = userService.update_login_time(user, db)

        access_token_exprires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
        access_token = security.create_access_token(data={"sub": str(user.user_id)}, expires_delta=access_token_exprires)
        return TokenResponse(
            access_token=access_token,
            token_type="bearer"
        )
        
    temp_token = security.create_access_token(data={"email": email, "type": "google_register"})
    return TokenResponse(
        access_token=temp_token,
        token_type="bearer"
    )

def update_fcm_token(user_id: int, fcm_token: str, db: Session):
    user = db.get(MasUserModel, user_id)
    if user is None:
        raise NotFoundException("ไม่พบข้อมูลผู้ใช้งาน โปรดติดต่อเจ้าหน้าที่")
    try:
        user.fcm_token = fcm_token
        db.commit()
        return True
    except Exception as ex:
        print(f"error: {str(ex)}")
        db.rollback()
        raise

def google_register_process(request_body: GoogleRegisterDTO, db: Session):
    try:
        payload = jwt.decode(request_body.temp_token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception as ex:
        print(str(ex))
        return BadRequestException("Invalid token")
    
    if payload.get("type") != "google_register":
        print("Invalid token")
        raise BadRequestException("Invalid token")

    email = payload.get("email")
    existing = userService.get_user_by_username_or_email(email, db)
    if existing:
        raise BadRequestException("Email นี้ถูกใช้งานแล้ว")

    new_user = MasUserModel(
        email = email,
        username = request_body.username,
        gender = request_body.gender,
        birth_date = request_body.birth_date,
        provider = "google"
    )

    user = userService.create_user_account_with_google(new_user, db)
    login_time = userService.update_login_time(user, db)
    
        # user = userService.get_user_info_by_id(user_result, db)
        # if not user:
        #     return StandardResponse.fail(message="ไม่พบข้อมูลผู้ใช้งาน โปรดติดต่อเจ้าหน้าที่")

    access_token_exprires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
    access_token = security.create_access_token(
        data={"sub":str(user.user_id)},
        expires_delta=access_token_exprires
    )

    return TokenResponse(
        access_token = access_token,
        token_type = "bearer"
    )

def request_otp_process(email: str, db: Session):
    try:
        email_result = userService.get_user_by_email(email, db)
        if not email_result:
            return True

        otp = security.generate_otp()
        expire_at = datetimezone.get_thai_now() + timedelta(minutes=5)

        otp_record = SysResetOTPModel(
            email=email,
            otp_code=otp,
            expire_at=expire_at
        )

        db.add(otp_record)

        send_email_result = emailService.send_otp_email(email, otp)
        if not send_email_result:
            db.rollback()
            return True

        db.commit()
        print(f"[Email Service] ส่งอีเมลไปที่ {email})")
        return True
    
    except Exception as ex:
        db.rollback()
        print(ex)
        raise
    
def verify_otp_process(email: str, otp: str, db: Session):
    try:
        query = select(SysResetOTPModel).where(
            SysResetOTPModel.email == email,
            SysResetOTPModel.otp_code == otp,
            SysResetOTPModel.expire_at > datetimezone.get_thai_now(),
            SysResetOTPModel.is_used == False
        )

        result = db.exec(query).first()
        if not result:
            raise BadRequestException("รหัส OTP ไม่ถูกต้อง")
        return result
    except Exception as ex:
        db.rollback()
        print(ex)
        raise
    
def reset_password_process(email: str, otp: str, new_password: str, db: Session):
    try:
        query = select(SysResetOTPModel).where(
            SysResetOTPModel.email == email,
            SysResetOTPModel.otp_code == otp,
            SysResetOTPModel.expire_at > datetimezone.get_thai_now(),
            SysResetOTPModel.is_used == False
        )

        result = db.exec(query).first()
        if not result:
            raise BadRequestException("ข้อมูลไม่ถูกต้อง")

        user = userService.get_user_by_username_or_email(email, db)
        user.password = security.create_hash_password(new_password)
        user.update_date = datetimezone.get_thai_now()
        result.is_used = True
        db.commit()
        return True
    except Exception as ex:
        db.rollback()
        print(ex)
        raise