#!/usr/bin/env python3
"""
WireGuard Server Management Module
"""

import shutil
from typing import TypedDict

import yaml

from vpn_manager.services import ServiceManager
from vpn_manager.utils import Color, Logger

from .config import (
    create_service_config,
    load_service_config,
)
from .utils import (
    ServerCreateConfigData,
    get_container_config_dir,
    get_server_dir,
    get_servers_dir,
)


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
            server_dir = get_server_dir(config.name)
            if server_dir.exists():
                Logger.error(f"Server '{config.name}' already exists")
                return False

            Logger.info(f"Creating server '{config.name}'...")

            # Create directory structure
            server_dir.mkdir(parents=True, exist_ok=True)
            get_container_config_dir(config.name).mkdir(exist_ok=True)

            # Create config.yml with server configuration
            create_service_config(config.name, {
                "server_url": config.url,
                "server_port": config.port,
                "peers": config.peers,
                "peer_dns": config.dns,
                "internal_subnet": config.subnet,
                "allowed_ips": config.allowed_ips,
                "container_name": f"wireguard-{config.name}",
            })

            # Generate docker-compose.generated.yml
            Logger.info("Generating docker-compose configuration...")
            self.build()

            # Start the server
            Logger.info("Starting the server...")
            service_manager = ServiceManager()
            if service_manager.start(config.name):
                Logger.success(f"Server '{config.name}' started successfully!")
            else:
                Logger.warning(f"Server '{config.name}' created but failed to start. You can start it manually with: vpn-manager service start {config.name}")

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
            print(f"  1. Add clients: vpn-manager client add {config.name} <client_name>")
            print(f"  2. Check server status: vpn-manager service status {config.name}")

            return True

        except Exception as e:
            Logger.error(f"Failed to create server: {e}")
            return False

    def build(self) -> bool:
        """Build docker-compose.generated.yml from all server configs"""
        try:
            servers_dir = get_servers_dir()
            if not servers_dir.exists():
                Logger.error("Servers directory not found")
                return False

            generated_compose: DockerComposeConfig = {
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

                try:
                    service_config = load_service_config(server_dir.name)
                except FileNotFoundError:
                    Logger.warning(f"No config.yml found for server '{server_dir.name}', skipping")
                    continue

                server_name = server_dir.name

                # Create service configuration
                service_name = service_config.container_name
                generated_compose["services"][service_name] = {
                    "image": service_config.image,
                    "container_name": service_name,
                    "cap_add": ["NET_ADMIN", "SYS_MODULE"],
                    "environment": [
                        "PUID=1000",
                        "PGID=1000",
                        f"TZ={service_config.tz}",
                        f"SERVERURL={service_config.server_url}",
                        f"SERVERPORT={service_config.server_port}",
                        f"PEERS={service_config.peers}",
                        f"PEERDNS={service_config.peer_dns}",
                        f"INTERNAL_SUBNET={service_config.internal_subnet}",
                        f"ALLOWEDIPS={service_config.allowed_ips}",
                        f"LOG_CONFS={str(service_config.log_confs).lower()}",
                    ],
                    "volumes": [
                        f"./{server_name}/container-config:/config",
                        "/lib/modules:/lib/modules:ro"
                    ],
                    "ports": [f"{service_config.server_port}:51820/udp"],
                    "sysctls": [
                        "net.ipv4.conf.all.src_valid_mark=1",
                        "net.ipv4.ip_forward=1",
                    ],
                    "restart": "unless-stopped",
                    "networks": ["wireguard-net"],
                }

            # Write generated compose file
            generated_file = get_servers_dir() / "docker-compose.generated.yml"
            # Ensure parent directory exists
            generated_file.parent.mkdir(parents=True, exist_ok=True)
            with open(generated_file, "w") as f:
                yaml.dump(generated_compose, f, default_flow_style=False, sort_keys=False)

            Logger.success(f"Generated docker-compose.generated.yml with {len(generated_compose['services'])} server(s)")
            return True

        except Exception as e:
            Logger.error(f"Failed to build docker-compose: {e}")
            return False

    def list_servers(self) -> None:
        """List all available servers"""
        servers_dir = get_servers_dir()
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
                try:
                    service_config = load_service_config(server)
                    print(f"  - {server} (url: {service_config.server_url}, port: {service_config.server_port}, subnet: {service_config.internal_subnet})")
                except Exception:
                    print(f"  - {server} (configuration error)")
        else:
            Logger.info("No servers found")

    def remove_server(self, server_name: str, force: bool = False) -> bool:
        """Remove a server (with confirmation)"""
        try:
            server_dir = get_server_dir(server_name)
            if not server_dir.exists():
                Logger.error(f"Server '{server_name}' not found")
                return False

            # Check if server has clients
            container_config_dir = get_container_config_dir(server_name)
            if container_config_dir.exists():
                client_files = list(container_config_dir.glob("peer*"))
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
