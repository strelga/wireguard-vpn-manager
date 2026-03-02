"""
Tests for manager.py module - External API testing with Typer
"""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from vpn_manager.manager import app
from vpn_manager.servers.utils import ServerCreateConfigData

runner = CliRunner()


class TestMainExternalAPI:
    """Test main function - external API integration with Typer"""

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_start_calls_service_manager(self, mock_service_manager, mock_chdir):
        """Test service start command calls ServiceManager.start"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.start.return_value = True
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "start"])

        assert result.exit_code == 0
        mock_instance.start.assert_called_once_with(None)

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_start_with_server_calls_service_manager(self, mock_service_manager, mock_chdir):
        """Test service start with server name calls ServiceManager.start"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = ["test-server"]
        mock_instance.start.return_value = True
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "start", "test-server"])

        assert result.exit_code == 0
        mock_instance.start.assert_called_once_with("test-server")

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_stop_calls_service_manager(self, mock_service_manager, mock_chdir):
        """Test service stop command calls ServiceManager.stop"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.stop.return_value = True
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "stop"])

        assert result.exit_code == 0
        mock_instance.stop.assert_called_once_with(None)

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_restart_calls_service_manager(self, mock_service_manager, mock_chdir):
        """Test service restart command calls ServiceManager.restart"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.restart.return_value = True
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "restart"])

        assert result.exit_code == 0
        mock_instance.restart.assert_called_once_with(None)

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_status_calls_service_manager(self, mock_service_manager, mock_chdir):
        """Test service status command calls ServiceManager.status"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.status.return_value = True
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "status"])

        assert result.exit_code == 0
        mock_instance.status.assert_called_once_with(None)

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_logs_calls_service_manager(self, mock_service_manager, mock_chdir) -> None:
        """Test service logs command calls ServiceManager.logs"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.logs.return_value = True
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "logs"])

        assert result.exit_code == 0
        mock_instance.logs.assert_called_once_with(None, follow=False, tail=100)

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_logs_with_server_calls_service_manager(self, mock_service_manager, mock_chdir) -> None:
        """Test service logs with server name calls ServiceManager.logs"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = ["test-server"]
        mock_instance.logs.return_value = True
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "logs", "test-server"])

        assert result.exit_code == 0
        mock_instance.logs.assert_called_once_with("test-server", follow=False, tail=100)

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_logs_with_follow_calls_service_manager(self, mock_service_manager, mock_chdir) -> None:
        """Test service logs with follow flag calls ServiceManager.logs"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.logs.return_value = True
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "logs", "-f"])

        assert result.exit_code == 0
        mock_instance.logs.assert_called_once_with(None, follow=True, tail=100)

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_logs_with_tail_calls_service_manager(self, mock_service_manager, mock_chdir) -> None:
        """Test service logs with tail option calls ServiceManager.logs"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.logs.return_value = True
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "logs", "-t", "50"])

        assert result.exit_code == 0
        mock_instance.logs.assert_called_once_with(None, follow=False, tail=50)

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_logs_with_all_options_calls_service_manager(self, mock_service_manager, mock_chdir) -> None:
        """Test service logs with all options calls ServiceManager.logs"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = ["test-server"]
        mock_instance.logs.return_value = True
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "logs", "test-server", "-f", "-t", "25"])

        assert result.exit_code == 0
        mock_instance.logs.assert_called_once_with("test-server", follow=True, tail=25)

    @patch("vpn_manager.manager.ServerManager")
    def test_service_generate_calls_server_manager(self, mock_server_manager, mock_chdir):
        """Test service generate command calls ServerManager.build"""
        mock_instance = MagicMock()
        mock_instance.build.return_value = True
        mock_server_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "generate"])

        assert result.exit_code == 0
        mock_instance.build.assert_called_once()

    @patch("vpn_manager.manager.ClientManager")
    def test_client_add_calls_client_manager(self, mock_client_manager, mock_chdir):
        """Test client add command calls ClientManager.add"""
        mock_instance = MagicMock()
        mock_instance.add.return_value = True
        mock_client_manager.return_value = mock_instance

        result = runner.invoke(app, ["client", "add", "test-server", "test-client"])

        assert result.exit_code == 0
        mock_instance.add.assert_called_once_with("test-server", "test-client")

    @patch("vpn_manager.manager.ClientManager")
    def test_client_remove_calls_client_manager(self, mock_client_manager, mock_chdir):
        """Test client remove command calls ClientManager.remove"""
        mock_instance = MagicMock()
        mock_instance.remove.return_value = True
        mock_client_manager.return_value = mock_instance

        result = runner.invoke(app, ["client", "remove", "test-server", "test-client"])

        assert result.exit_code == 0
        mock_instance.remove.assert_called_once_with("test-server", "test-client")

    @patch("vpn_manager.manager.ClientManager")
    def test_client_list_calls_client_manager(self, mock_client_manager, mock_chdir):
        """Test client list command calls ClientManager.list_clients"""
        mock_instance = MagicMock()
        mock_client_manager.return_value = mock_instance

        result = runner.invoke(app, ["client", "list", "test-server"])

        assert result.exit_code == 0
        mock_instance.list_clients.assert_called_once_with("test-server")

    @patch("vpn_manager.manager.ClientManager")
    def test_client_list_all_calls_client_manager(self, mock_client_manager, mock_chdir):
        """Test client list command without server calls ClientManager.list_all_clients"""
        mock_instance = MagicMock()
        mock_client_manager.return_value = mock_instance

        result = runner.invoke(app, ["client", "list"])

        assert result.exit_code == 0
        mock_instance.list_all_clients.assert_called_once()

    @patch("vpn_manager.manager.KeyManager")
    def test_key_generate_calls_key_manager(self, mock_key_manager, mock_chdir):
        """Test key generate command calls KeyManager.generate"""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = True
        mock_key_manager.return_value = mock_instance

        result = runner.invoke(app, ["key", "generate"])

        assert result.exit_code == 0
        mock_instance.generate.assert_called_once_with(None)

    @patch("vpn_manager.manager.KeyManager")
    def test_key_generate_with_dir_calls_key_manager(self, mock_key_manager, mock_chdir):
        """Test key generate with directory calls KeyManager.generate"""
        mock_instance = MagicMock()
        mock_instance.generate.return_value = True
        mock_key_manager.return_value = mock_instance

        result = runner.invoke(app, ["key", "generate", "/tmp/keys"])

        assert result.exit_code == 0
        mock_instance.generate.assert_called_once_with("/tmp/keys")

    @patch("vpn_manager.manager.ServerManager")
    def test_server_create_calls_server_manager(self, mock_server_manager, mock_chdir):
        """Test server create command calls ServerManager.create_server with correct arguments"""
        mock_instance = MagicMock()
        mock_instance.create_server.return_value = True
        mock_server_manager.return_value = mock_instance

        result = runner.invoke(app, [
            "server", "create",
            "-n", "test-server",
            "-u", "vpn.example.com",
            "-p", "51820",
            "-s", "10.13.13.0/24"
        ])

        assert result.exit_code == 0
        mock_instance.create_server.assert_called_once()
        call_args = mock_instance.create_server.call_args[0][0]
        assert call_args.name == "test-server"
        assert call_args.url == "vpn.example.com"
        assert call_args.port == 51820
        assert call_args.subnet == "10.13.13.0/24"

    @patch("vpn_manager.manager.ServerManager")
    def test_server_list_calls_server_manager(self, mock_server_manager, mock_chdir):
        """Test server list command calls ServerManager.list_servers"""
        mock_instance = MagicMock()
        mock_server_manager.return_value = mock_instance

        result = runner.invoke(app, ["server", "list"])

        assert result.exit_code == 0
        mock_instance.list_servers.assert_called_once()

    @patch("vpn_manager.manager.ServerManager")
    def test_server_remove_calls_server_manager(self, mock_server_manager, mock_chdir):
        """Test server remove command calls ServerManager.remove_server"""
        mock_instance = MagicMock()
        mock_instance.remove_server.return_value = True
        mock_server_manager.return_value = mock_instance

        result = runner.invoke(app, ["server", "remove", "test-server"])

        assert result.exit_code == 0
        mock_instance.remove_server.assert_called_once_with("test-server", False)

    @patch("vpn_manager.manager.ServerManager")
    def test_server_remove_force_calls_server_manager(self, mock_server_manager, mock_chdir):
        """Test server remove with force calls ServerManager.remove_server"""
        mock_instance = MagicMock()
        mock_instance.remove_server.return_value = True
        mock_server_manager.return_value = mock_instance

        result = runner.invoke(app, ["server", "remove", "test-server", "--force"])

        assert result.exit_code == 0
        mock_instance.remove_server.assert_called_once_with("test-server", True)

    @patch("vpn_manager.manager.ServiceManager")
    def test_command_failure_exits_with_code_1(self, mock_service_manager, mock_chdir) -> None:
        """Test that command failure exits with code 1"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = []
        mock_instance.start.return_value = False
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "start"])

        assert result.exit_code == 1

    @patch("vpn_manager.manager._interactive_server_create")
    @patch("vpn_manager.manager.ServerManager")
    def test_server_create_interactive_mode(self, mock_server_manager, mock_interactive, mock_chdir):
        """Test server create in interactive mode"""
        mock_config = ServerCreateConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
            dns="1.1.1.1,8.8.8.8",
            allowed_ips="0.0.0.0/0",
            peers=1,
        )
        mock_interactive.return_value = mock_config

        mock_instance = MagicMock()
        mock_instance.create_server.return_value = True
        mock_server_manager.return_value = mock_instance

        result = runner.invoke(app, ["server", "create"], input="test-server\nvpn.example.com\n51820\n10.13.13.0/24\n1.1.1.1,8.8.8.8\n0.0.0.0/0\n1\n")

        assert result.exit_code == 0
        mock_interactive.assert_called_once()
        mock_instance.create_server.assert_called_once_with(mock_config)

    def test_server_create_partial_args_error(self, mock_chdir) -> None:
        """Test server create with partial args returns error"""
        result = runner.invoke(app, ["server", "create", "-n", "test-server"])

        assert result.exit_code == 1
        assert "Missing required arguments" in result.stdout

    @patch("vpn_manager.manager.ServiceManager")
    def test_unknown_server_exits_with_code_1(self, mock_service_manager, mock_chdir) -> None:
        """Test that unknown server exits with code 1"""
        mock_instance = MagicMock()
        mock_instance.get_available_servers.return_value = ["server1", "server2"]
        mock_service_manager.return_value = mock_instance

        result = runner.invoke(app, ["service", "start", "unknown-server"])

        assert result.exit_code == 1
        assert "Unknown server: unknown-server" in result.stdout

    def test_no_command_shows_help(self, mock_chdir) -> None:
        """Test that running without command shows help"""
        result = runner.invoke(app, [])

        # Typer with no_args_is_help=True returns exit_code 2
        assert result.exit_code == 2
        assert "Usage:" in result.stdout or "usage:" in result.stdout.lower()

    def test_help_shows_all_commands(self, mock_chdir) -> None:
        """Test that help shows all command groups"""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "service" in result.stdout
        assert "client" in result.stdout
        assert "key" in result.stdout
        assert "server" in result.stdout

    @patch("vpn_manager.manager.ServiceManager")
    def test_service_help_shows_all_service_commands(self, mock_service_manager, mock_chdir) -> None:
        """Test that service help shows all service commands"""
        result = runner.invoke(app, ["service", "--help"])

        assert result.exit_code == 0
        assert "start" in result.stdout
        assert "stop" in result.stdout
        assert "restart" in result.stdout
        assert "status" in result.stdout
        assert "logs" in result.stdout
        assert "generate" in result.stdout

    @patch("vpn_manager.manager.ClientManager")
    def test_client_help_shows_all_client_commands(self, mock_client_manager, mock_chdir) -> None:
        """Test that client help shows all client commands"""
        result = runner.invoke(app, ["client", "--help"])

        assert result.exit_code == 0
        assert "add" in result.stdout
        assert "remove" in result.stdout
        assert "list" in result.stdout

    @patch("vpn_manager.manager.ServerManager")
    def test_server_help_shows_all_server_commands(self, mock_server_manager, mock_chdir) -> None:
        """Test that server help shows all server commands"""
        result = runner.invoke(app, ["server", "--help"])

        assert result.exit_code == 0
        assert "create" in result.stdout
        assert "list" in result.stdout
        assert "remove" in result.stdout

    @patch("vpn_manager.manager.KeyManager")
    def test_key_help_shows_all_key_commands(self, mock_key_manager, mock_chdir) -> None:
        """Test that key help shows all key commands"""
        result = runner.invoke(app, ["key", "--help"])

        assert result.exit_code == 0
        assert "generate" in result.stdout

    def test_invalid_server_name_validation(self, mock_chdir) -> None:
        """Test that invalid server name is rejected"""
        result = runner.invoke(app, ["client", "add", "invalid@name", "test-client"])

        assert result.exit_code == 2
        assert "Server name can only contain" in result.stderr

    def test_invalid_client_name_validation(self, mock_chdir) -> None:
        """Test that invalid client name is rejected"""
        result = runner.invoke(app, ["client", "add", "test-server", "invalid@name"])

        assert result.exit_code == 2
        assert "Client name can only contain" in result.stderr

    def test_invalid_port_validation(self, mock_chdir) -> None:
        """Test that invalid port is rejected"""
        result = runner.invoke(app, [
            "server", "create",
            "-n", "test-server",
            "-u", "vpn.example.com",
            "-p", "99999",
            "-s", "10.13.13.0/24"
        ])

        assert result.exit_code == 2
        assert "Port must be between" in result.stderr

    def test_invalid_subnet_validation(self, mock_chdir) -> None:
        """Test that invalid subnet is rejected"""
        result = runner.invoke(app, [
            "server", "create",
            "-n", "test-server",
            "-u", "vpn.example.com",
            "-p", "51820",
            "-s", "invalid-subnet"
        ])

        assert result.exit_code == 2
        assert "Subnet must be in CIDR format" in result.stderr

    def test_invalid_peers_validation(self, mock_chdir) -> None:
        """Test that invalid peers count is rejected"""
        result = runner.invoke(app, [
            "server", "create",
            "-n", "test-server",
            "-u", "vpn.example.com",
            "-p", "51820",
            "-s", "10.13.13.0/24",
            "-P", "0"
        ])

        assert result.exit_code == 2
        assert "Number of peers must be at least 1" in result.stderr
