"""
Link Refresh Background Tasks
Periodic tasks to refresh expiring RD links and cleanup old links
"""

from celery import Task
from sqlalchemy.orm import Session
import logging

from app.tasks.celery_app import celery_app
from app.database import SessionLocal
from app.models.user import User
from app.services.link_cache_manager import LinkCacheManager

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
    name="app.tasks.link_refresh.refresh_all_expiring_links",
    base=DatabaseTask,
    bind=True
)
def refresh_all_expiring_links(self):
    """
    Refresh all expiring RD streaming links for all users

    This task runs every 15 minutes to ensure links don't expire
    RD links typically expire in 4 hours, we refresh them when < 30 min remaining
    """
    db: Session = SessionLocal()
    self._db = db

    try:
        # Get all users with RD tokens
        users = db.query(User).filter(
            User.rd_api_token.isnot(None),
            User.is_active == True
        ).all()

        total_refreshed = 0

        for user in users:
            try:
                # Create link cache manager for this user
                link_manager = LinkCacheManager(db, user.rd_api_token)

                # Refresh expiring links
                count = link_manager.refresh_expiring_links()
                total_refreshed += count

                logger.info(f"Refreshed {count} links for user {user.username}")

            except Exception as e:
                logger.error(f"Error refreshing links for user {user.username}: {str(e)}")
                continue

        logger.info(f"Total links refreshed: {total_refreshed}")
        return {
            "status": "success",
            "users_processed": len(users),
            "links_refreshed": total_refreshed
        }

    except Exception as e:
        logger.error(f"Error in refresh_all_expiring_links task: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

    finally:
        db.close()


@celery_app.task(
    name="app.tasks.link_refresh.cleanup_expired_links",
    base=DatabaseTask,
    bind=True
)
def cleanup_expired_links(self):
    """
    Mark expired links as invalid and cleanup old invalid links

    This task runs every hour to maintain database cleanliness
    """
    db: Session = SessionLocal()
    self._db = db

    try:
        # Get all users with RD tokens
        users = db.query(User).filter(
            User.rd_api_token.isnot(None)
        ).all()

        total_invalidated = 0
        total_cleaned = 0

        for user in users:
            try:
                # Create link cache manager for this user
                link_manager = LinkCacheManager(db, user.rd_api_token)

                # Invalidate expired links
                invalidated = link_manager.invalidate_expired_links()
                total_invalidated += invalidated

                # Cleanup old invalid links (older than 7 days)
                cleaned = link_manager.cleanup_old_links(days_old=7)
                total_cleaned += cleaned

                logger.info(
                    f"User {user.username}: "
                    f"Invalidated {invalidated} links, "
                    f"Cleaned {cleaned} old links"
                )

            except Exception as e:
                logger.error(f"Error cleaning links for user {user.username}: {str(e)}")
                continue

        logger.info(
            f"Total links invalidated: {total_invalidated}, "
            f"Total links cleaned: {total_cleaned}"
        )

        return {
            "status": "success",
            "users_processed": len(users),
            "links_invalidated": total_invalidated,
            "links_cleaned": total_cleaned
        }

    except Exception as e:
        logger.error(f"Error in cleanup_expired_links task: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

    finally:
        db.close()


@celery_app.task(
    name="app.tasks.link_refresh.refresh_single_link",
    base=DatabaseTask,
    bind=True
)
def refresh_single_link(self, link_id: int, user_id: int):
    """
    Refresh a single RD link on demand

    Args:
        link_id: RDLink ID to refresh
        user_id: User ID owning the link

    Returns:
        Task result with refresh status
    """
    db: Session = SessionLocal()
    self._db = db

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.rd_api_token:
            logger.error(f"User {user_id} not found or has no RD token")
            return {"status": "error", "error": "User not found or no RD token"}

        # Create link cache manager
        link_manager = LinkCacheManager(db, user.rd_api_token)

        # Get the link
        from app.models.rd_link import RDLink
        rd_link = db.query(RDLink).filter(RDLink.id == link_id).first()

        if not rd_link:
            logger.error(f"Link {link_id} not found")
            return {"status": "error", "error": "Link not found"}

        # Refresh the link
        refreshed_link = link_manager.refresh_link(rd_link)

        if refreshed_link:
            logger.info(f"Successfully refreshed link {link_id}")
            return {
                "status": "success",
                "link_id": link_id,
                "new_expiry": refreshed_link.expires_at.isoformat()
            }
        else:
            logger.error(f"Failed to refresh link {link_id}")
            return {"status": "error", "error": "Refresh failed"}

    except Exception as e:
        logger.error(f"Error in refresh_single_link task: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

    finally:
        db.close()


@celery_app.task(
    name="app.tasks.link_refresh.get_link_statistics",
    base=DatabaseTask,
    bind=True
)
def get_link_statistics(self, user_id: int):
    """
    Get link cache statistics for a user

    Args:
        user_id: User ID

    Returns:
        Link statistics dictionary
    """
    db: Session = SessionLocal()
    self._db = db

    try:
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.rd_api_token:
            return {"status": "error", "error": "User not found or no RD token"}

        # Create link cache manager
        link_manager = LinkCacheManager(db, user.rd_api_token)

        # Get statistics
        stats = link_manager.get_link_statistics()

        return {
            "status": "success",
            "statistics": stats
        }

    except Exception as e:
        logger.error(f"Error in get_link_statistics task: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

    finally:
        db.close()
