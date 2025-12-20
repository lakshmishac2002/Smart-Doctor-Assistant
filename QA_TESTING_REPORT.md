# QA Testing Report & Fixes

## Issues Identified

### Issue 1: Chat/AI Assistant Not Responding ❌

**Symptoms:**
- User clicks "Send" in chat but nothing happens
- No error message displayed
- Chat appears frozen

**Root Causes:**
1. Frontend API URL may be incorrect
2. CORS issues preventing requests
3. Backend not running or Ollama not started
4. Network timeout before response received

**Diagnosis Steps:**

1. **Check Backend is Running:**
```bash
# Terminal 1 - Start backend
cd backend
python main.py

# Should see:
# [SUCCESS] Database initialized
# [INFO] Smart Doctor Assistant API is running
```

2. **Check Frontend API URL:**
```bash
# Check .env file in frontend/
cat frontend/.env

# Should contain:
VITE_API_URL=http://localhost:8000/api
```

3. **Test API Directly:**
```bash
curl http://localhost:8000/health
# Should return JSON with status: "healthy"
```

4. **Check Browser Console:**
- Open DevTools (F12)
- Go to Console tab
- Look for CORS errors or network errors
- Check Network tab for failed requests

**Solutions:**

**Solution A: Fix API URL**

Create/update `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

Note: Remove `/api` suffix - it's added by the code

**Solution B: Ensure Backend is Running**
```bash
cd backend
python main.py
```

**Solution C: Start Ollama**
```bash
# In a separate terminal
ollama serve

# Or warm up the model
ollama run llama2
```

**Solution D: Check Browser Console**

If you see CORS errors, verify `backend/main.py` has:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Issue 2: Appointments Not Persisting ❌

**Symptoms:**
- Appointment booking shows success message
- But appointments don't appear in database
- or they disappear after page refresh

**Root Causes:**
1. Database not initialized
2. Missing `db.commit()` call
3. Database connection issues
4. Transaction rollback on error

**Diagnosis Steps:**

1. **Check Database is Initialized:**
```bash
cd backend
python -c "from db.database import init_db; init_db()"
```

2. **Run Test Script:**
```bash
cd backend
python test_appointment_booking.py
```

This will test:
- Health check ✓
- List doctors ✓
- Book appointment ✓
- Verify persistence ✓
- Chat endpoint ✓

3. **Check Database Directly:**
```bash
# If using PostgreSQL
psql -U postgres -d smart_doctor

# Query appointments
SELECT * FROM appointments;
SELECT * FROM patients;
SELECT * FROM doctors;
```

**Solutions:**

**Solution A: Initialize Database**
```bash
cd backend
python -c "from db.database import init_db; init_db()"
python seed_data.py
```

**Solution B: Verify MCP Server is Committing**

Check `backend/mcp/server.py` line 395:
```python
db.add(appointment)
db.commit()  # ← This MUST be present
db.refresh(appointment)
```

**Solution C: Check for Exceptions**

Look at backend console for errors like:
- `IntegrityError` - constraint violation
- `OperationalError` - database connection failed
- `ValidationError` - invalid data

---

## Testing Checklist

### Pre-Testing Setup ☑️

- [ ] PostgreSQL running
- [ ] Database initialized (`init_db()`)
- [ ] Sample doctors seeded (`seed_data.py`)
- [ ] Backend server running (`python main.py`)
- [ ] Frontend server running (`npm run dev`)
- [ ] Ollama running (optional, for AI chat)

### Test 1: Direct Appointment Booking

**Steps:**
1. Open http://localhost:3001
2. Login as Patient
3. Click on any doctor
4. Click "Book Appointment" button
5. Fill form:
   - Name: Test Patient
   - Email: test@example.com
   - Date: Tomorrow
   - Time: 10:00
   - Symptoms: Test booking
6. Click "Confirm Booking"

**Expected Result:**
- ✅ Success banner appears
- ✅ Email confirmation message shows
- ✅ Modal closes

**Verify Persistence:**
1. Refresh the page (F5)
2. Check backend logs for appointment creation
3. Or run: `python test_appointment_booking.py`

**Status:** __________

---

### Test 2: Chat/AI Assistant

**Steps:**
1. Open http://localhost:3001
2. Login as Patient
3. Type in chat: "Show me available cardiologists"
4. Press Enter or click Send
5. Wait for response (3-60 seconds)

**Expected Result:**
- ✅ Message appears in chat
- ✅ Typing indicator shows
- ✅ AI responds with doctor list
- ✅ Response mentions Dr. Rajesh Ahuja

**If Fails:**
- Check Ollama is running: `ollama list`
- Check backend console for errors
- Check browser console (F12) for network errors

**Status:** __________

---

### Test 3: Chat Persistence

**Steps:**
1. Send a message in chat
2. Refresh page (F5)
3. Check if messages are still visible

**Expected Result:**
- ✅ Messages persist after refresh
- ✅ Can continue conversation
- ✅ "Clear Chat" button visible
- ✅ Clicking "Clear Chat" removes all messages

**Status:** __________

---

### Test 4: Appointment Persistence

**Steps:**
1. Book an appointment (see Test 1)
2. Note the appointment details
3. Stop backend server (Ctrl+C)
4. Restart backend server
5. Run: `curl http://localhost:8000/api/appointments`

**Expected Result:**
```json
{
  "appointments": [
    {
      "patient_name": "Test Patient",
      "doctor_name": "Dr. ...",
      "appointment_date": "2025-...",
      "status": "scheduled"
    }
  ],
  "count": 1
}
```

**Status:** __________

---

## Common Issues & Solutions

### Issue: "Cannot connect to database"

**Solution:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Or on Windows
# Check services for PostgreSQL

# Update DATABASE_URL in .env
DATABASE_URL=postgresql://postgres:password@localhost:5432/smart_doctor
```

---

### Issue: "Ollama connection timeout"

**Solution:**
```bash
# Option 1: Start Ollama
ollama serve

# Option 2: Switch to Groq (faster)
# Edit .env:
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-key

# Option 3: Use direct booking (bypasses AI)
# Click "Book Appointment" button instead of chat
```

---

### Issue: "CORS policy blocking request"

**Solution:**

Check `backend/main.py` has correct origins:
```python
allow_origins=[
    "http://localhost:3000",
    "http://localhost:3001",  # ← Add this if missing
    "http://localhost:5173"
]
```

Restart backend after changes.

---

### Issue: "Frontend can't reach API"

**Solution:**

1. **Check frontend .env:**
```bash
cat frontend/.env

# Should be:
VITE_API_URL=http://localhost:8000
```

2. **Restart frontend:**
```bash
cd frontend
npm run dev
```

3. **Hard refresh browser:**
```
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

---

## Automated Testing Script

Run comprehensive tests:

```bash
cd backend
python test_appointment_booking.py
```

This will:
1. Check backend health
2. List doctors
3. Book an appointment
4. Verify it was saved
5. Test chat endpoint
6. Print detailed results

**Expected Output:**
```
============================================================
SMART DOCTOR ASSISTANT - QA TEST SUITE
============================================================
✓ Health check: 200
✓ List doctors: 200
  Found 8 doctors
→ Booking appointment...
✓ Book appointment: 200
✅ Appointment booking WORKS!
✓ Get appointments: 200
  Total appointments: 1
✅ Appointments are being PERSISTED!
✓ Chat response: 200
✅ Chat endpoint WORKS!
============================================================
TEST SUITE COMPLETE
============================================================
```

---

## Production Checklist

Before deploying:

- [ ] Database migrations run
- [ ] Environment variables set
- [ ] Sample data seeded
- [ ] All tests passing
- [ ] CORS configured for production domain
- [ ] Ollama or Groq API configured
- [ ] Email SMTP configured
- [ ] Database backups enabled
- [ ] Monitoring setup
- [ ] Error logging configured

---

## Debug Mode

Enable debug logging:

**Backend:**
```python
# In main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```javascript
// In browser console
localStorage.setItem('debug', '*')
```

---

## Support

If issues persist:

1. **Check Logs:**
   - Backend: Terminal output
   - Frontend: Browser console (F12)
   - Database: PostgreSQL logs

2. **Test Endpoints:**
   ```bash
   # Health
   curl http://localhost:8000/health

   # Doctors
   curl http://localhost:8000/api/doctors

   # Appointments
   curl http://localhost:8000/api/appointments
   ```

3. **Run Test Script:**
   ```bash
   python backend/test_appointment_booking.py
   ```

4. **Check Documentation:**
   - [LATEST_FIXES.md](LATEST_FIXES.md) - Recent fixes
   - [PRODUCTION_READY.md](PRODUCTION_READY.md) - Production features
   - [CRITICAL_FIXES.md](CRITICAL_FIXES.md) - Bug fixes

---

## Test Results Summary

| Test | Status | Notes |
|------|--------|-------|
| Backend Health | ☐ Pass ☐ Fail | |
| Frontend Loading | ☐ Pass ☐ Fail | |
| Direct Booking | ☐ Pass ☐ Fail | |
| Appointment Persistence | ☐ Pass ☐ Fail | |
| Chat/AI Assistant | ☐ Pass ☐ Fail | |
| Chat Persistence | ☐ Pass ☐ Fail | |
| Email Notifications | ☐ Pass ☐ Fail | |
| Doctor Search/Filter | ☐ Pass ☐ Fail | |

**Overall Status:** __________

**Tested By:** __________

**Date:** __________

---

**END OF QA TESTING REPORT**
