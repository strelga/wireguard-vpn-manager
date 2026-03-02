#!/usr/bin/env python3
"""
WireGuard Services Management Module
"""

import subprocess
from pathlib import Path

from .servers.utils import ServerConfig
from .utils import Color, DockerManager, Logger


class ServiceManager:
    """WireGuard service management utility"""

    def __init__(self):
        self.compose_cmd = DockerManager.get_compose_command().split()
        self.server_containers = {}
        self._load_server_containers()

    def _load_server_containers(self):
        """Dynamically load server to container mapping"""
        servers_dir = Path("servers")
        if servers_dir.exists():
            for server_dir in servers_dir.iterdir():
                if server_dir.is_dir():
                    try:
                        wg_config = ServerConfig(server_dir.name)
                        server_info = wg_config.get_server_info()
                        self.server_containers[server_dir.name] = server_info.container_name
                    except Exception:
                        self.server_containers[server_dir.name] = (
                            f"wireguard-{server_dir.name}"
                        )

    def get_available_servers(self) -> list[str]:
        """Get list of available servers"""
        servers = []
        servers_dir = Path("servers")
        if servers_dir.exists():
            for server_dir in servers_dir.iterdir():
                if server_dir.is_dir():
                    servers.append(server_dir.name)
        return sorted(servers)

    def start(self, server_name: str | None = None) -> bool:
        """Start services"""
        try:
            if server_name:
                Logger.info(f"Starting {server_name} server...")
                container_name = self.server_containers.get(server_name)
                if not container_name:
                    Logger.error(f"Unknown server: {server_name}")
                    return False

                subprocess.run(
                    self.compose_cmd + ["up", "-d", container_name], check=True
                )
                Logger.success(f"Server '{server_name}' started successfully")
            else:
                Logger.info("Starting all services...")
                subprocess.run(self.compose_cmd + ["up", "-d"], check=True)
                Logger.success("All services started successfully")

            return True

        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to start services: {e}")
            return False

    def stop(self, server_name: str | None = None) -> bool:
        """Stop services"""
        try:
            if server_name:
                Logger.info(f"Stopping {server_name} server...")
                container_name = self.server_containers.get(server_name)
                if not container_name:
                    Logger.error(f"Unknown server: {server_name}")
                    return False

                subprocess.run(self.compose_cmd + ["stop", container_name], check=True)
                Logger.success(f"Server '{server_name}' stopped successfully")
            else:
                Logger.info("Stopping all services...")
                subprocess.run(self.compose_cmd + ["down"], check=True)
                Logger.success("All services stopped successfully")

            return True

        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to stop services: {e}")
            return False

    def restart(self, server_name: str | None = None) -> bool:
        """Restart services"""
        try:
            if server_name:
                Logger.info(f"Restarting {server_name} server...")
                container_name = self.server_containers.get(server_name)
                if not container_name:
                    Logger.error(f"Unknown server: {server_name}")
                    return False

                subprocess.run(
                    self.compose_cmd + ["restart", container_name], check=True
                )
                Logger.success(f"Server '{server_name}' restarted successfully")
            else:
                Logger.info("Restarting all services...")
                subprocess.run(self.compose_cmd + ["restart"], check=True)
                Logger.success("All services restarted successfully")

            return True

        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to restart services: {e}")
            return False

    def status(self, server_name: str | None = None) -> bool:
        """Show service status"""
        try:
            if server_name:
                Logger.info(f"Status for {server_name} server:")
                container_name = self.server_containers.get(server_name)
                if not container_name:
                    Logger.error(f"Unknown server: {server_name}")
                    return False

                result = subprocess.run(
                    self.compose_cmd + ["ps", container_name],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print(result.stdout)

                Logger.info(f"WireGuard status for {server_name}:")
                try:
                    subprocess.run(
                        self.compose_cmd + ["exec", container_name, "wg", "show"],
                        check=True,
                    )
                except subprocess.CalledProcessError:
                    Logger.warning(f"Could not get WireGuard status for {server_name}")

                Logger.info(f"Recent logs for {server_name}:")
                subprocess.run(
                    self.compose_cmd + ["logs", "--tail=10", container_name], check=True
                )
            else:
                Logger.info("Status for all services:")

                result = subprocess.run(
                    self.compose_cmd + ["ps"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                print(result.stdout)

                Logger.info("WireGuard status for all servers:")
                for server, container in self.server_containers.items():
                    try:
                        Logger.info(f"\n{server}:")
                        subprocess.run(
                            self.compose_cmd + ["exec", container, "wg", "show"],
                            check=True,
                        )
                    except subprocess.CalledProcessError:
                        Logger.warning(f"Could not get WireGuard status for {server}")

                Logger.info("Recent logs for all services:")
                subprocess.run(self.compose_cmd + ["logs", "--tail=5"], check=True)

            return True

        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get status: {e}")
            return False

    def logs(self, server_name: str | None = None, follow: bool = False, tail: int = 100) -> bool:
        """Show service logs"""
        try:
            if server_name:
                Logger.info(f"Logs for {server_name} server:")
                container_name = self.server_containers.get(server_name)
                if not container_name:
                    Logger.error(f"Unknown server: {server_name}")
                    return False

                cmd = ["logs"]
                if follow:
                    cmd.append("-f")
                cmd.append(f"--tail={tail}")
                cmd.append(container_name)
                subprocess.run(self.compose_cmd + cmd, check=True)
            else:
                Logger.info("Logs for all services:")
                cmd = ["logs"]
                if follow:
                    cmd.append("-f")
                cmd.append(f"--tail={tail}")
                subprocess.run(self.compose_cmd + cmd, check=True)

            return True

        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to get logs: {e}")
            return False

    def show_info(self) -> None:
        """Show general information about services"""
        print(f"\n{Color.BLUE}Available servers:{Color.NC}")
        servers = self.get_available_servers()
        for server in servers:
            container = self.server_containers.get(server, "unknown")
            print(f"  - {server} (container: {container})")

        print(f"\n{Color.BLUE}Service ports:{Color.NC}")
        for server in servers:
            try:
                server_config = ServerConfig(server)
                server_info = server_config.get_server_info()
                print(f"  - {server}: {server_info.port}/udp")
            except Exception:
                print(f"  - {server}: unknown port")

        print(f"\n{Color.BLUE}Useful commands:{Color.NC}")
        print("  - View logs: docker-compose logs -f [container_name]")
        print("  - Execute in container: docker-compose exec <container> /bin/bash")
        print("  - View WireGuard status: docker-compose exec <container> wg show")
