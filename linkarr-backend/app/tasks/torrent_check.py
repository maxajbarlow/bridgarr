"""
Torrent Status Check Background Tasks
Monitor torrent caching progress and update database accordingly
"""

from celery import Task
from sqlalchemy.orm import Session
import logging

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.models.rd_torrent import RDTorrent
from app.services.rd_client import RealDebridClient

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """
    Base task class that provides database session management
    """
    _db = None

    def after_return(self, *args, **kwargs):
        """Close database session after task completion"""
        if self._db is not None:
            self._db.close()


@celery_app.task(
    name="app.tasks.torrent_check.monitor_pending_torrents",
    base=DatabaseTask,
    bind=True
)
def monitor_pending_torrents(self):
    """
    Check status of all pending/downloading torrents

    Updates torrent status in database and creates RD links when ready
    Runs every 5 minutes
    """
    db: Session = SessionLocal()
    self._db = db

    try:
        # Get all pending/downloading torrents
        pending_torrents = db.query(RDTorrent).filter(
            RDTorrent.status.in_(["pending", "downloading", "queued"])
        ).all()

        if not pending_torrents:
            logger.info("No pending torrents to check")
            return {
                "status": "success",
                "torrents_checked": 0,
                "torrents_completed": 0
            }

        torrents_completed = 0

        for torrent in pending_torrents:
            try:
                # Get the user who owns this torrent
                media_item = torrent.media_item
                # TODO: Associate torrents with specific users
                # For now, find first active user with RD token
                user = db.query(User).filter(
                    User.rd_api_token.isnot(None),
                    User.is_active == True
                ).first()

                if not user:
                    logger.warning(f"No active user with RD token found for torrent {torrent.id}")
                    continue

                # Create RD client
                rd_client = RealDebridClient(user.rd_api_token)

                # Check torrent status
                torrent_info = rd_client.get_torrent_info(torrent.rd_torrent_id)
                new_status = torrent_info.get("status")

                # Update torrent status
                torrent.status = new_status
                torrent.progress = torrent_info.get("progress", 0)

                if new_status == "downloaded":
                    # Torrent is ready - create RD links
                    torrents_completed += 1
                    logger.info(f"Torrent {torrent.id} completed downloading")

                    # Get download links
                    links = torrent_info.get("links", [])

                    if links:
                        # Unrestrict links and create RDLink entries
                        from app.models.rd_link import RDLink
                        from datetime import datetime, timedelta

                        for link_url in links:
                            unrestrict_result = rd_client.unrestrict_link(link_url)
                            streaming_url = unrestrict_result.get("download")
                            filename = unrestrict_result.get("filename", "")
                            filesize = unrestrict_result.get("filesize", 0)

                            if streaming_url:
                                # Create RDLink
                                rd_link = RDLink(
                                    rd_torrent_id=torrent.id,
                                    streaming_url=streaming_url,
                                    quality=_detect_quality_from_filename(filename),
                                    is_valid=True,
                                    expires_at=datetime.utcnow() + timedelta(hours=4)
                                )
                                db.add(rd_link)

                        # Update media availability
                        if media_item:
                            media_item.is_available = True

                        db.commit()
                        logger.info(f"Created {len(links)} RD links for torrent {torrent.id}")

                elif new_status in ["error", "virus", "dead"]:
                    # Torrent failed
                    logger.error(f"Torrent {torrent.id} failed with status: {new_status}")

                db.commit()

            except Exception as e:
                logger.error(f"Error checking torrent {torrent.id}: {str(e)}")
                db.rollback()
                continue

        logger.info(
            f"Checked {len(pending_torrents)} pending torrents, "
            f"{torrents_completed} completed"
        )

        return {
            "status": "success",
            "torrents_checked": len(pending_torrents),
            "torrents_completed": torrents_completed
        }

    except Exception as e:
        logger.error(f"Error in monitor_pending_torrents task: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

    finally:
        db.close()


@celery_app.task(
    name="app.tasks.torrent_check.check_torrent_status",
    base=DatabaseTask,
    bind=True
)
def check_torrent_status(self, torrent_id: int, user_id: int):
    """
    Check status of a specific torrent on demand

    Args:
        torrent_id: RDTorrent ID to check
        user_id: User ID owning the torrent

    Returns:
        Task result with torrent status
    """
    db: Session = SessionLocal()
    self._db = db

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.rd_api_token:
            return {"status": "error", "error": "User not found or no RD token"}

        # Get torrent
        torrent = db.query(RDTorrent).filter(RDTorrent.id == torrent_id).first()
        if not torrent:
            return {"status": "error", "error": "Torrent not found"}

        # Create RD client
        rd_client = RealDebridClient(user.rd_api_token)

        # Get torrent info
        torrent_info = rd_client.get_torrent_info(torrent.rd_torrent_id)

        # Update torrent
        torrent.status = torrent_info.get("status")
        torrent.progress = torrent_info.get("progress", 0)
        db.commit()

        return {
            "status": "success",
            "torrent_id": torrent_id,
            "torrent_status": torrent.status,
            "progress": torrent.progress
        }

    except Exception as e:
        logger.error(f"Error in check_torrent_status task: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

    finally:
        db.close()


@celery_app.task(
    name="app.tasks.torrent_check.add_torrent_from_magnet",
    base=DatabaseTask,
    bind=True
)
def add_torrent_from_magnet(self, magnet_link: str, media_item_id: int, user_id: int):
    """
    Add magnet link to Real-Debrid and create database entries

    Args:
        magnet_link: Magnet URI
        media_item_id: MediaItem ID to associate with
        user_id: User ID

    Returns:
        Task result with torrent info
    """
    db: Session = SessionLocal()
    self._db = db

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.rd_api_token:
            return {"status": "error", "error": "User not found or no RD token"}

        # Create RD client
        rd_client = RealDebridClient(user.rd_api_token)

        # Add magnet to RD
        add_result = rd_client.add_magnet(magnet_link)
        rd_torrent_id = add_result.get("id")

        if not rd_torrent_id:
            return {"status": "error", "error": "Failed to add magnet to RD"}

        # Get torrent info
        torrent_info = rd_client.get_torrent_info(str(rd_torrent_id))

        # Select files (largest file for movies, all files for TV shows)
        files = torrent_info.get("files", [])
        if files:
            largest_file = max(files, key=lambda f: f.get("bytes", 0))
            rd_client.select_files(str(rd_torrent_id), [largest_file["id"]])

        # Create RDTorrent entry
        torrent = RDTorrent(
            media_item_id=media_item_id,
            rd_torrent_id=str(rd_torrent_id),
            magnet_link=magnet_link,
            status=torrent_info.get("status", "pending"),
            progress=torrent_info.get("progress", 0),
            torrent_name=torrent_info.get("filename", "Unknown")
        )
        db.add(torrent)
        db.commit()
        db.refresh(torrent)

        logger.info(f"Added torrent {rd_torrent_id} for media {media_item_id}")

        return {
            "status": "success",
            "torrent_id": torrent.id,
            "rd_torrent_id": rd_torrent_id,
            "torrent_status": torrent.status
        }

    except Exception as e:
        logger.error(f"Error in add_torrent_from_magnet task: {str(e)}")
        db.rollback()
        return {
            "status": "error",
            "error": str(e)
        }

    finally:
        db.close()


def _detect_quality_from_filename(filename: str) -> str:
    """
    Detect video quality from filename

    Args:
        filename: Video filename

    Returns:
        Quality label (4K, 1080p, 720p, etc.)
    """
    filename_lower = filename.lower()

    if "2160p" in filename_lower or "4k" in filename_lower:
        return "4K"
    elif "1080p" in filename_lower:
        return "1080p"
    elif "720p" in filename_lower:
        return "720p"
    elif "480p" in filename_lower:
        return "480p"
    else:
        return "Unknown"
