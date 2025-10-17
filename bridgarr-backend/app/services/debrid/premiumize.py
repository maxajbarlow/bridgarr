"""
Premiumize API Client
Handles all interactions with Premiumize API for torrent management and link generation

API Documentation: https://www.premiumize.me/static/api/torrent.html
"""

import requests
from typing import Optional, Dict, List, Any
import logging
import time
from .base import BaseDebridClient, DebridServiceError, TorrentStatus

logger = logging.getLogger(__name__)


class PremiumizeAPIError(DebridServiceError):
    """Custom exception for Premiumize API errors"""
    pass


class PremiumizeClient(BaseDebridClient):
    """
    Premiumize API client for torrent and link management

    API Documentation: https://www.premiumize.me/static/api/torrent.html
    """

    BASE_URL = "https://www.premiumize.me/api"

    def __init__(self, api_token: str):
        """
        Initialize Premiumize client with API token

        Args:
            api_token: User's Premiumize API token (customer_id:pin format or just API key)
        """
        super().__init__(api_token)
        self.session = requests.Session()

        # Parse customer_id and pin if provided in format "customer_id:pin"
        if ":" in api_token:
            self.customer_id, self.pin = api_token.split(":", 1)
        else:
            # Assume it's just an API key
            self.customer_id = api_token
            self.pin = None

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Premiumize API

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path
            data: Request body data
            params: URL query parameters

        Returns:
            JSON response as dictionary

        Raises:
            PremiumizeAPIError: If API request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"

        # Add authentication to request
        auth_data = {"apikey": self.customer_id} if not self.pin else {
            "customer_id": self.customer_id,
            "pin": self.pin
        }

        if data:
            data.update(auth_data)
        elif method == "POST":
            data = auth_data
        else:
            if not params:
                params = {}
            params.update(auth_data)

        try:
            response = self.session.request(
                method=method,
                url=url,
                data=data if method == "POST" else None,
                params=params if method == "GET" else None,
                timeout=30
            )

            response.raise_for_status()

            result = response.json()

            # Premiumize returns {"status": "success", ...} or {"status": "error", "message": "..."}
            if result.get("status") == "error":
                error_msg = result.get("message", "Unknown error")
                raise PremiumizeAPIError(f"Premiumize API error: {error_msg}")

            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Premiumize API request failed: {str(e)}")
            raise PremiumizeAPIError(f"Premiumize API error: {str(e)}")

    def validate_token(self) -> bool:
        """
        Validate API token by fetching account info

        Returns:
            True if token is valid and account is premium
        """
        try:
            user_info = self.get_user_info()
            return user_info.get("premium_until", 0) > time.time()
        except PremiumizeAPIError:
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information

        Returns:
            User info including premium status
        """
        return self._make_request("GET", "account/info")

    def add_magnet(self, magnet_link: str) -> Dict[str, Any]:
        """
        Add magnet link to Premiumize

        Args:
            magnet_link: Magnet URI

        Returns:
            Transfer info with id
        """
        data = {"src": magnet_link}
        result = self._make_request("POST", "transfer/create", data=data)

        # Returns {"status": "success", "id": "...", "name": "...", "type": "torrent"}
        return {
            "id": result.get("id"),
            "name": result.get("name"),
            "type": result.get("type")
        }

    def get_torrent_info(self, torrent_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a transfer

        Args:
            torrent_id: Premiumize transfer ID

        Returns:
            Transfer info including status, files, progress
        """
        result = self._make_request("GET", "transfer/list")

        # Find the specific transfer
        transfers = result.get("transfers", [])
        for transfer in transfers:
            if transfer.get("id") == torrent_id:
                return transfer

        raise PremiumizeAPIError(f"Transfer {torrent_id} not found")

    def select_files(self, torrent_id: str, file_ids: List[int]) -> None:
        """
        Premiumize automatically processes all files, no selection needed
        This method exists for interface compliance

        Args:
            torrent_id: Premiumize transfer ID
            file_ids: List of file IDs (ignored)
        """
        # Premiumize doesn't require file selection
        # Files are automatically available once finished
        pass

    def get_instant_availability(self, info_hash: str) -> Dict[str, Any]:
        """
        Check if torrent is cached on Premiumize servers

        Args:
            info_hash: Torrent info hash

        Returns:
            Availability info
        """
        # Premiumize cache check endpoint
        params = {"items[]": info_hash}
        try:
            result = self._make_request("GET", "cache/check", params=params)
            # Returns {"status": "success", "response": [true/false], "transcoded": [...], "filename": [...]}
            return {
                "cached": result.get("response", [False])[0] if result.get("response") else False,
                "files": result.get("filename", [])
            }
        except PremiumizeAPIError:
            return {"cached": False}

    def unrestrict_link(self, link: str) -> Dict[str, Any]:
        """
        Generate direct download/streaming link from Premiumize

        Args:
            link: File link or ID

        Returns:
            Unrestricted link info with download URL
        """
        # Premiumize uses browse endpoint to get direct links
        # The link might be a folder_id from the transfer
        # For simplicity, return the link as-is if it's already a direct link
        return {
            "download": link,
            "filename": "",
            "filesize": 0
        }

    def get_direct_link_from_folder(self, folder_id: str, select_largest: bool = True) -> Optional[str]:
        """
        Get direct download link from a folder

        Args:
            folder_id: Premiumize folder ID
            select_largest: If True, select largest file

        Returns:
            Direct download URL
        """
        try:
            result = self._make_request("GET", "folder/list", params={"id": folder_id})

            # Get content items
            content = result.get("content", [])

            if not content:
                return None

            # Filter for video files
            video_files = [item for item in content if item.get("type") == "file" and
                          item.get("mime_type", "").startswith("video/")]

            if not video_files:
                # No video files, just take first file
                video_files = [item for item in content if item.get("type") == "file"]

            if not video_files:
                return None

            if select_largest:
                selected_file = max(video_files, key=lambda x: x.get("size", 0))
            else:
                selected_file = video_files[0]

            return selected_file.get("link")

        except PremiumizeAPIError as e:
            logger.error(f"Failed to get direct link from folder: {str(e)}")
            return None

    def delete_torrent(self, torrent_id: str) -> None:
        """
        Delete transfer from Premiumize account

        Args:
            torrent_id: Premiumize transfer ID
        """
        data = {"id": torrent_id}
        self._make_request("POST", "transfer/delete", data=data)

    def get_torrents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of user's transfers

        Args:
            limit: Max number to return

        Returns:
            List of transfer info dictionaries
        """
        result = self._make_request("GET", "transfer/list")
        transfers = result.get("transfers", [])
        return transfers[:limit]

    def process_torrent_for_content(
        self,
        magnet_link: str,
        select_largest: bool = True
    ) -> Optional[str]:
        """
        Complete workflow: Add magnet, wait for finish, get streaming URL

        Args:
            magnet_link: Magnet URI to add
            select_largest: If True, automatically select largest file

        Returns:
            Streaming URL if successful, None if failed
        """
        try:
            # Add magnet
            transfer_info = self.add_magnet(magnet_link)
            transfer_id = transfer_info.get("id")

            if not transfer_id:
                logger.error("Failed to get transfer ID from create response")
                return None

            # Wait for transfer to finish
            max_attempts = 60  # Premiumize can take longer
            for attempt in range(max_attempts):
                transfer_info = self.get_torrent_info(transfer_id)
                status = transfer_info.get("status")

                if status == "finished":
                    # Transfer finished, get folder contents
                    folder_id = transfer_info.get("folder_id")

                    if folder_id:
                        return self.get_direct_link_from_folder(folder_id, select_largest)
                    else:
                        logger.error(f"No folder_id for transfer {transfer_id}")
                        return None

                elif status in ["error", "banned", "timeout"]:
                    logger.error(f"Transfer {transfer_id} failed with status: {status}")
                    return None

                # Wait before next poll
                time.sleep(3)

            logger.error(f"Transfer {transfer_id} did not complete in time")
            return None

        except PremiumizeAPIError as e:
            logger.error(f"Premiumize API error processing torrent: {str(e)}")
            return None

    def refresh_link(self, original_link: str) -> Optional[str]:
        """
        Premiumize links don't expire like RD, just return the same link

        Args:
            original_link: Original Premiumize link

        Returns:
            Same link (Premiumize links are permanent)
        """
        return original_link

    def normalize_torrent_status(self, provider_status: str) -> TorrentStatus:
        """
        Convert Premiumize status to standardized status

        Args:
            provider_status: Status string from Premiumize API

        Returns:
            Standardized TorrentStatus enum value
        """
        status_map = {
            "waiting": TorrentStatus.QUEUED,
            "queued": TorrentStatus.QUEUED,
            "running": TorrentStatus.DOWNLOADING,
            "finishing": TorrentStatus.PROCESSING,
            "finished": TorrentStatus.READY,
            "error": TorrentStatus.ERROR,
            "banned": TorrentStatus.ERROR,
            "timeout": TorrentStatus.ERROR,
            "seeding": TorrentStatus.READY,
        }
        return status_map.get(provider_status.lower(), TorrentStatus.ERROR)
