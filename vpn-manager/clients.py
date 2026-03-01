#!/usr/bin/env python3
"""
WireGuard Client Management Module
"""

import subprocess
import sys
from pathlib import Path
from typing import List

from utils import (
    Color,
    DockerManager,
    KeyGenerator,
    Logger,
    QRCodeGenerator,
    WireGuardConfig,
    validate_client_name,
    validate_server_name,
)


class ClientManager:
    """WireGuard client management utility"""

    def _get_server_public_key(self, wg_config: WireGuardConfig) -> str:
        """Extract server public key from existing configuration"""
        if not wg_config.wg_config_file.exists():
            raise FileNotFoundError(
                f"Server configuration not found: {wg_config.wg_config_file}"
            )

        with open(wg_config.wg_config_file) as f:
            content = f.read()

        # Find PrivateKey in [Interface] section
        lines = content.split("\n")
        in_interface = False

        for line in lines:
            line = line.strip()
            if line == "[Interface]":
                in_interface = True
            elif line.startswith("[") and line != "[Interface]":
                in_interface = False
            elif in_interface and line.startswith("PrivateKey"):
                private_key = line.split("=")[1].strip()
                # Generate public key from private key
                try:
                    if KeyGenerator.command_exists("wg"):
                        result = subprocess.run(
                            ["wg", "pubkey"],
                            input=private_key,
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        return result.stdout.strip()
                    else:
                        # Use Docker
                        result = subprocess.run(
                            [
                                "docker",
                                "run",
                                "--rm",
                                "-i",
                                "linuxserver/wireguard:latest",
                                "wg",
                                "pubkey",
                            ],
                            input=private_key,
                            capture_output=True,
                            text=True,
                            check=True,
                        )
                        return result.stdout.strip()
                except Exception as e:
                    raise RuntimeError(f"Failed to generate server public key: {e}") from e

        raise ValueError("Server private key not found in configuration")

    def _check_client_exists(
        self, wg_config: WireGuardConfig, client_name: str
    ) -> bool:
        """Check if client already exists"""
        client_config_file = wg_config.clients_dir / f"{client_name}.conf"
        if client_config_file.exists():
            return True

        # Also check in server config
        if wg_config.wg_config_file.exists():
            with open(wg_config.wg_config_file) as f:
                content = f.read()
            if f"# Client: {client_name}" in content:
                return True

        return False

    def _add_peer_to_server_config(
        self,
        wg_config: WireGuardConfig,
        client_name: str,
        client_public_key: str,
        client_ip: str,
    ) -> None:
        """Add peer configuration to server config file"""
        peer_config = f"""
# Client: {client_name}
[Peer]
PublicKey = {client_public_key}
AllowedIPs = {client_ip}/32
"""

        # Append to server config
        with open(wg_config.wg_config_file, "a") as f:
            f.write(peer_config)

        Logger.success(f"Added peer {client_name} to server configuration")

    def _create_client_config(
        self,
        wg_config: WireGuardConfig,
        client_name: str,
        client_private_key: str,
        client_ip: str,
        server_public_key: str,
    ) -> str:
        """Create client configuration file and return its content"""
        server_info = wg_config.get_server_info()

        client_config = f"""[Interface]
PrivateKey = {client_private_key}
Address = {client_ip}/32
DNS = {server_info["dns"]}

[Peer]
PublicKey = {server_public_key}
Endpoint = {server_info["server_url"]}:{server_info["server_port"]}
AllowedIPs = {server_info["allowed_ips"]}
PersistentKeepalive = 25
"""

        # Save client config file
        client_config_file = wg_config.clients_dir / f"{client_name}.conf"
        with open(client_config_file, "w") as f:
            f.write(client_config)

        client_config_file.chmod(0o600)  # Secure permissions

        Logger.success(f"Created client configuration: {client_config_file}")

        return client_config

    def add(self, server_name: str, client_name: str) -> bool:
        """Add a new client to WireGuard server"""
        try:
            # Validate inputs
            if not validate_server_name(server_name):
                return False

            if not validate_client_name(client_name):
                return False

            # Initialize configuration
            wg_config = WireGuardConfig(server_name)

            # Check if client already exists
            if self._check_client_exists(wg_config, client_name):
                Logger.error(f"Client '{client_name}' already exists")
                return False

            # Get server info
            server_info = wg_config.get_server_info()
            Logger.info(f"Server subnet: {server_info['subnet']}")
            Logger.info(
                f"Server endpoint: {server_info['server_url']}:{server_info['server_port']}"
            )

            # Generate client keys
            Logger.info("Generating client key pair...")
            client_private_key, client_public_key = KeyGenerator.generate_keypair()

            # Find next available IP
            Logger.info("Finding next available IP address...")
            client_ip = wg_config.get_next_client_ip()
            Logger.info(f"Assigned IP: {client_ip}")

            # Get server public key
            Logger.info("Extracting server public key...")
            server_public_key = self._get_server_public_key(wg_config)

            # Add peer to server config
            Logger.info("Adding peer to server configuration...")
            self._add_peer_to_server_config(
                wg_config, client_name, client_public_key, client_ip
            )

            # Create client config
            Logger.info("Creating client configuration...")
            client_config_content = self._create_client_config(
                wg_config, client_name, client_private_key, client_ip, server_public_key
            )

            # Restart container
            Logger.info("Restarting container...")
            container_name = server_info["container_name"]
            if DockerManager.restart_container(container_name):
                Logger.success(f"Container '{container_name}' restarted successfully")
            else:
                Logger.warning(
                    "Failed to restart container - you may need to restart manually"
                )

            # Display results
            Logger.success(f"Client '{client_name}' added successfully!")

            print(f"\n{Color.BLUE}Client Configuration:{Color.NC}")
            print(f"  Name: {client_name}")
            print(f"  IP: {client_ip}")
            print(f"  Config file: {wg_config.clients_dir}/{client_name}.conf")

            # Generate QR code
            print(f"\n{Color.BLUE}QR Code for mobile devices:{Color.NC}")
            QRCodeGenerator.generate_qr(client_config_content)

            print(f"\n{Color.BLUE}Configuration content:{Color.NC}")
            print(client_config_content)

            return True

        except Exception as e:
            Logger.error(f"Failed to add client: {e}")
            return False

    def _remove_peer_from_server_config(
        self, wg_config: WireGuardConfig, client_name: str
    ) -> bool:
        """Remove peer configuration from server config file"""
        if not wg_config.wg_config_file.exists():
            Logger.warning(
                f"Server configuration file not found: {wg_config.wg_config_file}"
            )
            return False

        with open(wg_config.wg_config_file) as f:
            content = f.read()

        # Find and remove the client's peer section
        lines = content.split("\n")
        new_lines = []
        skip_section = False
        client_found = False

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for client comment
            if line == f"# Client: {client_name}":
                client_found = True
                skip_section = True
                # Skip this line and the following [Peer] section
                i += 1
                continue

            # If we're in a section to skip
            if skip_section:
                # Skip until we find the next section or end of file
                if line.startswith("[") and line != "[Peer]":
                    # Found next section, stop skipping
                    skip_section = False
                    new_lines.append(lines[i])
                elif line.startswith("# Client:") or (i == len(lines) - 1):
                    # Found another client or end of file, stop skipping
                    skip_section = False
                    if line.startswith("# Client:"):
                        new_lines.append(lines[i])
                # Otherwise, skip this line
            else:
                new_lines.append(lines[i])

            i += 1

        if not client_found:
            Logger.warning(f"Client '{client_name}' not found in server configuration")
            return False

        # Write updated configuration
        with open(wg_config.wg_config_file, "w") as f:
            f.write("\n".join(new_lines))

        Logger.success(f"Removed peer {client_name} from server configuration")
        return True

    def _remove_client_files(
        self, wg_config: WireGuardConfig, client_name: str
    ) -> bool:
        """Remove client configuration files"""
        client_config_file = wg_config.clients_dir / f"{client_name}.conf"

        if client_config_file.exists():
            client_config_file.unlink()
            Logger.success(f"Removed client configuration file: {client_config_file}")
            return True
        else:
            Logger.warning(f"Client configuration file not found: {client_config_file}")
            return False

    def remove(self, server_name: str, client_name: str) -> bool:
        """Remove a client from WireGuard server"""
        try:
            # Validate inputs
            if not validate_server_name(server_name):
                return False

            if not validate_client_name(client_name):
                return False

            # Initialize configuration
            wg_config = WireGuardConfig(server_name)

            # Check if client exists
            if not self._check_client_exists(wg_config, client_name):
                Logger.error(f"Client '{client_name}' not found")

                # Show available clients
                existing_clients = self.list_clients(server_name, show_output=False)
                if existing_clients:
                    Logger.info("Available clients:")
                    for client in existing_clients:
                        Logger.info(f"  - {client}")
                else:
                    Logger.info("No clients found")

                return False

            # Get server info
            server_info = wg_config.get_server_info()

            # Remove peer from server config
            Logger.info("Removing peer from server configuration...")
            server_config_removed = self._remove_peer_from_server_config(
                wg_config, client_name
            )

            # Remove client files
            Logger.info("Removing client configuration files...")
            client_files_removed = self._remove_client_files(wg_config, client_name)

            if not server_config_removed and not client_files_removed:
                Logger.error("No client data was found to remove")
                return False

            # Restart container
            Logger.info("Restarting container...")
            container_name = server_info["container_name"]
            if DockerManager.restart_container(container_name):
                Logger.success(f"Container '{container_name}' restarted successfully")
            else:
                Logger.warning(
                    "Failed to restart container - you may need to restart manually"
                )

            # Display results
            Logger.success(f"Client '{client_name}' removed successfully!")

            # Show remaining clients
            remaining_clients = self.list_clients(server_name, show_output=False)
            if remaining_clients:
                print(f"\n{Color.BLUE}Remaining clients:{Color.NC}")
                for client in remaining_clients:
                    print(f"  - {client}")
            else:
                print(
                    f"\n{Color.BLUE}No clients remaining on server '{server_name}'{Color.NC}"
                )

            return True

        except Exception as e:
            Logger.error(f"Failed to remove client: {e}")
            return False

    def list_clients(self, server_name: str, show_output: bool = True) -> List[str]:
        """List clients for a specific server"""
        if not validate_server_name(server_name):
            return []

        wg_config = WireGuardConfig(server_name)
        clients = []

        # From client config files
        if wg_config.clients_dir.exists():
            for config_file in wg_config.clients_dir.glob("*.conf"):
                clients.append(config_file.stem)

        # From server config
        if wg_config.wg_config_file.exists():
            with open(wg_config.wg_config_file) as f:
                content = f.read()

            # Find all client comments
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("# Client: "):
                    client_name = line.replace("# Client: ", "")
                    if client_name not in clients:
                        clients.append(client_name)

        clients = sorted(clients)

        if show_output:
            if clients:
                Logger.success(f"Clients on server '{server_name}':")
                for client in clients:
                    print(f"  - {client}")
            else:
                Logger.info(f"No clients found on server '{server_name}'")

        return clients

    def list_all_clients(self) -> None:
        """List clients for all servers"""
        from services import ServiceManager

        service_manager = ServiceManager()
        servers = service_manager.get_available_servers()

        all_clients_found = False

        for server in servers:
            clients = self.list_clients(server, show_output=False)
            if clients:
                all_clients_found = True
                print(f"\n{Color.BLUE}Server '{server}':{Color.NC}")
                for client in clients:
                    print(f"  - {client}")

        if not all_clients_found:
            Logger.info("No clients found on any server")
