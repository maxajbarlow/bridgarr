"""
Content Manager
High-level service for adding and managing media content with torrent search and RD integration
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.media import MediaItem, Season, Episode, MediaType
from app.models.rd_torrent import RDTorrent
from app.models.rd_link import RDLink
from app.services.metadata_manager import MetadataManager
from app.services.rd_client import RealDebridClient

logger = logging.getLogger(__name__)


class ContentManager:
    """
    High-level service for content management

    Orchestrates:
    - Metadata fetching from TMDb
    - Torrent searching (placeholder for now)
    - Real-Debrid integration
    - Database updates
    """

    def __init__(self, db: Session, rd_api_token: str):
        """
        Initialize content manager

        Args:
            db: SQLAlchemy database session
            rd_api_token: User's Real-Debrid API token
        """
        self.db = db
        self.metadata_manager = MetadataManager()
        self.rd_client = RealDebridClient(rd_api_token)

    def add_movie_from_tmdb(
        self,
        tmdb_id: int,
        magnet_link: Optional[str] = None
    ) -> Optional[MediaItem]:
        """
        Add movie to library from TMDb ID

        Args:
            tmdb_id: TMDb movie ID
            magnet_link: Optional magnet link to add to RD

        Returns:
            Created MediaItem or None if failed
        """
        try:
            # Check if movie already exists
            existing = self.db.query(MediaItem).filter(
                MediaItem.tmdb_id == tmdb_id,
                MediaItem.media_type == MediaType.MOVIE
            ).first()

            if existing:
                logger.info(f"Movie {tmdb_id} already exists in library")
                return existing

            # Fetch metadata from TMDb
            tmdb_data = self.metadata_manager.get_movie_details(tmdb_id)

            # Enrich and format data
            enriched_data = self.metadata_manager.enrich_media_item(
                tmdb_data,
                MediaType.MOVIE
            )

            # Create media item
            media_item = MediaItem(**enriched_data)
            self.db.add(media_item)
            self.db.commit()
            self.db.refresh(media_item)

            logger.info(f"Added movie: {media_item.title} (TMDb ID: {tmdb_id})")

            # If magnet link provided, add to RD
            if magnet_link:
                self._add_magnet_to_rd(media_item, magnet_link)

            return media_item

        except Exception as e:
            logger.error(f"Error adding movie {tmdb_id}: {str(e)}")
            self.db.rollback()
            return None

    def add_tv_show_from_tmdb(
        self,
        tmdb_id: int,
        fetch_all_seasons: bool = True
    ) -> Optional[MediaItem]:
        """
        Add TV show to library from TMDb ID

        Args:
            tmdb_id: TMDb TV show ID
            fetch_all_seasons: Whether to fetch all season/episode metadata

        Returns:
            Created MediaItem or None if failed
        """
        try:
            # Check if show already exists
            existing = self.db.query(MediaItem).filter(
                MediaItem.tmdb_id == tmdb_id,
                MediaItem.media_type == MediaType.TV_SHOW
            ).first()

            if existing:
                logger.info(f"TV show {tmdb_id} already exists in library")
                return existing

            # Fetch metadata from TMDb
            tmdb_data = self.metadata_manager.get_tv_show_details(tmdb_id)

            # Enrich and format data
            enriched_data = self.metadata_manager.enrich_media_item(
                tmdb_data,
                MediaType.TV_SHOW
            )

            # Create media item
            media_item = MediaItem(**enriched_data)
            self.db.add(media_item)
            self.db.commit()
            self.db.refresh(media_item)

            logger.info(f"Added TV show: {media_item.title} (TMDb ID: {tmdb_id})")

            # Fetch seasons and episodes if requested
            if fetch_all_seasons:
                self._fetch_seasons_and_episodes(media_item, tmdb_data)

            return media_item

        except Exception as e:
            logger.error(f"Error adding TV show {tmdb_id}: {str(e)}")
            self.db.rollback()
            return None

    def _fetch_seasons_and_episodes(
        self,
        media_item: MediaItem,
        tv_show_data: Dict[str, Any]
    ) -> None:
        """
        Fetch and create all seasons and episodes for TV show

        Args:
            media_item: TV show MediaItem
            tv_show_data: TMDb TV show details
        """
        seasons_data = tv_show_data.get("seasons", [])

        for season_data in seasons_data:
            # Skip season 0 (specials) for now
            season_number = season_data.get("season_number", 0)
            if season_number == 0:
                continue

            try:
                # Fetch detailed season info
                detailed_season = self.metadata_manager.get_season_details(
                    media_item.tmdb_id,
                    season_number
                )

                # Create season
                season = Season(
                    media_item_id=media_item.id,
                    season_number=season_number,
                    episode_count=detailed_season.get("episodes", []).__len__(),
                    name=detailed_season.get("name"),
                    overview=detailed_season.get("overview"),
                    poster_path=detailed_season.get("poster_path"),
                    air_date=self.metadata_manager.parse_release_date(
                        detailed_season.get("air_date")
                    )
                )
                self.db.add(season)
                self.db.commit()
                self.db.refresh(season)

                # Create episodes
                episodes_data = detailed_season.get("episodes", [])
                for ep_data in episodes_data:
                    episode = Episode(
                        season_id=season.id,
                        episode_number=ep_data.get("episode_number"),
                        name=ep_data.get("name"),
                        overview=ep_data.get("overview"),
                        still_path=ep_data.get("still_path"),
                        air_date=self.metadata_manager.parse_release_date(
                            ep_data.get("air_date")
                        ),
                        runtime=ep_data.get("runtime")
                    )
                    self.db.add(episode)

                self.db.commit()
                logger.info(f"Added season {season_number} with {len(episodes_data)} episodes")

            except Exception as e:
                logger.error(f"Error fetching season {season_number}: {str(e)}")
                continue

    def _add_magnet_to_rd(
        self,
        media_item: MediaItem,
        magnet_link: str,
        episode_id: Optional[int] = None
    ) -> Optional[RDLink]:
        """
        Add magnet link to Real-Debrid and create RDTorrent/RDLink entries

        Args:
            media_item: MediaItem to associate with
            magnet_link: Magnet URI
            episode_id: Optional episode ID for TV shows

        Returns:
            Created RDLink or None if failed
        """
        try:
            # Process torrent and get streaming URL
            streaming_url = self.rd_client.process_torrent_for_content(magnet_link)

            if not streaming_url:
                logger.error("Failed to get streaming URL from RD")
                return None

            # Create RDTorrent entry
            rd_torrent = RDTorrent(
                media_item_id=media_item.id,
                rd_torrent_id=f"temp_{datetime.utcnow().timestamp()}",  # Will be updated
                magnet_link=magnet_link,
                status="downloaded",
                torrent_name=f"{media_item.title} - RD Torrent"
            )
            self.db.add(rd_torrent)
            self.db.commit()
            self.db.refresh(rd_torrent)

            # Create RDLink entry
            rd_link = RDLink(
                rd_torrent_id=rd_torrent.id,
                episode_id=episode_id,
                streaming_url=streaming_url,
                quality="1080p",  # TODO: Detect quality from filename
                is_valid=True,
                expires_at=datetime.utcnow() + timedelta(hours=4)  # RD links expire in ~4 hours
            )
            self.db.add(rd_link)
            self.db.commit()
            self.db.refresh(rd_link)

            # Update media item availability
            media_item.is_available = True
            self.db.commit()

            logger.info(f"Successfully added RD link for {media_item.title}")
            return rd_link

        except Exception as e:
            logger.error(f"Error adding magnet to RD: {str(e)}")
            self.db.rollback()
            return None

    def search_and_add_movie(
        self,
        tmdb_id: int,
        quality_preference: str = "1080p"
    ) -> Optional[MediaItem]:
        """
        Search for movie torrent and automatically add to RD

        Args:
            tmdb_id: TMDb movie ID
            quality_preference: Preferred quality (1080p, 720p, 2160p)

        Returns:
            MediaItem with RD link added, or None if failed
        """
        # TODO: Implement torrent search integration
        # For now, this is a placeholder that adds the movie without torrent

        logger.warning("Torrent search not yet implemented - adding movie without RD link")
        return self.add_movie_from_tmdb(tmdb_id)

    def update_media_metadata(self, media_item: MediaItem) -> bool:
        """
        Refresh metadata from TMDb for existing media item

        Args:
            media_item: MediaItem to update

        Returns:
            True if successful, False otherwise
        """
        try:
            if media_item.media_type == MediaType.MOVIE:
                tmdb_data = self.metadata_manager.get_movie_details(media_item.tmdb_id)
            else:
                tmdb_data = self.metadata_manager.get_tv_show_details(media_item.tmdb_id)

            # Update fields
            enriched = self.metadata_manager.enrich_media_item(
                tmdb_data,
                media_item.media_type
            )

            for key, value in enriched.items():
                if key not in ["tmdb_id", "media_type", "is_available"]:
                    setattr(media_item, key, value)

            self.db.commit()
            logger.info(f"Updated metadata for {media_item.title}")
            return True

        except Exception as e:
            logger.error(f"Error updating metadata: {str(e)}")
            self.db.rollback()
            return False

    def remove_media_item(self, media_id: int) -> bool:
        """
        Remove media item and all associated data

        Args:
            media_id: MediaItem ID to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            media_item = self.db.query(MediaItem).filter(
                MediaItem.id == media_id
            ).first()

            if not media_item:
                logger.warning(f"Media item {media_id} not found")
                return False

            # Delete associated RD torrents (cascades to RDLinks)
            rd_torrents = self.db.query(RDTorrent).filter(
                RDTorrent.media_item_id == media_id
            ).all()

            for torrent in rd_torrents:
                # Try to delete from RD account
                try:
                    self.rd_client.delete_torrent(torrent.rd_torrent_id)
                except Exception as e:
                    logger.warning(f"Failed to delete RD torrent: {str(e)}")

            # Delete media item (cascades to seasons, episodes, torrents, links)
            self.db.delete(media_item)
            self.db.commit()

            logger.info(f"Removed media item: {media_item.title}")
            return True

        except Exception as e:
            logger.error(f"Error removing media item: {str(e)}")
            self.db.rollback()
            return False
