from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.templating import Jinja2Templates

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError
from contextlib import asynccontextmanager

from app.database import collection
from app.cache import redis_client, lru_cache
from app.utils import generate_short_code
from app.models import ShortenRequest, ShortenResponse
from app.bloom_filter import BloomFilter
from app.hotkey import record_access, is_hot_key, replica_key
from app.config import REDIS_TTL_SECONDS

bloom = BloomFilter()
MAX_RETRIES = 3

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Cold start fix: rebuild Bloom Filter from DB
    for doc in collection.find({}, {"shortCode": 1}):
        bloom.add(doc["shortCode"])
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="app/templates")

@app.post("/shorten", response_model=ShortenResponse)
def shorten_url(request: ShortenRequest):
    for _ in range(MAX_RETRIES):
        code = generate_short_code()
        try:
            collection.insert_one({
                "shortCode": code,
                "longUrl": str(request.longUrl)
            })
            bloom.add(code)
            return {"shortCode": code}
        except DuplicateKeyError:
            continue
    raise HTTPException(status_code=500, detail="Failed to create short URL")

@app.get("/{shortCode}")
def redirect(shortCode: str):
    # 1. Bloom filter check
    if not bloom.might_exist(shortCode):
        raise HTTPException(status_code=404, detail="URL not found")

    '''if not bloom.might_exist(shortCode):
        print("BLOOM FILTER BLOCKED:", shortCode)
        raise HTTPException(status_code=404)'''

    # 2. Hot-key detection
    record_access(shortCode)
    redis_key = replica_key(shortCode)
    if is_hot_key(shortCode):
        redis_key = replica_key(shortCode)
        print("USING REDIS KEY:", redis_key)

    # 3. Redis
    try:
        cached = redis_client.get(redis_key)
        if cached:
            return RedirectResponse(cached)
    except Exception:
        pass

    # 4. LRU fallback
    lru_val = lru_cache.get(shortCode)
    if lru_val:
        return RedirectResponse(lru_val)

    # 5. DB lookup
    doc = collection.find_one({"shortCode": shortCode})
    if not doc:
        raise HTTPException(status_code=404, detail="URL not found")

    long_url = doc["longUrl"]

    # 6. Populate caches
    try:
        redis_client.setex(shortCode, REDIS_TTL_SECONDS, long_url)
        if is_hot_key(shortCode):
            for i in range(1, 4):
                redis_client.setex(
                    f"{shortCode}:replica:{i}",
                    REDIS_TTL_SECONDS,
                    long_url
                )
    except Exception:
        pass

    lru_cache.put(shortCode, long_url)
    return RedirectResponse(long_url)

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
