import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pm_sim.db")

engine = create_engine(DATABASE_URL)
SessionFactory = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)
