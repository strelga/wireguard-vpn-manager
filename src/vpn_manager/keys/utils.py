#!/usr/bin/env python3
"""
Key generation utilities
"""

from vpn_manager.services import DockerManager
from vpn_manager.utils import Logger


class KeyGenerator:
    """WireGuard key generation utility"""

    @staticmethod
    def generate_keypair() -> tuple[str, str]:
        """Generate WireGuard key pair (private, public)"""
        Logger.info("Using Docker container for key generation")

        # Generate private key
        private_key = DockerManager.run_container(
            "linuxserver/wireguard:latest", ["wg", "genkey"]
        )

        # Generate public key
        public_key = DockerManager.run_container(
            "linuxserver/wireguard:latest", ["wg", "pubkey"], input_data=private_key
        )

        return private_key, public_key

    @staticmethod
    def generate_public_key(private_key: str) -> str:
        """Generate public key from private key using Docker"""
        return DockerManager.run_container(
            "linuxserver/wireguard:latest", ["wg", "pubkey"], input_data=private_key
        )
