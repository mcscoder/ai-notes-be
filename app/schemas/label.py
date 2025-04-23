from pydantic import BaseModel
from typing import Optional

class LabelBase(BaseModel):
    name: str

class LabelCreate(LabelBase):
    pass

class LabelRead(LabelBase):
    id: int

class LabelUpdate(BaseModel):
    name: Optional[str] = None
