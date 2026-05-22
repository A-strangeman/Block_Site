"""Simple RQ-based worker helper.

Usage:
  - Enqueue a job: from app.services.worker import enqueue_job; enqueue_job('send_email', args)
  - Run a worker: `rq worker default -u $REDIS_URL`
"""
from typing import Any
import redis
from rq import Queue

from app.core.config import settings


def get_redis_conn():
    return redis.from_url(settings.redis_url)


def get_queue(name: str = 'default') -> Queue:
    return Queue(name, connection=get_redis_conn())


def enqueue_job(func_name: str, args: Any = (), kwargs: dict | None = None, queue: str = 'default'):
    q = get_queue(queue)
    return q.enqueue(func_name, args or (), kwargs or {})
