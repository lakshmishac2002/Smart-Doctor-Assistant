"""
Test script to verify appointment booking functionality
"""
import requests
import json
from datetime import date, timedelta
import sys
import io

# Fix Windows console encoding issues
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

API_BASE_URL = "http://localhost:8000/api"

def test_health():
    """Test if API is running"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"✓ Health check: {response.status_code}")
        print(f"  Response: {response.json()}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_list_doctors():
    """Test listing doctors"""
    try:
        response = requests.get(f"{API_BASE_URL}/doctors")
        print(f"\n✓ List doctors: {response.status_code}")
        data = response.json()
        doctors = data.get('doctors', data)  # Handle both formats
        print(f"  Found {len(doctors)} doctors")
        if doctors:
            print(f"  First doctor: {doctors[0]['name']} - {doctors[0]['specialization']}")
        return doctors
    except Exception as e:
        print(f"\n✗ List doctors failed: {e}")
        return []

def test_book_appointment(doctor_id):
    """Test booking an appointment"""
    try:
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        payload = {
            "patient_name": "Test Patient",
            "patient_email": "test@example.com",
            "doctor_id": doctor_id,
            "appointment_date": tomorrow,
            "appointment_time": "10:00",
            "symptoms": "Test booking - QA verification"
        }

        print(f"\n→ Booking appointment...")
        print(f"  Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(f"{API_BASE_URL}/appointments", json=payload)

        print(f"✓ Book appointment: {response.status_code}")
        print(f"  Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 200:
            return response.json()
        else:
            print(f"  Error: {response.text}")
            return None

    except Exception as e:
        print(f"\n✗ Book appointment failed: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_get_appointments():
    """Test getting appointments"""
    try:
        response = requests.get(f"{API_BASE_URL}/appointments")
        print(f"\n✓ Get appointments: {response.status_code}")
        data = response.json()
        print(f"  Total appointments: {data.get('count', 0)}")

        if data.get('appointments'):
            print(f"  Latest appointment:")
            appt = data['appointments'][-1]
            print(f"    Patient: {appt.get('patient_name')}")
            print(f"    Doctor: {appt.get('doctor_name')}")
            print(f"    Date: {appt.get('appointment_date')} at {appt.get('appointment_time')}")
            print(f"    Status: {appt.get('status')}")

        return data
    except Exception as e:
        print(f"\n✗ Get appointments failed: {e}")
        return None

def test_chat():
    """Test chat endpoint"""
    try:
        payload = {
            "message": "Show me available cardiologists",
            "user_type": "patient",
            "session_id": None
        }

        print(f"\n→ Testing chat endpoint...")
        print(f"  Message: {payload['message']}")

        response = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=30)

        print(f"✓ Chat response: {response.status_code}")
        data = response.json()
        print(f"  Session ID: {data.get('session_id')}")
        print(f"  Tool calls: {data.get('tool_calls_made')}")
        print(f"  Response: {data.get('response')[:200]}...")

        return data
    except requests.exceptions.Timeout:
        print(f"\n✗ Chat timed out (this is expected if Ollama is slow)")
        return None
    except Exception as e:
        print(f"\n✗ Chat failed: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("=" * 60)
    print("SMART DOCTOR ASSISTANT - QA TEST SUITE")
    print("=" * 60)

    # Test 1: Health check
    if not test_health():
        print("\n❌ Backend is not running! Start it with: python backend/main.py")
        exit(1)

    # Test 2: List doctors
    doctors = test_list_doctors()
    if not doctors:
        print("\n❌ No doctors found! Run: python backend/seed_data.py")
        exit(1)

    # Test 3: Book appointment
    doctor_id = doctors[0]['id']
    booking_result = test_book_appointment(doctor_id)

    if booking_result and booking_result.get('success'):
        print("\n✅ Appointment booking WORKS!")
    else:
        print("\n❌ Appointment booking FAILED!")

    # Test 4: Verify appointment was saved
    appointments = test_get_appointments()

    if appointments and appointments.get('count', 0) > 0:
        print("\n✅ Appointments are being PERSISTED!")
    else:
        print("\n❌ Appointments are NOT being saved!")

    # Test 5: Chat endpoint
    chat_result = test_chat()

    if chat_result:
        print("\n✅ Chat endpoint WORKS!")
    else:
        print("\n⚠️  Chat endpoint has issues (check Ollama)")

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)
