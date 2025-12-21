"""
Database migration script to add password columns to Patient and Doctor tables
Run this once to update the existing database schema
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/smart_doctor_db")

def migrate():
    """Add password column to patients and doctors tables"""
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as conn:
            # Add password column to patients table if it doesn't exist
            conn.execute(text("""
                ALTER TABLE patients
                ADD COLUMN IF NOT EXISTS password VARCHAR(255) NOT NULL DEFAULT 'temp_password_change_me';
            """))

            # Add password column to doctors table if it doesn't exist
            conn.execute(text("""
                ALTER TABLE doctors
                ADD COLUMN IF NOT EXISTS password VARCHAR(255) NOT NULL DEFAULT 'temp_password_change_me';
            """))

            conn.commit()

            print("[SUCCESS] Migration successful!")
            print("[WARNING] Note: Existing users have a default password. They need to update it.")
            print("          Default password: 'temp_password_change_me'")

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        raise

if __name__ == "__main__":
    print("Running database migration to add password columns...")
    migrate()
