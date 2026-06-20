import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rescuegrid.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    from . import models

    Base.metadata.create_all(engine)
    migrate_schema()


def migrate_schema() -> None:
    inspector = inspect(engine)
    if "intervention" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("intervention")}
    with engine.begin() as connection:
        if "disk_risk" not in columns:
            connection.execute(text("ALTER TABLE intervention ADD COLUMN disk_risk VARCHAR(80)"))
        if "offline_windows" not in columns:
            connection.execute(text("ALTER TABLE intervention ADD COLUMN offline_windows VARCHAR(80)"))


def get_session():
    with SessionLocal() as session:
        yield session
