"""
Tests for utils.py module - Color, Logger, and QRCodeGenerator classes
"""

import subprocess
from unittest.mock import MagicMock, patch

from vpn_manager.utils import Color, Logger, QRCodeGenerator


class TestColor:
    """Test Color class"""

    def test_color_constants(self) -> None:
        """Test that all color constants are defined"""
        assert hasattr(Color, "RED")
        assert hasattr(Color, "GREEN")
        assert hasattr(Color, "YELLOW")
        assert hasattr(Color, "BLUE")
        assert hasattr(Color, "PURPLE")
        assert hasattr(Color, "CYAN")
        assert hasattr(Color, "WHITE")
        assert hasattr(Color, "NC")

    def test_color_values(self) -> None:
        """Test that color values are ANSI codes"""
        assert Color.RED == "\033[0;31m"
        assert Color.GREEN == "\033[0;32m"
        assert Color.NC == "\033[0m"


class TestLogger:
    """Test Logger class"""

    @patch("builtins.print")
    def test_info(self, mock_print: MagicMock) -> None:
        """Test info logging"""
        Logger.info("Test message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "[INFO]" in args
        assert "Test message" in args

    @patch("builtins.print")
    def test_success(self, mock_print: MagicMock) -> None:
        """Test success logging"""
        Logger.success("Test message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "[SUCCESS]" in args
        assert "Test message" in args

    @patch("builtins.print")
    def test_warning(self, mock_print: MagicMock) -> None:
        """Test warning logging"""
        Logger.warning("Test message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "[WARNING]" in args
        assert "Test message" in args

    @patch("builtins.print")
    def test_error(self, mock_print: MagicMock) -> None:
        """Test error logging"""
        Logger.error("Test message")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "[ERROR]" in args
        assert "Test message" in args

    @patch("builtins.print")
    def test_header(self, mock_print: MagicMock) -> None:
        """Test header logging"""
        Logger.header("Test Header")
        mock_print.assert_called_once()
        args = mock_print.call_args[0][0]
        assert "Test Header" in args


class TestQRCodeGenerator:
    """Test QRCodeGenerator class"""

    @patch("subprocess.run")
    def test_generate_qr_success(self, mock_run: MagicMock) -> None:
        """Test successful QR code generation"""
        mock_run.return_value = MagicMock(stdout="QR_CODE_OUTPUT")
        with patch.object(QRCodeGenerator, "_command_exists", return_value=True):
            assert QRCodeGenerator.generate_qr("test content") is True

    @patch("subprocess.run")
    def test_generate_qr_to_file(self, mock_run: MagicMock) -> None:
        """Test QR code generation to file"""
        mock_run.return_value = MagicMock()
        with patch.object(QRCodeGenerator, "_command_exists", return_value=True):
            assert QRCodeGenerator.generate_qr("test content", "output.png") is True

    @patch("subprocess.run")
    def test_generate_qr_no_qrencode(self, mock_run: MagicMock) -> None:
        """Test QR code generation when qrencode is not available"""
        with patch.object(QRCodeGenerator, "_command_exists", return_value=False):
            assert QRCodeGenerator.generate_qr("test content") is False

    @patch("subprocess.run")
    def test_generate_qr_failure(self, mock_run: MagicMock) -> None:
        """Test failed QR code generation"""
        mock_run.side_effect = subprocess.CalledProcessError(1, "qrencode")
        with patch.object(QRCodeGenerator, "_command_exists", return_value=True):
            assert QRCodeGenerator.generate_qr("test content") is False
