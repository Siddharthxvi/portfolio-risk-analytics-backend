import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from core.database import engine
from core.database import Base
import models  # Loads all the models into Base.metadata

def verify_schema():
    print("Verifying Database Schema...")
    
    # Introspect the LIVE database
    inspector = inspect(engine)
    live_tables = set(inspector.get_table_names())
    
    # What the backend Python code expects
    expected_tables = set(Base.metadata.tables.keys())
    
    missing_in_db = expected_tables - live_tables
    extra_in_db = live_tables - expected_tables
    
    if not missing_in_db and not extra_in_db:
        print("✅ SUCCESS: The live database tables strictly match the Backend's expected tables!")
    else:
        print("⚠️ SCHEMA MISMATCH DETECTED!")
        if missing_in_db:
            print(f"-> The Database is missing these tables: {missing_in_db}")
        if extra_in_db:
            print(f"-> The Database has extra/unknown tables: {extra_in_db}")

    print("\nChecking columns for 'asset' table as an example...")
    if 'asset' in live_tables:
        live_columns = [col['name'] for col in inspector.get_columns('asset')]
        expected_columns = [col.name for col in Base.metadata.tables['asset'].columns]
        
        missing_cols = set(expected_columns) - set(live_columns)
        if missing_cols:
             print(f"⚠️ Asset table is missing expected backend columns: {missing_cols}")
        else:
             print(f"✅ Asset table columns match perfectly!")

if __name__ == "__main__":
    verify_schema()
