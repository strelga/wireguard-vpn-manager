"""
Tests for manager.py module - External API testing
"""

from unittest.mock import MagicMock, patch

import pytest

from vpn_manager.manager import main


class TestMainExternalAPI:
    """Test main function - external API integration"""

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "start"])
    def test_service_start_calls_service_manager(self, mock_service_manager):
        """Test service start command calls ServiceManager.start"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.start.return_value = True
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.start.assert_called_once_with(None)

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "start", "test-server"])
    def test_service_start_with_server_calls_service_manager(self, mock_service_manager):
        """Test service start with server name calls ServiceManager.start"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = ["test-server"]
        mock_instance.start.return_value = True
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.start.assert_called_once_with("test-server")

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "stop"])
    def test_service_stop_calls_service_manager(self, mock_service_manager):
        """Test service stop command calls ServiceManager.stop"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.stop.return_value = True
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.stop.assert_called_once_with(None)

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "restart"])
    def test_service_restart_calls_service_manager(self, mock_service_manager):
        """Test service restart command calls ServiceManager.restart"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.restart.return_value = True
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.restart.assert_called_once_with(None)

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "status"])
    def test_service_status_calls_service_manager(self, mock_service_manager):
        """Test service status command calls ServiceManager.status"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.status.return_value = True
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.status.assert_called_once_with(None)

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "logs"])
    def test_service_logs_calls_service_manager(self, mock_service_manager) -> None:
        """Test service logs command calls ServiceManager.logs"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.logs.return_value = True
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.logs.assert_called_once_with(None, follow=False, tail=100)

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "logs", "test-server"])
    def test_service_logs_with_server_calls_service_manager(self, mock_service_manager) -> None:
        """Test service logs with server name calls ServiceManager.logs"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = ["test-server"]
        mock_instance.logs.return_value = True
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.logs.assert_called_once_with("test-server", follow=False, tail=100)

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "logs", "-f"])
    def test_service_logs_with_follow_calls_service_manager(self, mock_service_manager) -> None:
        """Test service logs with follow flag calls ServiceManager.logs"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.logs.return_value = True
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.logs.assert_called_once_with(None, follow=True, tail=100)

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "logs", "-t", "50"])
    def test_service_logs_with_tail_calls_service_manager(self, mock_service_manager) -> None:
        """Test service logs with tail option calls ServiceManager.logs"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.logs.return_value = True
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.logs.assert_called_once_with(None, follow=False, tail=50)

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "logs", "test-server", "-f", "-t", "25"])
    def test_service_logs_with_all_options_calls_service_manager(self, mock_service_manager) -> None:
        """Test service logs with all options calls ServiceManager.logs"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = ["test-server"]
        mock_instance.logs.return_value = True
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.logs.assert_called_once_with("test-server", follow=True, tail=25)

    @patch("vpn_manager.manager.ServerManager")
    @patch("sys.argv", ["manager.py", "service", "generate"])
    def test_service_generate_calls_server_manager(self, mock_server_manager):
        """Test service generate command calls ServerManager.build"""
        mock_instance = MagicMock()
        mock_instance.build.return_value = True
        mock_server_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.build.assert_called_once()

    @patch("vpn_manager.manager.ClientManager")
    @patch("sys.argv", ["manager.py", "client", "add", "test-server", "test-client"])
    def test_client_add_calls_client_manager(self, mock_client_manager):
        """Test client add command calls ClientManager.add"""
        mock_instance = MagicMock()
        mock_instance.add.return_value = True
        mock_client_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.add.assert_called_once_with("test-server", "test-client")

    @patch("vpn_manager.manager.ClientManager")
    @patch("sys.argv", ["manager.py", "client", "remove", "test-server", "test-client"])
    def test_client_remove_calls_client_manager(self, mock_client_manager):
        """Test client remove command calls ClientManager.remove"""
        mock_instance = MagicMock()
        mock_instance.remove.return_value = True
        mock_client_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.remove.assert_called_once_with("test-server", "test-client")

    @patch("vpn_manager.manager.ClientManager")
    @patch("sys.argv", ["manager.py", "client", "list", "test-server"])
    def test_client_list_calls_client_manager(self, mock_client_manager):
        """Test client list command calls ClientManager.list_clients"""
        mock_instance = MagicMock()
        mock_client_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.list_clients.assert_called_once_with("test-server")

    @patch("vpn_manager.manager.ClientManager")
    @patch("sys.argv", ["manager.py", "client", "list", "test-server"])
    def test_client_list_all_calls_client_manager(self, mock_client_manager):
        """Test client list command calls ClientManager.list_clients"""
        mock_instance = MagicMock()
        mock_client_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.list_clients.assert_called_once_with("test-server")

    @patch("vpn_manager.manager.KeyManager")
    @patch("sys.argv", ["manager.py", "key", "generate"])
    def test_key_generate_calls_key_manager(self, mock_key_manager):
        """Test key generate command calls KeyManager.generate"""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = True
        mock_key_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.generate.assert_called_once_with(None)

    @patch("vpn_manager.manager.KeyManager")
    @patch("sys.argv", ["manager.py", "key", "generate", "/tmp/keys"])
    def test_key_generate_with_dir_calls_key_manager(self, mock_key_manager):
        """Test key generate with directory calls KeyManager.generate"""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = True
        mock_key_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.generate.assert_called_once_with("/tmp/keys")

    @patch("vpn_manager.manager.ServerManager")
    @patch("sys.argv", [
        "manager.py", "server", "create",
        "-n", "test-server",
        "-u", "vpn.example.com",
        "-p", "51820",
        "-s", "10.13.13.0/24"
    ])
    def test_server_create_calls_server_manager(self, mock_server_manager):
        """Test server create command calls ServerManager.create_server"""
        mock_instance = MagicMock()
        mock_instance.create_server.return_value = True
        mock_server_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.create_server.assert_called_once()

    @patch("vpn_manager.manager.ServerManager")
    @patch("sys.argv", ["manager.py", "server", "list"])
    def test_server_list_calls_server_manager(self, mock_server_manager):
        """Test server list command calls ServerManager.list_servers"""
        mock_instance = MagicMock()
        mock_server_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.list_servers.assert_called_once()

    @patch("vpn_manager.manager.ServerManager")
    @patch("sys.argv", ["manager.py", "server", "remove", "test-server"])
    def test_server_remove_calls_server_manager(self, mock_server_manager):
        """Test server remove command calls ServerManager.remove_server"""
        mock_instance = MagicMock()
        mock_instance.remove_server.return_value = True
        mock_server_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.remove_server.assert_called_once_with("test-server", False)

    @patch("vpn_manager.manager.ServerManager")
    @patch("sys.argv", ["manager.py", "server", "remove", "test-server", "--force"])
    def test_server_remove_force_calls_server_manager(self, mock_server_manager):
        """Test server remove with force calls ServerManager.remove_server"""
        mock_instance = MagicMock()
        mock_instance.remove_server.return_value = True
        mock_server_manager.return_value = mock_instance

        with patch("os.chdir"):
            main()

        mock_instance.remove_server.assert_called_once_with("test-server", True)

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "start"])
    def test_command_failure_exits_with_code_1(self, mock_service_manager):
        """Test that command failure exits with code 1"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.start.return_value = False
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1

    @patch("vpn_manager.manager.ServiceManager")
    @patch("sys.argv", ["manager.py", "service", "start", "test-server"])
    def test_exception_exits_with_code_1(self, mock_service_manager):
        """Test that exception exits with code 1"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.side_effect = Exception("Test error")
        mock_service_manager.return_value = mock_instance

        with patch("os.chdir"):
            with pytest.raises(SystemExit) as exc_info:
                main()

            assert exc_info.value.code == 1
