"""
Tests for clients/utils.py module - validate_client_name function
"""

from unittest.mock import MagicMock, patch

from vpn_manager.clients.utils import validate_client_name


class TestValidateClientName:
    """Test validate_client_name function"""

    @patch("vpn_manager.clients.utils.Logger")
    def test_valid_client_name(self, mock_logger: MagicMock) -> None:
        """Test valid client names"""
        assert validate_client_name("client1") is True
        assert validate_client_name("client-1") is True
        assert validate_client_name("client_1") is True
        assert validate_client_name("Client-Name_123") is True

    @patch("vpn_manager.clients.utils.Logger")
    def test_invalid_client_name_empty(self, mock_logger: MagicMock) -> None:
        """Test empty client name"""
        assert validate_client_name("") is False
        mock_logger.error.assert_called_once()

    @patch("vpn_manager.clients.utils.Logger")
    def test_invalid_client_name_special_chars(self, mock_logger: MagicMock) -> None:
        """Test client name with special characters"""
        assert validate_client_name("client@1") is False
        assert validate_client_name("client#1") is False
        assert validate_client_name("client 1") is False
        mock_logger.error.assert_called()
