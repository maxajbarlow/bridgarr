"""
Torrentio Scraper

Torrentio is a Strem addon that provides torrent streams
URL: http://torrentio.strem.fun
"""

import requests
from typing import List, Optional
from .base import BaseScraper, TorrentResult


class TorrentioScraper(BaseScraper):
    """Scraper for Torrentio Stremio addon"""

    def __init__(
        self,
        base_url: str = "http://torrentio.strem.fun",
        filter_query: str = "sort=qualitysize|qualityfilter=480p,scr,cam",
        enabled: bool = True,
        timeout: int = 30
    ):
        super().__init__(enabled=enabled, timeout=timeout)
        self.base_url = base_url.rstrip("/")
        self.filter_query = filter_query

    async def search_movie(self, title: str, year: Optional[int] = None, imdb_id: Optional[str] = None) -> List[TorrentResult]:
        """
        Search for movie torrents via Torrentio

        Torrentio uses IMDb ID for lookups
        """
        if not self.enabled:
            print("[Torrentio] Scraper is disabled")
            return []

        if not imdb_id:
            print(f"[Torrentio] No IMDb ID provided for '{title}'")
            return []

        try:
            # Torrentio endpoint format: /{filter}/stream/movie/{imdb_id}.json
            url = f"{self.base_url}/{self.filter_query}/stream/movie/{imdb_id}.json"

            print(f"[Torrentio] Searching movie: {title} ({year}) - IMDb: {imdb_id}")

            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            streams = data.get("streams", [])

            results = []
            for stream in streams:
                result = self._parse_stream(stream, title)
                if result:
                    results.append(result)

            print(f"[Torrentio] Found {len(results)} torrents for '{title}'")
            return results

        except requests.exceptions.RequestException as e:
            print(f"[Torrentio] Error searching '{title}': {str(e)}")
            return []
        except Exception as e:
            print(f"[Torrentio] Unexpected error: {str(e)}")
            return []

    async def search_episode(self, title: str, season: int, episode: int, imdb_id: Optional[str] = None) -> List[TorrentResult]:
        """
        Search for TV episode torrents via Torrentio
        """
        if not self.enabled:
            print("[Torrentio] Scraper is disabled")
            return []

        if not imdb_id:
            print(f"[Torrentio] No IMDb ID provided for '{title}'")
            return []

        try:
            # Torrentio endpoint format: /{filter}/stream/series/{imdb_id}:{season}:{episode}.json
            url = f"{self.base_url}/{self.filter_query}/stream/series/{imdb_id}:{season}:{episode}.json"

            print(f"[Torrentio] Searching episode: {title} S{season:02d}E{episode:02d} - IMDb: {imdb_id}")

            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()
            streams = data.get("streams", [])

            results = []
            for stream in streams:
                result = self._parse_stream(stream, f"{title} S{season:02d}E{episode:02d}")
                if result:
                    results.append(result)

            print(f"[Torrentio] Found {len(results)} torrents for '{title}' S{season:02d}E{episode:02d}")
            return results

        except requests.exceptions.RequestException as e:
            print(f"[Torrentio] Error searching episode: {str(e)}")
            return []
        except Exception as e:
            print(f"[Torrentio] Unexpected error: {str(e)}")
            return []

    def _parse_stream(self, stream: dict, title_context: str) -> Optional[TorrentResult]:
        """
        Parse Torrentio stream object into TorrentResult

        Stream format:
        {
            "name": "1080p\nYTS\n📂 1.80 GB",
            "title": "The Matrix 1999 1080p BluRay x264",
            "infoHash": "abc123...",
            "fileIdx": 0
        }
        """
        try:
            info_hash = stream.get("infoHash")
            if not info_hash:
                return None

            stream_title = stream.get("title", title_context)
            stream_name = stream.get("name", "")

            # Parse quality and size from name field
            # Format: "1080p\nYTS\n📂 1.80 GB"
            lines = stream_name.split("\n")

            quality = lines[0] if len(lines) > 0 else None
            size_str = lines[2] if len(lines) > 2 else "0 GB"

            # Clean size string (remove emoji)
            size_str = size_str.replace("📂", "").strip()

            size_bytes = self._parse_size_mb(size_str)

            return TorrentResult(
                title=stream_title,
                info_hash=info_hash,
                size=size_bytes,
                seeders=None,  # Torrentio doesn't provide seeder info
                quality=quality,
                source="torrentio"
            )

        except Exception as e:
            print(f"[Torrentio] Error parsing stream: {str(e)}")
            return None
