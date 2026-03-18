import logging
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.database import engine, Base, get_db, SessionLocal
from app.models import URLItem, Click, ShortenRequest, ShortenResponse, UpdateExpiryRequest
from app.cache import redis_client, lru_cache
from app.utils import generate_code, validate_alias, normalize_url, hash_ip
from app.bloom_filter import BloomFilter
from app.hotkey import record_access, is_hot_key, replica_key
from app.config import REDIS_TTL_SECONDS, RESERVED_KEYWORDS

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------- INIT ----------------
limiter = Limiter(key_func=get_remote_address)
bloom = BloomFilter()
MAX_RETRIES = 5

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Load all existing codes into Bloom Filter for fast O(1) checking
        for row in db.query(URLItem.short_code).yield_per(10000):
            bloom.add(row.short_code)
        logger.info("Bloom filter hydrated")
    except Exception as e:
        logger.error(f"Bloom init failed: {e}")
    finally:
        db.close()
    yield

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

templates = Jinja2Templates(directory="app/templates")

# ---------------- HELPERS ----------------

def get_base_url(request: Request):
    return str(request.base_url).rstrip("/")

def track_click_async(short_code: str, ip: str, user_agent: str):
    db = SessionLocal()
    try:
        ip_hash = hash_ip(ip)

        # Log individual click record
        db.add(Click(
            short_code=short_code,
            ip_hash=ip_hash,
            user_agent=user_agent
        ))

        # Update the aggregate counter in MySQL
        db.query(URLItem).filter(URLItem.short_code == short_code).update(
            {"clicks": URLItem.clicks + 1}
        )

        db.commit()

        # Update fast-access counter in Redis
        try:
            redis_client.incr(f"url:clicks:{short_code}")
        except Exception as e:
            logger.warning(f"Redis click increment failed: {e}")

    except Exception as e:
        db.rollback()
        logger.error(f"Click tracking failed: {e}")
    finally:
        db.close()

# ---------------- API ROUTES ----------------

@app.post("/api/shorten", response_model=ShortenResponse)
@limiter.limit("20/minute")
def shorten_url(request: Request, payload: ShortenRequest, db: Session = Depends(get_db)):
    normalized_url = normalize_url(str(payload.longUrl))
    expires_at = None
    if payload.expiresInHours:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.expiresInHours)

    if payload.customAlias:
        validate_alias(payload.customAlias)
        new_url = URLItem(
            long_url=normalized_url,
            short_code=payload.customAlias,
            expires_at=expires_at
        )
        db.add(new_url)
        try:
            db.commit()
            short_code = payload.customAlias
        except IntegrityError:
            db.rollback()
            raise HTTPException(400, "Alias already in use")
    else:
        for _ in range(MAX_RETRIES):
            code = generate_code()
            new_url = URLItem(long_url=normalized_url, short_code=code, expires_at=expires_at)
            db.add(new_url)
            try:
                db.commit()
                short_code = code
                break
            except IntegrityError:
                db.rollback()
                continue
        else:
            raise HTTPException(500, "Failed to generate unique code")

    bloom.add(short_code)
    base_url = get_base_url(request)
    return {"shortCode": short_code, "shortUrl": f"{base_url}/{short_code}"}

@app.get("/api/links")
@limiter.limit("30/minute")
def list_links(request: Request, db: Session = Depends(get_db)):
    try:
        return db.query(URLItem).order_by(URLItem.created_at.desc()).limit(50).all()
    except OperationalError:
        raise HTTPException(503, "Database unavailable")

@app.delete("/api/links/{shortCode}")
@limiter.limit("20/minute")
def delete_link(request: Request, shortCode: str, db: Session = Depends(get_db)):
    doc = db.query(URLItem).filter(URLItem.short_code == shortCode).first()
    if not doc:
        raise HTTPException(404)
    db.delete(doc)
    db.commit()
    lru_cache.delete(shortCode)
    redis_client.delete(f"url:{shortCode}")
    return {"detail": "Deleted"}

# ---------------- PAGES ----------------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/links", response_class=HTMLResponse)
def manage_links_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/analytics/{shortCode}", response_class=HTMLResponse)
def get_analytics(request: Request, shortCode: str, db: Session = Depends(get_db)):
    doc = db.query(URLItem).filter(URLItem.short_code == shortCode).first()
    if not doc:
        raise HTTPException(404)

    # Real-time Resilience Diagnostics
    system_status = {
        "is_hot": is_hot_key(shortCode),
        "cache_hits": redis_client.get(f"url:clicks:{shortCode}") or 0,
        "replicas_active": 0
    }
    
    # Check for active Redis replicas
    replica_pattern = f"url:{shortCode}:replica:*"
    found_replicas = redis_client.keys(replica_pattern)
    system_status["replicas_active"] = len(found_replicas)

    recent_clicks = db.query(Click).filter(Click.short_code == shortCode).order_by(Click.timestamp.desc()).limit(10).all()
    
    return templates.TemplateResponse("analytics.html", {
        "request": request, 
        "url": doc,
        "recent_clicks": recent_clicks,
        "system": system_status
    })

# ---------------- REDIRECT (DYNAMIC ROUTE) ----------------

@app.get("/{shortCode}")
@limiter.limit("100/minute")
def redirect_to_url(request: Request, shortCode: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):

    # 1. Block reserved keywords
    if shortCode in RESERVED_KEYWORDS:
        raise HTTPException(404)

    # 2. Bloom Filter check (prevents DB hits for non-existent codes)
    if not bloom.might_exist(shortCode):
        raise HTTPException(404)

    # 3. Check LRU Cache (Memory)
    cached = lru_cache.get(shortCode)
    if cached:
        if cached == "EXPIRED": raise HTTPException(410)
        # Background tracking still runs for cache hits
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        record_access(shortCode, cached) 
        background_tasks.add_task(track_click_async, shortCode, client_ip, user_agent)
        return RedirectResponse(cached)

    # 4. Check Redis (and Replicas if hot)
    redis_key = replica_key(shortCode) if is_hot_key(shortCode) else f"url:{shortCode}"
    try:
        cached_url = redis_client.get(redis_key)
        if cached_url:
            lru_cache.put(shortCode, cached_url)
            if cached_url == "EXPIRED": raise HTTPException(410)
            
            client_ip = request.client.host if request.client else "unknown"
            user_agent = request.headers.get("user-agent", "unknown")
            record_access(shortCode, cached_url)
            background_tasks.add_task(track_click_async, shortCode, client_ip, user_agent)
            return RedirectResponse(cached_url)
    except Exception:
        pass

    # 5. Database Fallback (Final check)
    doc = db.query(URLItem).filter(URLItem.short_code == shortCode).first()
    if not doc:
        raise HTTPException(404)

    # 6. Expiry Logic
    if doc.expires_at and doc.expires_at < datetime.now(timezone.utc):
        lru_cache.put(shortCode, "EXPIRED")
        redis_client.setex(f"url:{shortCode}", REDIS_TTL_SECONDS, "EXPIRED")
        raise HTTPException(410)

    # 7. Hot-Key Detection and Logging
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Passing doc.long_url here allows record_access to create replicas immediately
    record_access(shortCode, doc.long_url)
    background_tasks.add_task(track_click_async, shortCode, client_ip, user_agent)

    # 8. Repopulate Caches
    lru_cache.put(shortCode, doc.long_url)
    try:
        redis_client.setex(f"url:{shortCode}", REDIS_TTL_SECONDS, doc.long_url)
    except Exception:
        pass

    return RedirectResponse(doc.long_url)