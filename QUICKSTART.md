# 🚀 Quick Start Guide

Get the Smart Doctor Assistant running in 5 minutes with **100% FREE APIs**!

> **💡 No Paid APIs Required!**  
> This guide uses completely free services. See [FREE_APIS_SETUP.md](FREE_APIS_SETUP.md) for detailed configuration.

## Option 1: Docker (Recommended)

```bash
# 1. Clone and navigate to project
cd smart-doctor-assistant

# 2. Set environment variables
cp backend/.env.example backend/.env
# Edit backend/.env and add your API keys

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be ready (check logs)
docker-compose logs -f

# 5. Open in browser
http://localhost:3000
```

That's it! The application should be running.

## Option 2: Manual Setup

### Step 0: FREE API Setup (Choose Your Options)

**Option A: Ollama (Local, Recommended for Free)**
```bash
# Install Ollama
brew install ollama  # macOS
# or download from https://ollama.ai

# Download model
ollama pull llama2

# Start Ollama
ollama serve

# Configure in .env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```

**Option B: Groq (Cloud, Super Fast, Free Tier)**
```bash
# 1. Sign up at https://console.groq.com (free, no credit card)
# 2. Get API key
# 3. Configure in .env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
```

**Email (Optional - Gmail SMTP)**
```bash
# 1. Enable 2FA on your Gmail account
# 2. Generate App Password at https://myaccount.google.com/apppasswords
# 3. Configure in .env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

**Notifications (Optional - Discord)**
```bash
# 1. Create Discord webhook in server settings
# 2. Configure in .env
DISCORD_WEBHOOK_URL=your_webhook_url
```

For detailed setup instructions, see [FREE_APIS_SETUP.md](FREE_APIS_SETUP.md)

### Step 1: Database

```bash
# Install PostgreSQL if not already installed
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql

# Create database
createdb smart_doctor_db

# Initialize schema
psql -d smart_doctor_db -f backend/db/schema.sql
```

### Step 2: Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and choose your FREE LLM option:
# For Ollama: LLM_PROVIDER=ollama
# For Groq: LLM_PROVIDER=groq and add GROQ_API_KEY
# Email and notifications are optional

# Run server
python main.py
```

Backend will be running at http://localhost:8000

### Step 3: Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be running at http://localhost:3000

## 🧪 Test the Installation

### 1. Check Backend Health
```bash
curl http://localhost:8000/health
```

Should return: `{"status": "healthy", ...}`

### 2. List Available MCP Tools
```bash
curl http://localhost:8000/api/mcp/tools
```

Should return a list of 6 tools.

### 3. Test Chat Interface

Open http://localhost:3000 and try:
- "Show me all available doctors"
- "Check Dr. Ahuja's availability for tomorrow"
- "I want to book an appointment"

## 🎯 Sample Workflows

### Patient Booking Flow

1. Open Patient Portal (default view)
2. Type: "I want to book an appointment with Dr. Ahuja tomorrow at 10 AM"
3. Watch the AI agent:
   - Check availability
   - Book appointment
   - Send confirmation

### Doctor Dashboard

1. Click "Doctor Dashboard" in header
2. Select a doctor from dropdown
3. Try queries like:
   - "How many patients visited yesterday?"
   - "What are the common symptoms this week?"
4. Click "Generate Report"

## ⚙️ Configuration

### Environment Variables

**Required:**
- `DATABASE_URL`: PostgreSQL connection string
- `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: LLM API key

**Optional:**
- `SENDGRID_API_KEY`: For email notifications
- `SLACK_BOT_TOKEN`: For Slack notifications
- `GOOGLE_CALENDAR_CREDENTIALS_FILE`: For calendar integration

### Database Seed Data

The schema.sql includes sample data:
- 4 doctors (various specializations)
- 4 patients
- Sample appointments

## 🐛 Troubleshooting

### Database Connection Error
```bash
# Check if PostgreSQL is running
pg_isready

# Check connection string in .env
DATABASE_URL=postgresql://user:password@host:port/database
```

### Port Already in Use
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or change port in backend/main.py
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### LLM API Errors
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Or check .env file
cat backend/.env | grep OPENAI_API_KEY
```

### Frontend Not Connecting to Backend
```bash
# Check CORS settings in backend/main.py
# Ensure frontend URL is in allow_origins list

# Or use proxy in vite.config.js (already configured)
```

## 📚 Next Steps

1. **Explore MCP Tools**: Visit http://localhost:8000/api/mcp/tools
2. **Read Architecture**: See README.md for detailed architecture
3. **Try Multi-turn Conversations**: Test context preservation
4. **Check Doctor Stats**: Generate AI reports from the dashboard
5. **Run Tests**: `pytest backend/tests/`

## 🎓 Learning Resources

- **MCP Specification**: Model Context Protocol documentation
- **Tool Calling**: OpenAI/Anthropic function calling guides
- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/

## 🆘 Getting Help

If you encounter issues:

1. Check logs:
   ```bash
   # Docker logs
   docker-compose logs backend
   docker-compose logs frontend
   
   # Manual run logs
   # Check terminal output where servers are running
   ```

2. Verify database:
   ```bash
   psql -d smart_doctor_db -c "SELECT * FROM doctors;"
   ```

3. Test MCP tools directly:
   ```bash
   curl -X POST http://localhost:8000/api/mcp/tools/list_doctors \
     -H "Content-Type: application/json" \
     -d '{}'
   ```

## 🎉 Success Indicators

You'll know everything is working when:

✅ Backend returns `200 OK` on http://localhost:8000/health  
✅ Frontend loads at http://localhost:3000  
✅ MCP tools list shows 6 tools  
✅ Patient chat responds to messages  
✅ Doctor dashboard shows statistics  
✅ Console shows "🔧 Used X tools" after agent responses  

Happy coding! 🚀
