from collections import defaultdict, deque
from dataclasses import dataclass
from time import time

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


@dataclass(frozen=True)
class RateLimitConfig:
    max_requests: int = 120
    window_seconds: int = 60


class InMemoryRateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, config: RateLimitConfig | None = None):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.requests_by_key: dict[str, deque[float]] = defaultdict(deque)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path == "/health":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        cache_key = f"{client_ip}:{request.url.path}"
        now = time()
        bucket = self.requests_by_key[cache_key]

        while bucket and now - bucket[0] > self.config.window_seconds:
            bucket.popleft()

        if len(bucket) >= self.config.max_requests:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

        bucket.append(now)
        return await call_next(request)
