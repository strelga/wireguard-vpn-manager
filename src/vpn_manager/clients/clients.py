#!/usr/bin/env python3
"""
WireGuard Client Management Module
"""

import os
import shutil
import sys
import time
from pathlib import Path

from vpn_manager.servers import (
    ServerManager,
    add_peer,
    get_container_config_dir,
    get_container_name,
    list_peers,
    load_service_config,
    remove_peer,
    validate_server_name,
)
from vpn_manager.services import DockerComposeManager, ServiceManager
from vpn_manager.utils import Color, Logger

from .utils import validate_client_name


class ClientManager:
    """WireGuard client management utility"""

    _docker_compose_manager: DockerComposeManager

    def __init__(self):
        """Initialize ClientManager"""
        self._docker_compose_manager = DockerComposeManager()

    def _check_client_exists(self, server_name: str, client_name: str) -> bool:
        """Check if client already exists"""
        peers = list_peers(server_name)
        return client_name in peers

    def _get_client_config_file(self, server_name: str, client_name: str) -> Path:
        """Get the path to a client's configuration file"""
        container_config_dir = get_container_config_dir(server_name)
        # WireGuard creates a directory peer_<client_name>/ with peer_<client_name>.conf inside
        return container_config_dir / f"peer_{client_name}" / f"peer_{client_name}.conf"

    def _get_client_qr_file(self, server_name: str, client_name: str) -> Path:
        """Get the path to a client's QR code file"""
        container_config_dir = get_container_config_dir(server_name)
        # WireGuard creates a directory peer_<client_name>/ with peer_<client_name>.png inside
        return container_config_dir / f"peer_{client_name}" / f"peer_{client_name}.png"

    def _get_wg0_conf_file(self, server_name: str) -> Path:
        """Get the path to the wg0.conf file"""
        container_config_dir = get_container_config_dir(server_name)
        return container_config_dir / "wg_confs" / "wg0.conf"

    def _check_client_in_wg0_conf(self, server_name: str, client_name: str) -> bool:
        """Check if client appears in wg0.conf file"""
        wg0_conf_file = self._get_wg0_conf_file(server_name)
        if not wg0_conf_file.exists():
            return False

        try:
            # Force file system sync to ensure we read the latest content
            os.sync()

            with open(wg0_conf_file) as f:
                content = f.read()
                # Check if client's peer section exists in wg0.conf
                # The peer section format can be:
                # - [Peer] followed by # <client_name>
                # - peer_<client_name> in the content
                # - <client_name> in the content (more flexible check)
                return (
                    f"# {client_name}" in content or
                    f"peer_{client_name}" in content or
                    client_name in content
                )
        except Exception:
            return False

    def _wait_for_client_config(self, server_name: str, client_name: str, max_attempts: int = 30) -> bool:
        """Wait for container to generate client configuration file

        Process:
        1. First wait for client to appear in wg0.conf
        2. Then wait for client's config directory to be created
        """
        # Step 1: Wait for client to appear in wg0.conf
        for attempt in range(1, max_attempts + 1):
            if self._check_client_in_wg0_conf(server_name, client_name):
                sys.stdout.write(f"\rClient '{client_name}' appeared in wg0.conf (attempt {attempt}/{max_attempts})\n")
                sys.stdout.flush()
                break

            # Update the same line with attempt count
            sys.stdout.write(f"\rWaiting for client to appear in wg0.conf... ({attempt}/{max_attempts})")
            sys.stdout.flush()
            time.sleep(2)
        else:
            # Clear the line
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()
            return False

        # Step 2: Wait for client's config file to be created
        client_config_file = self._get_client_config_file(server_name, client_name)

        for attempt in range(1, max_attempts + 1):
            # Force file system sync to ensure we see the latest state
            os.sync()

            if client_config_file.exists():
                sys.stdout.write(f"\rClient config file created (attempt {attempt}/{max_attempts})\n")
                sys.stdout.flush()
                return True

            # Update the same line with attempt count
            sys.stdout.write(f"\rWaiting for client config file... ({attempt}/{max_attempts})")
            sys.stdout.flush()
            time.sleep(2)

        # Clear the line
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.flush()
        return False

    def add(self, server_name: str, client_name: str) -> bool:
        """Add a new client to WireGuard server"""
        try:
            # Validate inputs
            if not validate_server_name(server_name):
                return False

            if not validate_client_name(client_name):
                return False

            # Check if client already exists
            if self._check_client_exists(server_name, client_name):
                Logger.error(f"Client '{client_name}' already exists")
                return False

            # Get server info
            service_config = load_service_config(server_name)
            Logger.info(f"Server subnet: {service_config.internal_subnet}")
            Logger.info(
                f"Server endpoint: {service_config.server_url}:{service_config.server_port}"
            )

            # Add peer to config.yml
            Logger.info("Adding peer to server configuration...")
            add_peer(server_name, client_name)

            # Regenerate docker-compose to update container configuration
            Logger.info("Regenerating docker-compose configuration...")
            server_manager = ServerManager()
            server_manager.build()

            # Restart container to apply changes
            Logger.info("Restarting container...")
            container_name = get_container_name(server_name)
            if self._docker_compose_manager.restart_container(container_name):
                Logger.success(f"Container '{container_name}' restarted successfully")
            else:
                Logger.warning(
                    "Failed to restart container - you may need to restart manually"
                )

            # Wait for container to generate client configuration
            if not self._wait_for_client_config(server_name, client_name):
                Logger.warning(
                    f"Client configuration file not found: {self._get_client_config_file(server_name, client_name)}"
                )
                Logger.warning(
                    "The container may need more time to generate the configuration"
                )
                Logger.success(f"Client '{client_name}' added successfully!")
                return True

            # Read client configuration
            client_config_file = self._get_client_config_file(server_name, client_name)
            with open(client_config_file) as f:
                client_config_content = f.read()

            # Display results
            Logger.success(f"Client '{client_name}' added successfully!")

            print(f"\n{Color.BLUE}Client Configuration:{Color.NC}")
            print(f"  Name: {client_name}")
            print(f"  Config file: {client_config_file}")

            # Display QR code information
            client_qr_file = self._get_client_qr_file(server_name, client_name)
            print(f"\n{Color.BLUE}QR Code for mobile devices:{Color.NC}")
            if client_qr_file.exists():
                print(f"  QR code file: {client_qr_file}")
                print("  Scan this QR code with your WireGuard mobile app")
            else:
                print(f"  QR code file not found: {client_qr_file}")

            print(f"\n{Color.BLUE}Configuration content:{Color.NC}")
            print(client_config_content)

            return True

        except Exception as e:
            Logger.error(f"Failed to add client: {e}")
            return False

    def _remove_client_files(self, server_name: str, client_name: str) -> bool:
        """Remove client configuration files"""
        container_config_dir = get_container_config_dir(server_name)
        client_dir = container_config_dir / f"peer_{client_name}"

        removed = False

        if client_dir.exists() and client_dir.is_dir():
            shutil.rmtree(client_dir)
            Logger.success(f"Removed client directory: {client_dir}")
            removed = True
        else:
            Logger.warning(f"Client directory not found for '{client_name}'")

        return removed

    def _validate_remove_inputs(self, server_name: str, client_name: str) -> bool:
        """Validate inputs for remove operation"""
        if not validate_server_name(server_name):
            return False

        return validate_client_name(client_name)

    def _show_available_clients(self, server_name: str) -> None:
        """Show available clients when client not found"""
        existing_clients = self.list_clients(server_name, show_output=False)
        if existing_clients:
            Logger.info("Available clients:")
            for client in existing_clients:
                Logger.info(f"  - {client}")
        else:
            Logger.info("No clients found")

    def _perform_removal(self, server_name: str, client_name: str) -> bool:
        """Perform the actual removal of client data"""
        # Remove peer from config.yml
        Logger.info("Removing peer from server configuration...")
        remove_peer(server_name, client_name)

        # Remove client files
        Logger.info("Removing client configuration files...")
        client_files_removed = self._remove_client_files(server_name, client_name)

        return client_files_removed

    def _restart_after_removal(self, container_name: str) -> None:
        """Restart container after client removal"""
        Logger.info("Restarting container...")
        if self._docker_compose_manager.restart_container(container_name):
            Logger.success(f"Container '{container_name}' restarted successfully")
        else:
            Logger.warning(
                "Failed to restart container - you may need to restart manually"
            )

    def _show_remaining_clients(self, server_name: str) -> None:
        """Show remaining clients after removal"""
        remaining_clients = self.list_clients(server_name, show_output=False)
        if remaining_clients:
            print(f"\n{Color.BLUE}Remaining clients:{Color.NC}")
            for client in remaining_clients:
                print(f"  - {client}")
        else:
            print(
                f"\n{Color.BLUE}No clients remaining on server '{server_name}'{Color.NC}"
            )

    def remove(self, server_name: str, client_name: str) -> bool:
        """Remove a client from WireGuard server"""
        try:
            # Validate inputs
            if not self._validate_remove_inputs(server_name, client_name):
                return False

            # Check if client exists
            if not self._check_client_exists(server_name, client_name):
                Logger.error(f"Client '{client_name}' not found")
                self._show_available_clients(server_name)
                return False

            # Get server info
            service_config = load_service_config(server_name)

            # Perform removal
            if not self._perform_removal(server_name, client_name):
                return False

            # Regenerate docker-compose to update container configuration
            Logger.info("Regenerating docker-compose configuration...")
            server_manager = ServerManager()
            server_manager.build()

            # Restart container
            self._restart_after_removal(service_config.container_name)

            # Display results
            Logger.success(f"Client '{client_name}' removed successfully!")
            self._show_remaining_clients(server_name)

            return True

        except Exception as e:
            Logger.error(f"Failed to remove client: {e}")
            return False

    def list_clients(self, server_name: str, show_output: bool = True) -> list[str]:
        """List clients for a specific server"""
        if not validate_server_name(server_name):
            return []

        peers = list_peers(server_name)

        if show_output:
            if peers:
                Logger.success(f"Clients on server '{server_name}':")
                for client in peers:
                    print(f"  - {client}")
            else:
                Logger.info(f"No clients found on server '{server_name}'")

        return peers

    def list_all_clients(self) -> None:
        """List clients for all servers"""
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
