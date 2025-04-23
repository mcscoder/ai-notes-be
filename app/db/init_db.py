from sqlmodel import SQLModel, create_engine
from app.core.config import settings

query_logging = False
engine = create_engine(settings.DATABASE_URL, echo=query_logging)


def init_db():
    from app.models import user, note, setting, label

    SQLModel.metadata.create_all(engine)
