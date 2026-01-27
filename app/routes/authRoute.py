from fastapi import APIRouter, Request, Depends
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlmodel import Session
# from authlib.integrations.starlette_client import OAuth
import jwt
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import timedelta
from app.core.config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MIN
from app.core import security
from app.db import database
from app.services import userService
from app.models.userModel import MasUserModel
from app.schemas.userDTO import UserAccountDTO, GoogleRegisterDTO, GoogleLoginDTO
from app.schemas.response import TokenResponse, StandardResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# oauth = OAuth()
# oauth.register(
#     name = "google",
#     client_id = GOOGLE_CLIENT_ID,
#     client_secret = GOOGLE_CLIENT_SECRET,
#     server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration",
#     client_kwargs = {
#         "scope": "openid email profile"
#     }
# )

@router.post("/login")
async def login(request: Annotated[OAuth2PasswordRequestForm, Depends()], db:Session = Depends(database.get_db)):
    try:
        user = userService.authenticate_user(request.username, request.password,db)
        if not user:
            return StandardResponse.fail(message="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        
        access_token_exprires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
        access_token = security.create_access_token(
            data={"sub":str(user.user_id)},
            expires_delta=access_token_exprires
        )

        # user_info = userService.get_user_info_by_id(user.user_id, db)
        # if not user_info:
        #     # raise HTTPException(status_code=404, detail="User profile not found")
        #     return StandardResponse.fail(message="ไม่พบข้อมูลผู้ใช้งาน โปรดติดต่อเจ้าหน้าที่")
        
        login_time = userService.update_login_time(user, db)
        if not login_time:
            return StandardResponse.fail(message="เกิดข้อผิดพลาดในเข้าสู่ระบบ")
        
        user_info_data = UserAccountDTO(
            username = user.username,
            age = user.birth_date,
            gender = user.gender,
            email = user.email
        )
        return TokenResponse(
            access_token = access_token,
            token_type = "bearer",
            data = user_info_data
        )
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

# @router.get("/login/google")
# async def login_with_google(request: Request): 
#     redirect_url = request.url_for("auth_google")
#     return await oauth.google.authorize_redirect(request, redirect_url)

# @router.get("/google/callback")
# async def auth_google(request: Request, db: Session = Depends(database.get_db)):
#     try:
#         token = await oauth.google.authorize_access_token(request)
#         user_info = token.get("userinfo")
#         email = user_info.get("email")
#         google_id = user_info.get("sub")

#         user = userService.get_user_by_username(email, db)
#         if user:
#             login_time = userService.update_login_time(user, db)
#             if not login_time:
#                 return StandardResponse.fail(message="เกิดข้อผิดพลาดในเข้าสู่ระบบ")
#             access_token = security.create_access_token(data={"sub":str(user.user_id)})
#             # return RedirectResponse(url="/", status_code=302)
#             return TokenResponse(access_token=access_token, token_type="bearer", data="member")
#         else:
#             register_data = {
#                 "email": email,
#                 "type": "google_register"
#             }
#             temp_token = security.create_access_token(data=register_data)
#             # return RedirectResponse()
#             return TokenResponse(access_token=temp_token, token_type="bearer", data="register")

#     except Exception as ex:
#         print(ex)
#         return StandardResponse.fail(message=str(ex))

@router.post("/google/login")
def google_login(request_body: GoogleLoginDTO, db: Session = Depends(database.get_db)):
    try:
        id_info = id_token.verify_oauth2_token(request_body.id_token, requests.Request(), GOOGLE_CLIENT_ID)
        email = id_info["email"]
        google_id = id_info["sub"]
        user = userService.get_user_by_username(email, db)
        if user:
            if user.provider != "google":
                return StandardResponse.fail(message="บัญชีนี้ไม่ได้สมัครด้วย Google")
            access_token = security.create_access_token(data={"sub": str(user.user_id)})
            return TokenResponse(
                access_token=access_token,
                token_type="bearer"
            )
        
        temp_token = security.create_access_token(data={"email": email, "type": "google_register"})
        return TokenResponse(
            access_token=temp_token,
            token_type="bearer"
        )

    except ValueError:
        return StandardResponse.fail(message="Invalid token")

@router.post("/google/register")
def google_register(request: GoogleRegisterDTO, db: Session = Depends(database.get_db)):
    try:
        try:
            payload = jwt.decode(request.temp_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "google_register":
                return StandardResponse.fail(message="Invalid token")
        except Exception as ex:
            return StandardResponse.fail(message=str(ex))
        
        email = payload.get("email")
        existing = userService.get_user_by_username(email, db)
        if existing:
            return StandardResponse.fail(
                message="Email นี้ถูกใช้งานแล้ว"
            )

        new_user = MasUserModel(
            email = email,
            username = request.username,
            gender = request.gender,
            birth_date = request.age,
            provider = "google"
        )

        user, message = userService.create_user_account_with_google(new_user, db)
        if not user:
            return StandardResponse.fail(message=message)

        login_time = userService.update_login_time(user, db)
        if not login_time:
            return StandardResponse.fail(message="เกิดข้อผิดพลาดในเข้าสู่ระบบ")
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
    except Exception as ex:
        db.rollback()
        return StandardResponse.fail(message=str(ex))