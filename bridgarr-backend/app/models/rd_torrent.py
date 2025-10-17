"""Real-Debrid torrent tracking model"""

from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class RDTorrent(Base):
    """Real-Debrid torrent tracking"""

    __tablename__ = "rd_torrents"

    id = Column(Integer, primary_key=True, index=True)
    media_item_id = Column(Integer, ForeignKey("media_items.id", ondelete="CASCADE"), nullable=False)

    # Real-Debrid identifiers
    rd_torrent_id = Column(String(255), unique=True, nullable=False, index=True)

    # Torrent information
    torrent_hash = Column(String(255), nullable=False, index=True)
    torrent_name = Column(String(1000), nullable=False)
    torrent_size = Column(BigInteger, nullable=True)  # in bytes (supports files > 2GB)

    # Status tracking
    status = Column(String(50), nullable=False, default="pending")  # pending, downloading, downloaded, error
    progress = Column(Integer, default=0, nullable=False)  # 0-100
    error_message = Column(Text, nullable=True)

    # File selection
    selected_files = Column(Text, nullable=True)  # JSON array of file IDs

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    media_item = relationship("MediaItem", back_populates="rd_torrents")
    rd_links = relationship("RDLink", back_populates="rd_torrent", cascade="all, delete-orphan")
