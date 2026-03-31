"""
Creates 3 test users (one for each role) directly in the database.
Run this script locally; it will connect to the Render DB via your .env file.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core.auth import hash_password
from models.user import User, UserProfile

TEST_USERS = [
    {
        "username": "admin@dbadmin.quantrisk",
        "email": "admin@quantrisk.internal",
        "password": "Password123!",
        "name": "System Admin"
    },
    {
        "username": "analyst@analyst.quantrisk",
        "email": "analyst@quantrisk.internal",
        "password": "Password123!",
        "name": "Risk Analyst"
    },
    {
        "username": "viewer@portviewer.quantrisk",
        "email": "viewer@quantrisk.internal",
        "password": "Password123!",
        "name": "Portfolio Viewer"
    }
]

def seed_users():
    db = SessionLocal()
    try:
        print("Connecting to database...")
        for u_data in TEST_USERS:
            existing = db.query(User).filter(User.username == u_data["username"]).first()
            if existing:
                print(f"✅ User '{u_data['username']}' already exists. Skipping.")
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
            db.commit()

            print(f"✅ Created User -> Username: {u_data['username']} | Password: {u_data['password']}")
            
    except Exception as e:
        db.rollback()
        print(f"❌ Failed to seed users: {e}")
    finally:
        db.close()
        print("Done.")

if __name__ == "__main__":
    seed_users()
