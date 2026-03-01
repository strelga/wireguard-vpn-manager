#!/usr/bin/env python3
"""
WireGuard Server Management Module
"""

import sys
from pathlib import Path

import yaml

from utils import Color, KeyGenerator, Logger


class ServerManager:
    """WireGuard server management utility"""

    def create_server(
        self,
        server_name: str,
        server_url: str,
        port: int,
        subnet: str,
        dns: str = "1.1.1.1,8.8.8.8",
        allowed_ips: str = "0.0.0.0/0",
    ) -> bool:
        """Create a new WireGuard server from template"""
        try:
            # Validate server name
            if (
                not server_name
                or not server_name.replace("-", "").replace("_", "").isalnum()
            ):
                Logger.error(
                    "Server name must contain only alphanumeric characters, hyphens, and underscores"
                )
                return False

            # Check if server already exists
            server_dir = Path(f"servers/{server_name}")
            if server_dir.exists():
                Logger.error(f"Server '{server_name}' already exists")
                return False

            Logger.info(f"Creating server '{server_name}'...")

            # Create directory structure
            server_dir.mkdir(parents=True, exist_ok=True)
            (server_dir / "config").mkdir(exist_ok=True)
            (server_dir / "clients").mkdir(exist_ok=True)

            # Generate server keys
            Logger.info("Generating server key pair...")
            server_private_key, server_public_key = KeyGenerator.generate_keypair()

            # Create docker-compose.yml
            self._create_docker_compose(
                server_name, server_url, port, subnet, dns, allowed_ips
            )

            # Create initial server configuration
            self._create_server_config(server_name, server_private_key, subnet)

            # Update main docker-compose.yml
            self._update_main_compose(server_name)

            Logger.success(f"Server '{server_name}' created successfully!")

            print(f"\n{Color.BLUE}Server Configuration:{Color.NC}")
            print(f"  Name: {server_name}")
            print(f"  URL: {server_url}")
            print(f"  Port: {port}")
            print(f"  Subnet: {subnet}")
            print(f"  DNS: {dns}")
            print(f"  Allowed IPs: {allowed_ips}")
            print(f"  Directory: {server_dir}")

            print(f"\n{Color.BLUE}Next steps:{Color.NC}")
            print("  1. Update .env file with server configuration")
            print(f"  2. Start the server: python3 manager start {server_name}")
            print(
                f"  3. Add clients: python3 manager add-client {server_name} <client_name>"
            )

            return True

        except Exception as e:
            Logger.error(f"Failed to create server: {e}")
            return False

    def _create_docker_compose(
        self,
        server_name: str,
        server_url: str,
        port: int,
        subnet: str,
        dns: str,
        allowed_ips: str,
    ) -> None:
        """Create docker-compose.yml for the server"""
        compose_config = {
            "services": {
                f"wireguard-{server_name}": {
                    "image": "linuxserver/wireguard:latest",
                    "container_name": f"wireguard-{server_name}",
                    "cap_add": ["NET_ADMIN", "SYS_MODULE"],
                    "environment": [
                        "PUID=1000",
                        "PGID=1000",
                        "TZ=Europe/Moscow",
                        f"SERVERURL=${{{server_name.upper()}_SERVER_URL}}",
                        f"SERVERPORT={port}",
                        f"PEERS=${{{server_name.upper()}_PEERS}}",
                        f"PEERDNS={dns}",
                        f"INTERNAL_SUBNET={subnet}",
                        f"ALLOWEDIPS={allowed_ips}",
                    ],
                    "volumes": ["./config:/config", "/lib/modules:/lib/modules:ro"],
                    "ports": [f"{port}:{port}/udp"],
                    "sysctls": [
                        "net.ipv4.conf.all.src_valid_mark=1",
                        "net.ipv4.ip_forward=1",
                    ],
                    "restart": "unless-stopped",
                    "networks": ["wireguard-net"],
                }
            }
        }

        compose_file = Path(f"servers/{server_name}/docker-compose.yml")
        with open(compose_file, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)

        Logger.success(f"Created docker-compose.yml for server '{server_name}'")

    def _create_server_config(
        self, server_name: str, private_key: str, subnet: str
    ) -> None:
        """Create initial WireGuard server configuration"""
        config_dir = Path(f"servers/{server_name}/config/wg_confs")
        config_dir.mkdir(parents=True, exist_ok=True)

        # Extract server IP from subnet (first usable IP)
        import ipaddress

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

    def _update_main_compose(self, server_name: str) -> None:
        """Update main docker-compose.yml to include new server"""
        main_compose_file = Path("docker-compose.yml")

        if main_compose_file.exists():
            with open(main_compose_file) as f:
                compose_config = yaml.safe_load(f)
        else:
            compose_config = {
                "version": "3.8",
                "include": [],
                "networks": {"wireguard-net": {"driver": "bridge"}},
            }

        # Add include for new server
        new_include = f"servers/{server_name}/docker-compose.yml"
        if "include" not in compose_config:
            compose_config["include"] = []

        if new_include not in compose_config["include"]:
            compose_config["include"].append(new_include)

        # Write updated config
        with open(main_compose_file, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)

        Logger.success("Updated main docker-compose.yml")

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
                server_compose = Path(f"servers/{server}/docker-compose.yml")
                if server_compose.exists():
                    try:
                        with open(server_compose) as f:
                            config = yaml.safe_load(f)

                        # Extract port from first service
                        service_name = list(config["services"].keys())[0]
                        service_config = config["services"][service_name]
                        ports = service_config.get("ports", [])
                        port = ports[0].split(":")[0] if ports else "unknown"

                        print(f"  - {server} (port: {port})")
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
            import shutil

            shutil.rmtree(server_dir)

            # Update main docker-compose.yml
            self._remove_from_main_compose(server_name)

            Logger.success(f"Server '{server_name}' removed successfully")
            return True

        except Exception as e:
            Logger.error(f"Failed to remove server: {e}")
            return False

    def _remove_from_main_compose(self, server_name: str) -> None:
        """Remove server from main docker-compose.yml"""
        main_compose_file = Path("docker-compose.yml")

        if not main_compose_file.exists():
            return

        with open(main_compose_file) as f:
            compose_config = yaml.safe_load(f)

        # Remove include for server
        server_include = f"servers/{server_name}/docker-compose.yml"
        if "include" in compose_config and server_include in compose_config["include"]:
            compose_config["include"].remove(server_include)

        # Write updated config
        with open(main_compose_file, "w") as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)

        Logger.success("Updated main docker-compose.yml")
