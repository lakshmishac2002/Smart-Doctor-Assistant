# Production-Level Upgrade Guide

## Overview
This guide transforms the Smart Doctor Assistant into a production-ready application with enterprise-grade features.

## Key Production Features to Implement

### 1. Security Enhancements ✓

#### A. Environment Variables
**File: `.env.example`** (Template for users)
```env
# Backend Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/smart_doctor
SECRET_KEY=your-secret-key-here-min-32-chars
JWT_SECRET=your-jwt-secret-here-min-32-chars

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# LLM Configuration
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
GROQ_API_KEY=optional-for-faster-responses

# Frontend Configuration
VITE_API_URL=http://localhost:8000

# Security
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
RATE_LIMIT_PER_MINUTE=60
SESSION_TIMEOUT_MINUTES=30

# Production Settings
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO
```

#### B. Input Validation & Sanitization
**File: `backend/utils/validators.py`** (NEW)
```python
import re
from typing import Optional
from datetime import datetime, date
from email_validator import validate_email, EmailNotValidError

class ValidationError(Exception):
    """Custom validation error"""
    pass

class InputValidator:
    """Production-grade input validation"""

    @staticmethod
    def validate_email(email: str) -> str:
        """Validate and normalize email"""
        try:
            if not email or len(email) > 254:
                raise ValidationError("Invalid email length")

            valid = validate_email(email, check_deliverability=False)
            return valid.email
        except EmailNotValidError as e:
            raise ValidationError(f"Invalid email: {str(e)}")

    @staticmethod
    def validate_name(name: str, field_name: str = "Name") -> str:
        """Validate person name"""
        if not name or not name.strip():
            raise ValidationError(f"{field_name} is required")

        name = name.strip()

        if len(name) < 2:
            raise ValidationError(f"{field_name} must be at least 2 characters")

        if len(name) > 100:
            raise ValidationError(f"{field_name} must be less than 100 characters")

        # Allow letters, spaces, hyphens, apostrophes, dots
        if not re.match(r"^[a-zA-Z\s\-'.]+$", name):
            raise ValidationError(f"{field_name} contains invalid characters")

        return name

    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate phone number"""
        if not phone:
            raise ValidationError("Phone number is required")

        # Remove common formatting
        cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)

        # Should be 10-15 digits
        if not re.match(r'^\d{10,15}$', cleaned):
            raise ValidationError("Phone number must be 10-15 digits")

        return phone.strip()

    @staticmethod
    def validate_date(date_str: str) -> date:
        """Validate appointment date"""
        try:
            appt_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("Invalid date format. Use YYYY-MM-DD")

        if appt_date < date.today():
            raise ValidationError("Appointment date cannot be in the past")

        # Max 6 months in advance
        max_date = date.today().replace(month=date.today().month + 6)
        if appt_date > max_date:
            raise ValidationError("Cannot book more than 6 months in advance")

        return appt_date

    @staticmethod
    def validate_time(time_str: str) -> str:
        """Validate appointment time"""
        try:
            time_obj = datetime.strptime(time_str, "%H:%M").time()
        except ValueError:
            raise ValidationError("Invalid time format. Use HH:MM (24-hour)")

        # Business hours: 8 AM to 6 PM
        if time_obj.hour < 8 or time_obj.hour >= 18:
            raise ValidationError("Appointments only available 8:00 AM - 6:00 PM")

        return time_str

    @staticmethod
    def sanitize_text(text: str, max_length: int = 500) -> str:
        """Sanitize text input (symptoms, notes, etc.)"""
        if not text:
            return ""

        text = text.strip()

        if len(text) > max_length:
            raise ValidationError(f"Text exceeds maximum length of {max_length}")

        # Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

        return text

    @staticmethod
    def validate_id(id_value: any, field_name: str = "ID") -> int:
        """Validate database ID"""
        try:
            id_int = int(id_value)
            if id_int < 1:
                raise ValidationError(f"{field_name} must be positive")
            return id_int
        except (ValueError, TypeError):
            raise ValidationError(f"Invalid {field_name}")
```

#### C. Rate Limiting
**File: `backend/middleware/rate_limiter.py`** (NEW)
```python
from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    """Simple in-memory rate limiter"""

    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.cleanup_task = None

    async def check_rate_limit(self, request: Request):
        """Check if request exceeds rate limit"""
        # Get client IP
        client_ip = request.client.host

        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > minute_ago
        ]

        # Check limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )

        # Add current request
        self.requests[client_ip].append(now)

    async def cleanup_old_entries(self):
        """Periodic cleanup of old entries"""
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            now = datetime.now()
            minute_ago = now - timedelta(minutes=1)

            for ip in list(self.requests.keys()):
                self.requests[ip] = [
                    req_time for req_time in self.requests[ip]
                    if req_time > minute_ago
                ]
                if not self.requests[ip]:
                    del self.requests[ip]

# Global instance
rate_limiter = RateLimiter()
```

#### D. SQL Injection Prevention
Already handled by SQLAlchemy ORM, but add query validation:

**File: `backend/utils/security.py`** (NEW)
```python
import re
from typing import Any

class SecurityValidator:
    """Security validation utilities"""

    @staticmethod
    def is_safe_sql_value(value: Any) -> bool:
        """Check if value is safe for SQL (basic check)"""
        if value is None:
            return True

        str_value = str(value)

        # Check for SQL injection patterns
        dangerous_patterns = [
            r'(\s|^)(DROP|DELETE|TRUNCATE|ALTER|EXEC|EXECUTE)(\s|$)',
            r'(--|;|\/\*|\*\/|xp_|sp_)',
            r'(UNION.*SELECT|SELECT.*FROM.*WHERE)',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, str_value, re.IGNORECASE):
                return False

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        # Remove path separators
        filename = re.sub(r'[/\\]', '', filename)

        # Remove special characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')

        return filename
```

### 2. Error Handling & Logging

#### A. Structured Logging
**File: `backend/utils/logger.py`** (NEW)
```python
import logging
import sys
from datetime import datetime
from pathlib import Path

class ProductionLogger:
    """Production-grade logging"""

    def __init__(self, name: str = "smart_doctor"):
        self.logger = logging.getLogger(name)
        self.setup_handlers()

    def setup_handlers(self):
        """Setup logging handlers"""
        self.logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_format)

        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] - %(message)s'
        )
        file_handler.setFormatter(file_format)

        # Error file handler
        error_handler = logging.FileHandler(
            log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_format)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)

    def error(self, message: str, exc_info=None, **kwargs):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)

# Global logger
logger = ProductionLogger()
```

#### B. Error Response Handler
**File: `backend/middleware/error_handler.py`** (NEW)
```python
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from backend.utils.logger import logger

async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""

    # Log the error
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=exc,
        path=request.url.path,
        method=request.method
    )

    # Return generic error response
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "An unexpected error occurred. Please try again later.",
            "code": "INTERNAL_ERROR"
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors"""
    logger.warning(
        f"Validation error: {exc.errors()}",
        path=request.url.path,
        method=request.method
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "Invalid input data",
            "details": exc.errors(),
            "code": "VALIDATION_ERROR"
        }
    )

async def database_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle database errors"""
    logger.error(
        f"Database error: {str(exc)}",
        exc_info=exc,
        path=request.url.path
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "Database operation failed. Please try again.",
            "code": "DATABASE_ERROR"
        }
    )
```

### 3. Authentication & Authorization

#### A. JWT Authentication
**File: `backend/auth/jwt_handler.py`** (NEW)
```python
from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
import os

SECRET_KEY = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthHandler:
    """JWT authentication handler"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

auth_handler = AuthHandler()
```

### 4. Frontend Production Features

#### A. Error Boundary Component
**File: `frontend/src/components/ErrorBoundary.jsx`** (NEW)
```javascript
import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // Send to error tracking service (e.g., Sentry)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-page">
          <h1>Something went wrong</h1>
          <p>We're sorry for the inconvenience. Please refresh the page or try again later.</p>
          <button onClick={() => window.location.reload()}>
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

#### B. API Service with Retry Logic
**File: `frontend/src/services/api.js`** (ENHANCED)
```javascript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with defaults
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor (add auth token)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor (handle errors)
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      localStorage.removeItem('token');
      window.location.href = '/login';
      return Promise.reject(error);
    }

    // Handle 429 (rate limit)
    if (error.response?.status === 429) {
      return Promise.reject({
        message: 'Too many requests. Please wait a moment.',
        code: 'RATE_LIMIT',
      });
    }

    // Handle network errors
    if (!error.response) {
      return Promise.reject({
        message: 'Network error. Please check your connection.',
        code: 'NETWORK_ERROR',
      });
    }

    return Promise.reject(error);
  }
);

// Retry logic wrapper
const retryRequest = async (fn, maxRetries = 3, delay = 1000) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise((resolve) => setTimeout(resolve, delay * (i + 1)));
    }
  }
};

export { api, retryRequest };
export default api;
```

### 5. Production Build Configuration

#### A. Vite Production Config
**File: `frontend/vite.config.js`** (ENHANCED)
```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { compression } from 'vite-plugin-compression2';

export default defineConfig({
  plugins: [
    react(),
    compression({ algorithm: 'gzip' }),
    compression({ algorithm: 'brotliCompress' }),
  ],
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console logs in production
        drop_debugger: true,
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['axios'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
  server: {
    port: 3001,
    strictPort: true,
  },
});
```

### 6. Database & Performance

#### A. Connection Pooling
**File: `backend/db/database.py`** (ENHANCED)
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/smart_doctor"
)

# Production engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,  # Number of permanent connections
    max_overflow=20,  # Max temporary connections
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False,  # Set to True for query logging in dev
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Dependency for database sessions"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 7. Monitoring & Health Checks

#### A. Health Check Endpoint
**File: `backend/routes/health.py`** (NEW)
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.database import get_db
import psutil
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
        },
    }
```

## Implementation Priority

### Phase 1: Security (Critical) ⚠️
1. Create `.env.example` and `.env` files
2. Implement input validation (`validators.py`)
3. Add rate limiting (`rate_limiter.py`)
4. Setup security utilities (`security.py`)

### Phase 2: Error Handling (High Priority)
1. Setup structured logging (`logger.py`)
2. Add global error handlers (`error_handler.py`)
3. Create error boundary component (React)

### Phase 3: Authentication (High Priority)
1. Implement JWT authentication (`jwt_handler.py`)
2. Add login/logout endpoints
3. Protect routes with auth middleware

### Phase 4: Production Build (Medium Priority)
1. Configure production builds (Vite, backend)
2. Setup environment configurations
3. Add health check endpoints

### Phase 5: Monitoring (Medium Priority)
1. Setup logging infrastructure
2. Add performance monitoring
3. Create admin dashboard

## Quick Start Production Setup

1. **Create `.env` file:**
```bash
cp .env.example .env
# Edit .env with your actual values
```

2. **Install additional dependencies:**
```bash
# Backend
pip install email-validator passlib[bcrypt] python-jose[cryptography] psutil

# Frontend
npm install axios
```

3. **Run with production settings:**
```bash
# Backend
export ENVIRONMENT=production
python backend/main.py

# Frontend
npm run build
npm run preview
```

## Security Checklist

- [ ] All secrets in environment variables
- [ ] Input validation on all endpoints
- [ ] Rate limiting enabled
- [ ] SQL injection prevention (use ORM)
- [ ] XSS prevention (sanitize inputs)
- [ ] CORS properly configured
- [ ] HTTPS enabled (production)
- [ ] JWT authentication implemented
- [ ] Password hashing (bcrypt)
- [ ] Error messages don't leak info
- [ ] Logging doesn't log secrets
- [ ] Database connection pooling
- [ ] File upload validation (if applicable)

## Performance Checklist

- [ ] Database indexes on foreign keys
- [ ] Connection pooling configured
- [ ] Frontend code splitting
- [ ] Assets minified and compressed
- [ ] API response caching (where applicable)
- [ ] Database query optimization
- [ ] CDN for static assets (production)
- [ ] Load balancing (production scale)

## Monitoring Checklist

- [ ] Health check endpoint
- [ ] Structured logging
- [ ] Error tracking (Sentry, etc.)
- [ ] Performance metrics
- [ ] Uptime monitoring
- [ ] Database metrics
- [ ] API endpoint metrics

This production upgrade transforms the application into an enterprise-ready system with security, reliability, and scalability! 🚀
