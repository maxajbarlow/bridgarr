"""
TMDb Metadata Manager
Fetches and processes movie/TV show metadata from The Movie Database API
"""

import requests
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

from app.config import settings
from app.models.media import MediaType

logger = logging.getLogger(__name__)


class TMDbAPIError(Exception):
    """Custom exception for TMDb API errors"""
    pass


class MetadataManager:
    """
    TMDb API client for fetching movie and TV show metadata

    API Documentation: https://developers.themoviedb.org/3
    """

    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize metadata manager with TMDb API key

        Args:
            api_key: TMDb API key (defaults to settings.TMDB_API_KEY)
        """
        self.api_key = api_key or settings.TMDB_API_KEY
        self.session = requests.Session()

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Make request to TMDb API

        Args:
            endpoint: API endpoint path
            params: Query parameters

        Returns:
            JSON response as dictionary

        Raises:
            TMDbAPIError: If API request fails
        """
        url = f"{self.BASE_URL}/{endpoint}"

        # Add API key to params
        if params is None:
            params = {}
        params["api_key"] = self.api_key

        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"TMDb API request failed: {str(e)}")
            raise TMDbAPIError(f"TMDb API error: {str(e)}")

    def get_movie_details(self, tmdb_id: int) -> Dict[str, Any]:
        """
        Get detailed movie information

        Args:
            tmdb_id: TMDb movie ID

        Returns:
            Movie details including title, overview, images, etc.
        """
        endpoint = f"movie/{tmdb_id}"
        params = {"append_to_response": "credits,videos,external_ids"}
        return self._make_request(endpoint, params)

    def get_tv_show_details(self, tmdb_id: int) -> Dict[str, Any]:
        """
        Get detailed TV show information

        Args:
            tmdb_id: TMDb TV show ID

        Returns:
            TV show details including name, overview, seasons, etc.
        """
        endpoint = f"tv/{tmdb_id}"
        params = {"append_to_response": "credits,videos,external_ids"}
        return self._make_request(endpoint, params)

    def get_season_details(self, tmdb_id: int, season_number: int) -> Dict[str, Any]:
        """
        Get detailed season information

        Args:
            tmdb_id: TMDb TV show ID
            season_number: Season number

        Returns:
            Season details including episodes, air dates, etc.
        """
        endpoint = f"tv/{tmdb_id}/season/{season_number}"
        return self._make_request(endpoint)

    def search_movies(self, query: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for movies by title

        Args:
            query: Movie title to search
            year: Optional release year filter

        Returns:
            List of movie search results
        """
        params = {"query": query}
        if year:
            params["year"] = year

        response = self._make_request("search/movie", params)
        return response.get("results", [])

    def search_tv_shows(self, query: str, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search for TV shows by name

        Args:
            query: TV show name to search
            year: Optional first air date year filter

        Returns:
            List of TV show search results
        """
        params = {"query": query}
        if year:
            params["first_air_date_year"] = year

        response = self._make_request("search/tv", params)
        return response.get("results", [])

    def get_poster_url(self, poster_path: Optional[str], size: str = "w500") -> Optional[str]:
        """
        Generate full poster URL from path

        Args:
            poster_path: Poster path from TMDb
            size: Image size (w92, w154, w185, w342, w500, w780, original)

        Returns:
            Full poster URL or None
        """
        if not poster_path:
            return None
        return f"{self.IMAGE_BASE_URL}/{size}{poster_path}"

    def get_backdrop_url(self, backdrop_path: Optional[str], size: str = "w1280") -> Optional[str]:
        """
        Generate full backdrop URL from path

        Args:
            backdrop_path: Backdrop path from TMDb
            size: Image size (w300, w780, w1280, original)

        Returns:
            Full backdrop URL or None
        """
        if not backdrop_path:
            return None
        return f"{self.IMAGE_BASE_URL}/{size}{backdrop_path}"

    def get_still_url(self, still_path: Optional[str], size: str = "w300") -> Optional[str]:
        """
        Generate full episode still image URL from path

        Args:
            still_path: Still image path from TMDb
            size: Image size (w92, w185, w300, original)

        Returns:
            Full still image URL or None
        """
        if not still_path:
            return None
        return f"{self.IMAGE_BASE_URL}/{size}{still_path}"

    def extract_imdb_id(self, tmdb_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract IMDb ID from TMDb response

        Args:
            tmdb_data: TMDb API response

        Returns:
            IMDb ID (tt1234567) or None
        """
        external_ids = tmdb_data.get("external_ids", {})
        return external_ids.get("imdb_id")

    def format_runtime(self, minutes: Optional[int]) -> Optional[str]:
        """
        Format runtime in minutes to human-readable string

        Args:
            minutes: Runtime in minutes

        Returns:
            Formatted string (e.g., "2h 30m") or None
        """
        if not minutes:
            return None

        hours = minutes // 60
        mins = minutes % 60

        if hours > 0:
            return f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
        else:
            return f"{mins}m"

    def extract_genres(self, tmdb_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract and format genres from TMDb data

        Args:
            tmdb_data: TMDb API response

        Returns:
            Comma-separated genre string or None
        """
        genres = tmdb_data.get("genres", [])
        if not genres:
            return None

        genre_names = [g["name"] for g in genres]
        return ", ".join(genre_names)

    def parse_release_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parse and validate release date

        Args:
            date_str: Date string from TMDb (YYYY-MM-DD)

        Returns:
            Validated date string or None
        """
        if not date_str:
            return None

        try:
            # Validate date format
            datetime.strptime(date_str, "%Y-%m-%d")
            return date_str
        except ValueError:
            logger.warning(f"Invalid date format: {date_str}")
            return None

    def get_content_rating(self, tmdb_data: Dict[str, Any], media_type: MediaType) -> Optional[str]:
        """
        Extract content rating (PG, PG-13, R, etc.)

        Args:
            tmdb_data: TMDb API response
            media_type: MOVIE or TV_SHOW

        Returns:
            Content rating or None
        """
        if media_type == MediaType.MOVIE:
            # For movies, use release_dates
            release_dates = tmdb_data.get("release_dates", {}).get("results", [])
            for country_data in release_dates:
                if country_data.get("iso_3166_1") == "US":
                    releases = country_data.get("release_dates", [])
                    if releases:
                        return releases[0].get("certification")
        else:
            # For TV shows, use content_ratings
            content_ratings = tmdb_data.get("content_ratings", {}).get("results", [])
            for rating in content_ratings:
                if rating.get("iso_3166_1") == "US":
                    return rating.get("rating")

        return None

    def enrich_media_item(self, media_data: Dict[str, Any], media_type: MediaType) -> Dict[str, Any]:
        """
        Enrich media data with formatted fields ready for database

        Args:
            media_data: Raw TMDb API response
            media_type: MOVIE or TV_SHOW

        Returns:
            Enriched data dictionary with all fields formatted
        """
        is_movie = media_type == MediaType.MOVIE

        enriched = {
            "tmdb_id": media_data["id"],
            "imdb_id": self.extract_imdb_id(media_data),
            "title": media_data.get("title" if is_movie else "name"),
            "media_type": media_type,
            "overview": media_data.get("overview"),
            "release_date": self.parse_release_date(
                media_data.get("release_date" if is_movie else "first_air_date")
            ),
            "poster_path": media_data.get("poster_path"),
            "backdrop_path": media_data.get("backdrop_path"),
            "vote_average": media_data.get("vote_average"),
            "vote_count": media_data.get("vote_count"),
            "runtime": media_data.get("runtime") if is_movie else media_data.get("episode_run_time", [None])[0],
            "genres": self.extract_genres(media_data),
            "is_available": False  # Will be updated when RD link is added
        }

        return enriched
