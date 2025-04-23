from pydantic import BaseModel
from typing import Optional

class LabelBase(BaseModel):
    name: str
    color: int

class LabelCreate(LabelBase):
    pass

class LabelRead(LabelBase):
    id: int

class LabelUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[int] = None
