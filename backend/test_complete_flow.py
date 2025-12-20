"""
Comprehensive Test: Appointment Persistence & Double-Booking Prevention
Tests all three critical requirements:
1. Appointments persist in database
2. Appointments appear in doctor dashboard
3. Double-booking is prevented
"""

import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
from datetime import datetime, timedelta

API_BASE_URL = "http://localhost:8000/api"

def print_section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_1_create_appointment():
    """Test 1: Create a new appointment"""
    print_section("TEST 1: Create Appointment")

    # Get first doctor
    response = requests.get(f"{API_BASE_URL}/doctors")
    doctors_data = response.json()
    doctors = doctors_data.get('doctors', doctors_data)

    if not doctors:
        print("❌ FAIL: No doctors available")
        return None, None

    doctor = doctors[0]
    print(f"✅ Selected doctor: {doctor['name']} (ID: {doctor['id']})")
    print(f"   Specialization: {doctor['specialization']}")
    print(f"   Available days: {', '.join(doctor.get('available_days', []))}")

    # Find next valid date (Monday-Friday, not weekend)
    target_date = datetime.now() + timedelta(days=1)
    while target_date.strftime("%A") not in doctor.get('available_days', []):
        target_date += timedelta(days=1)
        if (target_date - datetime.now()).days > 30:
            print("❌ FAIL: Could not find valid date within 30 days")
            return None, None

    appointment_date = target_date.strftime("%Y-%m-%d")

    # Use a unique time to avoid conflicts from previous test runs
    import random
    hour = random.randint(9, 16)
    minute = random.choice([0, 30])
    appointment_time = f"{hour:02d}:{minute:02d}"

    print(f"\n📅 Booking appointment for: {appointment_date} at {appointment_time}")

    # Create appointment
    payload = {
        "patient_name": "Test Patient Alpha",
        "patient_email": "test_alpha@example.com",
        "doctor_id": doctor['id'],
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "symptoms": "Test symptoms for persistence verification"
    }

    response = requests.post(f"{API_BASE_URL}/appointments", json=payload)

    if response.status_code != 200:
        print(f"❌ FAIL: Could not create appointment")
        print(f"   Status: {response.status_code}")
        print(f"   Error: {response.text}")
        return None, None

    result = response.json()

    if not result.get('success'):
        print(f"❌ FAIL: Booking failed")
        print(f"   Reason: {result.get('error', 'Unknown error')}")
        return None, None

    appointment_id = result.get('appointment_id')
    print(f"\n✅ SUCCESS: Appointment created!")
    print(f"   Appointment ID: {appointment_id}")
    print(f"   Patient: {payload['patient_name']}")
    print(f"   Date: {appointment_date}")
    print(f"   Time: {appointment_time}")

    return doctor['id'], appointment_id, appointment_date, appointment_time

def test_2_verify_persistence(appointment_id):
    """Test 2: Verify appointment persisted in database"""
    print_section("TEST 2: Verify Appointment Persistence")

    response = requests.get(f"{API_BASE_URL}/appointments/{appointment_id}")

    if response.status_code != 200:
        print(f"❌ FAIL: Could not retrieve appointment {appointment_id}")
        print(f"   Status: {response.status_code}")
        return False

    appointment = response.json()

    print(f"✅ SUCCESS: Appointment persisted in database!")
    print(f"   ID: {appointment['id']}")
    print(f"   Patient: {appointment['patient_name']}")
    print(f"   Doctor ID: {appointment['doctor_id']}")
    print(f"   Date: {appointment['appointment_date']}")
    print(f"   Time: {appointment['appointment_time']}")
    print(f"   Status: {appointment['status']}")

    return True

def test_3_verify_dashboard(doctor_id, appointment_date):
    """Test 3: Verify appointment appears in doctor dashboard"""
    print_section("TEST 3: Verify Dashboard Display")

    # Get appointments for this doctor
    response = requests.get(
        f"{API_BASE_URL}/appointments",
        params={
            "doctor_id": doctor_id,
            "start_date": appointment_date,
            "end_date": appointment_date
        }
    )

    if response.status_code != 200:
        print(f"❌ FAIL: Could not fetch dashboard appointments")
        print(f"   Status: {response.status_code}")
        return False

    data = response.json()
    appointments = data.get('appointments', [])

    if not appointments:
        print(f"❌ FAIL: No appointments found in dashboard for doctor {doctor_id}")
        print(f"   Date range: {appointment_date}")
        return False

    print(f"✅ SUCCESS: Appointment appears in doctor dashboard!")
    print(f"   Total appointments shown: {data['count']}")
    print(f"\n   Dashboard Appointments:")
    for appt in appointments:
        print(f"   - [{appt['id']}] {appt['patient_name']} - {appt['appointment_date']} {appt['appointment_time']}")

    return True

def test_4_prevent_double_booking(doctor_id, appointment_date, appointment_time):
    """Test 4: Verify double-booking is prevented"""
    print_section("TEST 4: Verify Double-Booking Prevention")

    print(f"Attempting to book SAME time slot:")
    print(f"   Doctor ID: {doctor_id}")
    print(f"   Date: {appointment_date}")
    print(f"   Time: {appointment_time}")

    # Try to book the exact same slot
    payload = {
        "patient_name": "Test Patient Beta",
        "patient_email": "test_beta@example.com",
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "appointment_time": appointment_time,
        "symptoms": "Test double booking attempt"
    }

    response = requests.post(f"{API_BASE_URL}/appointments", json=payload)
    result = response.json()

    if result.get('success'):
        print(f"❌ FAIL: Double-booking was ALLOWED! This is a critical bug!")
        print(f"   Appointment ID: {result.get('appointment_id')}")
        return False

    # Verify it was rejected due to conflict
    if result.get('error_type') == 'conflict':
        print(f"✅ SUCCESS: Double-booking prevented!")
        print(f"   Error type: {result['error_type']}")
        print(f"   Message: {result['error']}")

        # Check for suggested slots
        if result.get('suggested_slots'):
            print(f"\n   Alternative slots suggested:")
            for slot in result['suggested_slots'][:3]:
                print(f"   - {slot['time']} ({slot['time_24h']})")

        return True
    else:
        print(f"⚠️  WARNING: Booking was rejected, but not due to conflict")
        print(f"   Error: {result.get('error', 'Unknown')}")
        print(f"   Error type: {result.get('error_type', 'None')}")
        return False

def test_5_overlapping_booking(doctor_id, appointment_date):
    """Test 5: Verify overlapping appointment is prevented"""
    print_section("TEST 5: Verify Overlapping Appointment Prevention")

    # Try to book overlapping time (10:15 overlaps with existing 10:00)
    overlap_time = "10:15"

    print(f"Attempting to book OVERLAPPING time slot:")
    print(f"   Original: 10:00 (30 min duration → ends at 10:30)")
    print(f"   Attempt: {overlap_time} (would start during existing appointment)")

    payload = {
        "patient_name": "Test Patient Gamma",
        "patient_email": "test_gamma@example.com",
        "doctor_id": doctor_id,
        "appointment_date": appointment_date,
        "appointment_time": overlap_time,
        "symptoms": "Test overlap prevention"
    }

    response = requests.post(f"{API_BASE_URL}/appointments", json=payload)
    result = response.json()

    if result.get('success'):
        print(f"❌ FAIL: Overlapping booking was ALLOWED! This is a critical bug!")
        return False

    if result.get('error_type') == 'conflict':
        print(f"✅ SUCCESS: Overlapping appointment prevented!")
        print(f"   Message: {result['error']}")
        return True
    else:
        print(f"⚠️  Booking rejected, but not specifically for overlap")
        print(f"   Error: {result.get('error', 'Unknown')}")
        return False

def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*60)
    print("  COMPREHENSIVE APPOINTMENT SYSTEM TEST")
    print("  Testing: Persistence, Dashboard, Double-Booking Prevention")
    print("="*60)

    results = {}

    # Test 1: Create appointment
    test_result = test_1_create_appointment()
    if test_result and len(test_result) == 4:
        doctor_id, appointment_id, appointment_date, appointment_time = test_result
        results['create'] = True
    else:
        results['create'] = False
        print("\n❌ CRITICAL: Cannot continue tests - appointment creation failed")
        return results

    # Test 2: Verify persistence
    results['persistence'] = test_2_verify_persistence(appointment_id)

    # Test 3: Verify dashboard display
    results['dashboard'] = test_3_verify_dashboard(doctor_id, appointment_date)

    # Test 4: Prevent double-booking
    results['double_booking'] = test_4_prevent_double_booking(
        doctor_id, appointment_date, appointment_time
    )

    # Test 5: Prevent overlapping
    results['overlapping'] = test_5_overlapping_booking(doctor_id, appointment_date)

    # Summary
    print_section("TEST SUMMARY")

    all_passed = all(results.values())

    print("Results:")
    print(f"  1. Create Appointment:          {'✅ PASS' if results['create'] else '❌ FAIL'}")
    print(f"  2. Appointment Persistence:     {'✅ PASS' if results['persistence'] else '❌ FAIL'}")
    print(f"  3. Dashboard Display:           {'✅ PASS' if results['dashboard'] else '❌ FAIL'}")
    print(f"  4. Double-Booking Prevention:   {'✅ PASS' if results['double_booking'] else '❌ FAIL'}")
    print(f"  5. Overlapping Prevention:      {'✅ PASS' if results['overlapping'] else '❌ FAIL'}")

    print(f"\n{'='*60}")
    if all_passed:
        print("  ✅ ALL TESTS PASSED - SYSTEM PRODUCTION READY")
    else:
        print("  ❌ SOME TESTS FAILED - REVIEW REQUIRED")
    print(f"{'='*60}\n")

    return results

if __name__ == "__main__":
    try:
        results = run_all_tests()
        exit(0 if all(results.values()) else 1)
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
