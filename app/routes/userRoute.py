from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from typing import Annotated
from datetime import timedelta

from app.core.config import ACCESS_TOKEN_EXPIRE_MIN
from app.core import security
from app.dependencies import oauth2_scheme, get_current_user
from app.db import database
from app.models.userModel import UserInfoModel
from app.schemas.userDTO import UserRegisterDTO, UserLoginResponseDTO, UserProfileDTO
from app.services import userService
from app.schemas.response import TokenResponse, StandardResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def root(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token":token}

@router.post("/createUser")
async def create_user(request:UserRegisterDTO, db:Session = Depends(database.get_db)):
    try:
        response, message = userService.create_login_user(request, db)
        if message:
            return StandardResponse(message=message)
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

@router.post("/login")
async def login(request: Annotated[OAuth2PasswordRequestForm, Depends()], db:Session = Depends(database.get_db)):
    try:
        user = userService.authenticate_user(request.username, request.password,db)
        if not user:
            # raise HTTPException(
            #         status_code=status.HTTP_401_UNAUTHORIZED,
            #         detail="Incorrect username or password",
            #         headers={"WWW-Authenticate": "Bearer"},
            #     )
            return StandardResponse.fail(message="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        
        access_token_exprires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN)
        access_token = security.create_access_token(
            data={"sub":str(user.user_id)},
            expires_delta=access_token_exprires
        )

        user_info = userService.get_user_info(user.user_id, db)
        if not user_info:
            # raise HTTPException(status_code=404, detail="User profile not found")
            return StandardResponse.fail(message="ไม่พบข้อมูลผู้ใช้งาน โปรดติดต่อเจ้าหน้าที่")
        
        user_info_data = UserProfileDTO(
            username = user_info.login_account.username,
            first_name = user_info.first_name,
            last_name = user_info.last_name,
            age = user_info.age,
            gender = user_info.gender,
            email = user_info.email
        )
        return TokenResponse(
            access_token = access_token,
            token_type = "bearer",
            data = user_info_data
        )
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))

# @router.get("/getCurrentUser", response_model=StandardResponse[UserProfileDTO])
# def get_current_user_data(current_user: Annotated[UserLoginDTO, Depends(get_current_user)]):
#     try:
#         return StandardResponse(
#             message="success",
#             data=current_user
#         )
#     except Exception as ex:
#         return StandardResponse(message=str(ex))

@router.post("/uploadUserImage")
async def upload_user_image(current_user: Annotated[UserInfoModel, Depends(get_current_user)], file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    try:
        response, message = userService.update_user_image(current_user, file, db)
        if message:
            return StandardResponse.fail(message=message)
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))