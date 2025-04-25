from app.models.base import BaseModel
from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, Optional, List
from . import NoteLabelLink

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.label import Label
    from app.models.task import Task


class NoteBase(BaseModel):
    title: str
    content: str
    type: int
    is_pinned: bool = False
    is_finished: bool = False
    is_archived: bool = False


class Note(NoteBase, table=True):
    # Many notes belong to one user
    user_id: int = Field(foreign_key="user.id", nullable=False)
    user: Optional["User"] = Relationship(back_populates="notes")

    # One note can have many labels
    labels: List["Label"] = Relationship(
        back_populates="notes", link_model=NoteLabelLink
    )
    
    # One note can have many tasks
    tasks: List["Task"] = Relationship(
        back_populates="note",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
