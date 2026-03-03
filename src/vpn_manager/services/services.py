#!/usr/bin/env python3
"""
WireGuard Services Management Module
"""


from vpn_manager.servers.config import load_service_config
from vpn_manager.servers.utils import (
    get_container_name,
    get_servers_dir,
)
from vpn_manager.utils import Color, Logger

from .docker import DockerComposeManager


class ServiceManager:
    """WireGuard service management utility"""

    _docker_compose_manager: DockerComposeManager
    _server_containers: dict[str, str]

    def __init__(self):
        self._docker_compose_manager = DockerComposeManager()
        self._server_containers = {}
        self._load_server_containers()

    def _load_server_containers(self):
        """Dynamically load server to container mapping"""
        servers_dir = get_servers_dir()
        if servers_dir.exists():
            for server_dir in servers_dir.iterdir():
                if server_dir.is_dir():
                    try:
                        service_config = load_service_config(server_dir.name)
                        self._server_containers[server_dir.name] = service_config.container_name
                    except Exception:
                        self._server_containers[server_dir.name] = get_container_name(server_dir.name)

    def get_available_servers(self) -> list[str]:
        """Get list of available servers"""
        servers = []
        servers_dir = get_servers_dir()
        if servers_dir.exists():
            for server_dir in servers_dir.iterdir():
                if server_dir.is_dir():
                    servers.append(server_dir.name)
        return sorted(servers)

    def start(self, server_name: str | None = None) -> bool:
        """Start services"""
        if server_name:
            Logger.info(f"Starting {server_name} server...")
            container_name = self._server_containers.get(server_name)
            if not container_name:
                Logger.error(f"Unknown server: {server_name}")
                return False

            if self._docker_compose_manager.start_container(container_name):
                Logger.success(f"Server '{server_name}' started successfully")
                return True
            return False
        else:
            Logger.info("Starting all services...")
            if self._docker_compose_manager.start_services():
                Logger.success("All services started successfully")
                return True
            return False

    def stop(self, server_name: str | None = None) -> bool:
        """Stop services"""
        if server_name:
            Logger.info(f"Stopping {server_name} server...")
            container_name = self._server_containers.get(server_name)
            if not container_name:
                Logger.error(f"Unknown server: {server_name}")
                return False

            if self._docker_compose_manager.stop_container(container_name):
                Logger.success(f"Server '{server_name}' stopped successfully")
                return True
            return False
        else:
            Logger.info("Stopping all services...")
            if self._docker_compose_manager.stop_services():
                Logger.success("All services stopped successfully")
                return True
            return False

    def restart(self, server_name: str | None = None) -> bool:
        """Restart services"""
        if server_name:
            Logger.info(f"Restarting {server_name} server...")
            container_name = self._server_containers.get(server_name)
            if not container_name:
                Logger.error(f"Unknown server: {server_name}")
                return False

            if self._docker_compose_manager.restart_container(container_name):
                Logger.success(f"Server '{server_name}' restarted successfully")
                return True
            return False
        else:
            Logger.info("Restarting all services...")
            if self._docker_compose_manager.restart_all_services():
                Logger.success("All services restarted successfully")
                return True
            return False

    def status(self, server_name: str | None = None) -> bool:
        """Show service status"""
        if server_name:
            Logger.info(f"Status for {server_name} server:")
            container_name = self._server_containers.get(server_name)
            if not container_name:
                Logger.error(f"Unknown server: {server_name}")
                return False

            result = self._docker_compose_manager.get_container_status(container_name=container_name)
            if result:
                print(result)

            Logger.info(f"WireGuard status for {server_name}:")
            if not self._docker_compose_manager.exec_container(container_name=container_name, command=["wg", "show"]):
                Logger.warning(f"Could not get WireGuard status for {server_name}")

            Logger.info(f"Recent logs for {server_name}:")
            self._docker_compose_manager.get_container_logs(container_name=container_name, follow=False, tail=10)
        else:
            Logger.info("Status for all services:")

            result = self._docker_compose_manager.get_container_status(container_name=None)
            if result:
                print(result)

            Logger.info("WireGuard status for all servers:")
            for server, container in self._server_containers.items():
                Logger.info(f"\n{server}:")
                if not self._docker_compose_manager.exec_container(container_name=container, command=["wg", "show"]):
                    Logger.warning(f"Could not get WireGuard status for {server}")

            Logger.info("Recent logs for all services:")
            self._docker_compose_manager.get_container_logs(container_name=None, follow=False, tail=5)

        return True

    def logs(self, server_name: str | None = None, follow: bool = False, tail: int = 100) -> bool:
        """Show service logs"""
        if server_name:
            Logger.info(f"Logs for {server_name} server:")
            container_name = self._server_containers.get(server_name)
            if not container_name:
                Logger.error(f"Unknown server: {server_name}")
                return False

            return self._docker_compose_manager.get_container_logs(container_name=container_name, follow=follow, tail=tail)
        else:
            Logger.info("Logs for all services:")
            return self._docker_compose_manager.get_container_logs(container_name=None, follow=follow, tail=tail)

    def show_info(self) -> None:
        """Show general information about services"""
        print(f"\n{Color.BLUE}Available servers:{Color.NC}")
        servers = self.get_available_servers()
        for server in servers:
            container = self._server_containers.get(server, "unknown")
            print(f"  - {server} (container: {container})")

        print(f"\n{Color.BLUE}Service ports:{Color.NC}")
        for server in servers:
            try:
                service_config = load_service_config(server)
                print(f"  - {server}: {service_config.server_port}/udp")
            except Exception:
                print(f"  - {server}: unknown port")

        print(f"\n{Color.BLUE}Useful commands:{Color.NC}")
        print("  - View logs: docker-compose logs -f [container_name]")
        print("  - Execute in container: docker-compose exec <container> /bin/bash")
        print("  - View WireGuard status: docker-compose exec <container> wg show")
