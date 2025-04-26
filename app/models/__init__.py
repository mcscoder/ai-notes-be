from sqlalchemy import event
from app.models.base import BaseModel, utc_now
from app.models import scheduler


@event.listens_for(BaseModel, "before_update", propagate=True)
def receive_before_update(mapper, connection, target):
    target.updated_at = utc_now()
