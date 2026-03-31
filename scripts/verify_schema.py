import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from core.database import engine, Base
import models

def verify_schema():
    print("Starting Deep Schema Verification...")
    
    try:
        inspector = inspect(engine)
        live_tables = set(inspector.get_table_names())
        print("Successfully connected to the database over SSL.\n")
    except Exception as e:
        print(f"FAILED TO CONNECT! Error: {e}")
        return

    expected_tables = set(Base.metadata.tables.keys())
    
    missing_in_db = expected_tables - live_tables
    extra_in_db = live_tables - expected_tables
    
    errors_found = 0

    if missing_in_db:
        print(f"❌ DATABASE MISSING TABLES: {missing_in_db}")
        errors_found += 1
    if extra_in_db:
        print(f"⚠️ DATABASE HAS EXTRA TABLES: {extra_in_db} (Usually safe to ignore)")

    tables_to_check = expected_tables.intersection(live_tables)
    print(f"Checking {len(tables_to_check)} core tables for column consistency...")
    
    for table_name in tables_to_check:
        live_columns = {col['name']: col for col in inspector.get_columns(table_name)}
        expected_columns = {col.name: col for col in Base.metadata.tables[table_name].columns}
        
        missing_cols = set(expected_columns.keys()) - set(live_columns.keys())
        extra_cols = set(live_columns.keys()) - set(expected_columns.keys())
        
        if missing_cols or extra_cols:
            print(f"\n❌ TABLE DRIFT DETECTED IN: '{table_name}'")
            if missing_cols:
                print(f"   -> Columns defined in Python but MISSING in DB: {missing_cols}")
                errors_found += 1
            if extra_cols:
                print(f"   -> Columns existing in DB but NOT in Python: {extra_cols}")

    print("\n-------------------------")
    if errors_found == 0:
        print("✅ SUCCESS: The Live Database schema EXACTLY matches the Backend Models!")
    else:
        print(f"❌ FAIL: Detected {errors_found} structural mismatches that will cause crashes.")

if __name__ == "__main__":
    verify_schema()
