import os
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy import event

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/database.db")

connect_args = {"check_same_thread": False}
engine = create_engine(DATABASE_URL, connect_args=connect_args)


def _set_wal(dbapi_conn, connection_record):
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA busy_timeout=5000")


event.listen(engine, "connect", _set_wal)


def create_db_and_tables():
    os.makedirs("data/backups", exist_ok=True)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
