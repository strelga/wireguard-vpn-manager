"""
Tests for utils.py module
"""

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

from vpn_manager.servers.utils import ServerConfig, validate_server_name
from vpn_manager.utils import (
    Color,
    DockerManager,
    KeyGenerator,
    Logger,
    QRCodeGenerator,
    validate_client_name,
)


class TestColor:
    """Test Color class"""

    def test_color_constants(self) -> None:
        """Test that all color constants are defined"""
        assert hasattr(Color, "RED")
        assert hasattr(Color, "GREEN")
        assert hasattr(Color, "YELLOW")
        assert hasattr(Color, "BLUE")
        assert hasattr(Color, "PURPLE")
        assert hasattr(Color, "CYAN")
        assert hasattr(Color, "WHITE")
        assert hasattr(Color, "NC")

    def test_color_values(self) -> None:
        """Test that color values are ANSI codes"""
        assert Color.RED == "\033[0;31m"
        assert Color.GREEN == "\033[0;32m"
        assert Color.NC == "\033[0m"


class TestLogger:
    """Test Logger class"""

    @patch("builtins.print")
    def test_info(self, mock_print: MagicMock) -> None:
        """Test info logging"""
        Logger.info("Test message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "[INFO]" in args
        assert "Test message" in args

    @patch("builtins.print")
    def test_success(self, mock_print: MagicMock) -> None:
        """Test success logging"""
        Logger.success("Test message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "[SUCCESS]" in args
        assert "Test message" in args

    @patch("builtins.print")
    def test_warning(self, mock_print: MagicMock) -> None:
        """Test warning logging"""
        Logger.warning("Test message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "[WARNING]" in args
        assert "Test message" in args

    @patch("builtins.print")
    def test_error(self, mock_print: MagicMock) -> None:
        """Test error logging"""
        Logger.error("Test message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "[ERROR]" in args
        assert "Test message" in args

    @patch("builtins.print")
    def test_header(self, mock_print: MagicMock) -> None:
        """Test header logging"""
        Logger.header("Test Header")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "Test Header" in args


class TestValidateClientName:
    """Test validate_client_name function"""

    @patch("vpn_manager.utils.Logger")
    def test_valid_client_name(self, mock_logger: MagicMock) -> None:
        """Test valid client names"""
        assert validate_client_name("client1") is True
        assert validate_client_name("client-1") is True
        assert validate_client_name("client_1") is True
        assert validate_client_name("Client-Name_123") is True

    @patch("vpn_manager.utils.Logger")
    def test_invalid_client_name_empty(self, mock_logger: MagicMock) -> None:
        """Test empty client name"""
        assert validate_client_name("") is False
        mock_logger.error.assert_called_once()

    @patch("vpn_manager.utils.Logger")
    def test_invalid_client_name_special_chars(self, mock_logger: MagicMock) -> None:
        """Test client name with special characters"""
        assert validate_client_name("client@1") is False
        assert validate_client_name("client#1") is False
        assert validate_client_name("client 1") is False
        mock_logger.error.assert_called()


class TestValidateServerName:
    """Test validate_server_name function"""

    def test_valid_server_name(self, tmp_dir: Path) -> None:
        """Test valid server name that exists"""
        server_dir = tmp_dir / "servers" / "test-server"
        server_dir.mkdir(parents=True)
        assert validate_server_name("test-server") is True

    def test_invalid_server_name_not_exists(self, tmp_dir: Path) -> None:
        """Test server name that doesn't exist"""
        assert validate_server_name("nonexistent") is False


class TestWireGuardConfig:
    """Test WireGuardConfig class"""

    def test_init_creates_directories(self, tmp_dir: Path) -> None:
        """Test that initialization creates necessary directories"""
        config = ServerConfig("test-server")
        assert config.server_name == "test-server"
        assert config.server_dir.exists()
        assert config.clients_dir.exists()

    def test_get_server_info_missing_config_file(self, tmp_dir: Path) -> None:
        """Test get_server_info when config.yml is missing"""
        config = ServerConfig("test-server")
        with pytest.raises(FileNotFoundError):
            config.get_server_info()

    def test_get_server_info_success(self, tmp_dir: Path, sample_server_config: dict[str, Any]) -> None:
        """Test successful retrieval of server info"""
        config = ServerConfig("test-server")
        config.server_config_file.write_text(yaml.dump(sample_server_config))

        server_info = config.get_server_info()
        assert server_info.subnet == "10.13.13.0/24"
        assert server_info.port == 51820
        assert server_info.dns == "1.1.1.1,8.8.8.8"
        assert server_info.allowed_ips == "0.0.0.0/0"

    def test_resolve_env_var_no_reference(self) -> None:
        """Test _resolve_env_var with no environment variable reference"""
        config = ServerConfig("test-server")
        assert config._resolve_env_var("plain_value") == "plain_value"

    def test_resolve_env_var_with_reference(self, tmp_dir: Path) -> None:
        """Test _resolve_env_var with environment variable reference"""
        config = ServerConfig("test-server")
        env_file = tmp_dir / ".env"
        env_file.write_text("TEST_VAR=test_value\n")

        result = config._resolve_env_var("${TEST_VAR}")
        assert result == "test_value"

    def test_load_env_vars(self, tmp_dir: Path) -> None:
        """Test _load_env_vars"""
        config = ServerConfig("test-server")
        env_file = tmp_dir / ".env"
        env_file.write_text("VAR1=value1\nVAR2=value2\n# Comment\nVAR3=value3\n")

        env_vars = config._load_env_vars()
        assert env_vars["VAR1"] == "value1"
        assert env_vars["VAR2"] == "value2"
        assert env_vars["VAR3"] == "value3"
        assert "Comment" not in env_vars

    def test_get_next_client_ip_no_existing_clients(self, tmp_dir: Path, sample_server_config: dict[str, Any]) -> None:
        """Test get_next_client_ip when no clients exist"""
        config = ServerConfig("test-server")
        config.server_config_file.write_text(yaml.dump(sample_server_config))
        config.wg_config_file.write_text("[Interface]\nPrivateKey = test\nAddress = 10.13.13.1/24\n")

        next_ip = config.get_next_client_ip()
        assert next_ip == "10.13.13.2"

    def test_get_next_client_ip_with_existing_clients(self, tmp_dir: Path, sample_server_config: dict[str, Any], sample_wg_config: str) -> None:
        """Test get_next_client_ip when clients exist"""
        config = ServerConfig("test-server")
        config.server_config_file.write_text(yaml.dump(sample_server_config))
        config.wg_config_file.write_text(sample_wg_config)

        next_ip = config.get_next_client_ip()
        assert next_ip == "10.13.13.2"

    def test_get_next_client_ip_no_available_ips(self, tmp_dir: Path, sample_server_config: dict[str, Any]) -> None:
        """Test get_next_client_ip when no IPs are available"""
        config = ServerConfig("test-server")
        config.server_config_file.write_text(yaml.dump(sample_server_config))

        # Create a config with all IPs used
        # In a /24 network, hosts() gives us .2 to .254 (253 hosts)
        # Server uses .1, so we need to use all .2 to .254
        wg_config = "[Interface]\nPrivateKey = test\nAddress = 10.13.13.1/24\n"
        for i in range(2, 255):  # Use all available IPs (.2 to .254)
            wg_config += f"\n# Client: client{i}\n[Peer]\nPublicKey = key{i}\nAllowedIPs = 10.13.13.{i}/32\n"
        config.wg_config_file.write_text(wg_config)

        # The implementation should raise RuntimeError when all IPs are used
        # Note: The function looks for "Address" in [Peer] sections, but the sample config
        # uses "AllowedIPs" instead. We need to add Address lines to properly test this.
        wg_config_with_address = "[Interface]\nPrivateKey = test\nAddress = 10.13.13.1/24\n"
        for i in range(2, 255):  # Use all available IPs (.2 to .254)
            wg_config_with_address += f"\n# Client: client{i}\n[Peer]\nPublicKey = key{i}\nAllowedIPs = 10.13.13.{i}/32\nAddress = 10.13.13.{i}/32\n"
        config.wg_config_file.write_text(wg_config_with_address)

        with pytest.raises(RuntimeError):
            config.get_next_client_ip()


class TestKeyGenerator:
    """Test KeyGenerator class"""

    @patch("subprocess.run")
    def test_command_exists_true(self, mock_run: MagicMock) -> None:
        """Test command_exists when command exists"""
        mock_run.return_value = MagicMock()
        assert KeyGenerator.command_exists("wg") is True

    @patch("subprocess.run")
    def test_command_exists_false(self, mock_run: MagicMock) -> None:
        """Test command_exists when command doesn't exist"""
        mock_run.side_effect = FileNotFoundError()
        assert KeyGenerator.command_exists("wg") is False

    @patch("subprocess.run")
    def test_generate_keypair_with_wg(self, mock_run: MagicMock) -> None:
        """Test generate_keypair using local wg command"""
        # Mock command_exists to return True for wg
        with patch.object(KeyGenerator, "command_exists", return_value=True):
            # Mock the subprocess calls
            mock_run.side_effect = [
                MagicMock(stdout="private_key\n"),
                MagicMock(stdout="public_key\n"),
            ]

            private_key, public_key = KeyGenerator.generate_keypair()
            assert private_key == "private_key"
            assert public_key == "public_key"

    @patch("subprocess.run")
    def test_generate_keypair_with_docker(self, mock_run: MagicMock) -> None:
        """Test generate_keypair using Docker"""
        # Mock command_exists to return False for wg and True for docker
        with patch.object(KeyGenerator, "command_exists") as mock_exists:
            mock_exists.side_effect = lambda cmd: cmd == "docker"

            # Mock the subprocess calls
            mock_run.side_effect = [
                MagicMock(stdout="private_key\n"),
                MagicMock(stdout="public_key\n"),
            ]

            private_key, public_key = KeyGenerator.generate_keypair()
            assert private_key == "private_key"
            assert public_key == "public_key"

    @patch("subprocess.run")
    def test_generate_keypair_no_tools(self, mock_run: MagicMock) -> None:
        """Test generate_keypair when no tools are available"""
        with (
            patch.object(KeyGenerator, "command_exists", return_value=False),
            pytest.raises(RuntimeError),
        ):
            KeyGenerator.generate_keypair()


class TestDockerManager:
    """Test DockerManager class"""

    @patch("subprocess.run")
    def test_get_compose_command_docker_compose(self, mock_run: MagicMock) -> None:
        """Test get_compose_command with docker-compose"""
        mock_run.return_value = MagicMock()
        command = DockerManager.get_compose_command()
        assert command == "docker-compose"

    @patch("subprocess.run")
    def test_get_compose_command_docker_compose_v2(self, mock_run: MagicMock) -> None:
        """Test get_compose_command with docker compose v2"""
        # First call fails (docker-compose not found), second succeeds (docker compose)
        mock_run.side_effect = [
            FileNotFoundError(),
            MagicMock(),
            MagicMock(),  # Additional call for version check
        ]
        command = DockerManager.get_compose_command()
        assert command == "docker compose"

    @patch("subprocess.run")
    def test_get_compose_command_not_available(self, mock_run: MagicMock) -> None:
        """Test get_compose_command when neither is available"""
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(RuntimeError):
            DockerManager.get_compose_command()

    @patch("subprocess.run")
    def test_restart_container_success(self, mock_run: MagicMock) -> None:
        """Test successful container restart"""
        mock_run.return_value = MagicMock()
        with patch.object(DockerManager, "get_compose_command", return_value="docker compose"):
            assert DockerManager.restart_container("test-container") is True

    @patch("subprocess.run")
    def test_restart_container_failure(self, mock_run: MagicMock) -> None:
        """Test failed container restart"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker compose")
        with patch.object(DockerManager, "get_compose_command", return_value="docker compose"):
            assert DockerManager.restart_container("test-container") is False

    @patch("subprocess.run")
    def test_start_services_success(self, mock_run: MagicMock) -> None:
        """Test successful services start"""
        mock_run.return_value = MagicMock()
        with patch.object(DockerManager, "get_compose_command", return_value="docker compose"):
            assert DockerManager.start_services() is True

    @patch("subprocess.run")
    def test_stop_services_success(self, mock_run: MagicMock) -> None:
        """Test successful services stop"""
        mock_run.return_value = MagicMock()
        with patch.object(DockerManager, "get_compose_command", return_value="docker compose"):
            assert DockerManager.stop_services() is True


class TestQRCodeGenerator:
    """Test QRCodeGenerator class"""

    @patch("subprocess.run")
    def test_generate_qr_success(self, mock_run: MagicMock) -> None:
        """Test successful QR code generation"""
        mock_run.return_value = MagicMock(stdout="QR_CODE_OUTPUT")
        with patch.object(QRCodeGenerator, "_command_exists", return_value=True):
            assert QRCodeGenerator.generate_qr("test content") is True

    @patch("subprocess.run")
    def test_generate_qr_to_file(self, mock_run: MagicMock) -> None:
        """Test QR code generation to file"""
        mock_run.return_value = MagicMock()
        with patch.object(QRCodeGenerator, "_command_exists", return_value=True):
            assert QRCodeGenerator.generate_qr("test content", "output.png") is True

    @patch("subprocess.run")
    def test_generate_qr_no_qrencode(self, mock_run: MagicMock) -> None:
        """Test QR code generation when qrencode is not available"""
        with patch.object(QRCodeGenerator, "_command_exists", return_value=False):
            assert QRCodeGenerator.generate_qr("test content") is False

    @patch("subprocess.run")
    def test_generate_qr_failure(self, mock_run: MagicMock) -> None:
        """Test failed QR code generation"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "qrencode")
        with patch.object(QRCodeGenerator, "_command_exists", return_value=True):
            assert QRCodeGenerator.generate_qr("test content") is False
