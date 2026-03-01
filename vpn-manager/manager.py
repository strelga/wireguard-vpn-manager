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

from clients import ClientManager
from keys import KeyManager
from servers import ServerCreateConfig, ServerManager
from services import ServiceManager
from utils import Logger


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
  vpn-manager service start internet           - Start internet gateway
  vpn-manager service generate                 - Generate docker-compose configuration
  vpn-manager client add internet phone        - Add phone client
  vpn-manager client remove tunnel laptop      - Remove laptop client
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


def _handle_service_command(command: str, server_name: str | None) -> bool:
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
            return False

    Logger.header(
        f"{command.upper()} SERVICES{' - ' + server_name.upper() if server_name else ''}"
    )

    if command == "start":
        success = service_manager.start(server_name)
        if success and not server_name:
            service_manager.show_info()
    elif command == "stop":
        success = service_manager.stop(server_name)
    elif command == "restart":
        success = service_manager.restart(server_name)
    elif command == "status":
        success = service_manager.status(server_name)
        if success and not server_name:
            service_manager.show_info()
    elif command == "generate":
        Logger.header("GENERATING DOCKER-COMPOSE CONFIGURATION")
        server_manager = ServerManager()
        success = server_manager.build()

    return success


def _handle_client_command(command: str, server: str, client: str | None = None) -> bool:
    """Handle client management commands"""
    client_manager = ClientManager()

    if command == "add":
        Logger.header(f"ADDING CLIENT '{client}' TO SERVER '{server}'")
        return client_manager.add(server, client)
    elif command == "remove":
        Logger.header(f"REMOVING CLIENT '{client}' FROM SERVER '{server}'")
        return client_manager.remove(server, client)
    elif command == "list":
        if server:
            Logger.header(f"LISTING CLIENTS - {server.upper()}")
            client_manager.list_clients(server)
        else:
            Logger.header("LISTING ALL CLIENTS")
            client_manager.list_all_clients()
        return True

    return False


def _handle_key_command(output_dir: str | None) -> bool:
    """Handle key management commands"""
    Logger.header("GENERATING WIREGUARD KEYS")
    key_manager = KeyManager()
    return key_manager.generate(output_dir)


def _handle_server_command(command: str, args) -> bool:
    """Handle server management commands"""
    server_manager = ServerManager()

    if command == "create":
        Logger.header(f"CREATING SERVER '{args.name}'")
        config = ServerCreateConfig(
            name=args.name,
            url=args.url,
            port=args.port,
            subnet=args.subnet,
            dns=args.dns,
            allowed_ips=args.allowed_ips,
            peers=args.peers,
        )
        return server_manager.create_server(config)
    elif command == "list":
        Logger.header("LISTING SERVERS")
        server_manager.list_servers()
        return True
    elif command == "remove":
        Logger.header(f"REMOVING SERVER '{args.name}'")
        return server_manager.remove_server(args.name, args.force)

    return False


def main():
    parser = _create_parser()
    args = parser.parse_args()

    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    try:
        success = True

        # Service management commands
        if args.group == "service":
            success = _handle_service_command(args.command, args.server_name)

        # Client management commands
        elif args.group == "client":
            success = _handle_client_command(args.command, args.server, args.client)

        # Key management commands
        elif args.group == "key":
            success = _handle_key_command(args.output_dir)

        # Server management commands
        elif args.group == "server":
            success = _handle_server_command(args.command, args)

        if not success:
            sys.exit(1)

    except Exception as e:
        Logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
