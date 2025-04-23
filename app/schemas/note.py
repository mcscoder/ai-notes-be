from pydantic import BaseModel
from typing import Optional, List

from app.schemas.label import LabelRead

class NoteBase(BaseModel):
    title: str
    content: str
    is_pinned: bool = False
    is_finished: bool = False
    is_archived: bool = False


class NoteCreate(NoteBase):
    label_ids: Optional[List[int]] = None


class NoteRead(NoteBase):
    id: int
    labels: List[LabelRead]


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_finished: Optional[bool] = None
    is_archived: Optional[bool] = None
    label_ids: Optional[List[int]] = None
