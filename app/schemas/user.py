from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    full_name: str
    email: str
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class SignupVerifyRequest(BaseModel):
    email: str
    otp: str

class ForgotPasswordVerifyRequest(BaseModel):
    email: str
    otp: str
    new_password: str

class UserRead(UserBase):
    id: int

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
