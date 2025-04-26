from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SchedulerBase(BaseModel):
    note_id: int
    scheduled_time: datetime
    is_sent: bool = False

class SchedulerCreate(BaseModel):
    note_id: int
    scheduled_time: datetime

class SchedulerRead(SchedulerBase):
    id: int

class SchedulerUpdate(BaseModel):
    scheduled_time: Optional[datetime] = None
    is_sent: Optional[bool] = None
