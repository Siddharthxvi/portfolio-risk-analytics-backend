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
from sqlalchemy import text, inspect
from fastapi import Depends
from core.database import get_db, engine, Base
import models

@app.get("/")
def read_root():
    return {"message": "Welcome to the Portfolio Risk Analytics API"}

@app.get("/bootstrap-users")
def bootstrap_users(db: Session = Depends(get_db)):
    """Creates the 3 default users required to login and test the platform."""
    from scripts.seed_users import TEST_USERS
    from core.auth import hash_password
    from models.user import User, UserProfile
    
    results = []
    try:
        for u_data in TEST_USERS:
            existing = db.query(User).filter(User.username == u_data["username"]).first()
            if existing:
                results.append(f"User '{u_data['username']}' already exists.")
                continue

            user = User(
                username=u_data["username"],
                email=u_data["email"],
                password_hash=hash_password(u_data["password"]),
                is_active=True,
            )
            db.add(user)
            db.flush()

            profile = UserProfile(user_id=user.user_id, full_name=u_data["name"])
            db.add(profile)
            results.append(f"Created: {u_data['username']}")
            
        db.commit()
        return {"status": "success", "actions": results, "passwords": "Password123!"}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": "disconnected", "details": str(e)}

@app.get("/verify-schema")
def verify_schema_endpoint():
    try:
        inspector = inspect(engine)
        live_tables = set(inspector.get_table_names())
    except Exception as e:
        return {"status": "error", "message": f"Failed to connect: {str(e)}"}

    expected_tables = set(Base.metadata.tables.keys())
    
    missing_in_db = list(expected_tables - live_tables)
    extra_in_db = list(live_tables - expected_tables)
    
    table_drift = {}
    tables_to_check = expected_tables.intersection(live_tables)
    
    for table_name in tables_to_check:
        live_columns = {col['name']: col for col in inspector.get_columns(table_name)}
        expected_columns = {col.name: col for col in Base.metadata.tables[table_name].columns}
        
        missing_cols = list(set(expected_columns.keys()) - set(live_columns.keys()))
        extra_cols = list(set(live_columns.keys()) - set(expected_columns.keys()))
        
        if missing_cols or extra_cols:
            table_drift[table_name] = {
                "missing_columns": missing_cols,
                "extra_columns": extra_cols
            }
            
    is_success = len(missing_in_db) == 0 and len(table_drift) == 0
            
    return {
        "status": "success" if is_success else "drift_detected",
        "message": "Database schema strictly matches!" if is_success else "Structural mismatches found.",
        "missing_tables": missing_in_db,
        "extra_tables": extra_in_db,
        "table_drift": table_drift
    }
