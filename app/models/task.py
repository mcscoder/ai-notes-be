from app.models.base import BaseModel
from sqlmodel import Field, Relationship
from typing import TYPE_CHECKING, Optional, List

if TYPE_CHECKING:
    from app.models.note import Note


class TaskBase(BaseModel):
    title: str
    is_finished: bool = False


class Task(TaskBase, table=True):
    # Many tasks belong to one note
    note_id: Optional[int] = Field(foreign_key="note.id")
    note: Optional["Note"] = Relationship(back_populates="tasks")

    parent_id: Optional[int] = Field(default=None, foreign_key="task.id")
    parent: Optional["Task"] = Relationship(
        back_populates="tasks", sa_relationship_kwargs={"remote_side": "Task.id"}
    )
    tasks: Optional[List["Task"]] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
 