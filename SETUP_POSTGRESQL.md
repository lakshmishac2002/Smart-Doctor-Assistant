# PostgreSQL Setup Guide for Smart Doctor Assistant

## Install PostgreSQL

### Step 1: Download PostgreSQL

Download PostgreSQL 15 or 16 from:
**https://www.postgresql.org/download/windows/**

Click "Download the installer" and get the Windows x86-64 version.

### Step 2: Install PostgreSQL

1. Run the installer (postgresql-xx-windows-x64.exe)
2. Click "Next" through the welcome screen
3. Choose installation directory (default is fine: C:\Program Files\PostgreSQL\16)
4. Select components to install:
   - ✅ PostgreSQL Server
   - ✅ pgAdmin 4 (GUI tool)
   - ✅ Command Line Tools
   - ✅ Stack Builder (optional)
5. Choose data directory (default is fine)
6. **Set password for postgres user** - Remember this password!
   - Suggestion: Use `postgres` for simplicity (it's already in your .env file)
7. Port: 5432 (default - keep this)
8. Locale: Default locale (keep this)
9. Click "Next" and wait for installation to complete

### Step 3: Verify PostgreSQL is Running

1. Open Windows Services:
   - Press `Win + R`
   - Type `services.msc`
   - Press Enter
2. Look for "postgresql-x64-16" (or your version)
3. Status should be "Running"
4. If not, right-click and select "Start"

### Step 4: Create the Database

Open Command Prompt or PowerShell and run:

```bash
# Add PostgreSQL to PATH temporarily (adjust version number if different)
set PATH=%PATH%;C:\Program Files\PostgreSQL\16\bin

# Connect to PostgreSQL
psql -U postgres

# You'll be prompted for the password you set during installation
# Enter the password

# In the PostgreSQL prompt, create the database:
CREATE DATABASE smart_doctor_db;

# Verify it was created:
\l

# Exit PostgreSQL:
\q
```

Alternatively, use pgAdmin 4 (GUI):
1. Open pgAdmin 4 from Start Menu
2. Enter your master password
3. Expand "Servers" → "PostgreSQL 16" (or your version)
4. Right-click "Databases" → Create → Database
5. Name: `smart_doctor_db`
6. Click Save

### Step 5: Update .env File (if needed)

Check your `.env` file in the backend directory:
```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smart_doctor_db
```

If you used a different password, update the second `postgres` (the password part):
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/smart_doctor_db
```

## Run the Application

Now you can start the backend and frontend servers.

### Terminal 1 - Backend API

```bash
cd "c:\Users\laksh\Desktop\Dobbe Ai\smart-doctor-assistant-final\smart-doctor-assistant\backend"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2 - Frontend

```bash
cd "c:\Users\laksh\Desktop\Dobbe Ai\smart-doctor-assistant-final\smart-doctor-assistant\frontend"
npm run dev
```

You should see:
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
```

## Access the Application

- **Frontend**: http://localhost:3000
- **Backend API Documentation**: http://localhost:8000/docs
- **pgAdmin 4**: Available from Start Menu for database management

## Test Email Functionality

Email is already configured and working! Test it by registering a new user or booking an appointment.

## Troubleshooting

### "psql: command not found"

Add PostgreSQL to your PATH permanently:
1. Open System Properties → Environment Variables
2. Edit "Path" under System Variables
3. Add: `C:\Program Files\PostgreSQL\16\bin` (adjust version if different)
4. Click OK and restart your terminal

### "Connection refused" or "could not connect to server"

- Check if PostgreSQL service is running in Windows Services
- Verify port 5432 is not blocked by firewall
- Try restarting PostgreSQL service

### "database does not exist"

Run the CREATE DATABASE command again:
```bash
psql -U postgres -c "CREATE DATABASE smart_doctor_db;"
```

### "password authentication failed"

The password in your .env file doesn't match your PostgreSQL password.
Update DATABASE_URL in .env with the correct password.

## Next Steps

Once both servers are running successfully:

1. Open http://localhost:3000 in your browser
2. Register a new user account
3. Login
4. Test the features:
   - Book an appointment
   - Check your email for confirmation
   - View appointments in the dashboard

All features including email notifications are fully configured and ready to use!
