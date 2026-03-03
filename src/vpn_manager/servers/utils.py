from dataclasses import dataclass
from pathlib import Path

from ..utils import Logger


def get_project_root() -> Path:
    """Get the project root directory"""
    # This file is at src/vpn_manager/servers/utils.py
    # Go up 4 levels to get to project root
    return Path(__file__).parent.parent.parent.parent


def get_servers_dir() -> Path:
    """Get the path to the servers directory"""
    return get_project_root() / "servers"


def get_server_dir(server_name: str) -> Path:
    """Get the path to a server directory"""
    return get_servers_dir() / server_name


def get_server_config_file(server_name: str) -> Path:
    """Get the path to a server's config.yml file"""
    return get_server_dir(server_name) / "config.yml"


def get_container_config_dir(server_name: str) -> Path:
    """Get the path to a server's container-config directory"""
    return get_server_dir(server_name) / "container-config"


def get_container_name(server_name: str) -> str:
    """Get the container name for a server"""
    return f"wireguard-{server_name}"


@dataclass
class ServerCreateConfigData:
    """Input configuration for creating a server"""
    name: str
    url: str
    port: int
    subnet: str
    dns: str = "auto"
    allowed_ips: str = "0.0.0.0/0"
    peers: str = "0"  # List of peer names separated by commas


def validate_server_name(server_name: str) -> bool:
    """Validate server name"""
    server_dir = get_server_dir(server_name)
    if not server_dir.exists():
        Logger.error(f"Server '{server_name}' not found")
        Logger.info("Available servers:")
        servers_dir = get_servers_dir()
        if servers_dir.exists():
            for server in servers_dir.iterdir():
                if server.is_dir():
                    Logger.info(f"  - {server.name}")
        return False
    return True
