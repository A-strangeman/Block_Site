from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import Request

from app.api.router import api_router
from app.core.config import settings
from app.core.rate_limit import InMemoryRateLimitMiddleware
from app.core.rate_limit_redis import RedisRateLimitMiddleware
from app.db import session as db_session
from fastapi.responses import Response

import sentry_sdk
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST


if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn)


app = FastAPI(title="FocusGuard API", version="1.0.0")

# prefer Redis rate limit if configured
if settings.redis_url:
    app.add_middleware(RedisRateLimitMiddleware)
else:
    app.add_middleware(InMemoryRateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def readiness_check(request: Request) -> dict[str, str]:
    # check DB connectivity
    try:
        engine = db_session.engine
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
    except Exception:
        return {"status": "unhealthy"}
    return {"status": "ready"}


@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
