from app.models.base import BaseModel
from sqlmodel import Field, Relationship
from typing import Optional
from datetime import datetime

class SchedulerBase(BaseModel):
    note_id: int = Field(foreign_key="note.id", nullable=False)
    scheduled_time: datetime
    is_sent: bool = False

class Scheduler(SchedulerBase, table=True):
    pass
