from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis.asyncio as redis
import time
from app.core.config import settings


class RedisRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests: int = 60, window_seconds: int = 60):
        super().__init__(app)
        self.requests = requests
        self.window = window_seconds
        self._redis = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self._redis is None:
            self._redis = await redis.from_url(settings.redis_url)

        client_ip = request.client.host if request.client else 'unknown'
        key = f"rl:{client_ip}:{int(time.time() // self.window)}"
        try:
            count = await self._redis.incr(key)
            if count == 1:
                await self._redis.expire(key, self.window)
            if count > self.requests:
                return Response(status_code=429, content="Too Many Requests")
        except Exception:
            # Fail open if Redis is unavailable
            pass

        response = await call_next(request)
        return response
