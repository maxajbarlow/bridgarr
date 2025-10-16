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
from app.services.tmdb import tmdb_service
from app.services.content_processor import ContentProcessor

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
        # Log incoming webhook data
        print(f"[WEBHOOK] Notification type: {notification_type}")
        print(f"[WEBHOOK] Media data: {media_data}")

        # Only process approved or available requests
        if notification_type not in ["MEDIA_APPROVED", "MEDIA_AVAILABLE", "MEDIA_AUTO_APPROVED"]:
            print(f"[WEBHOOK] Skipping notification type: {notification_type}")
            return

        # Extract media info
        tmdb_id = media_data.get("tmdbId")
        media_type_str = media_data.get("media_type", "movie")

        print(f"[WEBHOOK] Extracted TMDb ID: {tmdb_id}, Media type: {media_type_str}")

        if not tmdb_id:
            print(f"[WEBHOOK] No TMDb ID found in payload!")
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

        print(f"[WEBHOOK] ✓ Created media item: ID={new_media.id}, Title={new_media.title}, TMDb ID={tmdb_id}")

        # Fetch metadata from TMDb
        print(f"[WEBHOOK] Fetching metadata from TMDb for ID {tmdb_id}...")

        if media_type == MediaType.MOVIE:
            metadata = tmdb_service.get_movie_details(tmdb_id)
        else:
            metadata = tmdb_service.get_tv_details(tmdb_id)

        if metadata:
            # Update media item with fetched metadata
            new_media.title = metadata.get("title", new_media.title)
            new_media.overview = metadata.get("overview")
            new_media.poster_path = metadata.get("poster_path")
            new_media.backdrop_path = metadata.get("backdrop_path")
            new_media.release_date = metadata.get("release_date") or metadata.get("first_air_date")
            new_media.runtime = metadata.get("runtime")
            new_media.imdb_id = metadata.get("imdb_id")
            new_media.vote_average = int(metadata.get("vote_average", 0) * 10) if metadata.get("vote_average") else None
            new_media.vote_count = metadata.get("vote_count")

            # Convert genres list to comma-separated string
            genres_list = metadata.get("genres", [])
            new_media.genres = ", ".join(genres_list) if genres_list else None

            db.commit()
            db.refresh(new_media)

            print(f"[WEBHOOK] ✓ Updated metadata for: {new_media.title}")
        else:
            print(f"[WEBHOOK] ⚠ Could not fetch metadata from TMDb")

        # Step 3: Search torrents and add to Real-Debrid
        print(f"[WEBHOOK] Starting content processing...")

        # Note: User's RD token should be fetched from database/context
        # For now, we'll try without RD token to test scraping
        processor = ContentProcessor(rd_api_token=None)  # TODO: Get user's RD token

        import asyncio
        processing_result = asyncio.run(processor.process_movie(
            title=new_media.title,
            year=int(new_media.release_date[:4]) if new_media.release_date else None,
            imdb_id=new_media.imdb_id,
            tmdb_id=tmdb_id
        ))

        print(f"[WEBHOOK] Processing result: {processing_result.get('message')}")
        print(f"[WEBHOOK] Torrents found: {processing_result.get('torrents_found', 0)}")

        if processing_result.get("success"):
            # Update media item with RD info
            new_media.is_available = True
            db.commit()
            print(f"[WEBHOOK] ✓ Media marked as available!")
        else:
            print(f"[WEBHOOK] ⚠ Content processing incomplete: {processing_result.get('message')}")

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

        print(f"[WEBHOOK HANDLER] Received notification: {notification_type}")
        print(f"[WEBHOOK HANDLER] Media data present: {webhook_data.media is not None}")
        if webhook_data.media:
            print(f"[WEBHOOK HANDLER] Media dict: {webhook_data.media}")

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
