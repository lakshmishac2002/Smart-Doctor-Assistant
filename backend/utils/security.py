"""
Security utilities for production
"""
import re
import secrets
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
            r'(\bOR\b.*=.*|AND.*=.*)',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, str_value, re.IGNORECASE):
                return False

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal"""
        if not filename:
            return "unnamed_file"

        # Remove path separators
        filename = re.sub(r'[/\\]', '', filename)

        # Remove special characters
        filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)

        # Remove leading dots (hidden files)
        filename = filename.lstrip('.')

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:250] + ('.' + ext if ext else '')

        return filename or "unnamed_file"

    @staticmethod
    def generate_session_token() -> str:
        """Generate secure random session token"""
        return secrets.token_urlsafe(32)

    @staticmethod
    def sanitize_html(text: str) -> str:
        """Remove HTML tags and potentially dangerous content"""
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove script content
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)

        # Remove event handlers
        text = re.sub(r'on\w+\s*=\s*["\'].*?["\']', '', text, flags=re.IGNORECASE)

        # Escape remaining special characters
        text = text.replace('<', '&lt;').replace('>', '&gt;')
        text = text.replace('"', '&quot;').replace("'", '&#x27;')

        return text

    @staticmethod
    def is_valid_origin(origin: str, allowed_origins: list) -> bool:
        """Check if origin is in allowed list"""
        return origin in allowed_origins

    @staticmethod
    def mask_sensitive_data(data: str, show_chars: int = 4) -> str:
        """Mask sensitive data (email, phone, etc.)"""
        if not data or len(data) <= show_chars:
            return '*' * len(data) if data else ''

        visible = data[-show_chars:]
        masked = '*' * (len(data) - show_chars)
        return masked + visible
