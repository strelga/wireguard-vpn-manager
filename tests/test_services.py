"""
Tests for services.py module
"""

import subprocess
from unittest.mock import MagicMock, patch

from vpn_manager.servers.utils import ServerConfigData
from vpn_manager.services import ServiceManager


class TestServiceManager:
    """Test ServiceManager class"""

    @patch("vpn_manager.services.DockerManager")
    @patch("vpn_manager.servers.utils.ServerConfig")
    def test_init_loads_server_containers(self, mock_wg_config, mock_docker, tmp_dir):
        """Test ServiceManager initialization loads server containers"""
        mock_docker.get_compose_command.return_value = "docker compose"

        # Create a test server directory
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()
        test_server_dir = servers_dir / "test-server"
        test_server_dir.mkdir()

        mock_config_instance = MagicMock()
        mock_config_instance.get_server_info.return_value = {
            "container_name": "wireguard-test",
        }
        mock_wg_config.return_value = mock_config_instance

        with patch("vpn_manager.services.Path", return_value=servers_dir):
            manager = ServiceManager()

        assert manager.compose_cmd == ["docker", "compose"]
        assert "test-server" in manager.server_containers

    @patch("vpn_manager.services.DockerManager")
    @patch("vpn_manager.servers.utils.ServerConfig")
    def test_init_handles_config_error(self, mock_wg_config, mock_docker):
        """Test ServiceManager initialization handles config errors gracefully"""
        mock_docker.get_compose_command.return_value = "docker compose"

        mock_wg_config.side_effect = Exception("Config error")

        manager = ServiceManager()

        assert manager.compose_cmd == ["docker", "compose"]
        # Should still have server with default container name
        assert len(manager.server_containers) > 0

    @patch("vpn_manager.services.DockerManager")
    def test_get_available_servers(self, mock_docker, tmp_dir):
        """Test get_available_servers"""
        mock_docker.get_compose_command.return_value = "docker compose"

        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()
        (servers_dir / "server1").mkdir()
        (servers_dir / "server2").mkdir()
        (servers_dir / "file.txt").write_text("test")

        manager = ServiceManager()
        servers = manager.get_available_servers()

        assert len(servers) == 2
        assert "server1" in servers
        assert "server2" in servers
        assert "file.txt" not in servers

    @patch("vpn_manager.services.DockerManager")
    def test_get_available_servers_no_servers(self, mock_docker, tmp_dir):
        """Test get_available_servers when no servers exist"""
        mock_docker.get_compose_command.return_value = "docker compose"

        # Create empty servers directory
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()

        with patch("vpn_manager.services.Path", return_value=servers_dir):
            manager = ServiceManager()
            servers = manager.get_available_servers()

        assert len(servers) == 0

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_start_specific_server(self, mock_run, mock_docker):
        """Test starting a specific server"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.return_value = MagicMock()

        manager = ServiceManager()
        manager.server_containers = {"test-server": "wireguard-test"}

        result = manager.start("test-server")

        assert result is True
        mock_run.assert_called_once_with(
            ["docker", "compose", "up", "-d", "wireguard-test"], check=True
        )

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_start_all_servers(self, mock_run, mock_docker):
        """Test starting all servers"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.return_value = MagicMock()

        manager = ServiceManager()
        result = manager.start()

        assert result is True
        mock_run.assert_called_once_with(["docker", "compose", "up", "-d"], check=True)

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_start_unknown_server(self, mock_run, mock_docker):
        """Test starting an unknown server"""
        mock_docker.get_compose_command.return_value = "docker compose"

        manager = ServiceManager()
        manager.server_containers = {}

        result = manager.start("unknown-server")

        assert result is False
        mock_run.assert_not_called()

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_start_exception(self, mock_run, mock_docker):
        """Test start when exception occurs"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker compose")

        manager = ServiceManager()
        result = manager.start()

        assert result is False

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_stop_specific_server(self, mock_run, mock_docker):
        """Test stopping a specific server"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.return_value = MagicMock()

        manager = ServiceManager()
        manager.server_containers = {"test-server": "wireguard-test"}

        result = manager.stop("test-server")

        assert result is True
        mock_run.assert_called_once_with(
            ["docker", "compose", "stop", "wireguard-test"], check=True
        )

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_stop_all_servers(self, mock_run, mock_docker):
        """Test stopping all servers"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.return_value = MagicMock()

        manager = ServiceManager()
        result = manager.stop()

        assert result is True
        mock_run.assert_called_once_with(["docker", "compose", "down"], check=True)

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_stop_unknown_server(self, mock_run, mock_docker):
        """Test stopping an unknown server"""
        mock_docker.get_compose_command.return_value = "docker compose"

        manager = ServiceManager()
        manager.server_containers = {}

        result = manager.stop("unknown-server")

        assert result is False
        mock_run.assert_not_called()

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_stop_exception(self, mock_run, mock_docker):
        """Test stop when exception occurs"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker compose")

        manager = ServiceManager()
        result = manager.stop()

        assert result is False

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_restart_specific_server(self, mock_run, mock_docker):
        """Test restarting a specific server"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.return_value = MagicMock()

        manager = ServiceManager()
        manager.server_containers = {"test-server": "wireguard-test"}

        result = manager.restart("test-server")

        assert result is True
        mock_run.assert_called_once_with(
            ["docker", "compose", "restart", "wireguard-test"], check=True
        )

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_restart_all_servers(self, mock_run, mock_docker):
        """Test restarting all servers"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.return_value = MagicMock()

        manager = ServiceManager()
        result = manager.restart()

        assert result is True
        mock_run.assert_called_once_with(["docker", "compose", "restart"], check=True)

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_restart_unknown_server(self, mock_run, mock_docker):
        """Test restarting an unknown server"""
        mock_docker.get_compose_command.return_value = "docker compose"

        manager = ServiceManager()
        manager.server_containers = {}

        result = manager.restart("unknown-server")

        assert result is False
        mock_run.assert_not_called()

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_restart_exception(self, mock_run, mock_docker):
        """Test restart when exception occurs"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker compose")

        manager = ServiceManager()
        result = manager.restart()

        assert result is False

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_status_specific_server(self, mock_run, mock_docker):
        """Test getting status of a specific server"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.return_value = MagicMock(stdout="Status output")

        manager = ServiceManager()
        manager.server_containers = {"test-server": "wireguard-test"}

        result = manager.status("test-server")

        assert result is True
        assert mock_run.call_count == 2  # ps and logs

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_status_all_servers(self, mock_run, mock_docker):
        """Test getting status of all servers"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.return_value = MagicMock(stdout="Status output")

        manager = ServiceManager()
        result = manager.status()

        assert result is True
        assert mock_run.call_count == 2  # ps and logs

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_status_unknown_server(self, mock_run, mock_docker):
        """Test getting status of an unknown server"""
        mock_docker.get_compose_command.return_value = "docker compose"

        manager = ServiceManager()
        manager.server_containers = {}

        result = manager.status("unknown-server")

        assert result is False
        mock_run.assert_not_called()

    @patch("vpn_manager.services.DockerManager")
    @patch("subprocess.run")
    def test_status_exception(self, mock_run, mock_docker):
        """Test status when exception occurs"""
        mock_docker.get_compose_command.return_value = "docker compose"
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker compose")

        manager = ServiceManager()
        result = manager.status()

        assert result is False

    @patch("vpn_manager.services.DockerManager")
    @patch("vpn_manager.servers.utils.ServerConfig")
    def test_show_info(self, mock_wg_config, mock_docker, tmp_dir):
        """Test show_info"""
        mock_docker.get_compose_command.return_value = "docker compose"

        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()
        (servers_dir / "server1").mkdir()
        (servers_dir / "server2").mkdir()

        mock_config_instance = MagicMock()
        mock_config_instance.get_server_info.return_value = {
            "server_port": 51820,
        }
        mock_wg_config.return_value = mock_config_instance

        manager = ServiceManager()
        manager.show_info()

        # Should not raise any exceptions
        assert True

    @patch("vpn_manager.services.DockerManager")
    @patch("vpn_manager.servers.utils.ServerConfig")
    def test_show_info_with_config_error(self, mock_wg_config, mock_docker, tmp_dir):
        """Test show_info handles config errors gracefully"""
        mock_docker.get_compose_command.return_value = "docker compose"

        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()
        (servers_dir / "server1").mkdir()

        mock_wg_config.side_effect = Exception("Config error")

        manager = ServiceManager()
        manager.show_info()

        # Should not raise any exceptions
        assert True

    @patch("vpn_manager.services.DockerManager")
    @patch("vpn_manager.servers.utils.ServerConfig")
    def test_load_server_containers(self, mock_wg_config, mock_docker, tmp_dir):
        """Test _load_server_containers"""
        mock_docker.get_compose_command.return_value = "docker compose"

        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()
        (servers_dir / "server1").mkdir()
        (servers_dir / "server2").mkdir()

        mock_config_instance = MagicMock()
        mock_config_instance.get_server_info.return_value = ServerConfigData(
            name="server1",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
            dns="1.1.1.1",
            allowed_ips="0.0.0.0/0",
            peers=1,
            public_key="test_public_key",
        )
        mock_wg_config.return_value = mock_config_instance

        manager = ServiceManager()
        manager._load_server_containers()

        assert "server1" in manager.server_containers
        assert "server2" in manager.server_containers
        assert manager.server_containers["server1"] == "wireguard-server1"
        assert manager.server_containers["server2"] == "wireguard-server2"

    @patch("vpn_manager.services.DockerManager")
    def test_load_server_containers_no_servers(self, mock_docker, tmp_dir):
        """Test _load_server_containers when no servers exist"""
        mock_docker.get_compose_command.return_value = "docker compose"

        # Create empty servers directory
        servers_dir = tmp_dir / "servers"
        servers_dir.mkdir()

        with patch("vpn_manager.services.Path", return_value=servers_dir):
            manager = ServiceManager()
            manager._load_server_containers()

        assert len(manager.server_containers) == 0
