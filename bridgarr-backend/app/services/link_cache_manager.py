"""
Link Cache Manager
Manages Real-Debrid streaming link caching, refresh, and expiration
"""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.rd_link import RDLink
from app.models.rd_torrent import RDTorrent
from app.models.media import MediaItem
from app.services.debrid import RealDebridClient

logger = logging.getLogger(__name__)


class LinkCacheManager:
    """
    Service for managing RD link cache lifecycle

    Responsibilities:
    - Refresh expiring links
    - Invalidate expired links
    - Generate new streaming URLs
    - Clean up old/invalid links
    """

    # RD links typically expire in 4 hours
    LINK_EXPIRATION_HOURS = 4

    # Refresh links when they have less than this time remaining
    REFRESH_THRESHOLD_MINUTES = 30

    def __init__(self, db: Session, rd_api_token: str):
        """
        Initialize link cache manager

        Args:
            db: SQLAlchemy database session
            rd_api_token: User's Real-Debrid API token
        """
        self.db = db
        self.rd_client = RealDebridClient(rd_api_token)

    def get_valid_link(
        self,
        media_item_id: int,
        episode_id: Optional[int] = None
    ) -> Optional[RDLink]:
        """
        Get a valid streaming link for media item or episode

        If link is expiring soon, automatically refreshes it

        Args:
            media_item_id: MediaItem ID
            episode_id: Optional Episode ID for TV shows

        Returns:
            Valid RDLink or None if not available
        """
        # Find most recent valid link
        query = self.db.query(RDLink).join(RDTorrent).filter(
            RDTorrent.media_item_id == media_item_id,
            RDLink.is_valid == True,
            RDLink.expires_at > datetime.utcnow()
        )

        if episode_id:
            query = query.filter(RDLink.episode_id == episode_id)
        else:
            query = query.filter(RDLink.episode_id.is_(None))

        rd_link = query.order_by(RDLink.created_at.desc()).first()

        if not rd_link:
            logger.info(f"No valid link found for media {media_item_id}, episode {episode_id}")
            return None

        # Check if link needs refresh
        time_until_expiry = rd_link.expires_at - datetime.utcnow()
        if time_until_expiry.total_seconds() < (self.REFRESH_THRESHOLD_MINUTES * 60):
            logger.info(f"Link expiring soon, refreshing: {rd_link.id}")
            refreshed = self.refresh_link(rd_link)
            return refreshed if refreshed else rd_link

        return rd_link

    def refresh_link(self, rd_link: RDLink) -> Optional[RDLink]:
        """
        Refresh an expiring or expired RD streaming link

        Args:
            rd_link: RDLink to refresh

        Returns:
            Refreshed RDLink or None if failed
        """
        try:
            # Get the RD torrent to find original download link
            rd_torrent = self.db.query(RDTorrent).filter(
                RDTorrent.id == rd_link.rd_torrent_id
            ).first()

            if not rd_torrent:
                logger.error(f"RD torrent not found for link {rd_link.id}")
                return None

            # Try to refresh the link using RD API
            # Note: We need to get torrent info and unrestrict the link again
            torrent_info = self.rd_client.get_torrent_info(rd_torrent.rd_torrent_id)

            if torrent_info.get("status") != "downloaded":
                logger.error(f"Torrent {rd_torrent.rd_torrent_id} is not downloaded")
                return None

            links = torrent_info.get("links", [])
            if not links:
                logger.error(f"No links found for torrent {rd_torrent.rd_torrent_id}")
                return None

            # Unrestrict the first link to get new streaming URL
            # TODO: Match the original file if multiple files exist
            unrestrict_result = self.rd_client.unrestrict_link(links[0])
            new_streaming_url = unrestrict_result.get("download")

            if not new_streaming_url:
                logger.error("Failed to get new streaming URL")
                return None

            # Update existing link
            rd_link.streaming_url = new_streaming_url
            rd_link.expires_at = datetime.utcnow() + timedelta(hours=self.LINK_EXPIRATION_HOURS)
            rd_link.is_valid = True
            rd_link.updated_at = datetime.utcnow()

            self.db.commit()
            self.db.refresh(rd_link)

            logger.info(f"Successfully refreshed link {rd_link.id}")
            return rd_link

        except Exception as e:
            logger.error(f"Error refreshing link {rd_link.id}: {str(e)}")
            self.db.rollback()
            return None

    def invalidate_expired_links(self) -> int:
        """
        Mark all expired links as invalid

        Returns:
            Number of links invalidated
        """
        try:
            expired_links = self.db.query(RDLink).filter(
                and_(
                    RDLink.is_valid == True,
                    RDLink.expires_at <= datetime.utcnow()
                )
            ).all()

            count = 0
            for link in expired_links:
                link.is_valid = False
                count += 1

            self.db.commit()

            if count > 0:
                logger.info(f"Invalidated {count} expired links")

            return count

        except Exception as e:
            logger.error(f"Error invalidating expired links: {str(e)}")
            self.db.rollback()
            return 0

    def refresh_expiring_links(self) -> int:
        """
        Refresh all links that are expiring soon

        Returns:
            Number of links successfully refreshed
        """
        try:
            # Find links expiring within threshold
            threshold_time = datetime.utcnow() + timedelta(
                minutes=self.REFRESH_THRESHOLD_MINUTES
            )

            expiring_links = self.db.query(RDLink).filter(
                and_(
                    RDLink.is_valid == True,
                    RDLink.expires_at <= threshold_time,
                    RDLink.expires_at > datetime.utcnow()
                )
            ).all()

            count = 0
            for link in expiring_links:
                if self.refresh_link(link):
                    count += 1

            logger.info(f"Refreshed {count} expiring links")
            return count

        except Exception as e:
            logger.error(f"Error refreshing expiring links: {str(e)}")
            return 0

    def cleanup_old_links(self, days_old: int = 7) -> int:
        """
        Delete old invalid links to keep database clean

        Args:
            days_old: Delete links older than this many days

        Returns:
            Number of links deleted
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            old_links = self.db.query(RDLink).filter(
                and_(
                    RDLink.is_valid == False,
                    RDLink.created_at < cutoff_date
                )
            ).all()

            count = 0
            for link in old_links:
                self.db.delete(link)
                count += 1

            self.db.commit()

            if count > 0:
                logger.info(f"Cleaned up {count} old invalid links")

            return count

        except Exception as e:
            logger.error(f"Error cleaning up old links: {str(e)}")
            self.db.rollback()
            return 0

    def get_link_statistics(self) -> dict:
        """
        Get statistics about cached links

        Returns:
            Dictionary with link statistics
        """
        try:
            total_links = self.db.query(RDLink).count()
            valid_links = self.db.query(RDLink).filter(
                and_(
                    RDLink.is_valid == True,
                    RDLink.expires_at > datetime.utcnow()
                )
            ).count()

            expired_links = self.db.query(RDLink).filter(
                and_(
                    RDLink.is_valid == True,
                    RDLink.expires_at <= datetime.utcnow()
                )
            ).count()

            threshold_time = datetime.utcnow() + timedelta(
                minutes=self.REFRESH_THRESHOLD_MINUTES
            )
            expiring_soon = self.db.query(RDLink).filter(
                and_(
                    RDLink.is_valid == True,
                    RDLink.expires_at <= threshold_time,
                    RDLink.expires_at > datetime.utcnow()
                )
            ).count()

            return {
                "total_links": total_links,
                "valid_links": valid_links,
                "expired_links": expired_links,
                "expiring_soon": expiring_soon,
                "invalid_links": total_links - valid_links
            }

        except Exception as e:
            logger.error(f"Error getting link statistics: {str(e)}")
            return {}

    def create_link_from_magnet(
        self,
        media_item_id: int,
        magnet_link: str,
        episode_id: Optional[int] = None,
        quality: str = "1080p"
    ) -> Optional[RDLink]:
        """
        Create new RD link from magnet link

        Args:
            media_item_id: MediaItem ID
            magnet_link: Magnet URI
            episode_id: Optional Episode ID for TV shows
            quality: Video quality label

        Returns:
            Created RDLink or None if failed
        """
        try:
            # Process torrent and get streaming URL
            streaming_url = self.rd_client.process_torrent_for_content(magnet_link)

            if not streaming_url:
                logger.error("Failed to get streaming URL from RD")
                return None

            # Get or create RDTorrent entry
            rd_torrent = self.db.query(RDTorrent).filter(
                RDTorrent.magnet_link == magnet_link
            ).first()

            if not rd_torrent:
                rd_torrent = RDTorrent(
                    media_item_id=media_item_id,
                    rd_torrent_id=f"temp_{datetime.utcnow().timestamp()}",
                    magnet_link=magnet_link,
                    status="downloaded",
                    torrent_name=f"Torrent for media {media_item_id}"
                )
                self.db.add(rd_torrent)
                self.db.commit()
                self.db.refresh(rd_torrent)

            # Create RDLink
            rd_link = RDLink(
                rd_torrent_id=rd_torrent.id,
                episode_id=episode_id,
                streaming_url=streaming_url,
                quality=quality,
                is_valid=True,
                expires_at=datetime.utcnow() + timedelta(hours=self.LINK_EXPIRATION_HOURS)
            )
            self.db.add(rd_link)
            self.db.commit()
            self.db.refresh(rd_link)

            # Update media availability
            media_item = self.db.query(MediaItem).filter(
                MediaItem.id == media_item_id
            ).first()
            if media_item:
                media_item.is_available = True
                self.db.commit()

            logger.info(f"Created new RD link for media {media_item_id}")
            return rd_link

        except Exception as e:
            logger.error(f"Error creating link from magnet: {str(e)}")
            self.db.rollback()
            return None
