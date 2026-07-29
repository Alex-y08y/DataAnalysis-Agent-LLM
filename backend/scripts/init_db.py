"""Initialize database tables and seed default data."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils.db_utils import init_db, SessionLocal
from services.auth_service import AuthService, hash_password
from models.user import UserRole, User
from models.datasource import DataSource, DataSourceType


def seed_default_admin():
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == "admin").first()
        if existing:
            print("Default admin user already exists, skipping.")
            return
        admin = User(
            username="admin",
            password_hash=hash_password("admin123"),
            email="admin@example.com",
            role=UserRole.admin,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("Default admin user created (admin / admin123).")
    finally:
        db.close()


def seed_test_data():
    db = SessionLocal()
    try:
        # Test analyst user
        analyst = User(
            username="analyst",
            password_hash=hash_password("analyst123"),
            email="analyst@example.com",
            role=UserRole.analyst,
            is_active=True,
        )
        db.add(analyst)

        # Test datasource
        ds = DataSource(
            name="Sample MySQL",
            type=DataSourceType.mysql,
            host="localhost",
            port=3306,
            user="root",
            password_encrypted="",
            database_name="test",
        )
        db.add(ds)
        db.commit()
        print("Test data seeded (analyst user + sample datasource).")
    finally:
        db.close()


if __name__ == "__main__":
    print("Creating database tables ...")
    init_db()
    print("Tables created successfully.")
    seed_default_admin()
    seed_test_data()
    print("Database initialization complete.")
