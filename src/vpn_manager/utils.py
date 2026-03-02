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
