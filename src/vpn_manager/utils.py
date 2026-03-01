#!/usr/bin/env python3
"""
Common utilities for WireGuard VPN management scripts
"""

import subprocess


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


def validate_client_name(client_name: str) -> bool:
    """Validate client name"""
    if not client_name or not client_name.replace("-", "").replace("_", "").isalnum():
        Logger.error(
            "Client name must contain only alphanumeric characters, hyphens, and underscores"
        )
        return False
    return True
