import random
from app.cache import redis_client
from app.config import REDIS_TTL_SECONDS

HOT_KEY_THRESHOLD = 20
WINDOW_SECONDS = 10
REPLICA_COUNT = 3

def record_access(key: str, long_url: str = None):
    """Increments access count and creates replicas immediately if threshold hit."""
    redis_counter_key = f"url:access_count:{key}"
    try:
        count = redis_client.incr(redis_counter_key)
        if count == 1:
            redis_client.expire(redis_counter_key, WINDOW_SECONDS)
        
        # If we hit the threshold, create replicas immediately
        if count >= HOT_KEY_THRESHOLD and long_url:
            for i in range(1, REPLICA_COUNT + 1):
                replica_key_name = f"url:{key}:replica:{i}"
                if not redis_client.exists(replica_key_name):
                    redis_client.setex(replica_key_name, REDIS_TTL_SECONDS, long_url)
    except Exception:
        pass

def is_hot_key(key: str) -> bool:
    """Checks if the access count has crossed the hot-key threshold."""
    redis_counter_key = f"url:access_count:{key}"
    try:
        count = redis_client.get(redis_counter_key)
        if count and int(count) >= HOT_KEY_THRESHOLD:
            return True
    except Exception:
        return False
    return False

def replica_key(key: str) -> str:
    """Returns a random replica key for distributed reads."""
    return f"url:{key}:replica:{random.randint(1, REPLICA_COUNT)}"