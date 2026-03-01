#!/usr/bin/env python3
"""
WireGuard VPN Orchestration Tool

Unified command-line interface for WireGuard VPN management.
Usage: python3 manager.py <group> <command> [options]
"""

import argparse
import os
import sys
from pathlib import Path

from .clients import ClientManager
from .keys import KeyManager
from .servers.servers import ServerCreateConfigData, ServerManager
from .services import ServiceManager
from .utils import Logger


def _create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="Comprehensive WireGuard VPN management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Command Groups:
  service    - Service management (start, stop, restart, status, generate)
  client     - Client management (add, remove, list)
  key        - Key management (generate)
  server     - Server management (create, list, remove)

Examples:
  vpn-manager service start                    - Start all services
  vpn-manager service start myserver           - Start specific server
  vpn-manager service generate                 - Generate docker-compose configuration
  vpn-manager client add myserver phone        - Add phone client
  vpn-manager client remove myserver laptop    - Remove laptop client
  vpn-manager client list                      - List all clients
  vpn-manager key generate /tmp/keys           - Generate keys to directory
  vpn-manager server create -n myserver -u example.com -p 51820 -s 10.13.13.0/24
  vpn-manager server list                      - List all servers
        """,
    )

    subparsers = parser.add_subparsers(dest="group", help="Command group")

    # Service management group
    service_parser = subparsers.add_parser("service", help="Service management")
    service_subparsers = service_parser.add_subparsers(dest="command", help="Service command")

    start_parser = service_subparsers.add_parser("start", help="Start services")
    start_parser.add_argument("server_name", nargs="?", help="Server name (optional)")

    stop_parser = service_subparsers.add_parser("stop", help="Stop services")
    stop_parser.add_argument("server_name", nargs="?", help="Server name (optional)")

    restart_parser = service_subparsers.add_parser("restart", help="Restart services")
    restart_parser.add_argument("server_name", nargs="?", help="Server name (optional)")

    status_parser = service_subparsers.add_parser("status", help="Show status")
    status_parser.add_argument("server_name", nargs="?", help="Server name (optional)")

    service_subparsers.add_parser("generate", help="Generate docker-compose configuration")

    # Client management group
    client_parser = subparsers.add_parser("client", help="Client management")
    client_subparsers = client_parser.add_subparsers(dest="command", help="Client command")

    add_client_parser = client_subparsers.add_parser("add", help="Add new client")
    add_client_parser.add_argument("server", help="Server name")
    add_client_parser.add_argument("client", help="Client name")

    remove_client_parser = client_subparsers.add_parser("remove", help="Remove client")
    remove_client_parser.add_argument("server", help="Server name")
    remove_client_parser.add_argument("client", help="Client name")

    list_clients_parser = client_subparsers.add_parser("list", help="List clients")
    list_clients_parser.add_argument("server", nargs="?", help="Server name (optional)")

    # Key management group
    key_parser = subparsers.add_parser("key", help="Key management")
    key_subparsers = key_parser.add_subparsers(dest="command", help="Key command")

    generate_keys_parser = key_subparsers.add_parser("generate", help="Generate key pair")
    generate_keys_parser.add_argument("output_dir", nargs="?", help="Output directory (optional)")

    # Server management group
    server_parser = subparsers.add_parser("server", help="Server management")
    server_subparsers = server_parser.add_subparsers(dest="command", help="Server command")

    create_server_parser = server_subparsers.add_parser("create", help="Create new server")
    create_server_parser.add_argument("-n", "--name", required=True, help="Server name")
    create_server_parser.add_argument("-u", "--url", required=True, help="Server URL")
    create_server_parser.add_argument("-p", "--port", type=int, required=True, help="Server port")
    create_server_parser.add_argument("-s", "--subnet", required=True, help="Server subnet")
    create_server_parser.add_argument("-d", "--dns", default="1.1.1.1,8.8.8.8", help="DNS servers")
    create_server_parser.add_argument("-a", "--allowed-ips", default="0.0.0.0/0", help="Allowed IPs")
    create_server_parser.add_argument("-P", "--peers", type=int, default=1, help="Number of peers")

    server_subparsers.add_parser("list", help="List all servers")

    remove_server_parser = server_subparsers.add_parser("remove", help="Remove server")
    remove_server_parser.add_argument("name", help="Server name")
    remove_server_parser.add_argument("--force", action="store_true", help="Force removal")

    return parser

def _parse_argument(args: argparse.Namespace, arg_name: str) -> str | None:
    return getattr(args, arg_name, None)


def _handle_service_command(command: str, server_name: str | None) -> None:
    """Handle service management commands"""
    service_manager = ServiceManager()

    # Validate server name if provided
    if server_name:
        available_servers = service_manager.get_available_servers()
        if server_name not in available_servers:
            Logger.error(f"Unknown server: {server_name}")
            Logger.info("Available servers:")
            for server in available_servers:
                Logger.info(f"  - {server}")
            raise ValueError(f"Unknown server: {server_name}")

    Logger.header(
        f"{command.upper()} SERVICES{' - ' + server_name.upper() if server_name else ''}"
    )

    if command == "start":
        if not service_manager.start(server_name):
            raise RuntimeError("Failed to start services")
        if not server_name:
            service_manager.show_info()
    elif command == "stop":
        if not service_manager.stop(server_name):
            raise RuntimeError("Failed to stop services")
    elif command == "restart":
        if not service_manager.restart(server_name):
            raise RuntimeError("Failed to restart services")
    elif command == "status":
        if not service_manager.status(server_name):
            raise RuntimeError("Failed to get status")
        if not server_name:
            service_manager.show_info()
    elif command == "generate":
        Logger.header("GENERATING DOCKER-COMPOSE CONFIGURATION")
        server_manager = ServerManager()
        if not server_manager.build():
            raise RuntimeError("Failed to generate docker-compose configuration")


def _handle_client_command(command: str, server: str | None, client: str | None = None) -> None:
    """Handle client management commands"""
    if server is None:
        raise ValueError("Server name is required for client commands")

    client_manager = ClientManager()

    if command == "add":
        if client is None:
            Logger.error("Client name is required for add command")
            raise ValueError("Client name is required for add command")
        Logger.header(f"ADDING CLIENT '{client}' TO SERVER '{server}'")
        if not client_manager.add(server, client):
            raise RuntimeError(f"Failed to add client '{client}' to server '{server}'")
    elif command == "remove":
        if client is None:
            Logger.error("Client name is required for remove command")
            raise ValueError("Client name is required for remove command")
        Logger.header(f"REMOVING CLIENT '{client}' FROM SERVER '{server}'")
        if not client_manager.remove(server, client):
            raise RuntimeError(f"Failed to remove client '{client}' from server '{server}'")
    elif command == "list":
        if server:
            Logger.header(f"LISTING CLIENTS - {server.upper()}")
            client_manager.list_clients(server)
        else:
            Logger.header("LISTING ALL CLIENTS")
            client_manager.list_all_clients()


def _handle_key_command(output_dir: str | None) -> None:
    """Handle key management commands"""
    Logger.header("GENERATING WIREGUARD KEYS")
    key_manager = KeyManager()
    if not key_manager.generate(output_dir):
        raise RuntimeError("Failed to generate WireGuard keys")


def _handle_server_command(command: str, args) -> None:
    """Handle server management commands"""
    server_manager = ServerManager()

    if command == "create":
        Logger.header(f"CREATING SERVER '{args.name}'")
        config = ServerCreateConfigData(
            name=args.name,
            url=args.url,
            port=args.port,
            subnet=args.subnet,
            dns=args.dns,
            allowed_ips=args.allowed_ips,
            peers=args.peers,
        )
        if not server_manager.create_server(config):
            raise RuntimeError(f"Failed to create server '{args.name}'")
    elif command == "list":
        Logger.header("LISTING SERVERS")
        server_manager.list_servers()
    elif command == "remove":
        Logger.header(f"REMOVING SERVER '{args.name}'")
        if not server_manager.remove_server(args.name, args.force):
            raise RuntimeError(f"Failed to remove server '{args.name}'")


def main():
    parser = _create_parser()
    args = parser.parse_args()

    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    try:
        # Service management commands
        if args.group == "service":
            server_name = _parse_argument(args, 'server_name')
            _handle_service_command(args.command, server_name)

        # Client management commands
        elif args.group == "client":
            server = _parse_argument(args, 'server')
            client = _parse_argument(args, 'client')
            _handle_client_command(args.command, server, client)

        # Key management commands
        elif args.group == "key":
            output_dir = _parse_argument(args, 'output_dir')
            _handle_key_command(output_dir)

        # Server management commands
        elif args.group == "server":
            _handle_server_command(args.command, args)

    except Exception as e:
        Logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
