from pydantic import BaseModel, HttpUrl

class ShortenRequest(BaseModel):
    longUrl: HttpUrl

class ShortenResponse(BaseModel):
    shortCode: str