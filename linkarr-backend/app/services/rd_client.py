"""
Real-Debrid API Client
Handles all interactions with Real-Debrid API for torrent management and link generation
"""

import requests
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RealDebridAPIError(Exception):
    """Custom exception for Real-Debrid API errors"""
    pass


class RealDebridClient:
    """
    Real-Debrid API client for torrent and link management

    API Documentation: https://api.real-debrid.com/
    """

    BASE_URL = "https://api.real-debrid.com/rest/1.0"

    def __init__(self, api_token: str):
        """
        Initialize RD client with API token

        Args:
            api_token: User's Real-Debrid API token
        """
        self.api_token = api_token
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "User-Agent": "Linkarr/1.0"
        })

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated request to RD API

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: URL query parameters

        Returns:
            JSON response as dictionary

        Raises:
            RealDebridAPIError: If API request fails
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

            # Some endpoints return empty response
            if response.status_code == 204:
                return {}

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"RD API request failed: {str(e)}")
            raise RealDebridAPIError(f"Real-Debrid API error: {str(e)}")

    def validate_token(self) -> bool:
        """
        Validate API token by fetching user info

        Returns:
            True if token is valid, False otherwise
        """
        try:
            user_info = self._make_request("GET", "user")
            return user_info.get("type") == "premium"
        except RealDebridAPIError:
            return False

    def get_user_info(self) -> Dict[str, Any]:
        """
        Get current user information

        Returns:
            User info including username, email, premium status, expiration
        """
        return self._make_request("GET", "user")

    def add_magnet(self, magnet_link: str) -> Dict[str, Any]:
        """
        Add magnet link to Real-Debrid

        Args:
            magnet_link: Magnet URI

        Returns:
            Torrent info with id and uri
        """
        data = {"magnet": magnet_link}
        return self._make_request("POST", "torrents/addMagnet", data=data)

    def get_torrent_info(self, torrent_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a torrent

        Args:
            torrent_id: RD torrent ID

        Returns:
            Torrent info including status, files, progress
        """
        return self._make_request("GET", f"torrents/info/{torrent_id}")

    def select_files(self, torrent_id: str, file_ids: List[int]) -> None:
        """
        Select files to download from torrent

        Args:
            torrent_id: RD torrent ID
            file_ids: List of file IDs to select (use "all" for all files)
        """
        # Convert file IDs to comma-separated string
        file_ids_str = ",".join(map(str, file_ids)) if file_ids else "all"
        data = {"files": file_ids_str}
        self._make_request("POST", f"torrents/selectFiles/{torrent_id}", data=data)

    def get_torrent_instant_availability(self, info_hash: str) -> Dict[str, Any]:
        """
        Check if torrent is instantly available (cached) on RD servers

        Args:
            info_hash: Torrent info hash

        Returns:
            Availability info with cached files
        """
        endpoint = f"torrents/instantAvailability/{info_hash}"
        return self._make_request("GET", endpoint)

    def unrestrict_link(self, link: str) -> Dict[str, Any]:
        """
        Generate direct download/streaming link from RD torrent file

        Args:
            link: RD download link from torrent file

        Returns:
            Unrestricted link info with download URL, filename, filesize, etc.
        """
        data = {"link": link}
        return self._make_request("POST", "unrestrict/link", data=data)

    def delete_torrent(self, torrent_id: str) -> None:
        """
        Delete torrent from RD account

        Args:
            torrent_id: RD torrent ID
        """
        self._make_request("DELETE", f"torrents/delete/{torrent_id}")

    def get_torrents(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get list of user's torrents

        Args:
            limit: Max number of torrents to return
            offset: Pagination offset

        Returns:
            List of torrent info dictionaries
        """
        params = {"limit": limit, "offset": offset}
        return self._make_request("GET", "torrents", params=params)

    def get_available_hosts(self) -> List[str]:
        """
        Get list of supported hosts for link unrestriction

        Returns:
            List of supported host domains
        """
        response = self._make_request("GET", "hosts/domains")
        return response

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
        try:
            # Add magnet
            add_result = self.add_magnet(magnet_link)
            torrent_id = add_result.get("id")

            if not torrent_id:
                logger.error("Failed to get torrent ID from add_magnet response")
                return None

            # Get torrent info to find files
            torrent_info = self.get_torrent_info(str(torrent_id))
            files = torrent_info.get("files", [])

            if not files:
                logger.error(f"No files found in torrent {torrent_id}")
                return None

            # Select files
            if select_largest:
                # Find largest file (usually the main video)
                largest_file = max(files, key=lambda f: f.get("bytes", 0))
                file_ids = [largest_file["id"]]
            else:
                # Select all files
                file_ids = [f["id"] for f in files]

            self.select_files(str(torrent_id), file_ids)

            # Wait for torrent to be ready (poll status)
            import time
            max_attempts = 30
            for attempt in range(max_attempts):
                torrent_info = self.get_torrent_info(str(torrent_id))
                status = torrent_info.get("status")

                if status == "downloaded":
                    # Torrent is ready, get download link
                    links = torrent_info.get("links", [])
                    if links:
                        # Unrestrict first link
                        unrestrict_result = self.unrestrict_link(links[0])
                        streaming_url = unrestrict_result.get("download")
                        return streaming_url
                    else:
                        logger.error(f"No links found for torrent {torrent_id}")
                        return None

                elif status in ["error", "virus", "dead"]:
                    logger.error(f"Torrent {torrent_id} failed with status: {status}")
                    return None

                # Wait before next poll
                time.sleep(2)

            logger.error(f"Torrent {torrent_id} did not complete in time")
            return None

        except RealDebridAPIError as e:
            logger.error(f"RD API error processing torrent: {str(e)}")
            return None

    def refresh_link(self, original_link: str) -> Optional[str]:
        """
        Refresh an expired RD streaming link

        Args:
            original_link: Original RD download link

        Returns:
            New streaming URL if successful, None if failed
        """
        try:
            unrestrict_result = self.unrestrict_link(original_link)
            return unrestrict_result.get("download")
        except RealDebridAPIError as e:
            logger.error(f"Failed to refresh link: {str(e)}")
            return None
