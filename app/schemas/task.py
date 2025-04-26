from pydantic import BaseModel
from typing import Optional, List


class TaskBase(BaseModel):
    title: str
    content: Optional[str] = None
    is_finished: bool = False


class TaskCreate(TaskBase):
    parent_id: Optional[int] = None


class TaskRead(TaskBase):
    id: int
    tasks: Optional[List["TaskRead"]] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    is_finished: Optional[bool] = None
    parent_id: Optional[int] = None
