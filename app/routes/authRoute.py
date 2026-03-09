from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlmodel import Session
from app.db import database
from app.dependencies import get_current_active_user
from app.services import authService
from app.models.userModel import MasUserModel
from app.schemas.userDTO import (
    UserAccountDTO, GoogleRegisterDTO, GoogleLoginDTO, UpdateFCMTokenDTO,
    UserForgetPasswordEmailDTO, VerifyOTPDTO, ResetPasswordDTO
)
from app.schemas.response import TokenResponse, StandardResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(request_body: Annotated[OAuth2PasswordRequestForm, Depends()], db:Session = Depends(database.get_db)):
    response = authService.login_process(request_body.username, request_body.password, db)
    return response

@router.post("/google/login", response_model=TokenResponse)
async def google_login(request_body: GoogleLoginDTO, db: Session = Depends(database.get_db)):
    response = authService.google_login_process(request_body.id_token, db)
    return response

@router.post("/google/register", response_model=TokenResponse)
async def google_register(request_body: GoogleRegisterDTO, db: Session = Depends(database.get_db)):
    response = authService.google_register_process(request_body, db)
    return response

@router.post("/updateFCMToken")
def update_fcm_token(current_user: Annotated[MasUserModel, Depends(get_current_active_user)],
                     request_body: UpdateFCMTokenDTO,
                     db: Session = Depends(database.get_db)):
    response = authService.update_fcm_token(current_user.user_id, request_body.fcm_token, db)
    return StandardResponse.success()

@router.post("/forgetPassword/requestOTP")
def request_otp(request_body: UserForgetPasswordEmailDTO, db: Session = Depends(database.get_db)):
    response = authService.request_otp_process(request_body.email, db)
    return StandardResponse.success()

@router.post("/forgetPassword/verifyOTP")
def verify_otp(request_body: VerifyOTPDTO, db: Session = Depends(database.get_db)):
    response = authService.verify_otp_process(request_body.email, request_body.otp, db)
    return StandardResponse.success()

@router.post("/forgetPassword/resetPassword")
def reset_password(Response, request_body: ResetPasswordDTO, db: Session = Depends(database.get_db)):
    response = authService.reset_password_process(request_body.email, request_body.otp, request_body.new_password, db)
    return StandardResponse.success()