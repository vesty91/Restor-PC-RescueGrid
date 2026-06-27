import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./rescuegrid.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def _add_column_if_missing(connection, table: str, column: str, ddl: str) -> None:
    inspector = inspect(connection)
    if table not in inspector.get_table_names():
        return
    columns = {c["name"] for c in inspector.get_columns(table)}
    if column not in columns:
        connection.execute(text(ddl))


def init_db() -> None:
    from . import models

    Base.metadata.create_all(engine)
    migrate_schema()


def migrate_schema() -> None:
    with engine.begin() as connection:
        _add_column_if_missing(connection, "client", "address", "ALTER TABLE client ADD COLUMN address VARCHAR(1000)")
        _add_column_if_missing(connection, "client", "contact_name", "ALTER TABLE client ADD COLUMN contact_name VARCHAR(255)")
        _add_column_if_missing(connection, "intervention", "disk_risk", "ALTER TABLE intervention ADD COLUMN disk_risk VARCHAR(80)")
        _add_column_if_missing(connection, "intervention", "offline_windows", "ALTER TABLE intervention ADD COLUMN offline_windows VARCHAR(80)")
        _add_column_if_missing(connection, "intervention", "labor_minutes", "ALTER TABLE intervention ADD COLUMN labor_minutes INTEGER DEFAULT 0")
        _add_column_if_missing(connection, "intervention", "labor_rate", "ALTER TABLE intervention ADD COLUMN labor_rate FLOAT DEFAULT 0")
        _add_column_if_missing(connection, "intervention", "signature_path", "ALTER TABLE intervention ADD COLUMN signature_path VARCHAR(1024)")
        _add_column_if_missing(connection, "intervention", "ai_summary", "ALTER TABLE intervention ADD COLUMN ai_summary TEXT")
        _add_column_if_missing(connection, "invoice", "quote_id", "ALTER TABLE invoice ADD COLUMN quote_id INTEGER")
        _add_column_if_missing(connection, "invoice", "payment_method", "ALTER TABLE invoice ADD COLUMN payment_method VARCHAR(80)")


def get_session():
    with SessionLocal() as session:
        yield session
