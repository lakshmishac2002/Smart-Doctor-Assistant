# Docker Fix Guide - "Unexpected end of JSON input" Error

## Problem
Docker shows error: `unable to get image 'postgres:15-alpine': unexpected end of JSON input`

This is a Docker cache corruption issue. Docker Desktop is also not currently running.

## Solution

### Step 1: Start Docker Desktop

1. **Open Docker Desktop**
   - Search for "Docker Desktop" in Windows Start Menu
   - Launch the application
   - Wait 1-2 minutes for it to fully start
   - Look for the Docker whale icon in the system tray
   - When the whale stops animating, Docker is ready

### Step 2: Clean Docker Cache (Run these commands)

Open a terminal in the project directory and run:

```bash
cd "c:\Users\laksh\Desktop\Dobbe Ai\smart-doctor-assistant-final\smart-doctor-assistant"

# Stop any running containers
docker-compose down -v

# Remove all unused containers, networks, images
docker system prune -a -f

# Optional: If above doesn't work, reset Docker completely
# This removes ALL Docker data (do this only if needed)
# docker system prune -a -f --volumes
```

### Step 3: Rebuild and Start Services

```bash
# Build fresh images and start services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs if there are issues
docker-compose logs -f
```

## Alternative: Run Without Docker

If Docker issues persist, you can run the application directly without Docker:

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (download from https://www.postgresql.org/download/)

### Setup PostgreSQL Database

1. Start PostgreSQL service
2. Create database:
```sql
CREATE DATABASE smart_doctor_db;
```

### Terminal 1 - Backend API

```bash
cd backend

# Install dependencies (if not already done)
pip install -r requirements.txt

# Start backend server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Backend will run on: http://localhost:8000

### Terminal 2 - Frontend

```bash
cd frontend

# Install dependencies (if not already done)
npm install

# Start frontend dev server
npm run dev
```

Frontend will run on: http://localhost:3000

### Terminal 3 - Ollama (Optional - for AI features)

If you want to use local LLM:

```bash
# Download Ollama from: https://ollama.ai
# Then run:
ollama pull llama2
ollama serve
```

## Configuration Notes

- The `.env` file in the backend directory is already configured
- Email functionality is working correctly after the recent fix
- Database URL for local setup: `postgresql://postgres:postgres@localhost:5432/smart_doctor_db`
- Update DATABASE_URL in `.env` if using different credentials

## Verification

After starting the services, verify they're working:

1. **Backend API**: http://localhost:8000/docs (FastAPI Swagger UI)
2. **Frontend**: http://localhost:3000
3. **Database**: Connect using any PostgreSQL client on port 5432

## Troubleshooting

### Docker Desktop won't start
- Restart your computer
- Check Windows WSL 2 is installed and updated
- Try running Docker Desktop as Administrator

### Port conflicts
If ports 3000, 5432, or 8000 are already in use:
```bash
# Find what's using the port (example for port 8000)
netstat -ano | findstr :8000

# Kill the process using the PID from above
taskkill /PID <process_id> /F
```

### Database connection errors
- Ensure PostgreSQL is running
- Check DATABASE_URL in `.env` matches your setup
- Verify database exists: `psql -U postgres -c "\l"`
