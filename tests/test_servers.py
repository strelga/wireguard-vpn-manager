"""
Tests for servers.py module
"""

from unittest.mock import patch

from vpn_manager.servers.servers import (
    ServerConfigData,
    ServerCreateConfigData,
    ServerManager,
)


class TestServerCreateConfig:
    """Test ServerCreateConfig dataclass"""

    def test_server_create_config_defaults(self):
        """Test ServerCreateConfig with default values"""
        config = ServerCreateConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
        )
        assert config.name == "test-server"
        assert config.url == "vpn.example.com"
        assert config.port == 51820
        assert config.subnet == "10.13.13.0/24"
        assert config.dns == "1.1.1.1,8.8.8.8"
        assert config.allowed_ips == "0.0.0.0/0"
        assert config.peers == 1

    def test_server_create_config_custom(self):
        """Test ServerCreateConfig with custom values"""
        config = ServerCreateConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51821,
            subnet="10.14.14.0/24",
            dns="8.8.8.8",
            allowed_ips="192.168.1.0/24",
            peers=5,
        )
        assert config.dns == "8.8.8.8"
        assert config.allowed_ips == "192.168.1.0/24"
        assert config.peers == 5


class TestServerConfig:
    """Test ServerConfig dataclass"""

    def test_server_config(self):
        """Test ServerConfig with public key"""
        config = ServerConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
            public_key="test_public_key",
        )
        assert config.public_key == "test_public_key"


class TestServerManager:
    """Test ServerManager class"""

    @patch("vpn_manager.servers.servers.KeyGenerator")
    @patch("vpn_manager.servers.servers.Logger")
    def test_create_server_success(self, mock_logger, mock_key_gen, tmp_dir, snapshot):
        """Test successful server creation"""
        mock_key_gen.generate_keypair.return_value = ("private_key", "public_key")

        config = ServerCreateConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
        )

        manager = ServerManager()
        result = manager.create_server(config)

        assert result is True
        server_dir = tmp_dir / "servers" / "test-server"
        assert server_dir.exists()
        assert (server_dir / "config").exists()
        assert (server_dir / "clients").exists()

        # Check config.yml content using snapshot
        config_file = server_dir / "config.yml"
        assert config_file.exists()
        snapshot.assert_match(config_file.read_text(), "config.yml")

        # Check wg0.conf content using snapshot
        wg_config_file = server_dir / "config" / "wg_confs" / "wg0.conf"
        assert wg_config_file.exists()
        snapshot.assert_match(wg_config_file.read_text(), "wg0.conf")

    @patch("vpn_manager.servers.servers.KeyGenerator")
    @patch("vpn_manager.servers.servers.Logger")
    def test_create_server_custom_config(self, mock_logger, mock_key_gen, tmp_dir, snapshot):
        """Test server creation with custom configuration"""
        mock_key_gen.generate_keypair.return_value = ("private_key", "public_key")

        config = ServerCreateConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51821,
            subnet="10.14.14.0/24",
            dns="8.8.8.8",
            allowed_ips="192.168.1.0/24",
            peers=5,
        )

        manager = ServerManager()
        result = manager.create_server(config)

        assert result is True
        server_dir = tmp_dir / "servers" / "test-server"

        # Check config.yml content using snapshot
        config_file = server_dir / "config.yml"
        snapshot.assert_match(config_file.read_text(), "config_custom.yml")

        # Check wg0.conf content using snapshot
        wg_config_file = server_dir / "config" / "wg_confs" / "wg0.conf"
        snapshot.assert_match(wg_config_file.read_text(), "wg0_custom.conf")

    @patch("vpn_manager.servers.servers.Logger")
    def test_create_server_invalid_name(self, mock_logger):
        """Test server creation with invalid name"""
        config = ServerCreateConfigData(
            name="invalid@server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
        )

        manager = ServerManager()
        result = manager.create_server(config)

        assert result is False
        mock_logger.error.assert_called_once()

    @patch("vpn_manager.servers.servers.Logger")
    def test_create_server_already_exists(self, mock_logger, tmp_dir):
        """Test server creation when server already exists"""
        server_dir = tmp_dir / "servers" / "test-server"
        server_dir.mkdir(parents=True)

        config = ServerCreateConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
        )

        manager = ServerManager()
        result = manager.create_server(config)

        assert result is False
        mock_logger.error.assert_called_once()

    @patch("vpn_manager.servers.servers.KeyGenerator")
    @patch("vpn_manager.servers.servers.Logger")
    def test_create_server_exception(self, mock_logger, mock_key_gen):
        """Test server creation when exception occurs"""
        mock_key_gen.generate_keypair.side_effect = Exception("Key generation failed")

        config = ServerCreateConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
        )

        manager = ServerManager()
        result = manager.create_server(config)

        assert result is False
        mock_logger.error.assert_called_once()

    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_create_server_config_yml(self, mock_logger, mock_yaml, tmp_dir, snapshot):
        """Test _create_server_config_yml"""
        # Create server directory first
        server_dir = tmp_dir / "servers" / "test-server"
        server_dir.mkdir(parents=True)

        config = ServerConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
            dns="1.1.1.1",
            allowed_ips="0.0.0.0/0",
            peers=1,
            public_key="test_public_key",
        )

        manager = ServerManager()
        manager._create_server_config_yml(config)

        # Check file was created with correct content using snapshot
        config_file = tmp_dir / "servers" / "test-server" / "config.yml"
        assert config_file.exists()
        snapshot.assert_match(config_file.read_text(), "server_config_yml.yml")

    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_build_success(self, mock_logger, mock_yaml, tmp_dir, snapshot):
        """Test successful build of docker-compose"""
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()

        server_dir = servers_dir / "test-server"
        server_dir.mkdir()

        config_file = server_dir / "config.yml"
        config_file.write_text(
            """server:
  name: test-server
  url: vpn.example.com
  port: 51820
  subnet: 10.13.13.0/24
  dns: 1.1.1.1,8.8.8.8
  allowed_ips: 0.0.0.0/0
  peers: 1
  public_key: test_public_key
"""
        )

        mock_yaml.safe_load.return_value = {
            "server": {
                "name": "test-server",
                "url": "vpn.example.com",
                "port": 51820,
                "subnet": "10.13.13.0/24",
                "dns": "1.1.1.1,8.8.8.8",
                "allowed_ips": "0.0.0.0/0",
                "peers": 1,
                "public_key": "test_public_key",
            }
        }

        manager = ServerManager()
        result = manager.build()

        assert result is True
        generated_file = servers_dir / "docker-compose.generated.yml"
        assert generated_file.exists()

        # Check docker-compose content using snapshot
        snapshot.assert_match(generated_file.read_text(), "docker-compose.yml")
        mock_logger.success.assert_called_once()

    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_build_multiple_servers(self, mock_logger, mock_yaml, tmp_dir, snapshot):
        """Test build with multiple servers"""
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()

        # Create first server
        server1_dir = servers_dir / "server1"
        server1_dir.mkdir()
        config1 = server1_dir / "config.yml"
        config1.write_text(
            """server:
  name: server1
  url: vpn1.example.com
  port: 51820
  subnet: 10.13.13.0/24
  dns: 1.1.1.1
  allowed_ips: 0.0.0.0/0
  peers: 1
  public_key: key1
"""
        )

        # Create second server
        server2_dir = servers_dir / "server2"
        server2_dir.mkdir()
        config2 = server2_dir / "config.yml"
        config2.write_text(
            """server:
  name: server2
  url: vpn2.example.com
  port: 51821
  subnet: 10.14.14.0/24
  dns: 8.8.8.8
  allowed_ips: 192.168.1.0/24
  peers: 2
  public_key: key2
"""
        )

        mock_yaml.safe_load.side_effect = [
            {
                "server": {
                    "name": "server1",
                    "url": "vpn1.example.com",
                    "port": 51820,
                    "subnet": "10.13.13.0/24",
                    "dns": "1.1.1.1",
                    "allowed_ips": "0.0.0.0/0",
                    "peers": 1,
                    "public_key": "key1",
                }
            },
            {
                "server": {
                    "name": "server2",
                    "url": "vpn2.example.com",
                    "port": 51821,
                    "subnet": "10.14.14.0/24",
                    "dns": "8.8.8.8",
                    "allowed_ips": "192.168.1.0/24",
                    "peers": 2,
                    "public_key": "key2",
                }
            },
        ]

        manager = ServerManager()
        result = manager.build()

        assert result is True
        generated_file = servers_dir / "docker-compose.generated.yml"
        assert generated_file.exists()

        # Check docker-compose content using snapshot
        snapshot.assert_match(generated_file.read_text(), "docker-compose-multiple.yml")

    @patch("vpn_manager.servers.servers.Logger")
    def test_build_no_servers_dir(self, mock_logger, tmp_dir):
        """Test build when servers directory doesn't exist"""
        manager = ServerManager()
        result = manager.build()

        assert result is False
        mock_logger.error.assert_called()

    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_build_no_config_yml(self, mock_logger, mock_yaml, tmp_dir):
        """Test build when server has no config.yml"""
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()

        server_dir = servers_dir / "test-server"
        server_dir.mkdir()

        manager = ServerManager()
        result = manager.build()

        assert result is True  # Should succeed but skip server without config
        mock_logger.warning.assert_called_once()

    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_build_exception(self, mock_logger, mock_yaml, tmp_dir):
        """Test build when exception occurs"""
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()

        # Create a server directory with config.yml
        server_dir = servers_dir / "test-server"
        server_dir.mkdir()
        config_file = server_dir / "config.yml"
        config_file.write_text("test")

        mock_yaml.safe_load.side_effect = Exception("Load failed")

        manager = ServerManager()
        result = manager.build()

        assert result is False
        mock_logger.error.assert_called()

    @patch("vpn_manager.servers.servers.Logger")
    def test_create_wg_server_config(self, mock_logger, tmp_dir, snapshot):
        """Test _create_wg_server_config"""
        server_dir = tmp_dir / "servers" / "test-server"
        server_dir.mkdir(parents=True)

        manager = ServerManager()
        manager._create_wg_server_config("test-server", "private_key", "10.13.13.0/24")

        config_dir = server_dir / "config" / "wg_confs"
        assert config_dir.exists()
        config_file = config_dir / "wg0.conf"
        assert config_file.exists()

        # Check content using snapshot
        snapshot.assert_match(config_file.read_text(), "wg_server_config.conf")
        mock_logger.success.assert_called_once()

    @patch("vpn_manager.servers.servers.Logger")
    def test_create_wg_server_config_different_subnet(self, mock_logger, tmp_dir, snapshot):
        """Test _create_wg_server_config with different subnet"""
        server_dir = tmp_dir / "servers" / "test-server"
        server_dir.mkdir(parents=True)

        manager = ServerManager()
        manager._create_wg_server_config("test-server", "private_key", "192.168.100.0/24")

        config_file = server_dir / "config" / "wg_confs" / "wg0.conf"
        snapshot.assert_match(config_file.read_text(), "wg_server_config_custom_subnet.conf")

    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_list_servers_success(self, mock_logger, mock_yaml, tmp_dir):
        """Test successful server listing"""
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()

        server1_dir = servers_dir / "server1"
        server1_dir.mkdir()
        config1 = server1_dir / "config.yml"
        config1.write_text(
            """server:
  name: server1
  url: vpn1.example.com
  port: 51820
  subnet: 10.13.13.0/24
"""
        )

        server2_dir = servers_dir / "server2"
        server2_dir.mkdir()
        config2 = server2_dir / "config.yml"
        config2.write_text(
            """server:
  name: server2
  url: vpn2.example.com
  port: 51821
  subnet: 10.14.14.0/24
"""
        )

        mock_yaml.safe_load.side_effect = [
            {
                "server": {
                    "name": "server1",
                    "url": "vpn1.example.com",
                    "port": 51820,
                    "subnet": "10.13.13.0/24",
                }
            },
            {
                "server": {
                    "name": "server2",
                    "url": "vpn2.example.com",
                    "port": 51821,
                    "subnet": "10.14.14.0/24",
                }
            },
        ]

        manager = ServerManager()
        manager.list_servers()

        mock_logger.success.assert_called_once()

    @patch("vpn_manager.servers.servers.Logger")
    def test_list_servers_no_servers_dir(self, mock_logger, tmp_dir):
        """Test list_servers when servers directory doesn't exist"""
        manager = ServerManager()
        manager.list_servers()

        mock_logger.info.assert_called()

    @patch("vpn_manager.servers.servers.Logger")
    def test_list_servers_empty(self, mock_logger, tmp_dir):
        """Test list_servers when no servers exist"""
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()

        manager = ServerManager()
        manager.list_servers()

        mock_logger.info.assert_called_once()

    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_list_servers_config_error(self, mock_logger, mock_yaml, tmp_dir):
        """Test list_servers when server config has error"""
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()

        server_dir = servers_dir / "server1"
        server_dir.mkdir()
        config = server_dir / "config.yml"
        config.write_text("invalid yaml")

        mock_yaml.safe_load.side_effect = Exception("Parse error")

        manager = ServerManager()
        manager.list_servers()

        mock_logger.success.assert_called_once()

    @patch("vpn_manager.servers.servers.shutil")
    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_remove_server_success(self, mock_logger, mock_yaml, mock_shutil, tmp_dir):
        """Test successful server removal"""
        server_dir = tmp_dir / "servers" / "test-server"
        server_dir.mkdir(parents=True)

        manager = ServerManager()
        with (
            patch.object(manager, "build", return_value=True),
            patch("builtins.input", return_value="yes"),
        ):
            result = manager.remove_server("test-server")

        assert result is True
        mock_shutil.rmtree.assert_called_once()
        mock_logger.success.assert_called_once()

    @patch("vpn_manager.servers.servers.Logger")
    def test_remove_server_not_found(self, mock_logger):
        """Test server removal when server doesn't exist"""
        manager = ServerManager()
        result = manager.remove_server("nonexistent")

        assert result is False
        mock_logger.error.assert_called_once()

    @patch("vpn_manager.servers.servers.Logger")
    def test_remove_server_with_clients(self, mock_logger, tmp_dir):
        """Test server removal when server has clients"""
        server_dir = tmp_dir / "servers" / "test-server"
        server_dir.mkdir(parents=True)
        clients_dir = server_dir / "clients"
        clients_dir.mkdir()
        (clients_dir / "client1.conf").write_text("test")

        manager = ServerManager()
        result = manager.remove_server("test-server")

        assert result is False
        mock_logger.error.assert_called_once()

    @patch("vpn_manager.servers.servers.shutil")
    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_remove_server_with_clients_force(self, mock_logger, mock_yaml, mock_shutil, tmp_dir):
        """Test server removal with clients using force flag"""
        server_dir = tmp_dir / "servers" / "test-server"
        server_dir.mkdir(parents=True)
        clients_dir = server_dir / "clients"
        clients_dir.mkdir()
        (clients_dir / "client1.conf").write_text("test")

        manager = ServerManager()
        with patch.object(manager, "build", return_value=True):
            result = manager.remove_server("test-server", force=True)

        assert result is True
        mock_shutil.rmtree.assert_called_once()

    @patch("vpn_manager.servers.servers.Logger")
    def test_remove_server_cancelled(self, mock_logger, tmp_dir):
        """Test server removal when cancelled by user"""
        server_dir = tmp_dir / "servers" / "test-server"
        server_dir.mkdir(parents=True)

        manager = ServerManager()
        with patch("builtins.input", return_value="no"):
            result = manager.remove_server("test-server")

        assert result is False
        mock_logger.info.assert_called_once()

    @patch("vpn_manager.servers.servers.shutil")
    @patch("vpn_manager.servers.servers.Logger")
    def test_remove_server_exception(self, mock_logger, mock_shutil):
        """Test server removal when exception occurs"""
        mock_shutil.rmtree.side_effect = Exception("Remove failed")

        manager = ServerManager()
        with patch("builtins.input", return_value="yes"):
            result = manager.remove_server("test-server")

        assert result is False
        mock_logger.error.assert_called_once()
