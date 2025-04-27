from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import text
from app.core.config import settings

query_logging = False
engine = create_engine(settings.DATABASE_URL, echo=query_logging)


def setup_pg_trgm_and_indexes(session: Session):
    # 1. Check extension pg_trgm
    result = session.exec(
        text("SELECT 1 FROM pg_extension WHERE extname = 'pg_trgm';")
    ).first()
    if not result:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        print("✅ Created extension: pg_trgm")
    else:
        print("✅ Extension pg_trgm already exists.")

    # 2. Check index on note.title
    result = session.exec(
        text(
            """
            SELECT 1 FROM pg_indexes 
            WHERE tablename = 'note' AND indexname = 'idx_note_title_trgm';
            """
        )
    ).first()
    if not result:
        session.exec(
            text(
                """
                CREATE INDEX idx_note_title_trgm 
                ON note USING gin (title gin_trgm_ops);
                """
            )
        )
        print("✅ Created GIN index on note.title")
    else:
        print("✅ GIN index on note.title already exists.")

    # 3. Check index on note.content
    result = session.exec(
        text(
            """
            SELECT 1 FROM pg_indexes 
            WHERE tablename = 'note' AND indexname = 'idx_note_content_trgm';
            """
        )
    ).first()
    if not result:
        session.exec(
            text(
                """
                CREATE INDEX idx_note_content_trgm 
                ON note USING gin (content gin_trgm_ops);
                """
            )
        )
        print("✅ Created GIN index on note.content")
    else:
        print("✅ GIN index on note.content already exists.")


def init_db():
    from app.models import user, note, setting, task, scheduler

    SQLModel.metadata.create_all(engine)

    # After create_all, start setting up extension + index
    with Session(engine) as session:
        setup_pg_trgm_and_indexes(session)
        session.commit()
