import json
import logging
import time
from typing import Any

logger = logging.getLogger("trustscore.cache")


class _InMemoryCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}

    async def get(self, key: str) -> Any | None:
        item = self._store.get(key)
        if item is None:
            return None

        expires_at, value = item
        if time.time() > expires_at:
            self._store.pop(key, None)
            return None

        return value

    async def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (time.time() + ttl_seconds, value)

    async def close(self) -> None:
        return None

    async def health(self) -> str:
        return "memory"


class CacheService:
    """Use Redis when available and fall back to in-memory caching otherwise."""

    def __init__(self) -> None:
        self._redis = None
        self._fallback = _InMemoryCache()

    async def connect(self) -> None:
        try:
            import os
            from redis.asyncio import Redis

            redis_url = os.getenv("REDIS_URL")
            if not redis_url:
                logger.info("REDIS_URL not set, using in-memory cache fallback.")
                return

            self._redis = Redis.from_url(redis_url, decode_responses=True)
            await self._redis.ping()
            logger.info("Connected to Redis cache.")
        except Exception as exc:  # pragma: no cover - depends on runtime services
            logger.warning("Redis unavailable, using in-memory cache: %s", exc)
            self._redis = None

    async def get(self, key: str) -> Any | None:
        if self._redis is not None:
            payload = await self._redis.get(key)
            return json.loads(payload) if payload else None
        return await self._fallback.get(key)

    async def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        if self._redis is not None:
            await self._redis.setex(key, ttl_seconds, json.dumps(value))
            return
        await self._fallback.set(key, value, ttl_seconds)

    async def close(self) -> None:
        if self._redis is not None:
            await self._redis.close()
        await self._fallback.close()

    async def health(self) -> str:
        if self._redis is not None:
            try:
                await self._redis.ping()
                return "redis"
            except Exception:
                return "degraded"
        return await self._fallback.health()


cache_service = CacheService()
