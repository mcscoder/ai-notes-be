from app.models.base import BaseModel
from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, Optional
from . import NoteLabelLink

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.label import Label


class NoteBase(BaseModel):
    title: str
    content: str
    is_pinned: bool = False
    is_finished: bool = False
    is_archived: bool = False


class Note(NoteBase, table=True):
    # Many notes belong to one user
    user_id: int = Field(foreign_key="user.id", nullable=False)
    user: Optional["User"] = Relationship(back_populates="notes")

    # One note can have many labels
    labels: list["Label"] = Relationship(
        back_populates="notes", link_model=NoteLabelLink
    )
