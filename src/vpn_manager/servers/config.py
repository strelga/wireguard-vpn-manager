#!/usr/bin/env python3
"""
Service Configuration Management Module
Handles config.yml for WireGuard servers
"""

from dataclasses import asdict, dataclass

import yaml

from ..utils import Logger
from .utils import get_server_config_file


@dataclass
class StoredServerConfigData:
    """Stored server configuration data structure"""
    server_url: str = "auto"
    server_port: int = 51820
    peers: str = "0"
    peer_dns: str = "auto"
    internal_subnet: str = "10.13.13.0"
    allowed_ips: str = "0.0.0.0/0"
    tz: str = "UTC"
    log_confs: bool = True
    container_name: str = "wireguard"
    image: str = "linuxserver/wireguard:latest"


def get_default_service_config() -> dict:
    """Get default service configuration as dict"""
    return asdict(StoredServerConfigData())


def create_service_config(server_name: str, config: dict) -> None:
    """Create config.yml for a server"""
    config_file = get_server_config_file(server_name)

    # Merge with defaults
    default_config = get_default_service_config()
    merged_config = {**default_config, **config}

    with open(config_file, "w") as f:
        yaml.dump(merged_config, f, default_flow_style=False, sort_keys=False)

    Logger.success(f"Created config.yml for server '{server_name}'")


def load_service_config(server_name: str) -> StoredServerConfigData:
    """Load config.yml for a server"""
    config_file = get_server_config_file(server_name)

    if not config_file.exists():
        raise FileNotFoundError(f"Service config not found for server '{server_name}'")

    with open(config_file) as f:
        config_dict = yaml.safe_load(f)

    return StoredServerConfigData(**config_dict)


def update_service_config(server_name: str, updates: dict) -> None:
    """Update config.yml for a server"""
    config = load_service_config(server_name)
    config_dict = asdict(config)
    config_dict.update(updates)

    config_file = get_server_config_file(server_name)
    with open(config_file, "w") as f:
        yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

    Logger.success(f"Updated config.yml for server '{server_name}'")


def parse_peers(peers_str: str) -> list[str]:
    """Parse peers string to list of peer names"""
    if not peers_str or peers_str.strip() == "":
        return []
    return [peer.strip() for peer in peers_str.split(",") if peer.strip()]


def format_peers(peers_list: list[str]) -> str:
    """Format list of peer names to string"""
    return ",".join(peers_list)


def add_peer(server_name: str, peer_name: str) -> None:
    """Add a peer to the server configuration"""
    config = load_service_config(server_name)
    peers = parse_peers(config.peers)

    if peer_name in peers:
        Logger.warning(f"Peer '{peer_name}' already exists in server '{server_name}'")
        return

    peers.append(peer_name)
    update_service_config(server_name, {"peers": format_peers(peers)})

    Logger.success(f"Added peer '{peer_name}' to server '{server_name}'")


def remove_peer(server_name: str, peer_name: str) -> None:
    """Remove a peer from the server configuration"""
    config = load_service_config(server_name)
    peers = parse_peers(config.peers)

    if peer_name not in peers:
        Logger.warning(f"Peer '{peer_name}' not found in server '{server_name}'")
        return

    peers.remove(peer_name)
    update_service_config(server_name, {"peers": format_peers(peers)})

    Logger.success(f"Removed peer '{peer_name}' from server '{server_name}'")


def list_peers(server_name: str) -> list[str]:
    """List all peers for a server"""
    config = load_service_config(server_name)
    return parse_peers(config.peers)
