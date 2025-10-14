"""
Webhook API Endpoints
Handle incoming webhooks from external services like Overseerr
"""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.models.media import MediaItem, MediaType

# Router setup
router = APIRouter()


# Pydantic schemas
class OverseerrWebhook(BaseModel):
    """
    Overseerr webhook payload schema

    Example payload:
    {
        "notification_type": "MEDIA_APPROVED",
        "subject": "Movie Request Approved",
        "message": "The Shawshank Redemption has been approved",
        "media": {
            "media_type": "movie",
            "tmdbId": 278,
            "tvdbId": null,
            "status": "APPROVED"
        },
        "request": {
            "request_id": 123,
            "requestedBy_username": "john_doe",
            "requestedBy_email": "john@example.com"
        },
        "extra": []
    }
    """
    notification_type: str
    subject: Optional[str]
    message: Optional[str]
    media: Optional[Dict[str, Any]]
    request: Optional[Dict[str, Any]]
    extra: Optional[list] = []


class WebhookResponse(BaseModel):
    success: bool
    message: str
    media_id: Optional[int] = None


# Background task functions
async def process_overseerr_request(
    notification_type: str,
    media_data: Dict[str, Any],
    db: Session
):
    """
    Process Overseerr media request in background

    Steps:
    1. Check if media already exists in database
    2. If not, create placeholder entry
    3. Trigger metadata fetch from TMDb
    4. Queue torrent search task

    This runs asynchronously after webhook response is sent
    """
    try:
        # Only process approved or available requests
        if notification_type not in ["MEDIA_APPROVED", "MEDIA_AVAILABLE"]:
            return

        # Extract media info
        tmdb_id = media_data.get("tmdbId")
        media_type_str = media_data.get("media_type", "movie")

        if not tmdb_id:
            return

        # Convert media type
        media_type = MediaType.MOVIE if media_type_str == "movie" else MediaType.TV_SHOW

        # Check if media already exists
        existing_media = db.query(MediaItem).filter(
            MediaItem.tmdb_id == tmdb_id
        ).first()

        if existing_media:
            # Media already exists, no action needed
            return

        # Create placeholder media item
        new_media = MediaItem(
            tmdb_id=tmdb_id,
            title=f"Loading... (TMDb ID: {tmdb_id})",
            media_type=media_type,
            is_available=False
        )

        db.add(new_media)
        db.commit()
        db.refresh(new_media)

        # TODO: Trigger background tasks:
        # 1. Fetch metadata from TMDb API
        # 2. Search for torrents
        # 3. Add to Real-Debrid
        # 4. Update media item with streaming URLs

        # Note: These will be implemented in the service layer and Celery tasks

    except Exception as e:
        # Log error but don't fail webhook response
        print(f"Error processing Overseerr request: {str(e)}")
        db.rollback()


# API Endpoints
@router.post("/overseerr", response_model=WebhookResponse)
async def handle_overseerr_webhook(
    webhook_data: OverseerrWebhook,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_agent: Optional[str] = Header(None)
):
    """
    Handle Overseerr webhook notifications

    Webhook Types:
    - MEDIA_PENDING: User requested content (not processed)
    - MEDIA_APPROVED: Admin approved request → Add to library
    - MEDIA_AVAILABLE: Content is now available → Update status
    - MEDIA_DECLINED: Request was declined (not processed)
    - MEDIA_AUTO_APPROVED: Auto-approved request → Add to library

    Setup in Overseerr:
    1. Go to Settings → Notifications → Webhook
    2. Enable webhook agent
    3. Set webhook URL: http://your-domain/api/webhooks/overseerr
    4. Select notification types: Media Approved, Media Available
    5. Choose JSON payload

    Returns immediate 200 response, processes request in background
    """
    try:
        # Validate webhook source (optional security check)
        # You can check user_agent or add webhook secret validation here

        notification_type = webhook_data.notification_type

        # Only process approved or available media
        if notification_type in ["MEDIA_APPROVED", "MEDIA_AVAILABLE", "MEDIA_AUTO_APPROVED"]:
            if not webhook_data.media:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Media data missing from webhook payload"
                )

            # Add background task to process the request
            background_tasks.add_task(
                process_overseerr_request,
                notification_type,
                webhook_data.media,
                db
            )

            return WebhookResponse(
                success=True,
                message=f"Webhook received. Processing {notification_type} request in background."
            )

        else:
            # Other notification types are acknowledged but not processed
            return WebhookResponse(
                success=True,
                message=f"Webhook received. Notification type '{notification_type}' does not require processing."
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing webhook: {str(e)}"
        )


@router.get("/test")
async def test_webhook_endpoint():
    """
    Test endpoint to verify webhook connectivity

    Use this to test if your webhook URL is reachable from Overseerr
    """
    return {
        "status": "ok",
        "message": "Webhook endpoint is reachable",
        "service": "Linkarr",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }
