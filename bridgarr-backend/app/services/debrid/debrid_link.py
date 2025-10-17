"""
Debrid-Link API Client
Handles all interactions with Debrid-Link API for torrent management and link generation

API Documentation: https://debrid-link.com/api_doc/v2/introduction
"""

import requests
from typing import Optional, Dict, List, Any
import logging
import time
from .base import BaseDebridClient, DebridServiceError, TorrentStatus

logger = logging.getLogger(__name__)


class DebridLinkAPIError(DebridServiceError):
    """Custom exception for Debrid-Link API errors"""
    pass


class DebridLinkClient(BaseDebridClient):
    """
    Debrid-Link API client for torrent and link management

    API Documentation: https://debrid-link.com/api_doc/v2/introduction
    """

    BASE_URL = "https://debrid-link.fr/api/v2"

    def __init__(self, api_token: str):
        """
        Initialize Debrid-Link client with API token

        Args:
            api_token: User's Debrid-Link API token (OAuth2 access token)
        """
        super().__init__(api_token)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "User-Agent": "Bridgarr/1.0"
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to Debrid-Link API

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: URL query parameters

        Returns:
            JSON response as dictionary

        Raises:
            DebridLinkAPIError: If API request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=30
            )

            response.raise_for_status()

            result = response.json()

            # Debrid-Link returns {"success": true/false, "error": "...", "value": {...}}
            if not result.get("success"):
                error_msg = result.get("error", "Unknown error")
                raise DebridLinkAPIError(f"Debrid-Link API error: {error_msg}")

            return result.get("value", {})

        except requests.exceptions.RequestException as e:
            logger.error(f"Debrid-Link API request failed: {str(e)}")
            raise DebridLinkAPIError(f"Debrid-Link API error: {str(e)}")

    def validate_token(self) -> bool:
        """
        Validate API token by fetching user info

        Returns:
            True if token is valid and account is premium
        """
        try:
            user_info = self.get_user_info()
            return user_info.get("premiumLeft", 0) > 0
        except DebridLinkAPIError:
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information

        Returns:
            User info including premium status
        """
        return self._make_request("GET", "account/infos")

    def add_magnet(self, magnet_link: str) -> Dict[str, Any]:
        """
        Add magnet link to Debrid-Link seedbox

        Args:
            magnet_link: Magnet URI

        Returns:
            Torrent info with id
        """
        data = {"url": magnet_link, "wait": False}
        result = self._make_request("POST", "seedbox/add", data=data)

        # Returns {"id": "...", "name": "...", ...}
        return result

    def get_torrent_info(self, torrent_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a torrent

        Args:
            torrent_id: Debrid-Link torrent ID

        Returns:
            Torrent info including status, files, progress
        """
        result = self._make_request("GET", "seedbox/list")

        # Returns array of torrents
        torrents = result if isinstance(result, list) else []

        for torrent in torrents:
            if torrent.get("id") == torrent_id:
                return torrent

        raise DebridLinkAPIError(f"Torrent {torrent_id} not found")

    def select_files(self, torrent_id: str, file_ids: List[int]) -> None:
        """
        Debrid-Link automatically processes all files, no selection needed
        This method exists for interface compliance

        Args:
            torrent_id: Debrid-Link torrent ID
            file_ids: List of file IDs (ignored)
        """
        # Debrid-Link downloads all files automatically
        pass

    def get_instant_availability(self, info_hash: str) -> Dict[str, Any]:
        """
        Check if torrent is cached on Debrid-Link servers

        Args:
            info_hash: Torrent info hash

        Returns:
            Availability info
        """
        try:
            data = {"url": f"magnet:?xt=urn:btih:{info_hash}"}
            result = self._make_request("POST", "seedbox/cached", data=data)

            # Returns {"cached": true/false}
            return result
        except DebridLinkAPIError:
            return {"cached": False}

    def unrestrict_link(self, link: str) -> Dict[str, Any]:
        """
        Generate direct download/streaming link from Debrid-Link

        Args:
            link: Original link to unrestrict

        Returns:
            Unrestricted link info with download URL
        """
        data = {"link": link}
        result = self._make_request("POST", "downloader/add", data=data)

        # Returns {"id": "...", "url": "...", "filename": "...", ...}
        return {
            "download": result.get("downloadUrl") or result.get("url"),
            "filename": result.get("filename", ""),
            "filesize": result.get("size", 0),
            "id": result.get("id")
        }

    def delete_torrent(self, torrent_id: str) -> None:
        """
        Delete torrent from Debrid-Link seedbox

        Args:
            torrent_id: Debrid-Link torrent ID
        """
        data = {"id": torrent_id}
        self._make_request("DELETE", "seedbox/remove", data=data)

    def get_torrents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of user's torrents

        Args:
            limit: Max number to return

        Returns:
            List of torrent info dictionaries
        """
        result = self._make_request("GET", "seedbox/list")
        torrents = result if isinstance(result, list) else []
        return torrents[:limit]

    def process_torrent_for_content(
        self,
        magnet_link: str,
        select_largest: bool = True
    ) -> Optional[str]:
        """
        Complete workflow: Add magnet, wait for ready, get streaming URL

        Args:
            magnet_link: Magnet URI to add
            select_largest: If True, automatically select largest file

        Returns:
            Streaming URL if successful, None if failed
        """
        try:
            # Add magnet
            torrent_info = self.add_magnet(magnet_link)
            torrent_id = torrent_info.get("id")

            if not torrent_id:
                logger.error("Failed to get torrent ID from add response")
                return None

            # Wait for torrent to finish
            max_attempts = 60
            for attempt in range(max_attempts):
                torrent_info = self.get_torrent_info(torrent_id)
                status = torrent_info.get("status")
                progress = torrent_info.get("downloadPercent", 0)

                # Debrid-Link statuses: 0=waiting, 1=downloading, 2=downloaded, 3=error, 4=virus
                if status == 2 or progress >= 100:
                    # Torrent finished, get files
                    files = torrent_info.get("files", [])

                    if not files:
                        logger.error(f"No files found for torrent {torrent_id}")
                        return None

                    # Filter video files
                    video_files = [f for f in files if f.get("downloadUrl") and
                                 any(f.get("name", "").endswith(ext) for ext in
                                     ['.mp4', '.mkv', '.avi', '.mov', '.webm'])]

                    if not video_files:
                        video_files = files  # Fallback to all files

                    if select_largest:
                        selected_file = max(video_files, key=lambda x: x.get("size", 0))
                    else:
                        selected_file = video_files[0]

                    # Get direct download URL
                    download_url = selected_file.get("downloadUrl")

                    if download_url:
                        return download_url
                    else:
                        logger.error(f"No download URL for file in torrent {torrent_id}")
                        return None

                elif status in [3, 4]:  # Error or virus
                    logger.error(f"Torrent {torrent_id} failed with status: {status}")
                    return None

                # Wait before next poll
                time.sleep(3)

            logger.error(f"Torrent {torrent_id} did not complete in time")
            return None

        except DebridLinkAPIError as e:
            logger.error(f"Debrid-Link API error processing torrent: {str(e)}")
            return None

    def refresh_link(self, original_link: str) -> Optional[str]:
        """
        Refresh an expired Debrid-Link streaming link

        Args:
            original_link: Original download link

        Returns:
            New streaming URL if successful, None if failed
        """
        try:
            # Debrid-Link links may need to be re-unrestricted
            unrestrict_result = self.unrestrict_link(original_link)
            return unrestrict_result.get("download")
        except DebridLinkAPIError as e:
            logger.error(f"Failed to refresh link: {str(e)}")
            return None

    def normalize_torrent_status(self, provider_status: str) -> TorrentStatus:
        """
        Convert Debrid-Link status to standardized status

        Args:
            provider_status: Status code or string from Debrid-Link API

        Returns:
            Standardized TorrentStatus enum value
        """
        # Debrid-Link status codes: 0=waiting, 1=downloading, 2=downloaded, 3=error, 4=virus
        if isinstance(provider_status, int):
            status_code_map = {
                0: TorrentStatus.QUEUED,
                1: TorrentStatus.DOWNLOADING,
                2: TorrentStatus.READY,
                3: TorrentStatus.ERROR,
                4: TorrentStatus.ERROR,
            }
            return status_code_map.get(provider_status, TorrentStatus.ERROR)

        # String status
        status_map = {
            "waiting": TorrentStatus.QUEUED,
            "downloading": TorrentStatus.DOWNLOADING,
            "downloaded": TorrentStatus.READY,
            "error": TorrentStatus.ERROR,
            "virus": TorrentStatus.ERROR,
        }
        return status_map.get(provider_status.lower(), TorrentStatus.ERROR)
