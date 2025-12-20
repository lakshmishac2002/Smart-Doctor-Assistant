# Production Deployment Guide

## 🚀 Complete Production Deployment Checklist

### Prerequisites
- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Ollama installed (or Groq API key)
- Domain name (for production)
- SSL certificate (Let's Encrypt recommended)

---

## Phase 1: Environment Setup (30 minutes)

### 1.1 Clone and Setup
```bash
cd /var/www/
git clone <your-repo> smart-doctor-assistant
cd smart-doctor-assistant
```

### 1.2 Create Environment File
```bash
cp .env.example .env
nano .env
```

**Critical Environment Variables:**
```env
# Production Database
DATABASE_URL=postgresql://dbuser:securepassword@localhost:5432/smart_doctor_prod

# Secure Secrets (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
SECRET_KEY=<generate-32-char-secret>
JWT_SECRET=<generate-32-char-secret>

# Email (Gmail)
SMTP_USER=your-production-email@gmail.com
SMTP_PASSWORD=<gmail-app-password>

# LLM (Groq recommended for production)
LLM_PROVIDER=groq
GROQ_API_KEY=<your-groq-key>

# Production Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# CORS (your actual domain)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30

# Frontend
VITE_API_URL=https://api.yourdomain.com
```

### 1.3 Generate Secrets
```bash
# Generate SECRET_KEY
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate JWT_SECRET
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
```

---

## Phase 2: Database Setup (15 minutes)

### 2.1 Create Production Database
```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE smart_doctor_prod;
CREATE USER dbuser WITH ENCRYPTED PASSWORD 'securepassword';
GRANT ALL PRIVILEGES ON DATABASE smart_doctor_prod TO dbuser;
\q
```

### 2.2 Run Migrations
```bash
cd backend
python -c "from db.database import init_db; init_db()"
```

### 2.3 Seed Initial Data
```bash
python seed_data.py
```

---

## Phase 3: Backend Deployment (20 minutes)

### 3.1 Install Dependencies
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install production dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install production-only packages
pip install gunicorn uvicorn[standard] python-dotenv psycopg2-binary
```

### 3.2 Create systemd Service
```bash
sudo nano /etc/systemd/system/smart-doctor-api.service
```

```ini
[Unit]
Description=Smart Doctor Assistant API
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/smart-doctor-assistant/backend
Environment="PATH=/var/www/smart-doctor-assistant/backend/venv/bin"
ExecStart=/var/www/smart-doctor-assistant/backend/venv/bin/gunicorn main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/smart-doctor/access.log \
    --error-logfile /var/log/smart-doctor/error.log \
    --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3.3 Create Log Directory
```bash
sudo mkdir -p /var/log/smart-doctor
sudo chown www-data:www-data /var/log/smart-doctor
```

### 3.4 Start Backend Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable smart-doctor-api
sudo systemctl start smart-doctor-api
sudo systemctl status smart-doctor-api
```

---

## Phase 4: Frontend Deployment (20 minutes)

### 4.1 Build Frontend
```bash
cd frontend

# Install dependencies
npm install

# Create production build
npm run build
```

### 4.2 Setup Nginx
```bash
sudo apt update
sudo apt install nginx
```

### 4.3 Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/smart-doctor
```

```nginx
# API Server
upstream api_backend {
    server 127.0.0.1:8000;
}

# Main Application
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Frontend Static Files
    root /var/www/smart-doctor-assistant/frontend/dist;
    index index.html;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    # Frontend
    location / {
        try_files $uri $uri/ /index.html;
        add_header Cache-Control "no-cache, must-revalidate";
    }

    # Static Assets (with caching)
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # API Proxy
    location /api/ {
        proxy_pass http://api_backend/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health Check
    location /health {
        proxy_pass http://api_backend/health;
        access_log off;
    }

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
```

### 4.4 Enable Nginx Configuration
```bash
sudo ln -s /etc/nginx/sites-available/smart-doctor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Phase 5: SSL Certificate (10 minutes)

### 5.1 Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

### 5.2 Obtain SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### 5.3 Auto-Renewal
```bash
# Test renewal
sudo certbot renew --dry-run

# Certbot automatically sets up cron job for renewal
```

---

## Phase 6: Firewall & Security (10 minutes)

### 6.1 Configure UFW Firewall
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

### 6.2 Secure PostgreSQL
```bash
sudo nano /etc/postgresql/13/main/pg_hba.conf
```

Change:
```
# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 6.3 File Permissions
```bash
sudo chown -R www-data:www-data /var/www/smart-doctor-assistant
sudo chmod -R 755 /var/www/smart-doctor-assistant
sudo chmod 600 /var/www/smart-doctor-assistant/.env
```

---

## Phase 7: Monitoring & Logging (15 minutes)

### 7.1 Log Rotation
```bash
sudo nano /etc/logrotate.d/smart-doctor
```

```
/var/log/smart-doctor/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload smart-doctor-api > /dev/null 2>&1 || true
    endscript
}
```

### 7.2 Setup Health Check Monitoring
```bash
# Create health check script
sudo nano /usr/local/bin/health-check.sh
```

```bash
#!/bin/bash
HEALTH_URL="https://yourdomain.com/health"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ $RESPONSE -ne 200 ]; then
    echo "Health check failed with status: $RESPONSE"
    # Send alert (email, SMS, Slack, etc.)
    systemctl restart smart-doctor-api
fi
```

```bash
sudo chmod +x /usr/local/bin/health-check.sh

# Add to crontab
sudo crontab -e

# Add this line (check every 5 minutes)
*/5 * * * * /usr/local/bin/health-check.sh
```

---

## Phase 8: Backup Strategy (10 minutes)

### 8.1 Database Backup Script
```bash
sudo nano /usr/local/bin/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/smart-doctor"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="smart_doctor_prod"

mkdir -p $BACKUP_DIR

# Create backup
pg_dump -U dbuser $DB_NAME | gzip > $BACKUP_DIR/db_backup_$DATE.sql.gz

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

```bash
sudo chmod +x /usr/local/bin/backup-db.sh

# Add to crontab (daily at 2 AM)
sudo crontab -e
0 2 * * * /usr/local/bin/backup-db.sh
```

---

## Phase 9: Performance Optimization

### 9.1 Optimize PostgreSQL
```bash
sudo nano /etc/postgresql/13/main/postgresql.conf
```

```ini
# Connection Settings
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 128MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
work_mem = 2621kB
min_wal_size = 1GB
max_wal_size = 4GB
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 9.2 Enable Database Indexes
```sql
-- Connect to database
psql -U dbuser -d smart_doctor_prod

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date);
CREATE INDEX IF NOT EXISTS idx_doctors_specialization ON doctors(specialization);
```

---

## Phase 10: Testing & Verification

### 10.1 Verify Services
```bash
# Check backend
sudo systemctl status smart-doctor-api

# Check nginx
sudo systemctl status nginx

# Check database
sudo systemctl status postgresql

# View logs
sudo journalctl -u smart-doctor-api -n 50
tail -f /var/log/smart-doctor/error.log
```

### 10.2 Test API Endpoints
```bash
# Health check
curl https://yourdomain.com/health

# Test API
curl https://yourdomain.com/api/doctors
```

### 10.3 Load Testing (Optional)
```bash
# Install Apache Bench
sudo apt install apache2-utils

# Test 1000 requests, 10 concurrent
ab -n 1000 -c 10 https://yourdomain.com/health
```

---

## Post-Deployment Checklist

- [ ] All services running
- [ ] SSL certificate valid
- [ ] Database backups configured
- [ ] Firewall configured
- [ ] Log rotation setup
- [ ] Health monitoring active
- [ ] Email notifications working
- [ ] API endpoints responding
- [ ] Frontend loading correctly
- [ ] Rate limiting functional
- [ ] Error logging working
- [ ] Domain DNS configured
- [ ] SSL auto-renewal configured

---

## Monitoring Recommendations

### Essential Tools:
1. **Uptime Monitoring**: UptimeRobot (free), Pingdom
2. **Error Tracking**: Sentry (free tier)
3. **Log Management**: Papertrail, Loggly
4. **Performance**: New Relic, DataDog

### Metrics to Monitor:
- API response times
- Database query times
- Error rates
- Request rates
- CPU/Memory usage
- Disk space
- SSL expiry
- Database connections

---

## Troubleshooting

### Backend Not Starting
```bash
# Check logs
sudo journalctl -u smart-doctor-api -n 100
sudo cat /var/log/smart-doctor/error.log

# Check permissions
ls -la /var/www/smart-doctor-assistant

# Test manually
cd /var/www/smart-doctor-assistant/backend
source venv/bin/activate
python main.py
```

### Database Connection Issues
```bash
# Test connection
psql -U dbuser -d smart_doctor_prod

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

### Nginx Configuration Errors
```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Reload configuration
sudo systemctl reload nginx
```

---

## Maintenance Commands

```bash
# Restart backend
sudo systemctl restart smart-doctor-api

# Reload Nginx (zero downtime)
sudo systemctl reload nginx

# View realtime logs
sudo journalctl -u smart-doctor-api -f

# Clean up old logs
sudo find /var/log/smart-doctor -name "*.log" -mtime +30 -delete

# Database vacuum (optimize)
sudo -u postgres psql -d smart_doctor_prod -c "VACUUM ANALYZE;"
```

---

## Scaling Considerations

When traffic grows:

1. **Horizontal Scaling**: Use load balancer (Nginx, HAProxy)
2. **Database**: Move to managed service (AWS RDS, DigitalOcean)
3. **Caching**: Add Redis for session management
4. **CDN**: CloudFlare for static assets
5. **Container**: Dockerize for easier scaling
6. **Queue**: Add Celery for async tasks

---

## Security Best Practices

- ✅ Use strong passwords (32+ characters)
- ✅ Enable firewall (UFW)
- ✅ Keep system updated (`sudo apt update && sudo apt upgrade`)
- ✅ Use SSL/TLS (Let's Encrypt)
- ✅ Limit SSH access (key-based auth only)
- ✅ Regular backups (automated daily)
- ✅ Monitor logs for suspicious activity
- ✅ Rate limiting enabled
- ✅ Input validation on all endpoints
- ✅ SQL injection prevention (use ORM)
- ✅ XSS prevention (sanitize inputs)

---

## Production is LIVE! 🎉

Your Smart Doctor Assistant is now production-ready and deployed!

**Access your application:**
- Frontend: https://yourdomain.com
- API: https://yourdomain.com/api
- Health: https://yourdomain.com/health

**Next Steps:**
1. Monitor logs for first 24 hours
2. Test all features thoroughly
3. Setup automated backups verification
4. Configure alerting for errors
5. Plan capacity scaling strategy

For support, refer to:
- [PRODUCTION_UPGRADE.md](PRODUCTION_UPGRADE.md) - Production features
- [CRITICAL_FIXES.md](CRITICAL_FIXES.md) - Recent fixes
- [FINAL_STATUS.md](FINAL_STATUS.md) - Application status
