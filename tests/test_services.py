"""
Tests for services.py module
"""

from unittest.mock import MagicMock, patch

from vpn_manager.servers import StoredServerConfigData
from vpn_manager.services import ServiceManager


class TestServiceManager:
    """Test ServiceManager class"""

    @patch("vpn_manager.services.services.DockerComposeManager")
    @patch("vpn_manager.services.services.load_service_config")
    @patch("vpn_manager.services.services.get_servers_dir")
    def test_init_loads_server_containers(self, mock_get_servers_dir, mock_load_config, mock_docker_class, test_server_dir):
        """Test ServiceManager initialization loads server containers"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        # Mock get_servers_dir to return the test directory
        mock_get_servers_dir.return_value = test_server_dir.parent

        mock_config = StoredServerConfigData(container_name="wireguard-test")
        mock_load_config.return_value = mock_config

        manager = ServiceManager()

        assert "test-server" in manager._server_containers

    @patch("vpn_manager.services.services.DockerComposeManager")
    @patch("vpn_manager.services.services.load_service_config")
    def test_init_handles_config_error(self, mock_load_config, mock_docker_class, test_server_dir):
        """Test ServiceManager initialization handles config errors gracefully"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        mock_load_config.side_effect = Exception("Config error")

        manager = ServiceManager()

        # Should still have server with default container name
        assert len(manager._server_containers) > 0

    @patch("vpn_manager.services.services.get_servers_dir")
    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_get_available_servers(self, mock_docker_class, mock_get_servers_dir, tmp_dir):
        """Test get_available_servers"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir(exist_ok=True)
        (servers_dir / "server1").mkdir()
        (servers_dir / "server2").mkdir()
        (servers_dir / "file.txt").write_text("test")

        mock_get_servers_dir.return_value = servers_dir

        manager = ServiceManager()
        servers = manager.get_available_servers()

        assert len(servers) == 2
        assert "server1" in servers
        assert "server2" in servers
        assert "file.txt" not in servers

    @patch("vpn_manager.services.services.get_servers_dir")
    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_get_available_servers_no_servers(self, mock_docker_class, mock_get_servers_dir, tmp_dir):
        """Test get_available_servers when no servers exist"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        # Create empty servers directory
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir(exist_ok=True)

        mock_get_servers_dir.return_value = servers_dir

        manager = ServiceManager()
        servers = manager.get_available_servers()

        assert len(servers) == 0

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_start_specific_server(self, mock_docker_class):
        """Test starting a specific server"""
        mock_docker = MagicMock()
        mock_docker.start_container.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {"test-server": "wireguard-test"}

        result = manager.start("test-server")

        assert result is True
        mock_docker.start_container.assert_called_once_with("wireguard-test")

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_start_all_servers(self, mock_docker_class):
        """Test starting all servers"""
        mock_docker = MagicMock()
        mock_docker.start_services.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        result = manager.start()

        assert result is True
        mock_docker.start_services.assert_called_once()

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_start_unknown_server(self, mock_docker_class):
        """Test starting an unknown server"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {}

        result = manager.start("unknown-server")

        assert result is False
        mock_docker.start_container.assert_not_called()

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_start_exception(self, mock_docker_class):
        """Test start when exception occurs"""
        mock_docker = MagicMock()
        mock_docker.start_services.return_value = False
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        result = manager.start()

        assert result is False

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_stop_specific_server(self, mock_docker_class):
        """Test stopping a specific server"""
        mock_docker = MagicMock()
        mock_docker.stop_container.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {"test-server": "wireguard-test"}

        result = manager.stop("test-server")

        assert result is True
        mock_docker.stop_container.assert_called_once_with("wireguard-test")

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_stop_all_servers(self, mock_docker_class):
        """Test stopping all servers"""
        mock_docker = MagicMock()
        mock_docker.stop_services.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        result = manager.stop()

        assert result is True
        mock_docker.stop_services.assert_called_once()

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_stop_unknown_server(self, mock_docker_class):
        """Test stopping an unknown server"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {}

        result = manager.stop("unknown-server")

        assert result is False
        mock_docker.stop_container.assert_not_called()

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_stop_exception(self, mock_docker_class):
        """Test stop when exception occurs"""
        mock_docker = MagicMock()
        mock_docker.stop_services.return_value = False
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        result = manager.stop()

        assert result is False

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_restart_specific_server(self, mock_docker_class):
        """Test restarting a specific server"""
        mock_docker = MagicMock()
        mock_docker.restart_container.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {"test-server": "wireguard-test"}

        result = manager.restart("test-server")

        assert result is True
        mock_docker.restart_container.assert_called_once_with("wireguard-test")

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_restart_all_servers(self, mock_docker_class):
        """Test restarting all servers"""
        mock_docker = MagicMock()
        mock_docker.restart_all_services.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        result = manager.restart()

        assert result is True
        mock_docker.restart_all_services.assert_called_once()

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_restart_unknown_server(self, mock_docker_class):
        """Test restarting an unknown server"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {}

        result = manager.restart("unknown-server")

        assert result is False
        mock_docker.restart_container.assert_not_called()

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_restart_exception(self, mock_docker_class):
        """Test restart when exception occurs"""
        mock_docker = MagicMock()
        mock_docker.restart_all_services.return_value = False
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        result = manager.restart()

        assert result is False

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_status_specific_server(self, mock_docker_class):
        """Test getting status of a specific server"""
        mock_docker = MagicMock()
        mock_docker.get_container_status.return_value = "Status output"
        mock_docker.exec_container.return_value = True
        mock_docker.get_container_logs.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {"test-server": "wireguard-test"}

        result = manager.status("test-server")

        assert result is True
        mock_docker.get_container_status.assert_called_once_with(container_name="wireguard-test")
        mock_docker.exec_container.assert_called_once_with(container_name="wireguard-test", command=["wg", "show"])
        mock_docker.get_container_logs.assert_called_once_with(container_name="wireguard-test", follow=False, tail=10)

    @patch("vpn_manager.services.services.DockerComposeManager")
    @patch("vpn_manager.services.services.load_service_config")
    @patch("vpn_manager.services.services.get_servers_dir")
    def test_status_all_servers(self, mock_get_servers_dir, mock_load_config, mock_docker_class, tmp_dir):
        """Test getting status of all servers"""
        mock_docker = MagicMock()
        mock_docker.get_container_status.return_value = "Status output"
        mock_docker.exec_container.return_value = True
        mock_docker.get_container_logs.return_value = True
        mock_docker_class.return_value = mock_docker

        # Mock get_servers_dir to return the test directory
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir(exist_ok=True)
        (servers_dir / "server1").mkdir()
        (servers_dir / "server2").mkdir()
        mock_get_servers_dir.return_value = servers_dir

        # Mock load_service_config to return valid configs
        mock_config1 = StoredServerConfigData(container_name="wireguard-server1")
        mock_config2 = StoredServerConfigData(container_name="wireguard-server2")
        mock_load_config.side_effect = [mock_config1, mock_config2]

        manager = ServiceManager()
        result = manager.status()

        assert result is True
        mock_docker.get_container_status.assert_called_once_with(container_name=None)
        # Should call exec_container twice (once for each server)
        assert mock_docker.exec_container.call_count == 2
        assert mock_docker.exec_container.call_count == 2
        mock_docker.get_container_logs.assert_called_once_with(container_name=None, follow=False, tail=5)

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_status_unknown_server(self, mock_docker_class):
        """Test getting status of an unknown server"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {}

        result = manager.status("unknown-server")

        assert result is False
        mock_docker.get_container_status.assert_not_called()

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_status_exception(self, mock_docker_class):
        """Test status when exception occurs"""
        mock_docker = MagicMock()
        mock_docker.get_container_status.return_value = ""
        mock_docker.exec_container.return_value = True
        mock_docker.get_container_logs.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        result = manager.status()

        assert result is True

    @patch("vpn_manager.services.services.DockerComposeManager")
    @patch("vpn_manager.services.services.load_service_config")
    def test_show_info(self, mock_load_config, mock_docker_class, tmp_dir):
        """Test show_info"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir(exist_ok=True)
        (servers_dir / "server1").mkdir()
        (servers_dir / "server2").mkdir()

        mock_config = StoredServerConfigData(server_port=51820)
        mock_load_config.return_value = mock_config

        manager = ServiceManager()
        # Should not raise any exceptions
        manager.show_info()

    @patch("vpn_manager.services.services.DockerComposeManager")
    @patch("vpn_manager.services.services.load_service_config")
    def test_show_info_with_config_error(self, mock_load_config, mock_docker_class, tmp_dir):
        """Test show_info handles config errors gracefully"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir(exist_ok=True)
        (servers_dir / "server1").mkdir()

        mock_load_config.side_effect = Exception("Config error")

        manager = ServiceManager()
        # Should not raise any exceptions
        manager.show_info()

    @patch("vpn_manager.services.services.get_servers_dir")
    @patch("vpn_manager.services.services.DockerComposeManager")
    @patch("vpn_manager.services.services.load_service_config")
    def test_load_server_containers(self, mock_load_config, mock_docker_class, mock_get_servers_dir, tmp_dir):
        """Test _load_server_containers"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir(exist_ok=True)
        (servers_dir / "server1").mkdir()
        (servers_dir / "server2").mkdir()

        mock_get_servers_dir.return_value = servers_dir

        # Return different config for each server
        def load_config_side_effect(server_name):
            if server_name == "server1":
                return StoredServerConfigData(container_name="wireguard-server1")
            else:
                return StoredServerConfigData(container_name="wireguard-server2")

        mock_load_config.side_effect = load_config_side_effect

        manager = ServiceManager()
        manager._load_server_containers()

        assert "server1" in manager._server_containers
        assert "server2" in manager._server_containers
        assert manager._server_containers["server1"] == "wireguard-server1"
        assert manager._server_containers["server2"] == "wireguard-server2"

    @patch("vpn_manager.services.services.get_servers_dir")
    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_load_server_containers_no_servers(self, mock_docker_class, mock_get_servers_dir, tmp_dir):
        """Test _load_server_containers when no servers exist"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        # Create empty servers directory
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir(exist_ok=True)

        mock_get_servers_dir.return_value = servers_dir

        manager = ServiceManager()
        manager._load_server_containers()
        assert len(manager._server_containers) == 0


    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_logs_specific_server(self, mock_docker_class) -> None:
        """Test showing logs for a specific server"""
        mock_docker = MagicMock()
        mock_docker.get_container_logs.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {"test-server": "wireguard-test"}

        result = manager.logs("test-server")

        assert result is True
        mock_docker.get_container_logs.assert_called_once_with(container_name="wireguard-test", follow=False, tail=100)

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_logs_all_servers(self, mock_docker_class) -> None:
        """Test showing logs for all servers"""
        mock_docker = MagicMock()
        mock_docker.get_container_logs.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        result = manager.logs()

        assert result is True
        mock_docker.get_container_logs.assert_called_once_with(container_name=None, follow=False, tail=100)

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_logs_with_follow(self, mock_docker_class) -> None:
        """Test showing logs with follow flag"""
        mock_docker = MagicMock()
        mock_docker.get_container_logs.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {"test-server": "wireguard-test"}

        result = manager.logs("test-server", follow=True)

        assert result is True
        mock_docker.get_container_logs.assert_called_once_with(container_name="wireguard-test", follow=True, tail=100)

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_logs_with_custom_tail(self, mock_docker_class) -> None:
        """Test showing logs with custom tail value"""
        mock_docker = MagicMock()
        mock_docker.get_container_logs.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {"test-server": "wireguard-test"}

        result = manager.logs("test-server", tail=50)

        assert result is True
        mock_docker.get_container_logs.assert_called_once_with(container_name="wireguard-test", follow=False, tail=50)

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_logs_with_follow_and_tail(self, mock_docker_class) -> None:
        """Test showing logs with both follow and tail options"""
        mock_docker = MagicMock()
        mock_docker.get_container_logs.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {"test-server": "wireguard-test"}

        result = manager.logs("test-server", follow=True, tail=25)

        assert result is True
        mock_docker.get_container_logs.assert_called_once_with(container_name="wireguard-test", follow=True, tail=25)

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_logs_unknown_server(self, mock_docker_class) -> None:
        """Test showing logs for an unknown server"""
        mock_docker = MagicMock()
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        manager._server_containers = {}

        result = manager.logs("unknown-server")

        assert result is False
        mock_docker.get_container_logs.assert_not_called()

    @patch("vpn_manager.services.services.DockerComposeManager")
    def test_logs_exception(self, mock_docker_class) -> None:
        """Test logs when exception occurs"""
        mock_docker = MagicMock()
        mock_docker.get_container_logs.return_value = False
        mock_docker_class.return_value = mock_docker

        manager = ServiceManager()
        result = manager.logs()

        assert result is False
        # Verify that get_container_logs was called despite the exception
        assert mock_docker.get_container_logs.called
