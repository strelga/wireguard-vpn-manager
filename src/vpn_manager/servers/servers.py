#!/usr/bin/env python3
"""
WireGuard Server Management Module
"""

import ipaddress
import shutil
from pathlib import Path
from typing import TypedDict

import yaml

from ..utils import (
    Color,
    KeyGenerator,
    Logger,
)
from .utils import ServerConfigData, ServerCreateConfigData


class NetworkConfig(TypedDict):
    """Network configuration for docker-compose"""
    driver: str


class ServiceConfig(TypedDict):
    """Service configuration for docker-compose"""
    image: str
    container_name: str
    cap_add: list[str]
    environment: list[str]
    volumes: list[str]
    ports: list[str]
    sysctls: list[str]
    restart: str
    networks: list[str]


class DockerComposeConfig(TypedDict):
    """Docker-compose configuration structure"""
    version: str
    services: dict[str, ServiceConfig]
    networks: dict[str, NetworkConfig]


class ServerManager:
    """WireGuard server management utility"""

    def create_server(self, config: ServerCreateConfigData) -> bool:
        """Create a new WireGuard server from template"""
        try:
            # Validate server name
            if (
                not config.name
                or not config.name.replace("-", "").replace("_", "").isalnum()
            ):
                Logger.error(
                    "Server name must contain only alphanumeric characters, hyphens, and underscores"
                )
                return False

            # Check if server already exists
            server_dir = Path(f"servers/{config.name}")
            if server_dir.exists():
                Logger.error(f"Server '{config.name}' already exists")
                return False

            Logger.info(f"Creating server '{config.name}'...")

            # Create directory structure
            server_dir.mkdir(parents=True, exist_ok=True)
            (server_dir / "config").mkdir(exist_ok=True)
            (server_dir / "clients").mkdir(exist_ok=True)

            # Generate server keys
            Logger.info("Generating server key pair...")
            server_private_key, server_public_key = KeyGenerator.generate_keypair()

            # Create complete server configuration
            complete_config = ServerConfigData(
                name=config.name,
                url=config.url,
                port=config.port,
                subnet=config.subnet,
                dns=config.dns,
                allowed_ips=config.allowed_ips,
                peers=config.peers,
                public_key=server_public_key,
            )

            # Create config.yml with server configuration
            self._create_server_config_yml(complete_config)

            # Create initial server configuration
            self._create_wg_server_config(config.name, server_private_key, config.subnet)

            # Generate docker-compose.generated.yml
            Logger.info("Generating docker-compose configuration...")
            self.build()

            Logger.success(f"Server '{config.name}' created successfully!")

            print(f"\n{Color.BLUE}Server Configuration:{Color.NC}")
            print(f"  Name: {config.name}")
            print(f"  URL: {config.url}")
            print(f"  Port: {config.port}")
            print(f"  Subnet: {config.subnet}")
            print(f"  DNS: {config.dns}")
            print(f"  Allowed IPs: {config.allowed_ips}")
            print(f"  Directory: {server_dir}")

            print(f"\n{Color.BLUE}Next steps:{Color.NC}")
            print(f"  1. Start the server: vpn-manager start {config.name}")
            print(
                f"  2. Add clients: vpn-manager add-client {config.name} <client_name>"
            )

            return True

        except Exception as e:
            Logger.error(f"Failed to create server: {e}")
            return False

    def _create_server_config_yml(self, config: ServerConfigData) -> None:
        """Create config.yml for the server"""
        config_dict = {
            "server": {
                "name": config.name,
                "url": config.url,
                "port": config.port,
                "subnet": config.subnet,
                "dns": config.dns,
                "allowed_ips": config.allowed_ips,
                "peers": config.peers,
                "public_key": config.public_key,
            }
        }

        config_file = Path(f"servers/{config.name}/config.yml")
        with open(config_file, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        Logger.success(f"Created config.yml for server '{config.name}'")

    def build(self) -> bool:
        """Build docker-compose.generated.yml from all server configs"""
        try:
            servers_dir = Path("servers")
            if not servers_dir.exists():
                Logger.error("Servers directory not found")
                return False

            generated_compose: DockerComposeConfig = {
                "version": "3.8",
                "services": {},
                "networks": {
                    "wireguard-net": {
                        "driver": "bridge"
                    }
                }
            }

            # Process each server directory
            for server_dir in servers_dir.iterdir():
                if not server_dir.is_dir():
                    continue

                config_file = server_dir / "config.yml"
                if not config_file.exists():
                    Logger.warning(f"No config.yml found for server '{server_dir.name}', skipping")
                    continue

                # Load server configuration
                with open(config_file) as f:
                    server_config = yaml.safe_load(f)

                server = server_config["server"]
                server_name = server["name"]

                # Create service configuration
                service_name = f"wireguard-{server_name}"
                generated_compose["services"][service_name] = {
                    "image": "linuxserver/wireguard:latest",
                    "container_name": service_name,
                    "cap_add": ["NET_ADMIN", "SYS_MODULE"],
                    "environment": [
                        "PUID=1000",
                        "PGID=1000",
                        "TZ=Europe/Moscow",
                        f"SERVERURL={server['url']}",
                        f"SERVERPORT={server['port']}",
                        f"PEERS={server['peers']}",
                        f"PEERDNS={server['dns']}",
                        f"INTERNAL_SUBNET={server['subnet']}",
                        f"ALLOWEDIPS={server['allowed_ips']}",
                    ],
                    "volumes": [
                        f"./{server_name}/config:/config",
                        "/lib/modules:/lib/modules:ro"
                    ],
                    "ports": [f"{server['port']}:51820/udp"],
                    "sysctls": [
                        "net.ipv4.conf.all.src_valid_mark=1",
                        "net.ipv4.ip_forward=1",
                    ],
                    "restart": "unless-stopped",
                    "networks": ["wireguard-net"],
                }

            # Write generated compose file
            generated_file = Path("servers/docker-compose.generated.yml")
            with open(generated_file, "w") as f:
                yaml.dump(generated_compose, f, default_flow_style=False, sort_keys=False)

            Logger.success(f"Generated docker-compose.generated.yml with {len(generated_compose['services'])} server(s)")
            return True

        except Exception as e:
            Logger.error(f"Failed to build docker-compose: {e}")
            return False

    def _create_wg_server_config(
        self, server_name: str, private_key: str, subnet: str
    ) -> None:
        """Create initial WireGuard server configuration"""
        config_dir = Path(f"servers/{server_name}/config/wg_confs")
        config_dir.mkdir(parents=True, exist_ok=True)

        # Extract server IP from subnet (first usable IP)
        network = ipaddress.IPv4Network(subnet)
        server_ip = str(network.network_address + 1)

        server_config = f"""[Interface]
PrivateKey = {private_key}
Address = {server_ip}/{network.prefixlen}
ListenPort = 51820
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth+ -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth+ -j MASQUERADE

"""

        config_file = config_dir / "wg0.conf"
        with open(config_file, "w") as f:
            f.write(server_config)

        config_file.chmod(0o600)

        Logger.success(f"Created server configuration for '{server_name}'")


    def list_servers(self) -> None:
        """List all available servers"""
        servers_dir = Path("servers")
        if not servers_dir.exists():
            Logger.info("No servers directory found")
            return

        servers = []
        for server_dir in servers_dir.iterdir():
            if server_dir.is_dir():
                servers.append(server_dir.name)

        if servers:
            Logger.success("Available servers:")
            for server in sorted(servers):
                server_config = Path(f"servers/{server}/config.yml")
                if server_config.exists():
                    try:
                        with open(server_config) as f:
                            config = yaml.safe_load(f)

                        server_info = config["server"]
                        print(f"  - {server} (url: {server_info['url']}, port: {server_info['port']}, subnet: {server_info['subnet']})")
                    except Exception:
                        print(f"  - {server} (configuration error)")
                else:
                    print(f"  - {server} (no configuration)")
        else:
            Logger.info("No servers found")

    def remove_server(self, server_name: str, force: bool = False) -> bool:
        """Remove a server (with confirmation)"""
        try:
            server_dir = Path(f"servers/{server_name}")
            if not server_dir.exists():
                Logger.error(f"Server '{server_name}' not found")
                return False

            # Check if server has clients
            clients_dir = server_dir / "clients"
            if clients_dir.exists():
                client_files = list(clients_dir.glob("*.conf"))
                if client_files and not force:
                    Logger.error(
                        f"Server '{server_name}' has {len(client_files)} client(s)"
                    )
                    Logger.info("Remove clients first or use --force flag")
                    Logger.info("Clients:")
                    for client_file in client_files:
                        Logger.info(f"  - {client_file.stem}")
                    return False

            if not force:
                Logger.warning(
                    f"This will permanently delete server '{server_name}' and all its data"
                )
                response = input("Are you sure? (yes/no): ").lower().strip()
                if response not in ["yes", "y"]:
                    Logger.info("Operation cancelled")
                    return False

            # Remove server directory
            shutil.rmtree(server_dir)

            # Regenerate docker-compose.generated.yml
            Logger.info("Regenerating docker-compose configuration...")
            self.build()

            Logger.success(f"Server '{server_name}' removed successfully")
            return True

        except Exception as e:
            Logger.error(f"Failed to remove server: {e}")
            return False

