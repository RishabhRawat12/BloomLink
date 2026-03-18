from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from pydantic import BaseModel, HttpUrl
from typing import Optional
from app.database import Base

class URLItem(Base):
    __tablename__ = "urls"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    long_url = Column(Text, nullable=False)
    short_code = Column(String(50), unique=True, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), index=True, nullable=True)
    clicks = Column(Integer, default=0)

class Click(Base):
    __tablename__ = "clicks"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    short_code = Column(String(50), ForeignKey("urls.short_code", ondelete="CASCADE"), index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ip_hash = Column(String(64))
    user_agent = Column(Text)

class ShortenRequest(BaseModel):
    longUrl: HttpUrl
    customAlias: Optional[str] = None
    expiresInHours: Optional[int] = None

class ShortenResponse(BaseModel):
    shortCode: str
    shortUrl: str

class UpdateExpiryRequest(BaseModel):
    expiresInHours: int