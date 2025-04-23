from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from typing import Optional


def utc_now():
    return datetime.now(timezone.utc)


class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
