import string
import secrets
import re
import hashlib
from app.config import RESERVED_KEYWORDS

def generate_code(length=6) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))

def validate_alias(alias: str):
    if alias.lower() in RESERVED_KEYWORDS:
        raise ValueError(f"'{alias}' is a reserved keyword and cannot be used.")
    
    if not re.match(r"^[a-zA-Z0-9_-]{3,20}$", alias):
        raise ValueError("Alias must be 3-20 characters long and contain only letters, numbers, dashes, or underscores.")

def normalize_url(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        return "https://" + url
    return url

def hash_ip(ip: str) -> str:
    if not ip:
        return "unknown"
    return hashlib.sha256(ip.encode()).hexdigest()