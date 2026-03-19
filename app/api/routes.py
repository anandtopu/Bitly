from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.models import models
from app.schemas import schemas
from app.services import crud
from app.core.database import get_db

router = APIRouter()

# Local dev URL
BASE_URL = "http://localhost:8000/"

@router.post("/api/v1/urls", response_model=schemas.URLResponse, status_code=status.HTTP_201_CREATED)
def create_short_url(url: schemas.URLCreate, db: Session = Depends(get_db)):
    db_url = crud.create_url(db, url)
    if not db_url:
        raise HTTPException(
            status_code=400,
            detail="Custom alias already exists."
        )
    
    return schemas.URLResponse(
        short_url=f"{BASE_URL}{db_url.short_code}",
        short_code=db_url.short_code,
        long_url=db_url.long_url,
        created_at=db_url.created_at,
        expires_at=db_url.expires_at
    )

@router.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    db_url = crud.get_active_url(db, short_code)
    if not db_url:
        raise HTTPException(
            status_code=404,
            detail="URL not found or has expired."
        )
    return RedirectResponse(url=db_url.long_url, status_code=status.HTTP_302_FOUND)
