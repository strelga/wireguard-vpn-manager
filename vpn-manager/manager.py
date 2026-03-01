#!/usr/bin/env python3
"""
WireGuard VPN Orchestration Tool

Unified command-line interface for WireGuard VPN management.
Usage: python3 manager.py <command> [options]
"""

import argparse
import sys
from pathlib import Path

from clients import ClientManager
from keys import KeyManager
from servers import ServerManager
from services import ServiceManager
from utils import Logger


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive WireGuard VPN management tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  Service Management:
    start [server_name]     - Start services (all or specific server)
    stop [server_name]      - Stop services (all or specific server)
    restart [server_name]   - Restart services (all or specific server)
    status [server_name]    - Show status (all or specific server)

  Client Management:
    add-client <server> <client>    - Add new client
    remove-client <server> <client> - Remove client
    list-clients [server]           - List clients

  Key Management:
    generate-keys [output_dir]      - Generate key pair

  Server Management:
    create-server <name> <url> <port> <subnet> [dns] [allowed_ips] - Create new server
    list-servers                    - List all servers
    remove-server <name> [--force]  - Remove server

Examples:
  vpn-manager start                        # Start all services
  vpn-manager start internet               # Start internet gateway
  vpn-manager add-client internet phone    # Add phone client
  vpn-manager remove-client tunnel laptop  # Remove laptop client
  vpn-manager list-clients                 # List all clients
  vpn-manager generate-keys /tmp/keys      # Generate keys to directory
        """,
    )

    parser.add_argument(
        "command",
        choices=[
            "start",
            "stop",
            "restart",
            "status",
            "add-client",
            "remove-client",
            "list-clients",
            "generate-keys",
            "create-server",
            "list-servers",
            "remove-server",
        ],
        help="Command to execute",
    )

    parser.add_argument("args", nargs="*", help="Command arguments")

    args = parser.parse_args()

    # Change to project root directory
    project_root = Path(__file__).parent.parent
    import os

    os.chdir(project_root)

    try:
        success = True

        # Service management commands
        if args.command in ["start", "stop", "restart", "status"]:
            service_manager = ServiceManager()
            server_name = args.args[0] if args.args else None

            # Validate server name if provided
            if server_name:
                available_servers = service_manager.get_available_servers()
                if server_name not in available_servers:
                    Logger.error(f"Unknown server: {server_name}")
                    Logger.info("Available servers:")
                    for server in available_servers:
                        Logger.info(f"  - {server}")
                    sys.exit(1)

            Logger.header(
                f"{args.command.upper()} SERVICES{' - ' + server_name.upper() if server_name else ''}"
            )

            if args.command == "start":
                success = service_manager.start(server_name)
                if success and not server_name:
                    service_manager.show_info()
            elif args.command == "stop":
                success = service_manager.stop(server_name)
            elif args.command == "restart":
                success = service_manager.restart(server_name)
            elif args.command == "status":
                success = service_manager.status(server_name)
                if success and not server_name:
                    service_manager.show_info()

        # Client management commands
        elif args.command == "add-client":
            if len(args.args) != 2:
                Logger.error("add-client requires server name and client name")
                Logger.info("Usage: vpn-manager add-client <server> <client>")
                sys.exit(1)

            server_name, client_name = args.args
            Logger.header(f"ADDING CLIENT '{client_name}' TO SERVER '{server_name}'")

            client_manager = ClientManager()
            success = client_manager.add(server_name, client_name)

        elif args.command == "remove-client":
            if len(args.args) != 2:
                Logger.error("remove-client requires server name and client name")
                Logger.info("Usage: vpn-manager remove-client <server> <client>")
                sys.exit(1)

            server_name, client_name = args.args
            Logger.header(
                f"REMOVING CLIENT '{client_name}' FROM SERVER '{server_name}'"
            )

            client_manager = ClientManager()
            success = client_manager.remove(server_name, client_name)

        elif args.command == "list-clients":
            client_manager = ClientManager()

            if args.args:
                server_name = args.args[0]
                Logger.header(f"LISTING CLIENTS - {server_name.upper()}")
                client_manager.list_clients(server_name)
            else:
                Logger.header("LISTING ALL CLIENTS")
                client_manager.list_all_clients()

        # Key management commands
        elif args.command == "generate-keys":
            output_dir = args.args[0] if args.args else None
            Logger.header("GENERATING WIREGUARD KEYS")

            key_manager = KeyManager()
            success = key_manager.generate(output_dir)

        # Server management commands
        elif args.command == "create-server":
            if len(args.args) < 4:
                Logger.error("create-server requires name, url, port, and subnet")
                Logger.info("Usage: vpn-manager create-server <name> <url> <port> <subnet> [dns] [allowed_ips]")
                sys.exit(1)

            server_name = args.args[0]
            server_url = args.args[1]
            try:
                port = int(args.args[2])
            except ValueError:
                Logger.error("Port must be a number")
                sys.exit(1)

            subnet = args.args[3]
            dns = args.args[4] if len(args.args) > 4 else "1.1.1.1,8.8.8.8"
            allowed_ips = args.args[5] if len(args.args) > 5 else "0.0.0.0/0"

            Logger.header(f"CREATING SERVER '{server_name}'")

            server_manager = ServerManager()
            success = server_manager.create_server(server_name, server_url, port, subnet, dns, allowed_ips)

        elif args.command == "list-servers":
            Logger.header("LISTING SERVERS")

            server_manager = ServerManager()
            server_manager.list_servers()

        elif args.command == "remove-server":
            if len(args.args) < 1:
                Logger.error("remove-server requires server name")
                Logger.info("Usage: vpn-manager remove-server <name> [--force]")
                sys.exit(1)

            server_name = args.args[0]
            force = "--force" in args.args

            Logger.header(f"REMOVING SERVER '{server_name}'")

            server_manager = ServerManager()
            success = server_manager.remove_server(server_name, force)

        if not success:
            sys.exit(1)

    except Exception as e:
        Logger.error(f"Command failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
