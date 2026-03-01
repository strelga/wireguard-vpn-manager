"""
Tests for keys.py module
"""

from unittest.mock import patch

from vpn_manager.keys import KeyManager


class TestKeyManager:
    """Test KeyManager class"""

    @patch("vpn_manager.keys.KeyGenerator")
    @patch("vpn_manager.keys.Logger")
    def test_generate_to_console_success(self, mock_logger, mock_key_generator):
        """Test successful key generation to console"""
        mock_key_generator.generate_keypair.return_value = ("private_key", "public_key")

        manager = KeyManager()
        result = manager.generate(output_directory=None)

        assert result is True
        mock_key_generator.generate_keypair.assert_called_once()
        mock_logger.success.assert_called()

    @patch("vpn_manager.keys.KeyGenerator")
    @patch("vpn_manager.keys.Logger")
    def test_generate_to_directory_success(self, mock_logger, mock_key_generator, tmp_dir):
        """Test successful key generation to directory"""
        mock_key_generator.generate_keypair.return_value = ("private_key", "public_key")

        output_dir = tmp_dir / "keys"
        manager = KeyManager()
        result = manager.generate(output_directory=str(output_dir))

        assert result is True
        assert output_dir.exists()
        assert (output_dir / "private.key").exists()
        assert (output_dir / "public.key").exists()

        # Check file contents
        assert (output_dir / "private.key").read_text() == "private_key"
        assert (output_dir / "public.key").read_text() == "public_key"

        # Check file permissions
        private_stat = (output_dir / "private.key").stat()
        public_stat = (output_dir / "public.key").stat()
        assert oct(private_stat.st_mode)[-3:] == "600"
        assert oct(public_stat.st_mode)[-3:] == "644"

    @patch("vpn_manager.keys.KeyGenerator")
    @patch("vpn_manager.keys.Logger")
    def test_generate_empty_keys(self, mock_logger, mock_key_generator):
        """Test key generation when keys are empty"""
        mock_key_generator.generate_keypair.return_value = ("", "")

        manager = KeyManager()
        result = manager.generate(output_directory=None)

        assert result is False
        mock_logger.error.assert_called_once()

    @patch("vpn_manager.keys.KeyGenerator")
    @patch("vpn_manager.keys.Logger")
    def test_generate_exception(self, mock_logger, mock_key_generator):
        """Test key generation when exception occurs"""
        mock_key_generator.generate_keypair.side_effect = Exception("Generation failed")

        manager = KeyManager()
        result = manager.generate(output_directory=None)

        assert result is False
        mock_logger.error.assert_called_once()

    @patch("vpn_manager.keys.KeyGenerator")
    @patch("vpn_manager.keys.Logger")
    def test_generate_creates_nested_directory(self, mock_logger, mock_key_generator, tmp_dir):
        """Test that nested directories are created"""
        mock_key_generator.generate_keypair.return_value = ("private_key", "public_key")

        output_dir = tmp_dir / "deep" / "nested" / "keys"
        manager = KeyManager()
        result = manager.generate(output_directory=str(output_dir))

        assert result is True
        assert output_dir.exists()
        assert (output_dir / "private.key").exists()
