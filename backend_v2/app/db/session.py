import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pm_sim.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionFactory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def get_session() -> Generator[Session]:
    with SessionFactory() as session:
        yield session
