from app.models import BaseModel
from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from app.models import User, Label


class NoteBase(BaseModel):
    title: str
    content: str
    is_pinned: bool = Field(default=False)
    is_finished: bool = Field(default=False)
    is_archived: bool = Field(default=False)

class Note(NoteBase, table=True):
    # Many notes belong to one user
    user_id: int = Field(foreign_key="user.id", nullable=False)
    user: Optional["User"] = Relationship(back_populates="notes")

    # Many notes belong to one label
    label_id: int = Field(foreign_key="label.id", nullable=False)
    label: Optional["Label"] = Relationship(back_populates="notes")
