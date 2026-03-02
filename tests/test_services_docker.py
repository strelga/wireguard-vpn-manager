"""
Tests for services/docker.py module - DockerManager class
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from vpn_manager.services import DockerManager


class TestDockerManager:
    """Test DockerManager class"""

    @patch("subprocess.run")
    def test_get_compose_command_docker_compose(self, mock_run: MagicMock) -> None:
        """Test get_compose_command with docker-compose"""
        mock_run.return_value = MagicMock()
        command = DockerManager.get_compose_command()
        assert command == "docker-compose"

    @patch("subprocess.run")
    def test_get_compose_command_docker_compose_v2(self, mock_run: MagicMock) -> None:
        """Test get_compose_command with docker compose v2"""
        def side_effect_func(*args, **kwargs):
            if "docker-compose" in args[0]:
                raise FileNotFoundError()
            return MagicMock()

        mock_run.side_effect = side_effect_func
        command = DockerManager.get_compose_command()
        assert command == "docker compose"

    @patch("subprocess.run")
    def test_get_compose_command_not_available(self, mock_run: MagicMock) -> None:
        """Test get_compose_command when neither is available"""
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(RuntimeError):
            DockerManager.get_compose_command()

    @patch("subprocess.run")
    def test_restart_container_success(self, mock_run: MagicMock) -> None:
        """Test successful container restart"""
        mock_run.return_value = MagicMock()
        with patch.object(DockerManager, "get_compose_command", return_value="docker compose"):
            assert DockerManager.restart_container("test-container") is True

    @patch("subprocess.run")
    def test_restart_container_failure(self, mock_run: MagicMock) -> None:
        """Test failed container restart"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "docker compose")
        with patch.object(DockerManager, "get_compose_command", return_value="docker compose"):
            assert DockerManager.restart_container("test-container") is False

    @patch("subprocess.run")
    def test_start_services_success(self, mock_run: MagicMock) -> None:
        """Test successful services start"""
        mock_run.return_value = MagicMock()
        with patch.object(DockerManager, "get_compose_command", return_value="docker compose"):
            assert DockerManager.start_services() is True

    @patch("subprocess.run")
    def test_stop_services_success(self, mock_run: MagicMock) -> None:
        """Test successful services stop"""
        mock_run.return_value = MagicMock()
        with patch.object(DockerManager, "get_compose_command", return_value="docker compose"):
            assert DockerManager.stop_services() is True
