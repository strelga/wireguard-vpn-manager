"""Clients module for WireGuard VPN management"""

from .clients import ClientManager
from .utils import validate_client_name

__all__ = ["ClientManager", "validate_client_name"]
