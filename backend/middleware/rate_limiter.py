"""
Rate limiting middleware for API protection
"""
from fastapi import Request, HTTPException
from collections import defaultdict
from datetime import datetime, timedelta
import os

class RateLimiter:
    """Simple in-memory rate limiter for production"""

    def __init__(self, requests_per_minute: int = None):
        self.requests_per_minute = requests_per_minute or int(os.getenv("RATE_LIMIT_PER_MINUTE", 60))
        self.requests = defaultdict(list)

    async def check_rate_limit(self, request: Request):
        """Check if request exceeds rate limit"""
        # Get client identifier (IP + user agent for better tracking)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")[:50]  # Limit length
        client_id = f"{client_ip}:{hash(user_agent)}"

        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Clean old requests for this client
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > minute_ago
        ]

        # Check limit
        if len(self.requests[client_id]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Too many requests. Please try again later.",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after": 60
                }
            )

        # Add current request
        self.requests[client_id].append(now)

    def get_remaining_requests(self, request: Request) -> int:
        """Get number of remaining requests for client"""
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")[:50]
        client_id = f"{client_ip}:{hash(user_agent)}"

        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Count recent requests
        recent_requests = [
            req_time for req_time in self.requests.get(client_id, [])
            if req_time > minute_ago
        ]

        return max(0, self.requests_per_minute - len(recent_requests))

    def cleanup_old_entries(self):
        """Manual cleanup of very old entries"""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > hour_ago
            ]
            if not self.requests[client_id]:
                del self.requests[client_id]

# Global instance
rate_limiter = RateLimiter()
