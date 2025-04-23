from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class UserRead(BaseModel):
    id: int
    full_name: str
    email: str
    avatar_url: Optional[str] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserPasswordUpdate(BaseModel):
    current_password: str
    new_password: str


class UserSettingsUpdate(BaseModel):
    text_size: Optional[int] = None
    theme: Optional[int] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None


class UserSettings(BaseModel):
    text_size: int
    theme: int
    email_notifications: bool
    push_notifications: bool
