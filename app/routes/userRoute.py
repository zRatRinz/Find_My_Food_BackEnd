from fastapi import APIRouter, Depends, File, UploadFile
from sqlmodel import Session
from typing import Annotated
from app.core.config import ACCESS_TOKEN_EXPIRE_MIN
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
async def create_user(request_body:UserRegisterDTO, db:Session = Depends(database.get_db)):
    response = userService.create_user_account(request_body, db)
    return StandardResponse.success()


@router.post("/uploadUserImage")
async def upload_user_image(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], file: UploadFile = File(...), db: Session = Depends(database.get_db)):
    response = userService.update_user_image(current_user, file, db)
    return StandardResponse.success()

@router.post("/changePassword")
def change_user_password(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], request_body: ChangePasswordDTO, db: Session = Depends(database.get_db)):
    response = userService.change_user_password(current_user, request_body, db)
    return StandardResponse.success()
    
@router.patch("/updateUsername")
def update_user_username(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], request_body: UpdateUsernameDTO, db: Session = Depends(database.get_db)):
    response = userService.update_user_username(current_user, request_body, db)
    return StandardResponse.success()

@router.get("getSimpleUserInfo")
def get_simple_user_info(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], db: Session = Depends(database.get_db)):
    response = userService.get_simple_user_info(current_user.user_id, db)
    return StandardResponse.success(data=response)
    
@router.get("/getUserLikeRecipe")
def get_user_like_recipe(current_user: Annotated[MasUserModel, Depends(get_current_active_user)], db: Session = Depends(database.get_db)):
    response = userService.get_user_like_recipe(current_user.user_id, db)
    return StandardResponse.success(data=response)
