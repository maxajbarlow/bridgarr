"""
Library API Endpoints
Browse movies, TV shows, and recently added content
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.media import MediaItem, Season, MediaType
from app.api.auth import get_current_user

# Router setup
router = APIRouter()


# Pydantic schemas
class MediaItemSummary(BaseModel):
    id: int
    tmdb_id: int
    imdb_id: Optional[str]
    title: str
    media_type: MediaType
    release_date: Optional[str]
    poster_path: Optional[str]
    backdrop_path: Optional[str]
    vote_average: Optional[float]
    is_available: bool
    added_at: datetime

    class Config:
        from_attributes = True


class LibraryStats(BaseModel):
    total_movies: int
    total_shows: int
    total_episodes: int
    available_movies: int
    available_shows: int


class PaginatedResponse(BaseModel):
    items: List[MediaItemSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


# API Endpoints
@router.get("/stats", response_model=LibraryStats)
async def get_library_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get library statistics

    - Total counts for movies, TV shows, episodes
    - Available content counts
    """
    # Count movies
    total_movies = db.query(MediaItem).filter(
        MediaItem.media_type == MediaType.MOVIE
    ).count()

    available_movies = db.query(MediaItem).filter(
        MediaItem.media_type == MediaType.MOVIE,
        MediaItem.is_available == True
    ).count()

    # Count TV shows
    total_shows = db.query(MediaItem).filter(
        MediaItem.media_type == MediaType.TV_SHOW
    ).count()

    available_shows = db.query(MediaItem).filter(
        MediaItem.media_type == MediaType.TV_SHOW,
        MediaItem.is_available == True
    ).count()

    # Count episodes
    from app.models.media import Episode
    total_episodes = db.query(Episode).count()

    return LibraryStats(
        total_movies=total_movies,
        total_shows=total_shows,
        total_episodes=total_episodes,
        available_movies=available_movies,
        available_shows=available_shows
    )


@router.get("/movies", response_model=PaginatedResponse)
async def get_movies(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("added_at", description="Sort field: added_at, title, release_date, vote_average"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    available_only: bool = Query(False, description="Show only available movies"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of movies

    - Supports pagination, sorting, and filtering
    - Can filter to show only available content
    - Default sort: recently added first
    """
    # Base query
    query = db.query(MediaItem).filter(MediaItem.media_type == MediaType.MOVIE)

    # Apply availability filter
    if available_only:
        query = query.filter(MediaItem.is_available == True)

    # Apply sorting
    sort_field_map = {
        "added_at": MediaItem.created_at,
        "title": MediaItem.title,
        "release_date": MediaItem.release_date,
        "vote_average": MediaItem.vote_average
    }

    sort_field = sort_field_map.get(sort_by, MediaItem.created_at)

    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(sort_field)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # Add added_at property
    for item in items:
        item.added_at = item.created_at

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/shows", response_model=PaginatedResponse)
async def get_tv_shows(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("added_at", description="Sort field: added_at, title, release_date, vote_average"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    available_only: bool = Query(False, description="Show only available TV shows"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of TV shows

    - Supports pagination, sorting, and filtering
    - Can filter to show only available content
    - Default sort: recently added first
    """
    # Base query
    query = db.query(MediaItem).filter(MediaItem.media_type == MediaType.TV_SHOW)

    # Apply availability filter
    if available_only:
        query = query.filter(MediaItem.is_available == True)

    # Apply sorting
    sort_field_map = {
        "added_at": MediaItem.created_at,
        "title": MediaItem.title,
        "release_date": MediaItem.release_date,
        "vote_average": MediaItem.vote_average
    }

    sort_field = sort_field_map.get(sort_by, MediaItem.created_at)

    if sort_order.lower() == "desc":
        query = query.order_by(desc(sort_field))
    else:
        query = query.order_by(sort_field)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # Add added_at property
    for item in items:
        item.added_at = item.created_at

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/recent", response_model=List[MediaItemSummary])
async def get_recently_added(
    limit: int = Query(20, ge=1, le=100, description="Number of items to return"),
    media_type: Optional[MediaType] = Query(None, description="Filter by media type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recently added content

    - Returns most recently added items
    - Can filter by media type (movie or tv_show)
    - Default: returns last 20 items
    """
    # Base query
    query = db.query(MediaItem)

    # Apply media type filter if specified
    if media_type:
        query = query.filter(MediaItem.media_type == media_type)

    # Order by creation date (most recent first) and limit
    items = query.order_by(desc(MediaItem.created_at)).limit(limit).all()

    # Add added_at property
    for item in items:
        item.added_at = item.created_at

    return items


@router.get("/search", response_model=PaginatedResponse)
async def search_library(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    media_type: Optional[MediaType] = Query(None, description="Filter by media type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search library content

    - Searches titles for matching text
    - Case-insensitive search
    - Can filter by media type
    - Supports pagination
    """
    # Base query with search
    query = db.query(MediaItem).filter(
        MediaItem.title.ilike(f"%{q}%")
    )

    # Apply media type filter if specified
    if media_type:
        query = query.filter(MediaItem.media_type == media_type)

    # Order by relevance (exact matches first, then alphabetically)
    query = query.order_by(MediaItem.title)

    # Get total count
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    items = query.offset(offset).limit(page_size).all()

    # Add added_at property
    for item in items:
        item.added_at = item.created_at

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
