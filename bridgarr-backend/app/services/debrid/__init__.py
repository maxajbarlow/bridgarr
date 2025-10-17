"""
Debrid Services Package
Provides unified interface for multiple debrid service providers
"""

from .base import (
    BaseDebridClient,
    DebridProvider,
    TorrentStatus,
    DebridServiceError
)
from .real_debrid import RealDebridClient
from .alldebrid import AllDebridClient
from .premiumize import PremiumizeClient
from .debrid_link import DebridLinkClient

__all__ = [
    "BaseDebridClient",
    "DebridProvider",
    "TorrentStatus",
    "DebridServiceError",
    "RealDebridClient",
    "AllDebridClient",
    "PremiumizeClient",
    "DebridLinkClient",
    "get_debrid_client",
]


def get_debrid_client(provider: DebridProvider, api_token: str) -> BaseDebridClient:
    """
    Factory function to get the appropriate debrid client

    Args:
        provider: DebridProvider enum value
        api_token: User's API token for the provider

    Returns:
        Initialized debrid client instance

    Raises:
        ValueError: If provider is not supported
    """
    clients = {
        DebridProvider.REAL_DEBRID: RealDebridClient,
        DebridProvider.ALL_DEBRID: AllDebridClient,
        DebridProvider.PREMIUMIZE: PremiumizeClient,
        DebridProvider.DEBRID_LINK: DebridLinkClient,
    }

    client_class = clients.get(provider)
    if not client_class:
        raise ValueError(f"Unsupported debrid provider: {provider}")

    return client_class(api_token)
