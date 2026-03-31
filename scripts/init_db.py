import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from core.database import engine

def init_db():
    print("Initializing Database using exact schema.sql...")
    try:
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "schema.sql")
        
        with open(schema_path, "r") as f:
            sql_commands = f.read()

        # Connect and execute raw SQL
        with engine.begin() as conn:
            conn.execute(text(sql_commands))
            
        print("✅ Successfully dropped existing tables and rebuilt the database directly from schema.sql!")

    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")

if __name__ == "__main__":
    init_db()
