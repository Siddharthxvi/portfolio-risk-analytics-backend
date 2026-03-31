from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import api_router

app = FastAPI(title="Portfolio Risk Analytics API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi import Depends
from core.database import get_db

@app.get("/")
def read_root():
    return {"message": "Welcome to the Portfolio Risk Analytics API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Tries to execute a raw SQL 'SELECT 1' against the connected database
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "details": str(e)}
