# 🐳 Docker Setup & Troubleshooting Guide

## Quick Fix for Your Error

The error `unable to get image 'postgres:15-alpine': unexpected end of JSON input` is a Docker registry issue.

### Solution 1: Pull Image Manually (Recommended)

```bash
# Pull the PostgreSQL image directly
docker pull postgres:15-alpine

# Verify it's downloaded
docker images | grep postgres

# Now run docker-compose
docker-compose up -d
```

### Solution 2: Clear Docker Cache

```bash
# Clean Docker system
docker system prune -a

# Pull image
docker pull postgres:15-alpine

# Try again
docker-compose up -d
```

### Solution 3: Check Docker Hub Access

```bash
# Test Docker Hub connectivity
docker pull hello-world

# If this fails, you have a network/Docker Hub issue
# Try restarting Docker:
# Windows: Restart Docker Desktop
# Mac: Restart Docker Desktop  
# Linux: sudo systemctl restart docker
```

## 🚀 Complete Docker Setup Guide

### Step 1: Install Docker

**Windows/Mac:**
- Download Docker Desktop: https://www.docker.com/products/docker-desktop

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Step 2: Configure Environment

```bash
# In project root directory
cd smart-doctor-assistant

# Copy environment template
cp .env.docker .env

# Edit .env file
nano .env  # or use your favorite editor
```

### Step 3: Choose Your LLM Setup

#### Option A: Ollama (Recommended for Docker)

```bash
# Install Ollama on HOST machine (not in Docker)
# Windows: Download from https://ollama.ai
# Mac: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama on host
ollama serve

# Pull a model
ollama pull llama2

# In .env file, set:
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama2
```

#### Option B: Groq (Cloud - No Local Install)

```bash
# 1. Sign up at https://console.groq.com (FREE, no credit card)
# 2. Get API key from dashboard
# 3. In .env file, set:
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

### Step 4: Start Services

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Check specific service
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```

### Step 5: Verify It's Working

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# Check database
docker-compose exec postgres psql -U postgres -d smart_doctor_db -c "SELECT * FROM doctors;"
```

### Step 6: Access the Application

Open browser: **http://localhost:3000**

## 🔧 Common Docker Issues & Fixes

### Issue 1: "Port already in use"

**Error:** `Bind for 0.0.0.0:8000 failed: port is already allocated`

**Fix:**
```bash
# Find what's using the port
# Windows:
netstat -ano | findstr :8000

# Mac/Linux:
lsof -i :8000

# Kill the process or change port in docker-compose.yml
ports:
  - "8001:8000"  # Change 8000 to 8001
```

### Issue 2: "Cannot connect to Docker daemon"

**Fix:**
```bash
# Windows/Mac: Start Docker Desktop

# Linux:
sudo systemctl start docker
sudo systemctl enable docker

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
# Log out and back in
```

### Issue 3: "Database connection failed"

**Fix:**
```bash
# Check if postgres is running
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Restart postgres
docker-compose restart postgres

# Verify database exists
docker-compose exec postgres psql -U postgres -l
```

### Issue 4: "Backend can't connect to Ollama"

**Fix:**
```bash
# Make sure Ollama is running on HOST
ollama serve

# Test from host
curl http://localhost:11434/api/tags

# On Windows, use this in .env:
OLLAMA_BASE_URL=http://host.docker.internal:11434

# On Mac/Linux, might need:
OLLAMA_BASE_URL=http://172.17.0.1:11434
```

### Issue 5: "Frontend build fails"

**Fix:**
```bash
# Remove node_modules and rebuild
docker-compose down
rm -rf frontend/node_modules
docker-compose up -d --build frontend
```

## 📋 Docker Commands Cheat Sheet

### Basic Commands
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart services
docker-compose restart

# Rebuild and start
docker-compose up -d --build

# View logs (all services)
docker-compose logs -f

# View logs (specific service)
docker-compose logs -f backend

# Check status
docker-compose ps

# Execute command in container
docker-compose exec backend bash
docker-compose exec postgres psql -U postgres
```

### Cleanup Commands
```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Clean everything (careful!)
docker system prune -a --volumes
```

### Debugging Commands
```bash
# Enter backend container
docker-compose exec backend bash

# Enter postgres container
docker-compose exec postgres bash

# Check backend environment
docker-compose exec backend env

# Test backend API
docker-compose exec backend curl http://localhost:8000/health

# Check Python packages
docker-compose exec backend pip list
```

## 🎯 Minimal Docker Setup (No Email/Notifications)

If you want the simplest setup:

```bash
# .env file (minimal)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://host.docker.internal:11434
OLLAMA_MODEL=llama2

# Start Ollama on host
ollama serve
ollama pull llama2

# Start Docker services
docker-compose up -d

# Access app
# http://localhost:3000
```

## 🔄 Update After Code Changes

```bash
# Update backend code
docker-compose restart backend

# Update frontend code
docker-compose restart frontend

# Rebuild after dependency changes
docker-compose up -d --build backend
docker-compose up -d --build frontend
```

## 📊 Monitor Resource Usage

```bash
# Check container resource usage
docker stats

# Check disk usage
docker system df

# Check specific container
docker stats smart_doctor_backend
```

## 🆘 Complete Reset

If everything is broken:

```bash
# Stop everything
docker-compose down -v

# Remove all containers
docker rm -f $(docker ps -aq)

# Remove all volumes
docker volume rm $(docker volume ls -q)

# Clean system
docker system prune -a --volumes

# Pull images fresh
docker pull postgres:15-alpine

# Start from scratch
docker-compose up -d --build
```

## ✅ Verify Everything Works

### 1. Check Services
```bash
docker-compose ps
# All should show "Up" status
```

### 2. Check Backend
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy", ...}
```

### 3. Check Frontend
```bash
curl http://localhost:3000
# Should return HTML
```

### 4. Check Database
```bash
docker-compose exec postgres psql -U postgres -d smart_doctor_db -c "SELECT COUNT(*) FROM doctors;"
# Should return: 4 doctors
```

### 5. Test Chat
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_type": "patient"}'
# Should return AI response
```

## 🎓 Docker Best Practices

### Development
- Use volumes for hot reload
- Don't commit .env file
- Keep containers running
- Check logs regularly

### Production
- Use specific image tags (not :latest)
- Set resource limits
- Use health checks
- Enable restart policies
- Use secrets for sensitive data

## 🐛 Debug Checklist

When something doesn't work:

1. ✅ Is Docker running?
   ```bash
   docker --version
   docker ps
   ```

2. ✅ Are all services up?
   ```bash
   docker-compose ps
   ```

3. ✅ Check logs for errors
   ```bash
   docker-compose logs
   ```

4. ✅ Is Ollama running (if using)?
   ```bash
   curl http://localhost:11434/api/tags
   ```

5. ✅ Can services communicate?
   ```bash
   docker-compose exec backend curl http://postgres:5432
   ```

6. ✅ Are ports available?
   ```bash
   netstat -an | grep 8000
   netstat -an | grep 3000
   ```

## 📚 Additional Resources

- Docker Documentation: https://docs.docker.com
- Docker Compose: https://docs.docker.com/compose
- Troubleshooting: https://docs.docker.com/config/daemon/troubleshoot
- Docker Desktop: https://docs.docker.com/desktop

---

## 🚀 Quick Start Summary

```bash
# 1. Pull Postgres image
docker pull postgres:15-alpine

# 2. Setup environment
cp .env.docker .env
nano .env  # Configure LLM

# 3. Start Ollama (if using)
ollama serve
ollama pull llama2

# 4. Start services
docker-compose up -d

# 5. Check logs
docker-compose logs -f

# 6. Access app
# http://localhost:3000
```

**Need help?** Check the logs first:
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs postgres
```
