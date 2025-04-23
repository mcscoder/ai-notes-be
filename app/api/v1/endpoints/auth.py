from datetime import timedelta
from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from app.schemas import user, token
from app.db import session
from app.crud import v1
from app.core import security

router = APIRouter()


@router.post(
    "/signup", response_model=user.UserRead, status_code=status.HTTP_201_CREATED
)
async def signup(
    user_create: user.UserCreate,
    session: Session = Depends(session.get_session),
):
    user_obj = v1.user.get_user_by_email(user_create.email, session)
    if user_obj:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    new_user = v1.user.create_user(user_create, session)
    return new_user


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
async def forgot_password():
    return {"message": "Forgot password endpoint is working!"}
