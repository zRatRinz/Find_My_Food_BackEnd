from sqlmodel import Session, select
from datetime import timedelta
from app.core import security, datetimezone
from app.enums.errorCodeEnum import ErrorCodeEnum
from app.models.systemModel import SysResetOTPModel
from app.services import userService, emailService

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
        db.commit()

        send_email_result = emailService.send_otp_email(email, otp)
        if not send_email_result:
            db.rollback()
            return True

        print(f"[Email Service] ส่งอีเมลไปที่ {email})")
        return True
    
    except Exception as ex:
        db.rollback()
        print(ex)
        return None
    
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
            return None, ErrorCodeEnum.BAD_REQUEST
        return result, None
    except Exception as ex:
        db.rollback()
        print(ex)
        return None, ErrorCodeEnum.INTERNAL_ERROR
    
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
            return None, ErrorCodeEnum.BAD_REQUEST

        user = userService.get_user_by_username_or_email(email, db)
        user.password = security.create_hash_password(new_password)
        user.update_date = datetimezone.get_thai_now()
        result.is_used = True
        db.commit()
        return True, None
    except Exception as ex:
        db.rollback()
        print(ex)
        return None, ErrorCodeEnum.INTERNAL_ERROR