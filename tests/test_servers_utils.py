"""
Tests for servers/utils.py module - ServerConfig class and validate_server_name function
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

from vpn_manager.servers.utils import ServerConfig, validate_server_name


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

    def test_get_next_client_ip_with_many_clients(self, tmp_dir: Path, sample_server_config: dict[str, Any]) -> None:
        """Test get_next_client_ip with many existing clients"""
        config = ServerConfig("test-server")
        config.server_config_file.write_text(yaml.dump(sample_server_config))

        # Create a config with several clients
        wg_config = "[Interface]\nPrivateKey = test\nAddress = 10.13.13.1/24\n"
        for i in range(2, 10):  # Add clients .2 to .9
            wg_config += f"\n# Client: client{i}\n[Peer]\nPublicKey = key{i}\nAllowedIPs = 10.13.13.{i}/32\nAddress = 10.13.13.{i}/32\n"
        config.wg_config_file.write_text(wg_config)

        next_ip = config.get_next_client_ip()
        assert next_ip == "10.13.13.10"

    def test_get_next_client_ip_exhausted(self, tmp_dir: Path, sample_server_config: dict[str, Any]) -> None:
        """Test get_next_client_ip when all IPs are exhausted"""
        config = ServerConfig("test-server")
        config.server_config_file.write_text(yaml.dump(sample_server_config))

        # Create a config with all IPs used (.2 to .254)
        wg_config = "[Interface]\nPrivateKey = test\nAddress = 10.13.13.1/24\n"
        for i in range(2, 255):  # Use all available IPs
            wg_config += f"\n# Client: client{i}\n[Peer]\nPublicKey = key{i}\nAllowedIPs = 10.13.13.{i}/32\nAddress = 10.13.13.{i}/32\n"
        config.wg_config_file.write_text(wg_config)

        with pytest.raises(RuntimeError):
            config.get_next_client_ip()
