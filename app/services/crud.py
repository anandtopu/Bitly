from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from app.models import models
from app.schemas import schemas
from app.utils import base62
from app.core.redis import redis_client

def create_url(db: Session, url: schemas.URLCreate) -> models.URL:
    db_url = models.URL(
        long_url=str(url.long_url),
        short_code="temp", # Placeholder
        expires_at=url.expires_at
    )
    
    if url.custom_alias:
        db_url.short_code = url.custom_alias
        db.add(db_url)
        try:
            db.commit()
            db.refresh(db_url)
            return db_url
        except IntegrityError:
            db.rollback()
            return None # Alias already exists
    else:
        # Generate unique ID from Redis counter
        unique_id = redis_client.incr("url_id_counter")
        
        # Generate short code from ID
        db_url.short_code = base62.encode(unique_id)
        
        db.add(db_url)
        try:
            db.commit()
            db.refresh(db_url)
            return db_url
        except IntegrityError:
            db.rollback()
            return None

def get_url_by_short_code(db: Session, short_code: str) -> models.URL:
    return db.query(models.URL).filter(models.URL.short_code == short_code).first()

def get_active_url(db: Session, short_code: str) -> models.URL:
    cache_key = f"url:{short_code}"
    
    # 1. Check Redis cache
    cached_url = redis_client.get(cache_key)
    if cached_url:
        return models.URL(long_url=cached_url, short_code=short_code)

    # 2. Database Fallback (Cache Miss)
    url = get_url_by_short_code(db, short_code)
    if url:
        if url.expires_at:
            expires_at = url.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                return None # Expired
        
        # 3. Cache the result
        if url.expires_at:
            now = datetime.now(timezone.utc)
            ttl = int((url.expires_at - now).total_seconds())
            if ttl > 0:
                redis_client.setex(cache_key, ttl, url.long_url)
        else:
            redis_client.setex(cache_key, 86400, url.long_url)
            
        return url
    return None
