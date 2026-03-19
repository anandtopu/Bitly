from fastapi import FastAPI
from app.api.routes import router as api_router
from app.models import models
from app.core.database import engine

# Create database tables defensively
try:
    if "sqlite" not in str(engine.url):
        models.Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create tables: {e}")

app = FastAPI(title="Bit.ly URL Shortener")

app.include_router(api_router)
