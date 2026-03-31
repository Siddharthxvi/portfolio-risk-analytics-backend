"""
Creates a bootstrap admin user so you can log in immediately after deployment.
Run with: python scripts/create_admin.py
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import SessionLocal
from core.auth import hash_password
from models.user import User, UserProfile

ADMIN_USERNAME = "admin@dbadmin.quantrisk"
ADMIN_EMAIL    = "admin@quantrisk.internal"
ADMIN_PASSWORD = "ChangeMe123!"

def create_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == ADMIN_USERNAME).first()
        if existing:
            print(f"✅ Admin user '{ADMIN_USERNAME}' already exists. Skipping.")
            return

        user = User(
            username=ADMIN_USERNAME,
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            is_active=True,
        )
        db.add(user)
        db.flush()

        profile = UserProfile(user_id=user.user_id, full_name="System Administrator")
        db.add(profile)
        db.commit()

        print(f"✅ Admin user created!")
        print(f"   Username : {ADMIN_USERNAME}")
        print(f"   Password : {ADMIN_PASSWORD}")
        print(f"   Role     : ADMIN (from username domain)")
        print(f"\n⚠️  Change the password after first login!")

    except Exception as e:
        db.rollback()
        print(f"❌ Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()
