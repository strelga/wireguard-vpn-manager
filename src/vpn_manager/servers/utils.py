import ipaddress
from dataclasses import dataclass
from pathlib import Path

import yaml

from ..utils import Logger


@dataclass
class ServerCreateConfigData:
    """Input configuration for creating a server"""
    name: str
    url: str
    port: int
    subnet: str
    dns: str = "1.1.1.1,8.8.8.8"
    allowed_ips: str = "0.0.0.0/0"
    peers: int = 1


@dataclass
class ServerConfigData(ServerCreateConfigData):
    """Complete server configuration with public key"""
    public_key: str = ""  # Required field, will be set during creation

    @property
    def container_name(self) -> str:
        """Get container name for this server"""
        return f"wireguard-{self.name}"

class ServerConfig:
    """Server configuration management"""

    server_name: str
    server_dir: Path
    clients_dir: Path
    wg_config_file: Path
    server_config_file: Path

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.server_dir = Path(f"servers/{server_name}")
        self.clients_dir = self.server_dir / "clients"
        self.wg_config_file = self.server_dir / "wg0.conf"
        self.server_config_file = self.server_dir / "config.yml"

        # Ensure directories exist
        self.clients_dir.mkdir(parents=True, exist_ok=True)

    def get_server_info(self) -> ServerConfigData:
        """Get server configuration from docker-compose.yml and .env"""
        if not self.server_config_file.exists():
            raise FileNotFoundError(
                f"Server config file not found: {self.server_config_file}"
            )

        # Load docker-compose.yml
        with open(self.server_config_file) as f:
            server_config = yaml.safe_load(f)

        # Build server info
        return ServerConfigData(
            name=server_config["name"],
            url=server_config["url"],
            port=server_config["port"],
            subnet=server_config["subnet"],
            dns=server_config["dns"],
            allowed_ips=server_config["allowed_ips"],
            peers=server_config["peers"],
            public_key=server_config["public_key"],
        )

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variable references like ${VAR}"""
        if not value or not value.startswith("${") or not value.endswith("}"):
            return value

        var_name = value[2:-1]  # Remove ${ and }
        env_vars = self._load_env_vars()
        return env_vars.get(var_name, value)

    def _load_env_vars(self) -> dict[str, str]:
        """Load environment variables from .env file"""
        env_vars = {}
        env_file = Path(".env")

        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith("#") and "=" in stripped_line:
                        key, value = stripped_line.split("=", 1)
                        env_vars[key.strip()] = value.strip()

        return env_vars

    def get_next_client_ip(self) -> str:
        """Find next available IP address in server subnet"""
        server_info = self.get_server_info()
        network = ipaddress.IPv4Network(server_info.subnet)

        # Server uses .1, start from .2
        used_ips = {network.network_address + 1}  # Server IP

        # Parse existing config to find used IPs
        if self.wg_config_file.exists():
            with open(self.wg_config_file) as f:
                content = f.read()

            # Find all Address lines in [Peer] sections
            lines = content.split("\n")
            in_peer = False

            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith("[Peer]"):
                    in_peer = True
                elif stripped_line.startswith("[") and stripped_line != "[Peer]":
                    in_peer = False
                elif in_peer and stripped_line.startswith("Address"):
                    # Extract IP from "Address = 10.13.13.2/32"
                    try:
                        ip_str = stripped_line.split("=")[1].strip().split("/")[0]
                        used_ips.add(ipaddress.IPv4Address(ip_str))
                    except (ValueError, IndexError):
                        continue

        # Find first available IP
        for ip in network.hosts():
            if ip not in used_ips:
                return str(ip)

        raise RuntimeError(
            f"No available IP addresses in subnet {server_info.subnet}"
        )

def validate_server_name(server_name: str) -> bool:
    """Validate server name"""
    server_dir = Path(f"servers/{server_name}")
    if not server_dir.exists():
        Logger.error(f"Server '{server_name}' not found")
        Logger.info("Available servers:")
        servers_dir = Path("servers")
        if servers_dir.exists():
            for server in servers_dir.iterdir():
                if server.is_dir():
                    Logger.info(f"  - {server.name}")
        return False
    return True
