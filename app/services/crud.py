from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from app.models import models
from app.schemas import schemas
from app.utils import base62

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
        # Save to get ID
        db.add(db_url)
        db.commit()
        db.refresh(db_url)
        
        # Generate short code from ID
        db_url.short_code = base62.encode(db_url.id)
        db.commit()
        db.refresh(db_url)
        return db_url

def get_url_by_short_code(db: Session, short_code: str) -> models.URL:
    return db.query(models.URL).filter(models.URL.short_code == short_code).first()

def get_active_url(db: Session, short_code: str) -> models.URL:
    url = get_url_by_short_code(db, short_code)
    if url:
        # Use timezone-aware datetime for comparison
        if url.expires_at:
            expires_at = url.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < datetime.now(timezone.utc):
                return None # Expired
        return url
    return None
