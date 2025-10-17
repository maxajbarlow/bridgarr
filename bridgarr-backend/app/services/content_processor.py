"""
Content Processor

Orchestrates scraping and adding content to Real-Debrid
"""

import asyncio
from typing import List, Optional
from app.services.scrapers import TorrentioScraper, ZileanScraper, TorrentResult
from app.services.rd_client import RealDebridClient


class ContentProcessor:
    """
    Processes media requests by:
    1. Searching multiple torrent scrapers
    2. Ranking/filtering results
    3. Adding best torrent to Real-Debrid
    4. Generating streaming URLs
    """

    def __init__(self, rd_api_token: Optional[str] = None):
        # Initialize scrapers
        self.torrentio = TorrentioScraper(enabled=True)
        self.zilean = ZileanScraper(enabled=True)

        # Initialize Real-Debrid client
        self.rd_client = RealDebridClient(api_token=rd_api_token) if rd_api_token else None

    async def process_movie(
        self,
        title: str,
        year: Optional[int] = None,
        imdb_id: Optional[str] = None,
        tmdb_id: Optional[int] = None
    ) -> dict:
        """
        Process a movie request

        Args:
            title: Movie title
            year: Release year
            imdb_id: IMDb ID
            tmdb_id: TMDb ID

        Returns:
            Dictionary with processing results
        """
        print(f"\n[ContentProcessor] Processing movie: {title} ({year})")
        print(f"[ContentProcessor] IMDb ID: {imdb_id}, TMDb ID: {tmdb_id}")

        # Step 1: Search all scrapers
        all_results = await self._search_all_scrapers_movie(title, year, imdb_id)

        if not all_results:
            print(f"[ContentProcessor] ⚠ No torrents found for '{title}'")
            return {
                "success": False,
                "message": "No torrents found",
                "torrents_found": 0
            }

        print(f"[ContentProcessor] Found {len(all_results)} total torrents")

        # Step 2: Rank and filter results
        best_torrent = self._select_best_torrent(all_results)

        if not best_torrent:
            print(f"[ContentProcessor] ⚠ No suitable torrent after filtering")
            return {
                "success": False,
                "message": "No suitable torrents after filtering",
                "torrents_found": len(all_results)
            }

        print(f"[ContentProcessor] Selected torrent: {best_torrent.title}")
        print(f"[ContentProcessor] Quality: {best_torrent.quality}, Size: {best_torrent.size / (1024**3):.2f} GB")

        # Step 3: Add to Real-Debrid
        if not self.rd_client:
            print(f"[ContentProcessor] ⚠ No Real-Debrid client configured")
            return {
                "success": False,
                "message": "Real-Debrid not configured",
                "torrents_found": len(all_results),
                "selected_torrent": {
                    "title": best_torrent.title,
                    "quality": best_torrent.quality,
                    "size": best_torrent.size,
                    "source": best_torrent.source
                }
            }

        rd_result = await self._add_to_real_debrid(best_torrent)

        return {
            "success": rd_result.get("success", False),
            "message": rd_result.get("message", ""),
            "torrents_found": len(all_results),
            "selected_torrent": {
                "title": best_torrent.title,
                "quality": best_torrent.quality,
                "size": best_torrent.size,
                "source": best_torrent.source,
                "info_hash": best_torrent.info_hash
            },
            "rd_info": rd_result.get("rd_info")
        }

    async def _search_all_scrapers_movie(
        self,
        title: str,
        year: Optional[int],
        imdb_id: Optional[str]
    ) -> List[TorrentResult]:
        """Search all enabled scrapers concurrently"""

        tasks = []

        # Torrentio (requires IMDb ID)
        if imdb_id:
            tasks.append(self.torrentio.search_movie(title, year, imdb_id))

        # Zilean (requires IMDb ID)
        if imdb_id:
            tasks.append(self.zilean.search_movie(title, year, imdb_id))

        # Run all searches concurrently
        if not tasks:
            return []

        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

        # Flatten results
        all_results = []
        for result in results_lists:
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                print(f"[ContentProcessor] Scraper error: {str(result)}")

        return all_results

    def _select_best_torrent(self, torrents: List[TorrentResult]) -> Optional[TorrentResult]:
        """
        Select best torrent based on quality, size, and seeders

        Prioritization:
        1. 1080p preferred
        2. Size between 700MB and 15GB for movies
        3. Higher seeders (if available)
        """
        if not torrents:
            return None

        # Filter by size (700MB - 15GB for movies)
        MIN_SIZE = 700 * 1024 * 1024  # 700 MB
        MAX_SIZE = 15 * 1024 * 1024 * 1024  # 15 GB

        filtered = [
            t for t in torrents
            if MIN_SIZE <= t.size <= MAX_SIZE
        ]

        if not filtered:
            print("[ContentProcessor] No torrents within size range, using all results")
            filtered = torrents

        # Sort by quality preference then seeders
        def quality_score(torrent):
            quality_scores = {
                "2160p": 4,
                "1080p": 3,
                "720p": 2,
                "480p": 1
            }
            q_score = quality_scores.get(torrent.quality, 0)
            seeder_score = torrent.seeders if torrent.seeders else 0
            return (q_score, seeder_score)

        filtered.sort(key=quality_score, reverse=True)

        return filtered[0] if filtered else None

    async def _add_to_real_debrid(self, torrent: TorrentResult) -> dict:
        """Add torrent to Real-Debrid and get download links"""

        try:
            print(f"[ContentProcessor] Adding to Real-Debrid: {torrent.title}")

            # Add magnet to RD - returns {"id": "...", "uri": "..."}
            magnet_result = self.rd_client.add_magnet(torrent.magnet_link)

            torrent_id = magnet_result.get("id")
            if not torrent_id:
                return {
                    "success": False,
                    "message": "Failed to add magnet - no ID returned"
                }

            print(f"[ContentProcessor] ✓ Added to RD with ID: {torrent_id}")

            # Get torrent info to find files
            torrent_info = self.rd_client.get_torrent_info(torrent_id)
            files = torrent_info.get("files", [])

            if not files:
                return {
                    "success": False,
                    "message": "No files found in torrent"
                }

            # Select all files (for movies, usually just one)
            file_ids = [f["id"] for f in files]
            self.rd_client.select_files(torrent_id, file_ids)

            print(f"[ContentProcessor] ✓ Selected {len(file_ids)} files for download")

            # Get updated torrent info
            updated_info = self.rd_client.get_torrent_info(torrent_id)

            return {
                "success": True,
                "message": "Added to Real-Debrid successfully",
                "rd_info": {
                    "id": torrent_id,
                    "status": updated_info.get("status"),
                    "filename": updated_info.get("filename"),
                    "progress": updated_info.get("progress", 0)
                }
            }

        except Exception as e:
            print(f"[ContentProcessor] ✗ Error adding to RD: {str(e)}")
            return {
                "success": False,
                "message": f"Real-Debrid error: {str(e)}"
            }
