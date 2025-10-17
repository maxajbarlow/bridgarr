"""
Bridgarr Services Package
Business logic layer for content management, metadata, and debrid service integration
"""

from app.services.debrid import (
    BaseDebridClient,
    DebridProvider,
    RealDebridClient,
    AllDebridClient,
    PremiumizeClient,
    DebridLinkClient,
    get_debrid_client
)
from app.services.metadata_manager import MetadataManager
from app.services.content_manager import ContentManager
from app.services.link_cache_manager import LinkCacheManager

__all__ = [
    "BaseDebridClient",
    "DebridProvider",
    "RealDebridClient",
    "AllDebridClient",
    "PremiumizeClient",
    "DebridLinkClient",
    "get_debrid_client",
    "MetadataManager",
    "ContentManager",
    "LinkCacheManager"
]
