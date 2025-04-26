from pydantic import BaseModel
from typing import Optional, List

from app.schemas.task import TaskRead


class NoteBase(BaseModel):
    title: str
    type: int
    content: Optional[str] = None
    labels: List[str] = []
    is_pinned: bool = False
    is_finished: bool = False
    is_archived: bool = False


class NoteCreate(NoteBase):
    pass


class NoteRead(NoteBase):
    id: int
    tasks: Optional[List[TaskRead]] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    labels: List[str] = []
    is_pinned: Optional[bool] = None
    is_finished: Optional[bool] = None
    is_archived: Optional[bool] = None
