from app.models.base import BaseModel
from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models import User, Note


class LabelBase(BaseModel):
    name: str
    color: int


class Label(LabelBase, table=True):
    # Many labels belong to one user
    user_id: int = Field(foreign_key="user.id", nullable=False)
    user: Optional["User"] = Relationship(back_populates="labels")

    # One label can have many notes
    notes: list["Note"] = Relationship(back_populates="label")
