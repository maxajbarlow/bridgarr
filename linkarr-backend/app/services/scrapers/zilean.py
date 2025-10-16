"""
Zilean Scraper

Zilean is a DMM (Debrid Media Manager) hash database
URL: http://YOUR_SERVER_IP:8181
"""

import requests
from typing import List, Optional
from .base import BaseScraper, TorrentResult


class ZileanScraper(BaseScraper):
    """Scraper for Zilean DMM hash database"""

    def __init__(
        self,
        base_url: str = "http://YOUR_SERVER_IP:8181",
        enabled: bool = True,
        timeout: int = 30
    ):
        super().__init__(enabled=enabled, timeout=timeout)
        self.base_url = base_url.rstrip("/")

    async def search_movie(self, title: str, year: Optional[int] = None, imdb_id: Optional[str] = None) -> List[TorrentResult]:
        """
        Search for movie torrents via Zilean

        Zilean searches by IMDb ID
        """
        if not self.enabled:
            print("[Zilean] Scraper is disabled")
            return []

        if not imdb_id:
            print(f"[Zilean] No IMDb ID provided for '{title}'")
            return []

        try:
            # Zilean DMM API endpoint
            url = f"{self.base_url}/dmm/filtered"

            params = {
                "imdbId": imdb_id
            }

            print(f"[Zilean] Searching movie: {title} ({year}) - IMDb: {imdb_id}")

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            results = []
            for item in data:
                result = self._parse_result(item, title)
                if result:
                    results.append(result)

            print(f"[Zilean] Found {len(results)} torrents for '{title}'")
            return results

        except requests.exceptions.RequestException as e:
            print(f"[Zilean] Error searching '{title}': {str(e)}")
            return []
        except Exception as e:
            print(f"[Zilean] Unexpected error: {str(e)}")
            return []

    async def search_episode(self, title: str, season: int, episode: int, imdb_id: Optional[str] = None) -> List[TorrentResult]:
        """
        Search for TV episode torrents via Zilean
        """
        if not self.enabled:
            print("[Zilean] Scraper is disabled")
            return []

        if not imdb_id:
            print(f"[Zilean] No IMDb ID provided for '{title}'")
            return []

        try:
            url = f"{self.base_url}/dmm/filtered"

            params = {
                "imdbId": imdb_id,
                "season": season,
                "episode": episode
            }

            print(f"[Zilean] Searching episode: {title} S{season:02d}E{episode:02d} - IMDb: {imdb_id}")

            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            results = []
            for item in data:
                result = self._parse_result(item, f"{title} S{season:02d}E{episode:02d}")
                if result:
                    results.append(result)

            print(f"[Zilean] Found {len(results)} torrents for '{title}' S{season:02d}E{episode:02d}")
            return results

        except requests.exceptions.RequestException as e:
            print(f"[Zilean] Error searching episode: {str(e)}")
            return []
        except Exception as e:
            print(f"[Zilean] Unexpected error: {str(e)}")
            return []

    def _parse_result(self, item: dict, title_context: str) -> Optional[TorrentResult]:
        """
        Parse Zilean result into TorrentResult

        Zilean format:
        {
            "info_hash": "abc123...",
            "raw_title": "The Matrix 1999 1080p BluRay x264",
            "size": 1933066240,
            "seeders": 10
        }
        """
        try:
            info_hash = item.get("info_hash") or item.get("infoHash")
            if not info_hash:
                return None

            raw_title = item.get("raw_title") or item.get("rawTitle") or title_context
            size = item.get("size", 0)
            seeders = item.get("seeders")

            quality = self._parse_quality(raw_title)

            return TorrentResult(
                title=raw_title,
                info_hash=info_hash,
                size=size,
                seeders=seeders,
                quality=quality,
                source="zilean"
            )

        except Exception as e:
            print(f"[Zilean] Error parsing result: {str(e)}")
            return None
