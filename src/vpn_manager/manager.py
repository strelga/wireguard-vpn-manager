#!/usr/bin/env python3
"""
WireGuard VPN Orchestration Tool

Unified command-line interface for WireGuard VPN management.
Usage: vpn-manager <group> <command> [options]
"""

import os
import sys
from collections.abc import Callable
from pathlib import Path

import typer

from .clients import ClientManager
from .keys import KeyManager
from .servers.servers import ServerCreateConfigData, ServerManager
from .services import ServiceManager
from .utils import Logger

# Constants for validation
MIN_PORT = 1
MAX_PORT = 65535
CIDR_PARTS_COUNT = 2
MIN_SUBNET_MASK = 0
MAX_SUBNET_MASK = 32

# Create main Typer app
app = typer.Typer(
    name="vpn-manager",
    help="Comprehensive WireGuard VPN management tool",
    add_completion=True,
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Create sub-apps for command groups
service_app = typer.Typer(help="Service management")
client_app = typer.Typer(help="Client management")
key_app = typer.Typer(help="Key management")
server_app = typer.Typer(help="Server management")

# Register sub-apps
app.add_typer(service_app, name="service")
app.add_typer(client_app, name="client")
app.add_typer(key_app, name="key")
app.add_typer(server_app, name="server")


def _prompt_for_input(prompt: str, default: str | None = None, validator: Callable[[str], bool] | None = None) -> str:
    """Prompt user for input with optional default and validation"""
    prompt = f"{prompt} [{default}]: " if default else f"{prompt}: "

    while True:
        try:
            value = input(prompt).strip()
            if not value and default:
                return default
            if validator and not validator(value):
                continue
            return value
        except (EOFError, KeyboardInterrupt):
            Logger.error("\nOperation cancelled by user")
            sys.exit(1)


def _validate_server_name(name: str) -> bool:
    """Validate server name"""
    if not name:
        Logger.error("Server name cannot be empty")
        return False
    if not name.replace("-", "").replace("_", "").isalnum():
        Logger.error("Server name can only contain alphanumeric characters, hyphens, and underscores")
        return False
    return True


def _validate_port(port: str) -> bool:
    """Validate port number"""
    try:
        port_int = int(port)
        if not (MIN_PORT <= port_int <= MAX_PORT):
            Logger.error(f"Port must be between {MIN_PORT} and {MAX_PORT}")
            return False
        return True
    except ValueError:
        Logger.error("Port must be a valid number")
        return False


def _validate_subnet(subnet: str) -> bool:
    """Validate subnet format"""
    if "/" not in subnet:
        Logger.error("Subnet must be in CIDR format (e.g., 10.13.13.0/24)")
        return False
    parts = subnet.split("/")
    if len(parts) != CIDR_PARTS_COUNT:
        Logger.error("Subnet must be in CIDR format (e.g., 10.13.13.0/24)")
        return False
    try:
        mask = int(parts[1])
        if not (MIN_SUBNET_MASK <= mask <= MAX_SUBNET_MASK):
            Logger.error(f"Subnet mask must be between {MIN_SUBNET_MASK} and {MAX_SUBNET_MASK}")
            return False
    except ValueError:
        Logger.error("Subnet mask must be a valid number")
        return False
    return True


def _validate_peers(peers: str) -> bool:
    """Validate number of peers"""
    try:
        peers_int = int(peers)
        if peers_int < 1:
            Logger.error("Number of peers must be at least 1")
            return False
        return True
    except ValueError:
        Logger.error("Number of peers must be a valid number")
        return False


def _interactive_server_create() -> ServerCreateConfigData:
    """Interactively prompt user for server creation parameters"""
    Logger.header("INTERACTIVE SERVER CREATION")
    Logger.info("Please provide the following information:")

    name = _prompt_for_input("Server name", validator=_validate_server_name)
    url = _prompt_for_input("Server URL (e.g., vpn.example.com)")
    port = _prompt_for_input("Server port", "51820", _validate_port)
    subnet = _prompt_for_input("Server subnet (CIDR)", "10.13.13.0/24", _validate_subnet)
    dns = _prompt_for_input("DNS servers", "1.1.1.1,8.8.8.8")
    allowed_ips = _prompt_for_input("Allowed IPs", "0.0.0.0/0")
    peers = _prompt_for_input("Number of peers", "1", _validate_peers)

    return ServerCreateConfigData(
        name=name,
        url=url,
        port=int(port),
        subnet=subnet,
        dns=dns,
        allowed_ips=allowed_ips,
        peers=int(peers),
    )


def _validate_server_name_option(value: str | None) -> str | None:
    """Validate server name option"""
    if value is None:
        return None
    if not _validate_server_name(value):
        raise typer.BadParameter("Server name can only contain alphanumeric characters, hyphens, and underscores")
    return value


def _validate_client_name_option(value: str) -> str:
    """Validate client name option"""
    if not value:
        raise typer.BadParameter("Client name cannot be empty")
    if not value.replace("-", "").replace("_", "").isalnum():
        raise typer.BadParameter("Client name can only contain alphanumeric characters, hyphens, and underscores")
    return value


def _validate_port_option(value: int | None) -> int | None:
    """Validate port option"""
    if value is None:
        return None
    if not (MIN_PORT <= value <= MAX_PORT):
        raise typer.BadParameter(f"Port must be between {MIN_PORT} and {MAX_PORT}")
    return value


def _validate_subnet_option(value: str | None) -> str | None:
    """Validate subnet option"""
    if value is None:
        return None
    if not _validate_subnet(value):
        raise typer.BadParameter("Subnet must be in CIDR format (e.g., 10.13.13.0/24)")
    return value


def _validate_peers_option(value: int) -> int:
    """Validate peers option"""
    if value < 1:
        raise typer.BadParameter("Number of peers must be at least 1")
    return value


# ============================================================================
# Service Management Commands
# ============================================================================

@service_app.command("start")
def service_start(
    server_name: str = typer.Argument(None, help="Server name (optional)"),
) -> None:
    """Start services"""
    service_manager = ServiceManager()

    # Validate server name if provided
    if server_name:
        available_servers = service_manager.get_available_servers()
        if server_name not in available_servers:
            Logger.error(f"Unknown server: {server_name}")
            Logger.info("Available servers:")
            for server in available_servers:
                Logger.info(f"  - {server}")
            raise typer.Exit(1)

    Logger.header(f"START SERVICES{' - ' + server_name.upper() if server_name else ''}")

    if not service_manager.start(server_name):
        Logger.error("Failed to start services")
        raise typer.Exit(1)

    if not server_name:
        service_manager.show_info()


@service_app.command("stop")
def service_stop(
    server_name: str = typer.Argument(None, help="Server name (optional)"),
) -> None:
    """Stop services"""
    service_manager = ServiceManager()

    # Validate server name if provided
    if server_name:
        available_servers = service_manager.get_available_servers()
        if server_name not in available_servers:
            Logger.error(f"Unknown server: {server_name}")
            Logger.info("Available servers:")
            for server in available_servers:
                Logger.info(f"  - {server}")
            raise typer.Exit(1)

    Logger.header(f"STOP SERVICES{' - ' + server_name.upper() if server_name else ''}")

    if not service_manager.stop(server_name):
        Logger.error("Failed to stop services")
        raise typer.Exit(1)


@service_app.command("restart")
def service_restart(
    server_name: str = typer.Argument(None, help="Server name (optional)"),
) -> None:
    """Restart services"""
    service_manager = ServiceManager()

    # Validate server name if provided
    if server_name:
        available_servers = service_manager.get_available_servers()
        if server_name not in available_servers:
            Logger.error(f"Unknown server: {server_name}")
            Logger.info("Available servers:")
            for server in available_servers:
                Logger.info(f"  - {server}")
            raise typer.Exit(1)

    Logger.header(f"RESTART SERVICES{' - ' + server_name.upper() if server_name else ''}")

    if not service_manager.restart(server_name):
        Logger.error("Failed to restart services")
        raise typer.Exit(1)


@service_app.command("status")
def service_status(
    server_name: str = typer.Argument(None, help="Server name (optional)"),
) -> None:
    """Show status"""
    service_manager = ServiceManager()

    # Validate server name if provided
    if server_name:
        available_servers = service_manager.get_available_servers()
        if server_name not in available_servers:
            Logger.error(f"Unknown server: {server_name}")
            Logger.info("Available servers:")
            for server in available_servers:
                Logger.info(f"  - {server}")
            raise typer.Exit(1)

    Logger.header(f"STATUS{' - ' + server_name.upper() if server_name else ''}")

    if not service_manager.status(server_name):
        Logger.error("Failed to get status")
        raise typer.Exit(1)

    if not server_name:
        service_manager.show_info()


@service_app.command("logs")
def service_logs(
    server_name: str = typer.Argument(None, help="Server name (optional)"),
    follow: bool = typer.Option(False, "-f", "--follow", help="Follow log output"),
    tail: int = typer.Option(100, "-t", "--tail", help="Number of lines to show (default: 100)"),
) -> None:
    """Show logs"""
    service_manager = ServiceManager()

    # Validate server name if provided
    if server_name:
        available_servers = service_manager.get_available_servers()
        if server_name not in available_servers:
            Logger.error(f"Unknown server: {server_name}")
            Logger.info("Available servers:")
            for server in available_servers:
                Logger.info(f"  - {server}")
            raise typer.Exit(1)

    Logger.header(f"LOGS{' - ' + server_name.upper() if server_name else ''}")

    if not service_manager.logs(server_name, follow=follow, tail=tail):
        Logger.error("Failed to get logs")
        raise typer.Exit(1)


@service_app.command("generate")
def service_generate() -> None:
    """Generate docker-compose configuration"""
    Logger.header("GENERATING DOCKER-COMPOSE CONFIGURATION")
    server_manager = ServerManager()
    if not server_manager.build():
        Logger.error("Failed to generate docker-compose configuration")
        raise typer.Exit(1)


# ============================================================================
# Client Management Commands
# ============================================================================

@client_app.command("add")
def client_add(
    server: str = typer.Argument(..., help="Server name", callback=_validate_server_name_option),
    client: str = typer.Argument(..., help="Client name", callback=_validate_client_name_option),
) -> None:
    """Add new client"""
    Logger.header(f"ADDING CLIENT '{client}' TO SERVER '{server}'")
    client_manager = ClientManager()
    if not client_manager.add(server, client):
        Logger.error(f"Failed to add client '{client}' to server '{server}'")
        raise typer.Exit(1)


@client_app.command("remove")
def client_remove(
    server: str = typer.Argument(..., help="Server name", callback=_validate_server_name_option),
    client: str = typer.Argument(..., help="Client name", callback=_validate_client_name_option),
) -> None:
    """Remove client"""
    Logger.header(f"REMOVING CLIENT '{client}' FROM SERVER '{server}'")
    client_manager = ClientManager()
    if not client_manager.remove(server, client):
        Logger.error(f"Failed to remove client '{client}' from server '{server}'")
        raise typer.Exit(1)


@client_app.command("list")
def client_list(
    server: str = typer.Argument(None, help="Server name (optional)"),
) -> None:
    """List clients"""
    client_manager = ClientManager()
    if server:
        Logger.header(f"LISTING CLIENTS - {server.upper()}")
        client_manager.list_clients(server)
    else:
        Logger.header("LISTING ALL CLIENTS")
        client_manager.list_all_clients()


# ============================================================================
# Key Management Commands
# ============================================================================

@key_app.command("generate")
def key_generate(
    output_dir: str = typer.Argument(None, help="Output directory (optional)"),
) -> None:
    """Generate key pair"""
    Logger.header("GENERATING WIREGUARD KEYS")
    key_manager = KeyManager()
    if not key_manager.generate(output_dir):
        Logger.error("Failed to generate WireGuard keys")
        raise typer.Exit(1)


# ============================================================================
# Server Management Commands
# ============================================================================

@server_app.command("create")
def server_create(  # noqa: PLR0913
    name: str = typer.Option(None, "-n", "--name", help="Server name", callback=_validate_server_name_option),
    url: str = typer.Option(None, "-u", "--url", help="Server URL"),
    port: int = typer.Option(None, "-p", "--port", help="Server port", callback=_validate_port_option),
    subnet: str = typer.Option(None, "-s", "--subnet", help="Server subnet", callback=_validate_subnet_option),
    dns: str = typer.Option("1.1.1.1,8.8.8.8", "-d", "--dns", help="DNS servers"),
    allowed_ips: str = typer.Option("0.0.0.0/0", "-a", "--allowed-ips", help="Allowed IPs"),
    peers: int = typer.Option(1, "-P", "--peers", help="Number of peers", callback=_validate_peers_option),
) -> None:
    """Create new server (interactive if no args provided)"""
    server_manager = ServerManager()

    # Check if we should use interactive mode
    has_name = name is not None
    has_url = url is not None
    has_port = port is not None
    has_subnet = subnet is not None

    if not has_name and not has_url and not has_port and not has_subnet:
        # Interactive mode - no args provided
        config = _interactive_server_create()
    elif has_name and has_url and has_port and has_subnet:
        # All required args provided - normal mode
        Logger.header(f"CREATING SERVER '{name}'")
        config = ServerCreateConfigData(
            name=name,
            url=url,
            port=port,
            subnet=subnet,
            dns=dns,
            allowed_ips=allowed_ips,
            peers=peers,
        )
    else:
        # Some args provided but not all - error
        Logger.error("Missing required arguments. Please provide all of: -n/--name, -u/--url, -p/--port, -s/--subnet")
        Logger.info("Or run without arguments for interactive mode")
        raise typer.Exit(1)

    if not server_manager.create_server(config):
        Logger.error(f"Failed to create server '{config.name}'")
        raise typer.Exit(1)


@server_app.command("list")
def server_list() -> None:
    """List all servers"""
    Logger.header("LISTING SERVERS")
    server_manager = ServerManager()
    server_manager.list_servers()


@server_app.command("remove")
def server_remove(
    name: str = typer.Argument(..., help="Server name"),
    force: bool = typer.Option(False, "--force", help="Force removal"),
) -> None:
    """Remove server"""
    Logger.header(f"REMOVING SERVER '{name}'")
    server_manager = ServerManager()
    if not server_manager.remove_server(name, force):
        Logger.error(f"Failed to remove server '{name}'")
        raise typer.Exit(1)


# ============================================================================
# Main entry point
# ============================================================================

def main() -> None:
    """Main entry point for the CLI"""
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    try:
        app()
    except Exception as e:
        Logger.error(f"Command failed: {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    main()
