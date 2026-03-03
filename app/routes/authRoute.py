from fastapi import APIRouter, Depends, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from sqlmodel import Session
from app.db import database
from app.services import authService
from app.schemas.userDTO import UserAccountDTO, GoogleRegisterDTO, GoogleLoginDTO, UserForgetPasswordEmailDTO, VerifyOTPDTO, ResetPasswordDTO
from app.schemas.response import TokenResponse, StandardResponse

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login")
async def login(request_body: Annotated[OAuth2PasswordRequestForm, Depends()], db:Session = Depends(database.get_db)):
    response = authService.login_process(request_body.username, request_body.password, db)
    return StandardResponse.success(data=response)

@router.post("/google/login")
async def google_login(request_body: GoogleLoginDTO, db: Session = Depends(database.get_db)):
    response = authService.google_login_process(request_body.id_token, db)
    return StandardResponse.success(data=response)

@router.post("/google/register")
async def google_register(request_body: GoogleRegisterDTO, db: Session = Depends(database.get_db)):
    response = authService.google_register_process(request_body, db)
    return StandardResponse.success(data=response)

@router.post("/forgetPassword/requestOTP")
def request_otp(response_obj: Response, request_body: UserForgetPasswordEmailDTO, db: Session = Depends(database.get_db)):
    response = authService.request_otp_process(request_body.email, db)
    return StandardResponse.success()

@router.post("/forgetPassword/verifyOTP")
def verify_otp(response_obj: Response, request_body: VerifyOTPDTO, db: Session = Depends(database.get_db)):
    response = authService.verify_otp_process(request_body.email, request_body.otp, db)
    return StandardResponse.success()

@router.post("/forgetPassword/resetPassword")
def reset_password(response_obj: Response, request_body: ResetPasswordDTO, db: Session = Depends(database.get_db)):
    response = authService.reset_password_process(request_body.email, request_body.otp, request_body.new_password, db)
    return StandardResponse.success()