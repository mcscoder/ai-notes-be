from sqlmodel import SQLModel, create_engine
from app.core.config import settings

query_logging = False
engine = create_engine(settings.DATABASE_URL, echo=query_logging)


def init_db():
    from app.models import user, note, setting, label, task
    SQLModel.metadata.create_all(engine)

    # Insert hard labels if not exist
    from sqlmodel import Session, select
    with Session(engine) as session:
        existing = session.exec(select(label.Label)).first()
        if not existing:
            for i in range(1, 6):  # Tạo 5 label mẫu
                session.add(label.Label(name=f"label {i}"))
            session.commit()
