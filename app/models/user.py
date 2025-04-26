from app.models.base import BaseModel
from sqlmodel import Relationship
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from app.models.setting import Setting
    from app.models.note import Note


class UserBase(BaseModel):
    full_name: str
    email: str
    avatar_url: Optional[str] = None


class User(UserBase, table=True):
    password: str

    # One user can have one setting
    setting: Optional["Setting"] = Relationship(back_populates="user")

    # One user can have many notes
    notes: List["Note"] = Relationship(back_populates="user")
