"""
Tests for servers.py module
"""

from unittest.mock import MagicMock, patch

from vpn_manager.servers import (
    ServerCreateConfigData,
    ServerManager,
    StoredServerConfigData,
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
        assert config.dns == "auto"
        assert config.allowed_ips == "0.0.0.0/0"
        assert config.peers == "0"

    def test_server_create_config_custom(self):
        """Test ServerCreateConfig with custom values"""
        config = ServerCreateConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51821,
            subnet="10.14.14.0/24",
            dns="8.8.8.8",
            allowed_ips="192.168.1.0/24",
            peers="peer1,peer2",
        )
        assert config.dns == "8.8.8.8"
        assert config.allowed_ips == "192.168.1.0/24"
        assert config.peers == "peer1,peer2"


class TestServiceConfig:
    """Test ServiceConfig dataclass"""

    def test_service_config(self):
        """Test ServiceConfig with default values"""
        config = StoredServerConfigData()
        assert config.server_url == "auto"
        assert config.server_port == 51820
        assert config.peers == "0"
        assert config.peer_dns == "auto"
        assert config.internal_subnet == "10.13.13.0"
        assert config.allowed_ips == "0.0.0.0/0"
        assert config.tz == "UTC"
        assert config.log_confs is True
        assert config.container_name == "wireguard"
        assert config.image == "linuxserver/wireguard:latest"


class TestServerManager:
    """Test ServerManager class"""

    @patch("vpn_manager.servers.servers.ServiceManager")
    @patch("vpn_manager.servers.servers.Logger")
    def test_create_server_success(self, mock_logger, mock_service_manager_class, tmp_dir, snapshot):
        """Test successful server creation"""
        config = ServerCreateConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
        )

        # Setup ServiceManager mock
        mock_service_manager = MagicMock()
        mock_service_manager.start.return_value = True
        mock_service_manager_class.return_value = mock_service_manager

        manager = ServerManager()
        result = manager.create_server(config)

        assert result is True
        server_dir = tmp_dir / "servers" / "test-server"
        assert server_dir.exists()
        assert (server_dir / "container-config").exists()

        # Check config.yml content using snapshot
        config_file = server_dir / "config.yml"
        assert config_file.exists()
        snapshot.assert_match(config_file.read_text(), "config.yml")

    @patch("vpn_manager.servers.servers.ServiceManager")
    @patch("vpn_manager.servers.servers.Logger")
    def test_create_server_custom_config(self, mock_logger, mock_service_manager_class, tmp_dir, snapshot):
        """Test server creation with custom configuration"""
        config = ServerCreateConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51821,
            subnet="10.14.14.0/24",
            dns="8.8.8.8",
            allowed_ips="192.168.1.0/24",
            peers="peer1,peer2",
        )

        # Setup ServiceManager mock
        mock_service_manager = MagicMock()
        mock_service_manager.start.return_value = True
        mock_service_manager_class.return_value = mock_service_manager

        manager = ServerManager()
        result = manager.create_server(config)

        assert result is True
        server_dir = tmp_dir / "servers" / "test-server"

        # Check config.yml content using snapshot
        config_file = server_dir / "config.yml"
        snapshot.assert_match(config_file.read_text(), "config_custom.yml")

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

    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_build_success(self, mock_logger, mock_yaml, tmp_dir, snapshot):
        """Test successful build of docker-compose"""
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir(exist_ok=True)

        server_dir = servers_dir / "test-server"
        server_dir.mkdir()

        config_file = server_dir / "config.yml"
        config_file.write_text(
            """server_url: vpn.example.com
server_port: 51820
peers: ""
peer_dns: auto
internal_subnet: 10.13.13.0
allowed_ips: 0.0.0.0/0
tz: UTC
log_confs: true
container_name: wireguard-test-server
image: linuxserver/wireguard:latest
"""
        )

        mock_yaml.safe_load.return_value = StoredServerConfigData(
            server_url="vpn.example.com",
            server_port=51820,
            peers="",
            peer_dns="auto",
            internal_subnet="10.13.13.0",
            allowed_ips="0.0.0.0/0",
            tz="UTC",
            log_confs=True,
            container_name="wireguard-test-server",
            image="linuxserver/wireguard:latest",
        )

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
        servers_dir.mkdir(exist_ok=True)

        # Create first server
        server1_dir = servers_dir / "server1"
        server1_dir.mkdir()
        config1 = server1_dir / "config.yml"
        config1.write_text(
            """server_url: vpn1.example.com
server_port: 51820
peers: ""
peer_dns: auto
internal_subnet: 10.13.13.0
allowed_ips: 0.0.0.0/0
tz: UTC
log_confs: true
container_name: wireguard-server1
image: linuxserver/wireguard:latest
"""
        )

        # Create second server
        server2_dir = servers_dir / "server2"
        server2_dir.mkdir()
        config2 = server2_dir / "config.yml"
        config2.write_text(
            """server_url: vpn2.example.com
server_port: 51821
peers: ""
peer_dns: auto
internal_subnet: 10.14.14.0
allowed_ips: 192.168.1.0/24
tz: UTC
log_confs: true
container_name: wireguard-server2
image: linuxserver/wireguard:latest
"""
        )

        mock_yaml.safe_load.side_effect = [
            StoredServerConfigData(
                server_url="vpn1.example.com",
                server_port=51820,
                peers="",
                peer_dns="auto",
                internal_subnet="10.13.13.0",
                allowed_ips="0.0.0.0/0",
                tz="UTC",
                log_confs=True,
                container_name="wireguard-server1",
                image="linuxserver/wireguard:latest",
            ),
            StoredServerConfigData(
                server_url="vpn2.example.com",
                server_port=51821,
                peers="",
                peer_dns="auto",
                internal_subnet="10.14.14.0",
                allowed_ips="192.168.1.0/24",
                tz="UTC",
                log_confs=True,
                container_name="wireguard-server2",
                image="linuxserver/wireguard:latest",
            ),
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
        servers_dir.mkdir(exist_ok=True)

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
        servers_dir.mkdir(exist_ok=True)

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

    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_list_servers_success(self, mock_logger, mock_yaml, tmp_dir):
        """Test successful server listing"""
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir(exist_ok=True)

        server1_dir = servers_dir / "server1"
        server1_dir.mkdir()
        config1 = server1_dir / "config.yml"
        config1.write_text(
            """server_url: vpn1.example.com
server_port: 51820
peers: ""
peer_dns: auto
internal_subnet: 10.13.13.0
allowed_ips: 0.0.0.0/0
tz: UTC
log_confs: true
container_name: wireguard-server1
image: linuxserver/wireguard:latest
"""
        )

        server2_dir = servers_dir / "server2"
        server2_dir.mkdir()
        config2 = server2_dir / "config.yml"
        config2.write_text(
            """server_url: vpn2.example.com
server_port: 51821
peers: ""
peer_dns: auto
internal_subnet: 10.14.14.0
allowed_ips: 0.0.0.0/0
tz: UTC
log_confs: true
container_name: wireguard-server2
image: linuxserver/wireguard:latest
"""
        )

        mock_yaml.safe_load.side_effect = [
            StoredServerConfigData(
                server_url="vpn1.example.com",
                server_port=51820,
                peers="",
                peer_dns="auto",
                internal_subnet="10.13.13.0",
                allowed_ips="0.0.0.0/0",
                tz="UTC",
                log_confs=True,
                container_name="wireguard-server1",
                image="linuxserver/wireguard:latest",
            ),
            StoredServerConfigData(
                server_url="vpn2.example.com",
                server_port=51821,
                peers="",
                peer_dns="auto",
                internal_subnet="10.14.14.0",
                allowed_ips="0.0.0.0/0",
                tz="UTC",
                log_confs=True,
                container_name="wireguard-server2",
                image="linuxserver/wireguard:latest",
            ),
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
        servers_dir.mkdir(exist_ok=True)

        manager = ServerManager()
        manager.list_servers()

        mock_logger.info.assert_called_once()

    @patch("vpn_manager.servers.servers.yaml")
    @patch("vpn_manager.servers.servers.Logger")
    def test_list_servers_config_error(self, mock_logger, mock_yaml, tmp_dir):
        """Test list_servers when server config has error"""
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir(exist_ok=True)

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
        container_config_dir = server_dir / "container-config"
        container_config_dir.mkdir()
        (container_config_dir / "peer1.conf").write_text("test")

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
        container_config_dir = server_dir / "container-config"
        container_config_dir.mkdir()
        (container_config_dir / "peer1.conf").write_text("test")

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
