"""
Tests for keys/utils.py module - KeyGenerator class
"""

from unittest.mock import MagicMock, patch

from vpn_manager.keys import KeyGenerator


class TestKeyGenerator:
    """Test KeyGenerator class"""

    @patch("vpn_manager.keys.utils.DockerManager")
    def test_generate_keypair(self, mock_docker: MagicMock) -> None:
        """Test generate_keypair using Docker"""
        # Mock the DockerManager.run_container calls
        mock_docker.run_container.side_effect = [
            "private_key",
            "public_key",
        ]

        private_key, public_key = KeyGenerator.generate_keypair()
        assert private_key == "private_key"
        assert public_key == "public_key"
        assert mock_docker.run_container.call_count == 2

    @patch("vpn_manager.keys.utils.DockerManager")
    def test_generate_public_key(self, mock_docker: MagicMock) -> None:
        """Test generate_public_key using Docker"""
        mock_docker.run_container.return_value = "public_key"

        public_key = KeyGenerator.generate_public_key("private_key")
        assert public_key == "public_key"
        mock_docker.run_container.assert_called_once_with(
            "linuxserver/wireguard:latest", ["wg", "pubkey"], input_data="private_key"
        )
