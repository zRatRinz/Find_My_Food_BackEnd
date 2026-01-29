from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from typing import Annotated
from app.core.config import ACCESS_TOKEN_EXPIRE_MIN
from app.core import security
from app.dependencies import oauth2_scheme, get_current_active_user
from app.db import database
from app.models.userModel import MasUserModel
from app.schemas.userDTO import UserRegisterDTO, UserAccountDTO, VerifyPasswordDTO, ChangePasswordDTO,UpdateUsernameDTO
from app.services import userService
from app.schemas.response import TokenResponse, StandardResponse

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/")
def root(token: Annotated[str, Depends(oauth2_scheme)]):
    return {"token":token}

@router.post("/createUser")
async def create_user(request:UserRegisterDTO, db:Session = Depends(database.get_db)):
    try:
        response, message = userService.create_user_account(request, db)
        if not response:
            return StandardResponse(message=message)
        return StandardResponse.success()
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
async def upload_user_image(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    try:
        response, message = userService.update_user_image(current_user, file, db)
        if message:
            return StandardResponse.fail(message=message)
        return StandardResponse.success()
    except Exception as ex:
        return StandardResponse.fail(message=str(ex))
    
# @router.post("/verifyCurrentPassword")
# def verify_current_password(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], request_body: VerifyPasswordDTO, db: Session = Depends(database.get_db)):
#     if not security.verify_password(current_user.password, request_body.password):
#         return StandardResponse.fail(message="รหัสผ่านไม่ถูกต้อง")
#     return StandardResponse.success()

@router.post("/changePassword")
def change_user_password(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], request_body: ChangePasswordDTO, db: Session = Depends(database.get_db)):
    response, message = userService.change_user_password(current_user, request_body, db)
    if not response:
        return StandardResponse.fail(message=message)
    return StandardResponse.success()
    
@router.patch("/updateUsername")
def update_user_username(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], request_body: UpdateUsernameDTO, db: Session = Depends(database.get_db)):
    response, message = userService.update_user_username(current_user, request_body, db)
    if not response:
        return StandardResponse.fail(message=message)
    return StandardResponse.success()

@router.get("getSimpleUserInfo")
def get_simple_user_info(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], db: Session = Depends(database.get_db)):
    response = userService.get_simple_user_info(current_user.user_id, db)
    if not response:
        return StandardResponse.fail(message="ไม่พบข้อมูล")
    return StandardResponse.success(data=response)
    