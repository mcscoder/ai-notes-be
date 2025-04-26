from app.models.base import BaseModel
from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, Optional, List
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.task import Task


class NoteBase(BaseModel):
    title: str
    type: int
    content: Optional[str] = None
    labels: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    is_pinned: bool = False
    is_finished: bool = False
    is_archived: bool = False


class Note(NoteBase, table=True):
    # Many notes belong to one user
    user_id: int = Field(foreign_key="user.id", nullable=False)
    user: Optional["User"] = Relationship(back_populates="notes")

    # One note can have many tasks
    tasks: List["Task"] = Relationship(
        back_populates="note", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
