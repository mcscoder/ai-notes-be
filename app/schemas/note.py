from pydantic import BaseModel
from typing import Optional, List

from app.schemas.label import LabelRead
from app.schemas.task import TaskRead


class NoteBase(BaseModel):
    title: str
    content: str
    type: int
    is_pinned: bool = False
    is_finished: bool = False
    is_archived: bool = False


class NoteCreate(NoteBase):
    label_ids: Optional[List[int]] = None


class NoteRead(NoteBase):
    id: int
    labels: Optional[List[LabelRead]] = None
    tasks: Optional[List[TaskRead]] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_finished: Optional[bool] = None
    is_archived: Optional[bool] = None
    label_ids: Optional[List[int]] = None
