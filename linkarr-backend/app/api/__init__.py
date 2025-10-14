"""
Linkarr API Package
FastAPI router registration and API versioning
"""

from fastapi import APIRouter
from app.api import auth, media, library, webhooks

# Create main API router
api_router = APIRouter(prefix="/api")

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(media.router, prefix="/media", tags=["Media"])
api_router.include_router(library.router, prefix="/library", tags=["Library"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

__all__ = ["api_router"]
