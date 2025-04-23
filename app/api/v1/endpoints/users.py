from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.core.deps import get_current_user
from app.crud import v1
from app.db import session

from app.models import user as UserModel
from app.schemas import user as UserSchema, common as CommonSchema

router = APIRouter()


@router.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint is working!"}


@router.get("/me", response_model=UserSchema.UserRead)
async def get_user_me(
    current_user: UserModel.User = Depends(get_current_user),
):
    return current_user


@router.put("/me", response_model=UserSchema.UserRead)
async def update_user_me(
    user_update: UserSchema.UserUpdate,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    user = v1.user.update_user(
        user_update=user_update,
        user=current_user,
        session=session,
    )
    return user


@router.put("/me/password", response_model=CommonSchema.Message)
async def update_user_password(
    user_password_update: UserSchema.UserPasswordUpdate,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    user = v1.user.update_user_password(
        user_password_update=user_password_update,
        user=current_user,
        session=session,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    return CommonSchema.Message(message="Password updated successfully")


@router.put("/me/settings", response_model=UserSchema.UserSettings)
async def update_user_settings(
    user_settings_update: UserSchema.UserSettingsUpdate,
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    setting = v1.user.update_user_settings(
        user_settings_update=user_settings_update,
        user=current_user,
        session=session,
    )
    return setting


@router.get("/me/settings", response_model=UserSchema.UserSettings)
async def get_user_settings(
    current_user: UserModel.User = Depends(get_current_user),
    session: Session = Depends(session.get_session),
):
    return v1.user.get_user_settings(user=current_user, session=session)
