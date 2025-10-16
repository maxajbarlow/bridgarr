"""
TMDb (The Movie Database) API Service

Handles fetching movie and TV show metadata from TMDb API
"""

import requests
from typing import Optional, Dict, Any
from datetime import datetime

from app.config import settings


class TMDbService:
    """Service for interacting with TMDb API"""

    BASE_URL = "https://api.themoviedb.org/3"
    IMAGE_BASE_URL = "https://image.tmdb.org/t/p"

    def __init__(self):
        self.api_key = settings.TMDB_API_KEY

    def get_movie_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch movie details from TMDb API

        Args:
            tmdb_id: TMDb movie ID

        Returns:
            Dictionary with movie metadata or None if failed
        """
        if not self.api_key or self.api_key == "YOUR_TMDB_API_KEY_HERE":
            print("[TMDb] API key not configured!")
            return None

        try:
            url = f"{self.BASE_URL}/movie/{tmdb_id}"
            params = {
                "api_key": self.api_key,
                "append_to_response": "credits,videos,release_dates"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract and format the data
            movie_data = {
                "tmdb_id": data.get("id"),
                "title": data.get("title"),
                "original_title": data.get("original_title"),
                "overview": data.get("overview"),
                "release_date": data.get("release_date"),
                "runtime": data.get("runtime"),
                "genres": [genre["name"] for genre in data.get("genres", [])],
                "vote_average": data.get("vote_average"),
                "vote_count": data.get("vote_count"),
                "popularity": data.get("popularity"),
                "poster_path": self._get_full_image_url(data.get("poster_path"), "w500"),
                "backdrop_path": self._get_full_image_url(data.get("backdrop_path"), "original"),
                "imdb_id": data.get("imdb_id"),
                "original_language": data.get("original_language"),
                "status": data.get("status"),
            }

            print(f"[TMDb] ✓ Fetched movie: {movie_data['title']} ({movie_data['release_date'][:4] if movie_data.get('release_date') else 'N/A'})")

            return movie_data

        except requests.exceptions.RequestException as e:
            print(f"[TMDb] ✗ Error fetching movie {tmdb_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"[TMDb] ✗ Unexpected error: {str(e)}")
            return None

    def get_tv_details(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch TV show details from TMDb API

        Args:
            tmdb_id: TMDb TV show ID

        Returns:
            Dictionary with TV show metadata or None if failed
        """
        if not self.api_key or self.api_key == "YOUR_TMDB_API_KEY_HERE":
            print("[TMDb] API key not configured!")
            return None

        try:
            url = f"{self.BASE_URL}/tv/{tmdb_id}"
            params = {
                "api_key": self.api_key,
                "append_to_response": "credits,videos,content_ratings"
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract and format the data
            tv_data = {
                "tmdb_id": data.get("id"),
                "title": data.get("name"),
                "original_title": data.get("original_name"),
                "overview": data.get("overview"),
                "first_air_date": data.get("first_air_date"),
                "last_air_date": data.get("last_air_date"),
                "genres": [genre["name"] for genre in data.get("genres", [])],
                "vote_average": data.get("vote_average"),
                "vote_count": data.get("vote_count"),
                "popularity": data.get("popularity"),
                "poster_path": self._get_full_image_url(data.get("poster_path"), "w500"),
                "backdrop_path": self._get_full_image_url(data.get("backdrop_path"), "original"),
                "number_of_seasons": data.get("number_of_seasons"),
                "number_of_episodes": data.get("number_of_episodes"),
                "status": data.get("status"),
                "original_language": data.get("original_language"),
            }

            print(f"[TMDb] ✓ Fetched TV show: {tv_data['title']} ({tv_data['first_air_date'][:4] if tv_data.get('first_air_date') else 'N/A'})")

            return tv_data

        except requests.exceptions.RequestException as e:
            print(f"[TMDb] ✗ Error fetching TV show {tmdb_id}: {str(e)}")
            return None
        except Exception as e:
            print(f"[TMDb] ✗ Unexpected error: {str(e)}")
            return None

    def _get_full_image_url(self, path: Optional[str], size: str = "original") -> Optional[str]:
        """
        Convert TMDb image path to full URL

        Args:
            path: TMDb image path (e.g., "/abc123.jpg")
            size: Image size (w500, original, etc.)

        Returns:
            Full image URL or None
        """
        if not path:
            return None
        return f"{self.IMAGE_BASE_URL}/{size}{path}"

    def search_movies(self, query: str, year: Optional[int] = None) -> list:
        """
        Search for movies by title

        Args:
            query: Movie title to search
            year: Optional release year

        Returns:
            List of movie results
        """
        if not self.api_key or self.api_key == "YOUR_TMDB_API_KEY_HERE":
            print("[TMDb] API key not configured!")
            return []

        try:
            url = f"{self.BASE_URL}/search/movie"
            params = {
                "api_key": self.api_key,
                "query": query,
            }

            if year:
                params["year"] = year

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            return data.get("results", [])

        except Exception as e:
            print(f"[TMDb] ✗ Error searching movies: {str(e)}")
            return []


# Singleton instance
tmdb_service = TMDbService()
