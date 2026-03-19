from pydantic import BaseModel, HttpUrl, Field
from typing import Optional
from datetime import datetime

class URLCreate(BaseModel):
    long_url: HttpUrl
    custom_alias: Optional[str] = Field(None, max_length=50)
    expires_at: Optional[datetime] = None

class URLResponse(BaseModel):
    short_url: str
    short_code: str
    long_url: str
    created_at: datetime
    expires_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
