from datetime import timedelta
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.schemas import user, token
from app.db import session
from app.crud import v1
from app.core import security
from app.services import otp_service, email_service

router = APIRouter()

@router.post("/signup", status_code=status.HTTP_200_OK)
async def signup_request(
    user_create: user.UserCreate,
    session: Session = Depends(session.get_session),
):
    if v1.user.get_user_by_email(user_create.email, session):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    otp = otp_service.generate_otp()
    otp_service.save_signup_otp(user_create.email, user_create.model_dump(), otp)
    email_service.send_otp_email(user_create.email, otp, subject="OTP for VKU Notes - Đăng ký tài khoản")
    return {"message": "OTP sent to email"}

@router.post("/signup/verify", response_model=user.UserRead)
async def signup_verify(
    data: user.SignupVerifyRequest,
    session: Session = Depends(session.get_session),
):
    user_obj = v1.user.verify_signup_otp_and_create_user(data, session)
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )
    return user_obj

@router.post("/login-form", response_model=token.Token)
async def form_login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(session.get_session),
):
    user_obj = v1.user.authenticate_user(
        user_login=user.UserLogin(
            email=form_data.username, password=form_data.password
        ),
        session=session,
    )
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = security.create_access_token(
        user_id=user_obj.id, expires_delta=timedelta(days=30)
    )
    return token.Token(access_token=access_token, token_type="bearer")

@router.post("/login", response_model=token.Token)
async def login_for_access_token(
    user_login: user.UserLogin,
    session: Session = Depends(session.get_session),
):
    user_obj = v1.user.authenticate_user(
        user_login=user_login,
        session=session,
    )
    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = security.create_access_token(
        user_id=user_obj.id, expires_delta=timedelta(days=30)
    )
    return token.Token(access_token=access_token, token_type="bearer")

@router.post("/forgot-password")
async def forgot_password(
    req: user.ForgotPasswordRequest,
    session: Session = Depends(session.get_session),
):
    if not v1.user.get_user_by_email(req.email, session):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found",
        )
    otp = otp_service.generate_otp()
    otp_service.save_forgot_otp(req.email, otp)
    email_service.send_otp_email(req.email, otp, subject="OTP for VKU Notes - Quên mật khẩu")
    return {"message": "OTP sent to email"}

@router.post("/forgot-password/verify")
async def forgot_password_verify(
    data: user.ForgotPasswordVerifyRequest,
    session: Session = Depends(session.get_session),
):
    success = v1.user.verify_forgot_otp_and_reset_password(data, session)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP",
        )
    return {"message": "Password reset successful"}
