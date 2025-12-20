"""
Seed script to populate database with sample doctors
"""

from datetime import time
from db.database import SessionLocal, init_db
from db.models import Doctor

def seed_doctors():
    """Add sample doctors to database"""
    db = SessionLocal()

    try:
        # Check if doctors already exist
        existing = db.query(Doctor).count()
        if existing > 0:
            print(f"Database already has {existing} doctors. Skipping seed.")
            return

        sample_doctors = [
            Doctor(
                name="Dr. Rajesh Ahuja",
                specialization="Cardiology",
                email="dr.ahuja@hospital.com",
                phone="+91-98765-43210",
                available_days=["Monday", "Tuesday", "Wednesday", "Friday"],
                available_start_time=time(9, 0),
                available_end_time=time(17, 0)
            ),
            Doctor(
                name="Dr. Priya Sharma",
                specialization="General Physician",
                email="dr.sharma@hospital.com",
                phone="+91-98765-43211",
                available_days=["Monday", "Wednesday", "Thursday", "Friday", "Saturday"],
                available_start_time=time(8, 0),
                available_end_time=time(16, 0)
            ),
            Doctor(
                name="Dr. Amit Patel",
                specialization="Orthopedics",
                email="dr.patel@hospital.com",
                phone="+91-98765-43212",
                available_days=["Tuesday", "Thursday", "Friday", "Saturday"],
                available_start_time=time(10, 0),
                available_end_time=time(18, 0)
            ),
            Doctor(
                name="Dr. Sneha Reddy",
                specialization="Pediatrics",
                email="dr.reddy@hospital.com",
                phone="+91-98765-43213",
                available_days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                available_start_time=time(9, 0),
                available_end_time=time(15, 0)
            ),
            Doctor(
                name="Dr. Vikram Singh",
                specialization="Dermatology",
                email="dr.singh@hospital.com",
                phone="+91-98765-43214",
                available_days=["Monday", "Wednesday", "Friday", "Saturday"],
                available_start_time=time(11, 0),
                available_end_time=time(19, 0)
            ),
            Doctor(
                name="Dr. Anita Gupta",
                specialization="Neurology",
                email="dr.gupta@hospital.com",
                phone="+91-98765-43215",
                available_days=["Tuesday", "Wednesday", "Thursday", "Saturday"],
                available_start_time=time(9, 0),
                available_end_time=time(17, 0)
            ),
            Doctor(
                name="Dr. Rahul Mehta",
                specialization="General Physician",
                email="dr.mehta@hospital.com",
                phone="+91-98765-43216",
                available_days=["Monday", "Tuesday", "Friday", "Saturday", "Sunday"],
                available_start_time=time(7, 0),
                available_end_time=time(15, 0)
            ),
            Doctor(
                name="Dr. Kavita Desai",
                specialization="Gynecology",
                email="dr.desai@hospital.com",
                phone="+91-98765-43217",
                available_days=["Monday", "Wednesday", "Thursday", "Friday"],
                available_start_time=time(10, 0),
                available_end_time=time(18, 0)
            )
        ]

        for doctor in sample_doctors:
            db.add(doctor)

        db.commit()
        print(f"[SUCCESS] Added {len(sample_doctors)} doctors to the database")

    except Exception as e:
        print(f"[ERROR] Failed to seed doctors: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Seeding doctors...")
    seed_doctors()
    print("Done!")
