from pydantic import BaseModel
from typing import Optional


class NoteBase(BaseModel):
    title: str
    content: str
    is_pinned: bool = False
    is_finished: bool = False
    is_archived: bool = False
    label_id: Optional[int] = None


class NoteCreate(NoteBase):
    pass


class NoteRead(NoteBase):
    id: int


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_finished: Optional[bool] = None
    is_archived: Optional[bool] = None
    label_id: Optional[int] = None
