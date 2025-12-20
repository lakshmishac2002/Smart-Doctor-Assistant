# 🆓 FREE APIs Setup Guide

This guide shows you how to set up **100% FREE** alternatives - no credit card required!

## 🧠 LLM Options (Choose One)

### Option 1: Ollama (Recommended - 100% Free, Local)

**Best for**: Privacy, no internet required, unlimited usage

1. **Install Ollama**:

   ```bash
   # macOS
   brew install ollama

   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh

   # Windows
   # Download from https://ollama.ai/download
   ```

2. **Download a model**:

   ```bash
   ollama pull llama2        # 3.8GB
   # or
   ollama pull mistral       # 4.1GB
   # or
   ollama pull phi           # 1.6GB (smallest, faster)
   ```

3. **Start Ollama**:

   ```bash
   ollama serve
   ```

4. **Configure in .env**:
   ```bash
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama2
   ```

### Option 2: Groq (Free Cloud API - Super Fast)

**Best for**: Speed, cloud-based, generous free tier

1. **Sign up** at https://console.groq.com (free, no credit card)

2. **Get API key**:

   - Go to API Keys section
   - Click "Create API Key"
   - Copy the key

3. **Configure in .env**:
   ```bash
   LLM_PROVIDER=groq
   GROQ_API_KEY=your_groq_api_key_here
   ```

**Free Tier**:

- 14,400 requests per day
- 30 requests per minute
- No expiration

### Option 3: Together AI (Free Tier)

**Best for**: Multiple models, good free tier

1. **Sign up** at https://api.together.xyz

2. **Get API key**:

   - Go to Settings → API Keys
   - Create new key

3. **Configure in .env**:
   ```bash
   LLM_PROVIDER=together
   TOGETHER_API_KEY=your_together_api_key_here
   ```

**Free Tier**:

- $25 free credits
- Never expires

### Option 4: Hugging Face (Free)

**Best for**: Open source models

1. **Sign up** at https://huggingface.co

2. **Get token**:

   - Go to Settings → Access Tokens
   - Create new token (read access)

3. **Configure in .env**:
   ```bash
   LLM_PROVIDER=huggingface
   HUGGINGFACE_API_KEY=your_hf_token_here
   ```

## 📧 Email Setup (Free Gmail SMTP)

**100% Free** - Use your existing Gmail account

### Step 1: Enable 2-Factor Authentication

1. Go to https://myaccount.google.com/security
2. Enable "2-Step Verification"

### Step 2: Generate App Password

1. Go to https://myaccount.google.com/apppasswords
2. Select app: "Mail"
3. Select device: "Other (Custom name)"
4. Enter name: "Smart Doctor Assistant"
5. Click "Generate"
6. Copy the 16-character password

### Step 3: Configure in .env

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx  # The app password you generated
SENDER_EMAIL=your_email@gmail.com
```

### Testing Gmail SMTP

```bash
# Test email sending
python -c "
from tools.free_email import get_email_client
client = get_email_client()
result = client.send_email(
    'your_email@gmail.com',
    'Test Email',
    'If you receive this, email is working!'
)
print(result)
"
```

## 🔔 Notifications Setup (Choose One)

### Option 1: Discord Webhooks (Recommended)

**100% Free, Easy Setup**

1. **Create Discord Server** (if you don't have one):

   - Open Discord
   - Click "+" to add server
   - Create "My Server"

2. **Create Webhook**:

   - Right-click on a text channel
   - Edit Channel → Integrations → Webhooks
   - Click "New Webhook"
   - Name it "Doctor Reports"
   - Copy Webhook URL

3. **Configure in .env**:

   ```bash
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
   ```

4. **Test**:
   ```bash
   python -c "
   from tools.free_notifications import get_notification_client
   client = get_notification_client()
   result = client.send_notification(
    'Test Notification',
    'If you see this in Discord, it works!',
    'success'
   )
   print(result)
   "
   ```

### Option 2: Telegram Bot

**100% Free, Mobile Notifications**

1. **Create Bot**:

   - Open Telegram
   - Message @BotFather
   - Send `/newbot`
   - Follow instructions
   - Copy bot token

2. **Get Chat ID**:

   - Message @userinfobot
   - It will reply with your chat ID
   - Or message your bot, then visit:
     `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`

3. **Configure in .env**:
   ```bash
   TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=123456789
   ```

## 📅 Google Calendar (Free - Optional)

**Free for personal use**

1. **Enable Google Calendar API**:

   - Go to https://console.cloud.google.com
   - Create new project (free)
   - Enable "Google Calendar API"

2. **Create Credentials**:

   - Go to Credentials
   - Create OAuth 2.0 Client ID
   - Application type: Desktop app
   - Download JSON

3. **Setup**:

   ```bash
   # Rename downloaded file
   mv ~/Downloads/client_secret_*.json backend/credentials.json

   # Configure in .env
   GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json
   GOOGLE_CALENDAR_TOKEN_FILE=token.json
   ```

4. **First run will open browser for authentication**

## 🎯 Quick Configuration Examples

### Minimal Setup (Ollama + Console Notifications)

```bash
# .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smart_doctor_db

# LLM - Ollama (local, free)
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Email - Not required for testing
# Notifications will log to console
```

### Cloud Setup (Groq + Discord)

```bash
# .env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smart_doctor_db

# LLM - Groq (cloud, free, fast)
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_key_here

# Notifications - Discord
DISCORD_WEBHOOK_URL=your_discord_webhook_url

# Email - Gmail (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SENDER_EMAIL=your_email@gmail.com
```

## 🧪 Testing Your Setup

### Test 1: Check LLM Connection

```bash
# For Ollama
curl http://localhost:11434/api/tags

# For Groq
curl https://api.groq.com/openai/v1/models \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Test 2: Test Full System

```bash
# Start backend
cd backend
python main.py

# In another terminal, test chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, can you help me?",
    "user_type": "patient"
  }'
```

### Test 3: Test MCP Tools

```bash
# List available tools
curl http://localhost:8000/api/mcp/tools

# Test doctor availability
curl -X POST http://localhost:8000/api/mcp/tools/list_doctors \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 🆘 Troubleshooting

### Ollama Not Working?

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve

# Check if model is downloaded
ollama list

# Pull model if needed
ollama pull llama2
```

### Gmail SMTP Errors?

- ✅ 2FA enabled?
- ✅ App password generated (not regular password)?
- ✅ Username is your full email address?
- ✅ No spaces in app password in .env?

### Discord Not Receiving?

- ✅ Webhook URL correct?
- ✅ No extra spaces in URL?
- ✅ Webhook not deleted from Discord?

### Database Connection Error?

```bash
# Check PostgreSQL is running
pg_isready

# Check connection string in .env
# Format: postgresql://user:password@host:port/database
```

## 💰 Cost Comparison

| Service        | Free Tier          | Our Usage | Cost         |
| -------------- | ------------------ | --------- | ------------ |
| **Ollama**     | Unlimited          | ∞         | $0           |
| **Groq**       | 14,400 req/day     | ~100/day  | $0           |
| **Gmail SMTP** | 500 emails/day     | ~10/day   | $0           |
| **Discord**    | Unlimited webhooks | ∞         | $0           |
| **Telegram**   | Unlimited messages | ∞         | $0           |
| **PostgreSQL** | Local/Free tiers   | 1 DB      | $0           |
| **Total**      | -                  | -         | **$0/month** |

Compare to:

- OpenAI GPT-4: $0.03/1K tokens = ~$10-50/month
- SendGrid: $15/month
- Slack: $8/user/month

## 🎉 You're All Set!

With this setup, you have:

- ✅ Free AI (Ollama/Groq/Together/HF)
- ✅ Free Email (Gmail SMTP)
- ✅ Free Notifications (Discord/Telegram)
- ✅ Free Database (Local PostgreSQL)
- ✅ $0/month cost!

Now run the project:

```bash
# Backend
cd backend
python main.py

# Frontend (new terminal)
cd frontend
npm run dev
```

Visit http://localhost:3000 and start chatting! 🚀
