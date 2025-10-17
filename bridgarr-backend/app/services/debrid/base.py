"""
Base Debrid Provider Interface
Defines the common interface that all debrid service providers must implement
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from enum import Enum


class DebridProvider(str, Enum):
    """Supported debrid service providers"""
    REAL_DEBRID = "real-debrid"
    ALL_DEBRID = "alldebrid"
    PREMIUMIZE = "premiumize"
    DEBRID_LINK = "debrid-link"


class TorrentStatus(str, Enum):
    """Standardized torrent status across all providers"""
    QUEUED = "queued"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    READY = "ready"
    ERROR = "error"
    EXPIRED = "expired"
    DEAD = "dead"


class DebridServiceError(Exception):
    """Base exception for debrid service errors"""
    pass


class BaseDebridClient(ABC):
    """
    Abstract base class for debrid service clients
    All debrid providers must implement this interface
    """

    def __init__(self, api_token: str):
        """
        Initialize debrid client with API token

        Args:
            api_token: User's API token for the debrid service
        """
        self.api_token = api_token

    @abstractmethod
    def validate_token(self) -> bool:
        """
        Validate API token

        Returns:
            True if token is valid and premium account is active
        """
        pass

    @abstractmethod
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information

        Returns:
            Dict with user info (username, email, premium status, expiration)
        """
        pass

    @abstractmethod
    def add_magnet(self, magnet_link: str) -> Dict[str, Any]:
        """
        Add magnet link to debrid service

        Args:
            magnet_link: Magnet URI

        Returns:
            Dict with torrent info (id, status, etc.)
        """
        pass

    @abstractmethod
    def get_torrent_info(self, torrent_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a torrent

        Args:
            torrent_id: Provider's torrent ID

        Returns:
            Dict with torrent info (status, files, progress, etc.)
        """
        pass

    @abstractmethod
    def select_files(self, torrent_id: str, file_ids: List[int]) -> None:
        """
        Select specific files to download from torrent

        Args:
            torrent_id: Provider's torrent ID
            file_ids: List of file IDs to select
        """
        pass

    @abstractmethod
    def get_instant_availability(self, info_hash: str) -> Dict[str, Any]:
        """
        Check if torrent is cached/instantly available

        Args:
            info_hash: Torrent info hash

        Returns:
            Dict with availability info
        """
        pass

    @abstractmethod
    def unrestrict_link(self, link: str) -> Dict[str, Any]:
        """
        Generate direct download/streaming link

        Args:
            link: Original link to unrestrict

        Returns:
            Dict with unrestricted link info (download_url, filename, size)
        """
        pass

    @abstractmethod
    def delete_torrent(self, torrent_id: str) -> None:
        """
        Delete torrent from account

        Args:
            torrent_id: Provider's torrent ID
        """
        pass

    @abstractmethod
    def get_torrents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of user's torrents

        Args:
            limit: Max number of torrents to return

        Returns:
            List of torrent info dicts
        """
        pass

    @abstractmethod
    def process_torrent_for_content(
        self,
        magnet_link: str,
        select_largest: bool = True
    ) -> Optional[str]:
        """
        Complete workflow: Add magnet, select files, get streaming URL

        Args:
            magnet_link: Magnet URI to add
            select_largest: If True, automatically select largest file

        Returns:
            Streaming URL if successful, None if failed
        """
        pass

    @abstractmethod
    def refresh_link(self, original_link: str) -> Optional[str]:
        """
        Refresh an expired streaming link

        Args:
            original_link: Original download link

        Returns:
            New streaming URL if successful, None if failed
        """
        pass

    @abstractmethod
    def normalize_torrent_status(self, provider_status: str) -> TorrentStatus:
        """
        Convert provider-specific status to standardized status

        Args:
            provider_status: Status string from provider API

        Returns:
            Standardized TorrentStatus enum value
        """
        pass
