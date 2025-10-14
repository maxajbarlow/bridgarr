"""
Media API Endpoints
Media details, streaming URLs, and playback information
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.models.media import MediaItem, Season, Episode, MediaType
from app.models.rd_link import RDLink
from app.models.rd_torrent import RDTorrent
from app.api.auth import get_current_user

# Router setup
router = APIRouter()


# Pydantic schemas
class SeasonResponse(BaseModel):
    id: int
    season_number: int
    episode_count: int
    name: Optional[str]
    overview: Optional[str]
    poster_path: Optional[str]
    air_date: Optional[str]

    class Config:
        from_attributes = True


class EpisodeResponse(BaseModel):
    id: int
    episode_number: int
    name: Optional[str]
    overview: Optional[str]
    still_path: Optional[str]
    air_date: Optional[str]
    runtime: Optional[int]
    has_streaming_url: bool

    class Config:
        from_attributes = True


class MediaItemResponse(BaseModel):
    id: int
    tmdb_id: int
    imdb_id: Optional[str]
    title: str
    media_type: MediaType
    overview: Optional[str]
    release_date: Optional[str]
    poster_path: Optional[str]
    backdrop_path: Optional[str]
    vote_average: Optional[float]
    vote_count: Optional[int]
    runtime: Optional[int]
    genres: Optional[str]
    is_available: bool
    season_count: Optional[int] = None

    class Config:
        from_attributes = True


class StreamingUrlResponse(BaseModel):
    streaming_url: str
    quality: Optional[str]
    expires_at: datetime
    media_id: int
    episode_id: Optional[int]


# Helper functions
def get_media_or_404(media_id: int, db: Session) -> MediaItem:
    """Get media item by ID or raise 404"""
    media = db.query(MediaItem).filter(MediaItem.id == media_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Media item with id {media_id} not found"
        )
    return media


def get_season_or_404(media_id: int, season_number: int, db: Session) -> Season:
    """Get season by media ID and season number or raise 404"""
    season = db.query(Season).filter(
        Season.media_item_id == media_id,
        Season.season_number == season_number
    ).first()

    if not season:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Season {season_number} not found for media item {media_id}"
        )
    return season


def get_episode_or_404(episode_id: int, db: Session) -> Episode:
    """Get episode by ID or raise 404"""
    episode = db.query(Episode).filter(Episode.id == episode_id).first()
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Episode with id {episode_id} not found"
        )
    return episode


# API Endpoints
@router.get("/{media_id}", response_model=MediaItemResponse)
async def get_media_details(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a media item

    - Returns movie or TV show details
    - Includes availability status
    - For TV shows, includes season count
    """
    media = get_media_or_404(media_id, db)

    # Add season count for TV shows
    if media.media_type == MediaType.TV_SHOW:
        media.season_count = len(media.seasons)

    return media


@router.get("/{media_id}/seasons", response_model=List[SeasonResponse])
async def get_media_seasons(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all seasons for a TV show

    - Only works for TV shows
    - Returns list of seasons with episode counts
    """
    media = get_media_or_404(media_id, db)

    if media.media_type != MediaType.TV_SHOW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media item is not a TV show"
        )

    return media.seasons


@router.get("/{media_id}/seasons/{season_number}/episodes", response_model=List[EpisodeResponse])
async def get_season_episodes(
    media_id: int,
    season_number: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all episodes for a specific season

    - Returns episode list with availability status
    - Each episode indicates if streaming URL is available
    """
    media = get_media_or_404(media_id, db)
    season = get_season_or_404(media_id, season_number, db)

    # Add has_streaming_url property to each episode
    episodes_with_urls = []
    for episode in season.episodes:
        # Check if there's a valid RD link for this episode
        has_url = db.query(RDLink).filter(
            RDLink.episode_id == episode.id,
            RDLink.is_valid == True,
            RDLink.expires_at > datetime.utcnow()
        ).first() is not None

        episode.has_streaming_url = has_url
        episodes_with_urls.append(episode)

    return episodes_with_urls


@router.get("/{media_id}/play", response_model=StreamingUrlResponse)
async def get_movie_streaming_url(
    media_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get streaming URL for a movie

    - Only works for movies
    - Returns Real-Debrid streaming URL
    - URL expires in ~4 hours (RD limitation)
    - Requires user to have RD token configured
    """
    media = get_media_or_404(media_id, db)

    if media.media_type != MediaType.MOVIE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Media item is not a movie. Use episode endpoint for TV shows."
        )

    # Check if user has RD token
    if not current_user.rd_api_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Real-Debrid token not configured. Please add your RD token first."
        )

    # Find a valid RD link for this movie
    rd_link = db.query(RDLink).join(RDTorrent).filter(
        RDTorrent.media_item_id == media_id,
        RDLink.is_valid == True,
        RDLink.expires_at > datetime.utcnow()
    ).first()

    if not rd_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid streaming URL found for this movie. Please add content first."
        )

    # Update last accessed time
    rd_link.last_accessed = datetime.utcnow()
    db.commit()

    return StreamingUrlResponse(
        streaming_url=rd_link.streaming_url,
        quality=rd_link.quality,
        expires_at=rd_link.expires_at,
        media_id=media_id,
        episode_id=None
    )


@router.get("/episodes/{episode_id}/play", response_model=StreamingUrlResponse)
async def get_episode_streaming_url(
    episode_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get streaming URL for a TV show episode

    - Returns Real-Debrid streaming URL for specific episode
    - URL expires in ~4 hours (RD limitation)
    - Requires user to have RD token configured
    """
    episode = get_episode_or_404(episode_id, db)

    # Check if user has RD token
    if not current_user.rd_api_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Real-Debrid token not configured. Please add your RD token first."
        )

    # Find a valid RD link for this episode
    rd_link = db.query(RDLink).filter(
        RDLink.episode_id == episode_id,
        RDLink.is_valid == True,
        RDLink.expires_at > datetime.utcnow()
    ).first()

    if not rd_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No valid streaming URL found for this episode. Please add content first."
        )

    # Update last accessed time
    rd_link.last_accessed = datetime.utcnow()
    db.commit()

    return StreamingUrlResponse(
        streaming_url=rd_link.streaming_url,
        quality=rd_link.quality,
        expires_at=rd_link.expires_at,
        media_id=episode.season.media_item_id,
        episode_id=episode_id
    )
