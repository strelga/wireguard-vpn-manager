"""
Tests for servers/utils.py module - validate_server_name function
"""

from pathlib import Path

from vpn_manager.servers.utils import validate_server_name


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
