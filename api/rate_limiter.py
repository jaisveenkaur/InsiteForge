"""
Rate limiter middleware for FastAPI.
Implements simple in-memory request throttling to prevent abuse.
"""

from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from fastapi import HTTPException


class RateLimiter:
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.requests = defaultdict(list)
        self.lock = asyncio.Lock()

    async def check_rate_limit(self, client_id: str):
        """Check if client has exceeded rate limit."""
        async with self.lock:
            now = datetime.utcnow()
            one_minute_ago = now - timedelta(minutes=1)

            # Clean old requests
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > one_minute_ago
            ]

            # Check limit
            if len(self.requests[client_id]) >= self.requests_per_minute:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {self.requests_per_minute} requests per minute"
                )

            # Record request
            self.requests[client_id].append(now)


rate_limiter = RateLimiter(requests_per_minute=30)
