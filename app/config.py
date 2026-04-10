import os

from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in environment")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_TTL_SECONDS = int(os.getenv("REDIS_TTL_SECONDS", 3600))

LRU_CAPACITY = int(os.getenv("LRU_CAPACITY", 1000))

RESERVED_KEYWORDS = {
    "api", "docs", "admin", "static", "analytics", 
    "shorten", "links", "dashboard", "favicon.ico"
}