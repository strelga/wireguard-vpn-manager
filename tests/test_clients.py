"""
Tests for clients.py module
"""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from vpn_manager.clients import ClientManager
from vpn_manager.servers.utils import ServerConfigData


class TestClientManager:
    """Test ClientManager class"""

    @patch("vpn_manager.clients.validate_server_name")
    @patch("vpn_manager.clients.validate_client_name")
    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.KeyGenerator")
    @patch("vpn_manager.clients.DockerManager")
    @patch("vpn_manager.clients.QRCodeGenerator")
    @patch("vpn_manager.clients.Logger")
    def test_add_client_success(
        self,
        mock_logger,
        mock_qr,
        mock_docker,
        mock_key_gen,
        mock_wg_config,
        mock_validate_client,
        mock_validate_server,
    ):
        """Test successful client addition"""
        # Setup mocks
        mock_validate_server.return_value = True
        mock_validate_client.return_value = True

        mock_config_instance = MagicMock()
        mock_config_instance.get_server_info.return_value = ServerConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
            dns="1.1.1.1",
            allowed_ips="0.0.0.0/0",
            peers=1,
            public_key="test_public_key",
        )
        mock_config_instance.get_next_client_ip.return_value = "10.13.13.2"
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = "[Interface]\nPrivateKey = test\n"
        mock_config_instance.clients_dir = MagicMock()
        mock_config_instance.clients_dir.exists.return_value = True
        mock_client_file = MagicMock()
        mock_client_file.chmod = MagicMock()
        mock_config_instance.clients_dir.__truediv__ = MagicMock(return_value=mock_client_file)
        mock_wg_config.return_value = mock_config_instance

        mock_key_gen.generate_keypair.return_value = ("private_key", "public_key")
        mock_docker.restart_container.return_value = True
        mock_qr.generate_qr.return_value = True

        manager = ClientManager()
        with (
            patch.object(manager, "_check_client_exists", return_value=False),
            patch.object(manager, "_get_server_public_key", return_value="server_public_key"),
            patch.object(manager, "_add_peer_to_server_config"),
            patch.object(manager, "_create_client_config", return_value="config_content"),
            patch("builtins.open", mock_open()),
        ):
            result = manager.add("test-server", "test-client")

        assert result is True
        mock_validate_server.assert_called_once_with("test-server")
        mock_validate_client.assert_called_once_with("test-client")
        mock_key_gen.generate_keypair.assert_called_once()

    @patch("vpn_manager.clients.validate_server_name")
    @patch("vpn_manager.clients.validate_client_name")
    @patch("vpn_manager.clients.Logger")
    def test_add_client_invalid_server(self, mock_logger, mock_validate_client, mock_validate_server):
        """Test client addition with invalid server"""
        mock_validate_server.return_value = False

        manager = ClientManager()
        result = manager.add("invalid-server", "test-client")

        assert result is False
        mock_validate_server.assert_called_once_with("invalid-server")

    @patch("vpn_manager.clients.validate_server_name")
    @patch("vpn_manager.clients.validate_client_name")
    @patch("vpn_manager.clients.Logger")
    def test_add_client_invalid_client_name(self, mock_logger, mock_validate_client, mock_validate_server):
        """Test client addition with invalid client name"""
        mock_validate_server.return_value = True
        mock_validate_client.return_value = False

        manager = ClientManager()
        result = manager.add("test-server", "invalid@client")

        assert result is False
        mock_validate_client.assert_called_once_with("invalid@client")

    @patch("vpn_manager.clients.validate_server_name")
    @patch("vpn_manager.clients.validate_client_name")
    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.Logger")
    def test_add_client_already_exists(
        self, mock_logger, mock_wg_config, mock_validate_client, mock_validate_server
    ):
        """Test client addition when client already exists"""
        mock_validate_server.return_value = True
        mock_validate_client.return_value = True

        mock_config_instance = MagicMock()
        mock_config_instance.clients_dir = Path("/tmp/clients")
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        with patch.object(manager, "_check_client_exists", return_value=True):
            result = manager.add("test-server", "existing-client")

        assert result is False
        mock_logger.error.assert_called()

    @patch("vpn_manager.clients.validate_server_name")
    @patch("vpn_manager.clients.validate_client_name")
    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.DockerManager")
    @patch("vpn_manager.clients.Logger")
    def test_remove_client_success(
        self, mock_logger, mock_docker, mock_wg_config, mock_validate_client, mock_validate_server
    ):
        """Test successful client removal"""
        mock_validate_server.return_value = True
        mock_validate_client.return_value = True

        mock_config_instance = MagicMock()
        mock_config_instance.get_server_info.return_value = ServerConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
            dns="1.1.1.1",
            allowed_ips="0.0.0.0/0",
            peers=1,
            public_key="test_public_key",
        )
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = "# Client: test-client\n[Peer]\nPublicKey = key\nAllowedIPs = 10.13.13.2/32\n"
        mock_config_instance.wg_config_file.write.return_value = None
        mock_config_instance.clients_dir = MagicMock()
        mock_config_instance.clients_dir.exists.return_value = False
        mock_wg_config.return_value = mock_config_instance

        mock_docker.restart_container.return_value = True

        manager = ClientManager()
        with (
            patch.object(manager, "_check_client_exists", return_value=True),
            patch.object(manager, "_remove_client_files", return_value=True),
            patch("builtins.open", mock_open()),
        ):
            result = manager.remove("test-server", "test-client")

        assert result is True

    @patch("vpn_manager.clients.validate_server_name")
    @patch("vpn_manager.clients.validate_client_name")
    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.Logger")
    def test_remove_client_not_found(
        self, mock_logger, mock_wg_config, mock_validate_client, mock_validate_server
    ):
        """Test client removal when client doesn't exist"""
        mock_validate_server.return_value = True
        mock_validate_client.return_value = True

        mock_config_instance = MagicMock()
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        with patch.object(manager, "_check_client_exists", return_value=False):
            result = manager.remove("test-server", "nonexistent-client")

        assert result is False
        mock_logger.error.assert_called()

    @patch("vpn_manager.clients.validate_server_name")
    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.Logger")
    def test_list_clients_success(self, mock_logger, mock_wg_config, mock_validate_server):
        """Test successful client listing"""
        mock_validate_server.return_value = True

        mock_config_instance = MagicMock()
        mock_clients_dir = MagicMock()
        mock_clients_dir.exists.return_value = True
        mock_clients_dir.glob.return_value = [
            MagicMock(stem="client1"),
            MagicMock(stem="client2"),
        ]
        mock_config_instance.clients_dir = mock_clients_dir
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = "# Client: client3\n[Peer]\n"
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        with patch("builtins.open", mock_open(read_data="# Client: client3\n[Peer]\n")):
            clients = manager.list_clients("test-server", show_output=False)

        assert len(clients) == 3
        assert "client1" in clients
        assert "client2" in clients
        assert "client3" in clients

    @patch("vpn_manager.clients.validate_server_name")
    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.Logger")
    def test_list_clients_empty(self, mock_logger, mock_wg_config, mock_validate_server):
        """Test client listing when no clients exist"""
        mock_validate_server.return_value = True

        mock_config_instance = MagicMock()
        mock_clients_dir = MagicMock()
        mock_clients_dir.exists.return_value = True
        mock_clients_dir.glob.return_value = []
        mock_config_instance.clients_dir = mock_clients_dir
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = ""
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        clients = manager.list_clients("test-server", show_output=False)

        assert len(clients) == 0

    @patch("vpn_manager.clients.validate_server_name")
    @patch("vpn_manager.clients.Logger")
    def test_list_clients_invalid_server(self, mock_logger, mock_validate_server):
        """Test client listing with invalid server"""
        mock_validate_server.return_value = False

        manager = ClientManager()
        clients = manager.list_clients("invalid-server", show_output=False)

        assert len(clients) == 0

    @patch("vpn_manager.clients.ServerConfig")
    def test_check_client_exists_in_file(self, mock_wg_config):
        """Test _check_client_exists when client exists in file"""
        mock_config_instance = MagicMock()
        mock_clients_dir = MagicMock()
        mock_client_file = MagicMock()
        mock_client_file.exists.return_value = True
        mock_clients_dir.__truediv__ = MagicMock(return_value=mock_client_file)
        mock_config_instance.clients_dir = mock_clients_dir
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        result = manager._check_client_exists(mock_config_instance, "test-client")

        assert result is True

    @patch("vpn_manager.clients.ServerConfig")
    def test_check_client_exists_in_config(self, mock_wg_config):
        """Test _check_client_exists when client exists in server config"""
        mock_config_instance = MagicMock()
        mock_clients_dir = MagicMock()
        mock_client_file = MagicMock()
        mock_client_file.exists.return_value = False
        mock_clients_dir.__truediv__ = MagicMock(return_value=mock_client_file)
        mock_config_instance.clients_dir = mock_clients_dir
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = "# Client: test-client\n[Peer]\n"
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        with patch("builtins.open", mock_open(read_data="# Client: test-client\n[Peer]\n")):
            result = manager._check_client_exists(mock_config_instance, "test-client")

        assert result is True

    @patch("vpn_manager.clients.ServerConfig")
    def test_check_client_not_exists(self, mock_wg_config):
        """Test _check_client_exists when client doesn't exist"""
        mock_config_instance = MagicMock()
        mock_clients_dir = MagicMock()
        mock_client_file = MagicMock()
        mock_client_file.exists.return_value = False
        mock_clients_dir.__truediv__ = MagicMock(return_value=mock_client_file)
        mock_config_instance.clients_dir = mock_clients_dir
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = "# Client: other-client\n[Peer]\n"
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        result = manager._check_client_exists(mock_config_instance, "test-client")

        assert result is False

    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.subprocess")
    @patch("vpn_manager.clients.KeyGenerator")
    def test_get_server_public_key_with_wg(self, mock_key_gen, mock_subprocess, mock_wg_config):
        """Test _get_server_public_key using local wg command"""
        mock_config_instance = MagicMock()
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = "[Interface]\nPrivateKey = test_private_key\n"
        mock_wg_config.return_value = mock_config_instance

        mock_key_gen.command_exists.return_value = True
        mock_subprocess.run.return_value = MagicMock(stdout="public_key\n")

        manager = ClientManager()
        with patch("builtins.open", mock_open(read_data="[Interface]\nPrivateKey = test_private_key\n")):
            public_key = manager._get_server_public_key(mock_config_instance)

        assert public_key == "public_key"

    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.subprocess")
    @patch("vpn_manager.clients.KeyGenerator")
    def test_get_server_public_key_with_docker(self, mock_key_gen, mock_subprocess, mock_wg_config):
        """Test _get_server_public_key using Docker"""
        mock_config_instance = MagicMock()
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = "[Interface]\nPrivateKey = test_private_key\n"
        mock_wg_config.return_value = mock_config_instance

        mock_key_gen.command_exists.side_effect = lambda cmd: cmd == "docker"
        mock_subprocess.run.return_value = MagicMock(stdout="public_key\n")

        manager = ClientManager()
        with patch("builtins.open", mock_open(read_data="[Interface]\nPrivateKey = test_private_key\n")):
            public_key = manager._get_server_public_key(mock_config_instance)

        assert public_key == "public_key"

    @patch("vpn_manager.clients.ServerConfig")
    def test_get_server_public_key_no_private_key(self, mock_wg_config):
        """Test _get_server_public_key when private key not found"""
        mock_config_instance = MagicMock()
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = "[Interface]\n"
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        with pytest.raises(ValueError):
            manager._get_server_public_key(mock_config_instance)

    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.Logger")
    def test_add_peer_to_server_config(self, mock_logger, mock_wg_config):
        """Test _add_peer_to_server_config"""
        mock_config_instance = MagicMock()
        mock_config_instance.wg_config_file = Path("/tmp/wg0.conf")
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        with patch("builtins.open", mock_open()) as mock_file:
            manager._add_peer_to_server_config(
                mock_config_instance, "test-client", "public_key", "10.13.13.2"
            )

        mock_file.assert_called_once()
        mock_logger.success.assert_called_once()

    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.Logger")
    def test_create_client_config(self, mock_logger, mock_wg_config):
        """Test _create_client_config"""

        mock_config_instance = MagicMock()
        mock_config_instance.get_server_info.return_value = ServerConfigData(
            name="test-server",
            url="vpn.example.com",
            port=51820,
            subnet="10.13.13.0/24",
            dns="1.1.1.1",
            allowed_ips="0.0.0.0/0",
            peers=1,
            public_key="test_public_key",
        )
        mock_clients_dir = MagicMock()
        mock_client_file = MagicMock()
        mock_client_file.chmod = MagicMock()
        mock_clients_dir.__truediv__ = MagicMock(return_value=mock_client_file)
        mock_config_instance.clients_dir = mock_clients_dir
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        with patch("builtins.open", mock_open()):
            config_content = manager._create_client_config(
                mock_config_instance, "test-client", "private_key", "10.13.13.2", "server_public_key"
            )

        assert "PrivateKey = private_key" in config_content
        assert "Address = 10.13.13.2/32" in config_content
        assert "PublicKey = server_public_key" in config_content
        mock_logger.success.assert_called_once()

    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.Logger")
    def test_remove_peer_from_server_config_success(self, mock_logger, mock_wg_config):
        """Test _remove_peer_from_server_config success"""
        mock_config_instance = MagicMock()
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = (
            "# Client: test-client\n[Peer]\nPublicKey = key\nAllowedIPs = 10.13.13.2/32\n"
        )
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        with patch("builtins.open", mock_open(read_data="# Client: test-client\n[Peer]\nPublicKey = key\nAllowedIPs = 10.13.13.2/32\n")):
            result = manager._remove_peer_from_server_config(mock_config_instance, "test-client")

        assert result is True
        mock_logger.success.assert_called_once()

    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.Logger")
    def test_remove_peer_from_server_config_not_found(self, mock_logger, mock_wg_config):
        """Test _remove_peer_from_server_config when client not found"""
        mock_config_instance = MagicMock()
        mock_config_instance.wg_config_file.exists.return_value = True
        mock_config_instance.wg_config_file.read.return_value = "# Client: other-client\n[Peer]\n"
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        result = manager._remove_peer_from_server_config(mock_config_instance, "test-client")

        assert result is False
        mock_logger.warning.assert_called_once()

    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.Logger")
    def test_remove_client_files_success(self, mock_logger, mock_wg_config):
        """Test _remove_client_files success"""
        mock_config_instance = MagicMock()
        mock_config_instance.clients_dir = Path("/tmp/clients")
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.unlink"),
        ):
            result = manager._remove_client_files(mock_config_instance, "test-client")

        assert result is True
        mock_logger.success.assert_called_once()

    @patch("vpn_manager.clients.ServerConfig")
    @patch("vpn_manager.clients.Logger")
    def test_remove_client_files_not_found(self, mock_logger, mock_wg_config):
        """Test _remove_client_files when file not found"""
        mock_config_instance = MagicMock()
        mock_config_instance.clients_dir = Path("/tmp/clients")
        mock_wg_config.return_value = mock_config_instance

        manager = ClientManager()
        with patch("pathlib.Path.exists", return_value=False):
            result = manager._remove_client_files(mock_config_instance, "test-client")

        assert result is False
        mock_logger.warning.assert_called_once()

    @patch("vpn_manager.clients.ServiceManager")
    @patch("vpn_manager.clients.Logger")
    def test_list_all_clients(self, mock_logger, mock_service_manager):
        """Test list_all_clients"""
        mock_service_instance = MagicMock()
        mock_service_instance.get_available_servers.return_value = ["server1", "server2"]
        mock_service_manager.return_value = mock_service_instance

        manager = ClientManager()
        with patch.object(manager, "list_clients") as mock_list:
            mock_list.side_effect = lambda server, show_output: ["client1"] if server == "server1" else ["client2"]
            manager.list_all_clients()

        mock_list.assert_called()
