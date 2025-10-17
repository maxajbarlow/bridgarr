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
from app.models.user import User
from app.models.rd_torrent import RDTorrent
from app.models.rd_link import RDLink
from app.services.tmdb import tmdb_service
from app.services.content_processor import ContentProcessor
from app.services.rd_client import RealDebridClient

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
def process_overseerr_request(
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
            new_media.error_message = f"⚠️ Could not fetch details for TMDb ID {tmdb_id}. TMDb may be unavailable."
            db.commit()
            return

        # Step 3: Search torrents and add to Real-Debrid
        print(f"[WEBHOOK] Starting content processing...")

        # Get RD token from first user with configured token
        rd_user = db.query(User).filter(User.rd_api_token.isnot(None)).first()
        rd_token = rd_user.rd_api_token if rd_user else None

        if not rd_token:
            error_msg = "⚠️ No Real-Debrid API token configured. Please add your RD token in Settings."
            print(f"[WEBHOOK] {error_msg}")
            new_media.error_message = error_msg
            db.commit()
            return

        print(f"[WEBHOOK] Using Real-Debrid token from user: {rd_user.username}")

        try:
            processor = ContentProcessor(rd_api_token=rd_token)

            # Run async processing in sync context
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            processing_result = loop.run_until_complete(processor.process_movie(
                title=new_media.title,
                year=int(new_media.release_date[:4]) if new_media.release_date else None,
                imdb_id=new_media.imdb_id,
                tmdb_id=tmdb_id
            ))
            loop.close()

            print(f"[WEBHOOK] Processing result: {processing_result.get('message')}")
            print(f"[WEBHOOK] Torrents found: {processing_result.get('torrents_found', 0)}")

            # Check for processing errors
            if not processing_result.get("success"):
                error_msg = processing_result.get('message', 'Unknown error during content processing')

                # Categorize errors for user-friendly messages
                if 'No torrents found' in error_msg:
                    new_media.error_message = f"❌ No torrents available for '{new_media.title}'. Try requesting a different release."
                elif '451' in error_msg or 'Unavailable For Legal Reasons' in error_msg:
                    new_media.error_message = f"🚫 '{new_media.title}' is blocked by Real-Debrid (regional restrictions or copyright). This content cannot be added."
                elif 'Real-Debrid not configured' in error_msg:
                    new_media.error_message = "⚠️ No Real-Debrid API token configured. Please add your RD token in Settings."
                elif 'timeout' in error_msg.lower():
                    new_media.error_message = f"⏱️ '{new_media.title}' took too long to process. Please try requesting again."
                else:
                    new_media.error_message = f"❌ Failed to process '{new_media.title}': {error_msg}"

                print(f"[WEBHOOK] ⚠ Setting error message: {new_media.error_message}")
                db.commit()
                return

            if processing_result.get("success"):
                rd_info = processing_result.get("rd_info", {})
                selected_torrent = processing_result.get("selected_torrent", {})

                # Save torrent to database
                rd_torrent = RDTorrent(
                    media_item_id=new_media.id,
                    rd_torrent_id=rd_info.get("id"),
                    torrent_hash=selected_torrent.get("info_hash", ""),
                    torrent_name=selected_torrent.get("title", ""),
                    torrent_size=selected_torrent.get("size", 0),
                    status=rd_info.get("status", "pending"),
                    progress=rd_info.get("progress", 0)
                )
                db.add(rd_torrent)
                db.commit()
                db.refresh(rd_torrent)

                print(f"[WEBHOOK] ✓ Saved RD torrent to database: {rd_torrent.rd_torrent_id}")

                # Get streaming URLs from RD
                try:
                    import time
                    rd_client = RealDebridClient(api_token=rd_token)

                    # Poll for torrent completion (max 30 seconds)
                    for attempt in range(15):
                        torrent_info = rd_client.get_torrent_info(rd_info.get("id"))
                        status = torrent_info.get("status")

                        print(f"[WEBHOOK] RD Torrent status: {status}, progress: {torrent_info.get('progress', 0)}%")

                        if status == "downloaded":
                            # Get download links and file info
                            links = torrent_info.get("links", [])
                            files = torrent_info.get("files", [])

                            if links and files:
                                print(f"[WEBHOOK] Found {len(links)} download links and {len(files)} files")

                                # Find the best video file (largest video file, skip archives)
                                video_extensions = {'.mp4', '.mkv', '.avi', '.mov', '.webm', '.flv', '.m4v', '.wmv'}
                                archive_extensions = {'.rar', '.zip', '.7z', '.tar', '.gz'}

                                video_files = []
                                for i, file_info in enumerate(files):
                                    file_path = file_info.get("path", "")
                                    file_size = file_info.get("bytes", 0)
                                    file_ext = file_path[file_path.rfind('.'):].lower() if '.' in file_path else ''

                                    print(f"[WEBHOOK] File {i}: {file_path} ({file_size} bytes)")

                                    # Skip archives
                                    if file_ext in archive_extensions:
                                        print(f"[WEBHOOK] Skipping archive: {file_path}")
                                        continue

                                    # Select video files
                                    if file_ext in video_extensions:
                                        video_files.append({
                                            'index': i,
                                            'path': file_path,
                                            'size': file_size,
                                            'link': links[i] if i < len(links) else None
                                        })

                                if not video_files:
                                    error_msg = f"❌ No video files found in torrent for '{new_media.title}'. Only archives or non-video files available."
                                    print(f"[WEBHOOK] {error_msg}")
                                    new_media.error_message = error_msg
                                    db.commit()
                                    break

                                # Select largest video file (usually the main movie)
                                selected_file = max(video_files, key=lambda x: x['size'])
                                print(f"[WEBHOOK] Selected video file: {selected_file['path']} ({selected_file['size']} bytes)")

                                # Unrestrict the selected video file link
                                unrestrict_result = rd_client.unrestrict_link(selected_file['link'])
                                print(f"[WEBHOOK] Unrestrict result: {unrestrict_result}")

                                filename = unrestrict_result.get("filename", "")
                                filesize = unrestrict_result.get("filesize", 0)

                                # Use direct download URL for streaming
                                streaming_url = unrestrict_result.get("download", "")
                                print(f"[WEBHOOK] Using direct download URL: {streaming_url}")

                                if streaming_url:
                                    # Save streaming link to database
                                    from datetime import timedelta
                                    rd_link = RDLink(
                                        rd_torrent_id=rd_torrent.id,
                                        rd_file_id=str(torrent_info.get("files", [{}])[0].get("id", "")),
                                        filename=filename,
                                        filesize=filesize,
                                        streaming_url=streaming_url,
                                        quality=selected_torrent.get("quality"),
                                        is_valid=True,
                                        expires_at=datetime.utcnow() + timedelta(hours=settings.RD_LINK_EXPIRY_HOURS)
                                    )
                                    db.add(rd_link)

                                    # Mark media as available
                                    new_media.is_available = True

                                    db.commit()
                                    print(f"[WEBHOOK] ✓ Saved streaming URL to database!")
                                    print(f"[WEBHOOK] ✓ Media marked as available!")
                                    break
                                else:
                                    error_msg = f"❌ Could not get streaming URL for video file"
                                    print(f"[WEBHOOK] {error_msg}")
                                    new_media.error_message = error_msg
                                    db.commit()
                                    break
                            else:
                                error_msg = f"❌ No files or links found in RD torrent for '{new_media.title}'"
                                print(f"[WEBHOOK] {error_msg}")
                                new_media.error_message = error_msg
                                db.commit()
                                break

                        elif status in ["error", "virus", "dead"]:
                            print(f"[WEBHOOK] ✗ Torrent failed with status: {status}")
                            rd_torrent.status = status
                            rd_torrent.error_message = f"RD torrent status: {status}"
                            db.commit()
                            break

                        # Wait before next poll
                        time.sleep(2)

                    # If we exit loop without breaking, download timed out
                    if not new_media.is_available:
                        error_msg = f"⏱️ '{new_media.title}' is still downloading on Real-Debrid. Check back in a few minutes!"
                        print(f"[WEBHOOK] {error_msg}")
                        new_media.error_message = error_msg
                        db.commit()

                except Exception as rd_error:
                    error_msg = f"❌ Failed to get streaming URL: {str(rd_error)}"
                    print(f"[WEBHOOK] {error_msg}")
                    new_media.error_message = error_msg
                    db.commit()
        except Exception as proc_error:
            error_msg = f"❌ Unexpected error: {str(proc_error)}"
            print(f"[WEBHOOK] ✗ Content processing error: {error_msg}")
            new_media.error_message = error_msg
            db.commit()

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
        "service": "Bridgarr",
        "version": settings.APP_VERSION,
        "timestamp": datetime.utcnow().isoformat()
    }
