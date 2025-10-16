"""Media models for movies, TV shows, seasons, and episodes"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class MediaType(str, enum.Enum):
    """Media type enumeration"""
    MOVIE = "movie"
    TV_SHOW = "tv_show"


class MediaItem(Base):
    """Movie or TV show metadata"""

    __tablename__ = "media_items"

    id = Column(Integer, primary_key=True, index=True)

    # TMDb identifiers
    tmdb_id = Column(Integer, unique=True, nullable=False, index=True)
    imdb_id = Column(String(50), nullable=True, index=True)

    # Basic information
    title = Column(String(500), nullable=False, index=True)
    original_title = Column(String(500), nullable=True)
    media_type = Column(SQLEnum(MediaType), nullable=False, index=True)

    # Metadata
    overview = Column(Text, nullable=True)
    release_date = Column(String(50), nullable=True)
    runtime = Column(Integer, nullable=True)  # in minutes
    genres = Column(String(500), nullable=True)  # Comma-separated list

    # Images
    poster_path = Column(String(500), nullable=True)
    backdrop_path = Column(String(500), nullable=True)

    # Ratings
    vote_average = Column(Integer, nullable=True)  # stored as int * 10 (e.g., 75 = 7.5)
    vote_count = Column(Integer, nullable=True)

    # Status
    is_available = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    seasons = relationship("Season", back_populates="media_item", cascade="all, delete-orphan")
    rd_torrents = relationship("RDTorrent", back_populates="media_item")


class Season(Base):
    """TV show season"""

    __tablename__ = "seasons"

    id = Column(Integer, primary_key=True, index=True)
    media_item_id = Column(Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)

    # TMDb identifiers
    tmdb_id = Column(Integer, unique=True, nullable=False, index=True)

    # Basic information
    season_number = Column(Integer, nullable=False)
    name = Column(String(500), nullable=True)
    overview = Column(Text, nullable=True)

    # Images
    poster_path = Column(String(500), nullable=True)

    # Metadata
    air_date = Column(String(50), nullable=True)
    episode_count = Column(Integer, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    media_item = relationship("MediaItem", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")


class Episode(Base):
    """TV show episode"""

    __tablename__ = "episodes"

    id = Column(Integer, primary_key=True, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id", ondelete="CASCADE"), nullable=False)

    # TMDb identifiers
    tmdb_id = Column(Integer, unique=True, nullable=False, index=True)

    # Basic information
    episode_number = Column(Integer, nullable=False)
    name = Column(String(500), nullable=False)
    overview = Column(Text, nullable=True)

    # Images
    still_path = Column(String(500), nullable=True)

    # Metadata
    air_date = Column(String(50), nullable=True)
    runtime = Column(Integer, nullable=True)  # in minutes

    # Ratings
    vote_average = Column(Integer, nullable=True)  # stored as int * 10
    vote_count = Column(Integer, nullable=True)

    # Status
    is_available = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    season = relationship("Season", back_populates="episodes")
    rd_links = relationship("RDLink", back_populates="episode")
