from app.models.base import BaseModel
from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models.user import User

class SettingBase(BaseModel):
    text_size: int
    theme: int
    email_notifications: bool
    push_notifications: bool

class Setting(SettingBase, table=True):
    # One setting belongs to one user
    user_id: int = Field(foreign_key="user.id", unique=True, nullable=False)
    user: Optional["User"] = Relationship(back_populates="setting")
