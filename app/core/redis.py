import redis
from .config import settings
from typing import Optional, Any
import json


class RedisClient:
    def __init__(self):
        self.redis_client = redis.from_url(settings.REDIS_URL)

    def set(self, key: str, value: Any, expire_seconds: Optional[int] = None):
        """Set a key-value pair in Redis"""
        if not isinstance(value, (str, bytes)):
            value = json.dumps(value)
        self.redis_client.set(key, value)
        if expire_seconds:
            self.redis_client.expire(key, expire_seconds)

    def get(self, key: str) -> Optional[str]:
        """Get value by key from Redis"""
        value = self.redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return value.decode() if isinstance(value, bytes) else value
        return None

    def delete(self, key: str):
        """Delete a key from Redis"""
        self.redis_client.delete(key)

    def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        return self.redis_client.exists(key)


# Create a singleton instance
redis_client = RedisClient()
