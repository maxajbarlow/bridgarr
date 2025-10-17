"""
AllDebrid API Client
Handles all interactions with AllDebrid API for torrent management and link generation

API Documentation: https://docs.alldebrid.com/
"""

import requests
from typing import Optional, Dict, List, Any
import logging
import time
from .base import BaseDebridClient, DebridServiceError, TorrentStatus

logger = logging.getLogger(__name__)


class AllDebridAPIError(DebridServiceError):
    """Custom exception for AllDebrid API errors"""
    pass


class AllDebridClient(BaseDebridClient):
    """
    AllDebrid API client for torrent and link management

    API Documentation: https://docs.alldebrid.com/
    """

    BASE_URL = "https://api.alldebrid.com/v4"

    def __init__(self, api_token: str):
        """
        Initialize AllDebrid client with API token

        Args:
            api_token: User's AllDebrid API token
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
        Make authenticated request to AllDebrid API

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: URL query parameters

        Returns:
            JSON response as dictionary

        Raises:
            AllDebridAPIError: If API request fails
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

            # AllDebrid returns {"status": "success", "data": {...}}
            if result.get("status") == "error":
                error_msg = result.get("error", {}).get("message", "Unknown error")
                raise AllDebridAPIError(f"AllDebrid API error: {error_msg}")

            return result.get("data", {})

        except requests.exceptions.RequestException as e:
            logger.error(f"AllDebrid API request failed: {str(e)}")
            raise AllDebridAPIError(f"AllDebrid API error: {str(e)}")

    def validate_token(self) -> bool:
        """
        Validate API token by fetching user info

        Returns:
            True if token is valid and account is premium
        """
        try:
            user_info = self.get_user_info()
            return user_info.get("isPremium", False)
        except AllDebridAPIError:
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information

        Returns:
            User info including username, email, premium status
        """
        return self._make_request("GET", "user")

    def add_magnet(self, magnet_link: str) -> Dict[str, Any]:
        """
        Add magnet link to AllDebrid

        Args:
            magnet_link: Magnet URI

        Returns:
            Magnet info with id
        """
        data = {"magnets[]": magnet_link}
        result = self._make_request("POST", "magnet/upload", data=data)

        # AllDebrid returns {"magnets": [{id, name, hash, ...}]}
        magnets = result.get("magnets", [])
        if magnets:
            return magnets[0]

        raise AllDebridAPIError("No magnet returned from upload")

    def get_torrent_info(self, torrent_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a magnet/torrent

        Args:
            torrent_id: AllDebrid magnet ID

        Returns:
            Magnet info including status, files, progress
        """
        result = self._make_request("POST", "magnet/status", data={"id": torrent_id})

        # Returns {"magnets": [{...}]}
        magnets = result.get("magnets", {})
        if torrent_id in magnets:
            return magnets[torrent_id]

        raise AllDebridAPIError(f"Magnet {torrent_id} not found")

    def select_files(self, torrent_id: str, file_ids: List[int]) -> None:
        """
        AllDebrid automatically processes all files, no selection needed
        This method exists for interface compliance

        Args:
            torrent_id: AllDebrid magnet ID
            file_ids: List of file IDs (ignored)
        """
        # AllDebrid doesn't require file selection
        # Files are automatically available once ready
        pass

    def get_instant_availability(self, info_hash: str) -> Dict[str, Any]:
        """
        Check if torrent is cached on AllDebrid servers

        Args:
            info_hash: Torrent info hash

        Returns:
            Availability info
        """
        # AllDebrid uses instant endpoint for cache check
        # Note: This may require different endpoint, documentation not fully clear
        try:
            result = self._make_request("GET", f"magnet/instant/{info_hash}")
            return result
        except AllDebridAPIError:
            return {}

    def unrestrict_link(self, link: str) -> Dict[str, Any]:
        """
        Generate direct download/streaming link from AllDebrid

        Args:
            link: AllDebrid file link

        Returns:
            Unrestricted link info with download URL
        """
        data = {"link": link}
        result = self._make_request("POST", "link/unlock", data=data)

        # Return with standardized keys
        return {
            "download": result.get("link"),
            "filename": result.get("filename"),
            "filesize": result.get("filesize"),
            "host": result.get("host"),
        }

    def delete_torrent(self, torrent_id: str) -> None:
        """
        Delete magnet from AllDebrid account

        Args:
            torrent_id: AllDebrid magnet ID
        """
        self._make_request("POST", "magnet/delete", data={"id": torrent_id})

    def get_torrents(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get list of user's magnets/torrents

        Args:
            limit: Max number to return (AllDebrid doesn't support limit param directly)

        Returns:
            List of magnet info dictionaries
        """
        result = self._make_request("GET", "magnet/status")

        # Returns {"magnets": {id: {...}, ...}}
        magnets_dict = result.get("magnets", {})
        magnets_list = list(magnets_dict.values())

        return magnets_list[:limit]

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
            magnet_info = self.add_magnet(magnet_link)
            magnet_id = str(magnet_info.get("id"))

            if not magnet_id:
                logger.error("Failed to get magnet ID from add_magnet response")
                return None

            # Wait for magnet to be ready
            max_attempts = 30
            for attempt in range(max_attempts):
                magnet_info = self.get_torrent_info(magnet_id)
                status = magnet_info.get("status")
                status_code = magnet_info.get("statusCode")

                # Status codes: 0=queued, 1=processing, 2=compressing, 3=uploading, 4=ready, 5=error, 6=expired
                if status_code == 4 or status == "Ready":
                    # Magnet is ready, get links
                    links = magnet_info.get("links", [])

                    if not links:
                        logger.error(f"No links found for magnet {magnet_id}")
                        return None

                    if select_largest:
                        # Find largest file
                        files = magnet_info.get("files", [])
                        if files:
                            largest_file = max(files, key=lambda f: f.get("size", 0))
                            # Find corresponding link
                            for link_data in links:
                                if link_data.get("filename") == largest_file.get("n"):
                                    # Unrestrict the link
                                    unrestrict_result = self.unrestrict_link(link_data.get("link"))
                                    return unrestrict_result.get("download")

                    # If not found or not select_largest, use first link
                    if links:
                        unrestrict_result = self.unrestrict_link(links[0].get("link"))
                        return unrestrict_result.get("download")

                elif status_code in [5, 6] or status in ["Error", "Expired"]:
                    logger.error(f"Magnet {magnet_id} failed with status: {status}")
                    return None

                # Wait before next poll
                time.sleep(2)

            logger.error(f"Magnet {magnet_id} did not complete in time")
            return None

        except AllDebridAPIError as e:
            logger.error(f"AllDebrid API error processing torrent: {str(e)}")
            return None

    def refresh_link(self, original_link: str) -> Optional[str]:
        """
        Refresh an expired AllDebrid streaming link

        Args:
            original_link: Original AllDebrid link

        Returns:
            New streaming URL if successful, None if failed
        """
        try:
            unrestrict_result = self.unrestrict_link(original_link)
            return unrestrict_result.get("download")
        except AllDebridAPIError as e:
            logger.error(f"Failed to refresh link: {str(e)}")
            return None

    def normalize_torrent_status(self, provider_status: str) -> TorrentStatus:
        """
        Convert AllDebrid status to standardized status

        Args:
            provider_status: Status string or code from AllDebrid API

        Returns:
            Standardized TorrentStatus enum value
        """
        # AllDebrid statusCode: 0=queued, 1=processing, 2=compressing, 3=uploading, 4=ready, 5=error, 6=expired
        if isinstance(provider_status, int):
            status_code_map = {
                0: TorrentStatus.QUEUED,
                1: TorrentStatus.DOWNLOADING,
                2: TorrentStatus.PROCESSING,
                3: TorrentStatus.PROCESSING,
                4: TorrentStatus.READY,
                5: TorrentStatus.ERROR,
                6: TorrentStatus.EXPIRED,
            }
            return status_code_map.get(provider_status, TorrentStatus.ERROR)

        # String status
        status_map = {
            "queued": TorrentStatus.QUEUED,
            "processing": TorrentStatus.DOWNLOADING,
            "compressing": TorrentStatus.PROCESSING,
            "uploading": TorrentStatus.PROCESSING,
            "ready": TorrentStatus.READY,
            "error": TorrentStatus.ERROR,
            "expired": TorrentStatus.EXPIRED,
        }
        return status_map.get(provider_status.lower(), TorrentStatus.ERROR)
