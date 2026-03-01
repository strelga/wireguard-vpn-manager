#!/usr/bin/env python3
"""
Common utilities for WireGuard VPN management scripts
"""

import ipaddress
import subprocess
from pathlib import Path
from typing import Any

import yaml


class Color:
    """ANSI color codes for terminal output"""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[1;37m"
    NC = "\033[0m"  # No Color


class Logger:
    """Colored logging utility"""

    @staticmethod
    def info(message: str) -> None:
        print(f"{Color.BLUE}[INFO]{Color.NC} {message}")

    @staticmethod
    def success(message: str) -> None:
        print(f"{Color.GREEN}[SUCCESS]{Color.NC} {message}")

    @staticmethod
    def warning(message: str) -> None:
        print(f"{Color.YELLOW}[WARNING]{Color.NC} {message}")

    @staticmethod
    def error(message: str) -> None:
        print(f"{Color.RED}[ERROR]{Color.NC} {message}")

    @staticmethod
    def header(message: str) -> None:
        print(f"\n{Color.BLUE}=== {message} ==={Color.NC}\n")


class WireGuardConfig:
    """WireGuard configuration management"""

    def __init__(self, server_name: str):
        self.server_name = server_name
        self.server_dir = Path(f"servers/{server_name}")
        self.config_dir = self.server_dir / "config"
        self.clients_dir = self.server_dir / "clients"
        self.wg_config_file = self.config_dir / "wg_confs" / "wg0.conf"
        self.docker_compose_file = self.server_dir / "docker-compose.yml"

        # Ensure directories exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.clients_dir.mkdir(parents=True, exist_ok=True)
        (self.config_dir / "wg_confs").mkdir(parents=True, exist_ok=True)

    def get_server_info(self) -> dict[str, Any]:
        """Get server configuration from docker-compose.yml and .env"""
        if not self.docker_compose_file.exists():
            raise FileNotFoundError(
                f"Docker compose file not found: {self.docker_compose_file}"
            )

        # Load docker-compose.yml
        with open(self.docker_compose_file) as f:
            compose_config = yaml.safe_load(f)

        # Find the wireguard service (should be the first/only service)
        services = compose_config.get("services", {})
        if not services:
            raise ValueError(f"No services found in {self.docker_compose_file}")

        # Get the first service (wireguard service)
        service_name = list(services.keys())[0]
        service_config = services[service_name]

        # Extract environment variables
        env_vars = {}
        env_list = service_config.get("environment", [])

        for env_item in env_list:
            if isinstance(env_item, str):
                if "=" in env_item:
                    key, value = env_item.split("=", 1)
                    env_vars[key.strip()] = value.strip()
                else:
                    # Environment variable reference like ${VAR}
                    env_vars[env_item.strip()] = self._resolve_env_var(env_item.strip())
            elif isinstance(env_item, dict):
                env_vars.update(env_item)

        # Extract port mapping
        ports = service_config.get("ports", [])
        server_port = None
        for port_mapping in ports:
            if isinstance(port_mapping, str) and "/udp" in port_mapping:
                # Format: "51820:51820/udp"
                external_port = port_mapping.split(":")[0]
                server_port = int(external_port)
                break

        # Build server info
        server_info = {
            "subnet": env_vars.get("INTERNAL_SUBNET", ""),
            "server_url": self._resolve_env_var(env_vars.get("SERVERURL", "")),
            "server_port": server_port or int(env_vars.get("SERVERPORT", 51820)),
            "dns": env_vars.get("PEERDNS", ""),
            "allowed_ips": env_vars.get("ALLOWEDIPS", ""),
            "container_name": service_config.get("container_name", service_name),
        }

        return server_info

    def _resolve_env_var(self, value: str) -> str:
        """Resolve environment variable references like ${VAR}"""
        if not value or not value.startswith("${") or not value.endswith("}"):
            return value

        var_name = value[2:-1]  # Remove ${ and }
        env_vars = self._load_env_vars()
        return env_vars.get(var_name, value)

    def _load_env_vars(self) -> dict[str, str]:
        """Load environment variables from .env file"""
        env_vars = {}
        env_file = Path(".env")

        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    stripped_line = line.strip()
                    if stripped_line and not stripped_line.startswith("#") and "=" in stripped_line:
                        key, value = stripped_line.split("=", 1)
                        env_vars[key.strip()] = value.strip()

        return env_vars

    def get_next_client_ip(self) -> str:
        """Find next available IP address in server subnet"""
        server_info = self.get_server_info()
        network = ipaddress.IPv4Network(server_info["subnet"])

        # Server uses .1, start from .2
        used_ips = {network.network_address + 1}  # Server IP

        # Parse existing config to find used IPs
        if self.wg_config_file.exists():
            with open(self.wg_config_file) as f:
                content = f.read()

            # Find all Address lines in [Peer] sections
            lines = content.split("\n")
            in_peer = False

            for line in lines:
                stripped_line = line.strip()
                if stripped_line.startswith("[Peer]"):
                    in_peer = True
                elif stripped_line.startswith("[") and stripped_line != "[Peer]":
                    in_peer = False
                elif in_peer and stripped_line.startswith("Address"):
                    # Extract IP from "Address = 10.13.13.2/32"
                    try:
                        ip_str = stripped_line.split("=")[1].strip().split("/")[0]
                        used_ips.add(ipaddress.IPv4Address(ip_str))
                    except (ValueError, IndexError):
                        continue

        # Find first available IP
        for ip in network.hosts():
            if ip not in used_ips:
                return str(ip)

        raise RuntimeError(
            f"No available IP addresses in subnet {server_info['subnet']}"
        )


class KeyGenerator:
    """WireGuard key generation utility"""

    @staticmethod
    def command_exists(command: str) -> bool:
        """Check if command exists in PATH"""
        try:
            subprocess.run([command, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def generate_keypair() -> tuple[str, str]:
        """Generate WireGuard key pair (private, public)"""

        # Try local wg command first
        if KeyGenerator.command_exists("wg"):
            Logger.info("Using local WireGuard tools")
            return KeyGenerator._generate_with_wg()

        # Fallback to Docker
        elif KeyGenerator.command_exists("docker"):
            Logger.info("Using Docker container for key generation")
            return KeyGenerator._generate_with_docker()

        else:
            raise RuntimeError("Neither WireGuard tools nor Docker are available")

    @staticmethod
    def _generate_with_wg() -> tuple[str, str]:
        """Generate keys using local wg command"""
        # Generate private key
        result = subprocess.run(
            ["wg", "genkey"], capture_output=True, text=True, check=True
        )
        private_key = result.stdout.strip()

        # Generate public key
        result = subprocess.run(
            ["wg", "pubkey"],
            input=private_key,
            capture_output=True,
            text=True,
            check=True,
        )
        public_key = result.stdout.strip()

        return private_key, public_key

    @staticmethod
    def _generate_with_docker() -> tuple[str, str]:
        """Generate keys using Docker container"""
        # Generate private key
        result = subprocess.run(
            ["docker", "run", "--rm", "linuxserver/wireguard:latest", "wg", "genkey"],
            capture_output=True,
            text=True,
            check=True,
        )
        private_key = result.stdout.strip()

        # Generate public key
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
        public_key = result.stdout.strip()

        return private_key, public_key


class DockerManager:
    """Docker Compose management utility"""

    @staticmethod
    def get_compose_command() -> str:
        """Determine available docker-compose command"""
        if DockerManager._command_exists("docker-compose"):
            return "docker-compose"
        elif DockerManager._command_exists("docker"):
            # Check if 'docker compose' works
            try:
                subprocess.run(
                    ["docker", "compose", "version"], capture_output=True, check=True
                )
                return "docker compose"
            except subprocess.CalledProcessError:
                pass

        raise RuntimeError("Neither docker-compose nor 'docker compose' is available")

    @staticmethod
    def _command_exists(command: str) -> bool:
        """Check if command exists"""
        try:
            subprocess.run([command, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    @staticmethod
    def restart_container(container_name: str) -> bool:
        """Restart specific container"""
        try:
            compose_cmd = DockerManager.get_compose_command().split()
            subprocess.run(
                compose_cmd + ["restart", container_name],
                check=True,
                capture_output=True,
            )
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to restart container {container_name}: {e}")
            return False

    @staticmethod
    def start_services() -> bool:
        """Start all services"""
        try:
            compose_cmd = DockerManager.get_compose_command().split()
            subprocess.run(compose_cmd + ["up", "-d"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to start services: {e}")
            return False

    @staticmethod
    def stop_services() -> bool:
        """Stop all services"""
        try:
            compose_cmd = DockerManager.get_compose_command().split()
            subprocess.run(compose_cmd + ["down"], check=True)
            return True
        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to stop services: {e}")
            return False


class QRCodeGenerator:
    """QR code generation utility"""

    @staticmethod
    def generate_qr(content: str, output_file: str | None = None) -> bool:
        """Generate QR code for given content"""
        if not QRCodeGenerator._command_exists("qrencode"):
            Logger.warning("qrencode not installed - QR code will not be generated")
            Logger.info(
                "To install: sudo apt install qrencode (Ubuntu/Debian) or brew install qrencode (macOS)"
            )
            return False

        try:
            cmd = ["qrencode", "-t", "ansiutf8"]
            if output_file:
                cmd.extend(["-o", output_file])

            result = subprocess.run(
                cmd, input=content, text=True, capture_output=True, check=True
            )

            if not output_file:
                print(result.stdout)

            return True

        except subprocess.CalledProcessError as e:
            Logger.error(f"Failed to generate QR code: {e}")
            return False

    @staticmethod
    def _command_exists(command: str) -> bool:
        """Check if command exists"""
        try:
            subprocess.run([command, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def validate_server_name(server_name: str) -> bool:
    """Validate server name"""
    server_dir = Path(f"servers/{server_name}")
    if not server_dir.exists():
        Logger.error(f"Server '{server_name}' not found")
        Logger.info("Available servers:")
        servers_dir = Path("servers")
        if servers_dir.exists():
            for server in servers_dir.iterdir():
                if server.is_dir():
                    Logger.info(f"  - {server.name}")
        return False
    return True


def validate_client_name(client_name: str) -> bool:
    """Validate client name"""
    if not client_name or not client_name.replace("-", "").replace("_", "").isalnum():
        Logger.error(
            "Client name must contain only alphanumeric characters, hyphens, and underscores"
        )
        return False
    return True
