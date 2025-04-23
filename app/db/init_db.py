from sqlmodel import SQLModel, create_engine
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, echo=True)


def init_db():
    from app.models import User, Note, Setting, Label

    SQLModel.metadata.create_all(engine)
