"""
Tests for clients.py module
"""

from unittest.mock import MagicMock, mock_open, patch

from vpn_manager.clients import ClientManager
from vpn_manager.servers import StoredServerConfigData


class TestClientManager:
    """Test ClientManager class"""

    @patch("vpn_manager.clients.clients.validate_server_name")
    @patch("vpn_manager.clients.clients.validate_client_name")
    @patch("vpn_manager.clients.clients.load_service_config")
    @patch("vpn_manager.clients.clients.list_peers")
    @patch("vpn_manager.clients.clients.add_peer")
    @patch("vpn_manager.clients.clients.ServerManager")
    @patch("vpn_manager.clients.clients.DockerComposeManager")
    @patch("vpn_manager.clients.clients.Logger")
    def test_add_client_success(
        self,
        mock_logger,
        mock_docker_class,
        mock_server_manager_class,
        mock_add_peer,
        mock_list_peers,
        mock_load_config,
        mock_validate_client,
        mock_validate_server,
    ):
        """Test successful client addition"""
        # Setup mocks
        mock_validate_server.return_value = True
        mock_validate_client.return_value = True
        mock_list_peers.return_value = []

        mock_config = StoredServerConfigData(
            server_url="vpn.example.com",
            server_port=51820,
            peers="1",
            peer_dns="1.1.1.1",
            internal_subnet="10.13.13.0",
            allowed_ips="0.0.0.0/0",
            tz="UTC",
            log_confs=True,
            container_name="wireguard",
            image="linuxserver/wireguard:latest",
        )
        mock_load_config.return_value = mock_config

        mock_server_manager = MagicMock()
        mock_server_manager.build.return_value = True
        mock_server_manager_class.return_value = mock_server_manager

        mock_docker = MagicMock()
        mock_docker.restart_container.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ClientManager()
        with (
            patch.object(manager, "_wait_for_client_config", return_value=True),
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data="[Interface]\nPrivateKey = test\n")),
        ):
            result = manager.add("test-server", "test-client")

        assert result is True
        mock_validate_server.assert_called_once_with("test-server")
        mock_validate_client.assert_called_once_with("test-client")
        mock_add_peer.assert_called_once_with("test-server", "test-client")

    @patch("vpn_manager.clients.clients.validate_server_name")
    @patch("vpn_manager.clients.clients.validate_client_name")
    @patch("vpn_manager.clients.clients.Logger")
    def test_add_client_invalid_server(self, mock_logger, mock_validate_client, mock_validate_server):
        """Test client addition with invalid server"""
        mock_validate_server.return_value = False

        manager = ClientManager()
        result = manager.add("invalid-server", "test-client")

        assert result is False
        mock_validate_server.assert_called_once_with("invalid-server")

    @patch("vpn_manager.clients.clients.validate_server_name")
    @patch("vpn_manager.clients.clients.validate_client_name")
    @patch("vpn_manager.clients.clients.Logger")
    def test_add_client_invalid_client_name(self, mock_logger, mock_validate_client, mock_validate_server):
        """Test client addition with invalid client name"""
        mock_validate_server.return_value = True
        mock_validate_client.return_value = False

        manager = ClientManager()
        result = manager.add("test-server", "invalid@client")

        assert result is False
        mock_validate_client.assert_called_once_with("invalid@client")

    @patch("vpn_manager.clients.clients.validate_server_name")
    @patch("vpn_manager.clients.clients.validate_client_name")
    @patch("vpn_manager.clients.clients.list_peers")
    @patch("vpn_manager.clients.clients.Logger")
    def test_add_client_already_exists(
        self, mock_logger, mock_list_peers, mock_validate_client, mock_validate_server
    ):
        """Test client addition when client already exists"""
        mock_validate_server.return_value = True
        mock_validate_client.return_value = True
        mock_list_peers.return_value = ["existing-client"]

        manager = ClientManager()
        result = manager.add("test-server", "existing-client")

        assert result is False
        mock_logger.error.assert_called()

    @patch("vpn_manager.clients.clients.validate_server_name")
    @patch("vpn_manager.clients.clients.validate_client_name")
    @patch("vpn_manager.clients.clients.load_service_config")
    @patch("vpn_manager.clients.clients.list_peers")
    @patch("vpn_manager.clients.clients.remove_peer")
    @patch("vpn_manager.clients.clients.ServerManager")
    @patch("vpn_manager.clients.clients.DockerComposeManager")
    @patch("vpn_manager.clients.clients.Logger")
    def test_remove_client_success(
        self,
        mock_logger,
        mock_docker_class,
        mock_server_manager_class,
        mock_remove_peer,
        mock_list_peers,
        mock_load_config,
        mock_validate_client,
        mock_validate_server,
    ):
        """Test successful client removal"""
        mock_validate_server.return_value = True
        mock_validate_client.return_value = True
        mock_list_peers.return_value = ["test-client"]

        mock_config = StoredServerConfigData(
            container_name="wireguard",
        )
        mock_load_config.return_value = mock_config

        mock_server_manager = MagicMock()
        mock_server_manager.build.return_value = True
        mock_server_manager_class.return_value = mock_server_manager

        mock_docker = MagicMock()
        mock_docker.restart_container.return_value = True
        mock_docker_class.return_value = mock_docker

        manager = ClientManager()
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch.object(manager, "_remove_client_files", return_value=True),
        ):
            result = manager.remove("test-server", "test-client")

        assert result is True
        mock_remove_peer.assert_called_once_with("test-server", "test-client")

    @patch("vpn_manager.clients.clients.validate_server_name")
    @patch("vpn_manager.clients.clients.validate_client_name")
    @patch("vpn_manager.clients.clients.list_peers")
    @patch("vpn_manager.clients.clients.Logger")
    def test_remove_client_not_found(
        self, mock_logger, mock_list_peers, mock_validate_client, mock_validate_server
    ):
        """Test client removal when client doesn't exist"""
        mock_validate_server.return_value = True
        mock_validate_client.return_value = True
        mock_list_peers.return_value = []

        manager = ClientManager()
        result = manager.remove("test-server", "nonexistent-client")

        assert result is False
        mock_logger.error.assert_called()

    @patch("vpn_manager.clients.clients.validate_server_name")
    @patch("vpn_manager.clients.clients.list_peers")
    @patch("vpn_manager.clients.clients.Logger")
    def test_list_clients_success(self, mock_logger, mock_list_peers, mock_validate_server):
        """Test successful client listing"""
        mock_validate_server.return_value = True
        mock_list_peers.return_value = ["client1", "client2"]

        manager = ClientManager()
        clients = manager.list_clients("test-server", show_output=False)

        assert len(clients) == 2
        assert "client1" in clients
        assert "client2" in clients

    @patch("vpn_manager.clients.clients.validate_server_name")
    @patch("vpn_manager.clients.clients.list_peers")
    @patch("vpn_manager.clients.clients.Logger")
    def test_list_clients_empty(self, mock_logger, mock_list_peers, mock_validate_server):
        """Test client listing when no clients exist"""
        mock_validate_server.return_value = True
        mock_list_peers.return_value = []

        manager = ClientManager()
        clients = manager.list_clients("test-server", show_output=False)

        assert len(clients) == 0

    @patch("vpn_manager.clients.clients.validate_server_name")
    @patch("vpn_manager.clients.clients.Logger")
    def test_list_clients_invalid_server(self, mock_logger, mock_validate_server):
        """Test client listing with invalid server"""
        mock_validate_server.return_value = False

        manager = ClientManager()
        clients = manager.list_clients("invalid-server", show_output=False)

        assert len(clients) == 0

    @patch("vpn_manager.clients.clients.list_peers")
    def test_check_client_exists_in_file(self, mock_list_peers):
        """Test _check_client_exists when client exists"""
        mock_list_peers.return_value = ["test-client"]

        manager = ClientManager()
        result = manager._check_client_exists("test-server", "test-client")

        assert result is True

    @patch("vpn_manager.clients.clients.list_peers")
    def test_check_client_not_exists(self, mock_list_peers):
        """Test _check_client_exists when client doesn't exist"""
        mock_list_peers.return_value = ["other-client"]

        manager = ClientManager()
        result = manager._check_client_exists("test-server", "test-client")

        assert result is False

    def test_check_client_in_wg0_conf_with_real_content(self, tmp_dir):
        """Test _check_client_in_wg0_conf with realistic wg0.conf content"""
        # Create server directory structure
        server_dir = tmp_dir / "servers" / "test-server" / "container-config" / "wg_confs"
        server_dir.mkdir(parents=True)

        # Create wg0.conf with realistic content (from actual WireGuard server)
        wg0_conf_file = server_dir / "wg0.conf"
        wg0_conf_content = """[Interface]
Address = 10.13.13.1
ListenPort = 51820
PrivateKey = qA+tyUS6b1itb74fH//w0099YzyMasiF53QjYY4GmV8=
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth+ -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth+ -j MASQUERADE

[Peer]
# peer_home
PublicKey = u8ASzpoAKVOet0XeRKC0HZ00g59d9isgIdPdrX0cUSc=
PresharedKey = UiHkwaj4RCk8KpNMHxg9/WRZ4CQCvI8mDXLROEbCkKA=
AllowedIPs = 10.13.13.2/32

[Peer]
# peer_home1
PublicKey = IATBjUUrDb/qvcubTY4hFPKYSmIza7dLFE6Zh8fE4Vs=
PresharedKey = W51qVP2GuyI9jTIs0lxEEZLaJZ5vfzsZLBs+/9QZrmk=
AllowedIPs = 10.13.13.3/32

[Peer]
# peer_home2
PublicKey = cxGZt/LHAmqyvSgrqA+3JT1Vls7pBrn3rKmyfy0OdXw=
PresharedKey = 4qgH38Ttr8kFdMioF02AzviySB1DsXK2mwnvu924C9w=
AllowedIPs = 10.13.13.4/32
"""
        wg0_conf_file.write_text(wg0_conf_content)

        manager = ClientManager()

        # Test that existing client "home" is found (comment format: # peer_home)
        result = manager._check_client_in_wg0_conf("test-server", "home")
        assert result is True

        # Test that existing client "home1" is found (comment format: # peer_home1)
        result = manager._check_client_in_wg0_conf("test-server", "home1")
        assert result is True

        # Test that existing client "home2" is found (comment format: # peer_home2)
        result = manager._check_client_in_wg0_conf("test-server", "home2")
        assert result is True

        # Test that non-existing client is not found
        result = manager._check_client_in_wg0_conf("test-server", "non-existing-client")
        assert result is False

    def test_check_client_in_wg0_conf_file_not_exists(self, tmp_dir):
        """Test _check_client_in_wg0_conf when wg0.conf file doesn't exist"""
        # Create server directory structure but without wg0.conf
        server_dir = tmp_dir / "servers" / "test-server" / "container-config" / "wg_confs"
        server_dir.mkdir(parents=True)

        manager = ClientManager()

        # Test that method returns False when file doesn't exist
        result = manager._check_client_in_wg0_conf("test-server", "test-client")
        assert result is False

    @patch("vpn_manager.clients.clients.time.sleep")
    def test_wait_for_client_config_success(self, mock_sleep):
        """Test _wait_for_client_config when config is generated"""
        manager = ClientManager()
        # Mock _check_client_in_wg0_conf to return False then True (step 1)
        # Then mock Path.exists to return True immediately (step 2 - file exists)
        with (
            patch.object(manager, "_check_client_in_wg0_conf", side_effect=[False, True]),
            patch("pathlib.Path.exists", return_value=True),
        ):
            result = manager._wait_for_client_config("test-server", "test-client", max_attempts=3)

        assert result is True
        # 1 sleep for step 1 (wg0.conf check), 0 sleeps for step 2 (file exists immediately)
        assert mock_sleep.call_count == 1

    @patch("vpn_manager.clients.clients.time.sleep")
    def test_wait_for_client_config_timeout(self, mock_sleep):
        """Test _wait_for_client_config when timeout occurs"""
        manager = ClientManager()
        # Mock _check_client_in_wg0_conf to always return False (step 1 timeout)
        with patch.object(manager, "_check_client_in_wg0_conf", return_value=False):
            result = manager._wait_for_client_config("test-server", "test-client", max_attempts=3)

        assert result is False
        # Should timeout in step 1 after 3 attempts
        assert mock_sleep.call_count == 3

    @patch("vpn_manager.clients.clients.Logger")
    @patch("vpn_manager.clients.clients.shutil.rmtree")
    def test_remove_client_files_success(self, mock_rmtree, mock_logger):
        """Test _remove_client_files success"""
        manager = ClientManager()
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_dir", return_value=True),
        ):
            result = manager._remove_client_files("test-server", "test-client")

        assert result is True
        # success is called once (for removing the client directory)
        assert mock_logger.success.call_count == 1
        # rmtree is called once to remove the client directory
        mock_rmtree.assert_called_once()

    @patch("vpn_manager.clients.clients.Logger")
    def test_remove_client_files_not_found(self, mock_logger):
        """Test _remove_client_files when file not found"""
        manager = ClientManager()
        with patch("pathlib.Path.exists", return_value=False):
            result = manager._remove_client_files("test-server", "test-client")

        assert result is False
        mock_logger.warning.assert_called_once()

    @patch("vpn_manager.clients.clients.ServiceManager")
    @patch("vpn_manager.clients.clients.Logger")
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
