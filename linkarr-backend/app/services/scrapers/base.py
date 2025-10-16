"""
Base Scraper Class and Data Models
"""

from dataclasses import dataclass
from typing import Optional, List
from abc import ABC, abstractmethod


@dataclass
class TorrentResult:
    """Torrent search result"""

    title: str
    info_hash: str
    size: int  # in bytes
    seeders: Optional[int] = None
    quality: Optional[str] = None  # 1080p, 720p, etc.
    source: Optional[str] = None  # scraper name
    magnet_link: Optional[str] = None

    def __post_init__(self):
        """Generate magnet link if not provided"""
        if not self.magnet_link and self.info_hash:
            self.magnet_link = f"magnet:?xt=urn:btih:{self.info_hash}"


class BaseScraper(ABC):
    """Base class for all torrent scrapers"""

    def __init__(self, enabled: bool = True, timeout: int = 30):
        self.enabled = enabled
        self.timeout = timeout

    @abstractmethod
    async def search_movie(self, title: str, year: Optional[int] = None, imdb_id: Optional[str] = None) -> List[TorrentResult]:
        """
        Search for movie torrents

        Args:
            title: Movie title
            year: Release year
            imdb_id: IMDb ID (if available)

        Returns:
            List of torrent results
        """
        pass

    @abstractmethod
    async def search_episode(self, title: str, season: int, episode: int, imdb_id: Optional[str] = None) -> List[TorrentResult]:
        """
        Search for TV episode torrents

        Args:
            title: Show title
            season: Season number
            episode: Episode number
            imdb_id: IMDb ID (if available)

        Returns:
            List of torrent results
        """
        pass

    def _parse_quality(self, title: str) -> Optional[str]:
        """Extract quality from torrent title"""
        title_upper = title.upper()

        if "2160P" in title_upper or "4K" in title_upper:
            return "2160p"
        elif "1080P" in title_upper:
            return "1080p"
        elif "720P" in title_upper:
            return "720p"
        elif "480P" in title_upper:
            return "480p"

        return None

    def _parse_size_mb(self, size_str: str) -> int:
        """
        Parse size string to bytes

        Examples: "1.5 GB", "750 MB", "2.3GB"
        """
        try:
            size_str = size_str.strip().upper()

            # Extract number and unit
            parts = size_str.split()
            if len(parts) == 2:
                value = float(parts[0])
                unit = parts[1]
            else:
                # Try to split number from unit (e.g., "1.5GB")
                import re
                match = re.match(r'([\d.]+)\s*([A-Z]+)', size_str)
                if not match:
                    return 0
                value = float(match.group(1))
                unit = match.group(2)

            # Convert to bytes
            if unit in ["GB", "G"]:
                return int(value * 1024 * 1024 * 1024)
            elif unit in ["MB", "M"]:
                return int(value * 1024 * 1024)
            elif unit in ["KB", "K"]:
                return int(value * 1024)
            else:
                return int(value)

        except Exception:
            return 0
