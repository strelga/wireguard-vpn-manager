"""
Pytest configuration and fixtures for vpn-manager tests
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def tmp_dir():
    """Create a temporary directory for tests"""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        yield Path(tmpdir)
        os.chdir(original_cwd)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess module"""
    with patch("subprocess.run") as mock_run:
        yield mock_run


@pytest.fixture
def sample_server_config():
    """Sample server configuration"""
    return {
        "name": "test-server",
        "url": "vpn.example.com",
        "port": 51820,
        "subnet": "10.13.13.0/24",
        "dns": "1.1.1.1,8.8.8.8",
        "allowed_ips": "0.0.0.0/0",
        "peers": 1,
        "public_key": "test_public_key_abc123",
    }


@pytest.fixture
def sample_client_config():
    """Sample client configuration"""
    return {
        "name": "test-client",
        "private_key": "test_private_key_xyz789",
        "public_key": "test_client_public_key_def456",
        "ip": "10.13.13.2",
    }


@pytest.fixture
def sample_docker_compose():
    """Sample docker-compose.yml content"""
    return """version: '3.8'
services:
  wireguard-test-server:
    image: linuxserver/wireguard:latest
    container_name: wireguard-test-server
    cap_add:
      - NET_ADMIN
      - SYS_MODULE
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Moscow
      - SERVERURL=vpn.example.com
      - SERVERPORT=51820
      - PEERS=1
      - PEERDNS=1.1.1.1,8.8.8.8
      - INTERNAL_SUBNET=10.13.13.0/24
      - ALLOWEDIPS=0.0.0.0/0
    volumes:
      - ./test-server/config:/config
      - /lib/modules:/lib/modules:ro
    ports:
      - 51820:51820/udp
    sysctls:
      - net.ipv4.conf.all.src_valid_mark=1
      - net.ipv4.ip_forward=1
    restart: unless-stopped
"""


@pytest.fixture
def sample_wg_config():
    """Sample WireGuard configuration"""
    return """[Interface]
PrivateKey = test_private_key_xyz789
Address = 10.13.13.1/24
ListenPort = 51820
PostUp = iptables -A FORWARD -i %i -j ACCEPT; iptables -A FORWARD -o %i -j ACCEPT; iptables -t nat -A POSTROUTING -o eth+ -j MASQUERADE
PostDown = iptables -D FORWARD -i %i -j ACCEPT; iptables -D FORWARD -o %i -j ACCEPT; iptables -t nat -D POSTROUTING -o eth+ -j MASQUERADE

# Client: test-client
[Peer]
PublicKey = test_client_public_key_def456
AllowedIPs = 10.13.13.2/32
"""


@pytest.fixture
def mock_logger():
    """Mock Logger to suppress output during tests"""
    with patch("vpn_manager.utils.Logger") as mock:
        yield mock
