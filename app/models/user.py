from app.models.base import BaseModel
from sqlmodel import Relationship
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models import Setting, Note, Label


class UserBase(BaseModel):
    full_name: str
    email: str
    avatar_url: str | None = None


class User(UserBase, table=True):
    password: str

    # One user can have one setting
    setting: Optional["Setting"] = Relationship(back_populates="user")

    # One user can have many labels
    labels: list["Label"] = Relationship(back_populates="user")

    # One user can have many notes
    notes: list["Note"] = Relationship(back_populates="user")
