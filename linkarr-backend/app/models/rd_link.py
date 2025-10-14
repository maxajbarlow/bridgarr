"""Real-Debrid streaming link caching model"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RDLink(Base):
    """Real-Debrid streaming link cache"""

    __tablename__ = "rd_links"

    id = Column(Integer, primary_key=True, index=True)
    rd_torrent_id = Column(Integer, ForeignKey("rd_torrents.id", ondelete="CASCADE"), nullable=False)
    episode_id = Column(Integer, ForeignKey("episodes.id", ondelete="CASCADE"), nullable=True)  # NULL for movies

    # Real-Debrid link information
    rd_file_id = Column(String(255), nullable=False)
    filename = Column(String(1000), nullable=False)
    filesize = Column(Integer, nullable=True)  # in bytes

    # Streaming URL (expires after ~4 hours)
    streaming_url = Column(Text, nullable=False)

    # Quality information
    quality = Column(String(50), nullable=True)  # e.g., "1080p", "4K"
    codec = Column(String(50), nullable=True)  # e.g., "h264", "h265"

    # Cache management
    is_valid = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    last_accessed = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    rd_torrent = relationship("RDTorrent", back_populates="rd_links")
    episode = relationship("Episode", back_populates="rd_links")
