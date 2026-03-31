from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from core.config import settings
import urllib.parse

# Force SSL requirement for external Render databases
connect_args = {}
if "render.com" in settings.DATABASE_URL or "sslmode=require" in settings.DATABASE_URL:
    connect_args["sslmode"] = "require"

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
