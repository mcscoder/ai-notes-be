from app.models.base import BaseModel
from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.user import User

class SettingBase(BaseModel):
    text_size: int = 14
    theme: int = 0  # 0: light, 1: dark
    email_notifications: bool = True
    push_notifications: bool = True

class Setting(SettingBase, table=True):
    # One setting belongs to one user
    user_id: int = Field(foreign_key="user.id", unique=True, nullable=False)
    user: Optional["User"] = Relationship(back_populates="setting")
