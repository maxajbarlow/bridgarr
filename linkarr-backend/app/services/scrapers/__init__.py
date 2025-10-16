"""
Torrent Scraper Services

Scrapers for finding torrents from various sources
"""

from .torrentio import TorrentioScraper
from .zilean import ZileanScraper
from .base import TorrentResult

__all__ = ["TorrentioScraper", "ZileanScraper", "TorrentResult"]
