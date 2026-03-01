#!/bin/bash
set -e

echo "🚀 Setting up WireGuard VPN Manager with pipx..."

# Check if we're in the right directory (should have pyproject.toml and src/vpn_manager)
if [ ! -f "pyproject.toml" ] || [ ! -d "src/vpn_manager" ]; then
    echo "❌ Error: pyproject.toml or src/vpn_manager not found. Run this script from the project root directory."
    exit 1
fi

# Check Python version
echo "🐍 Checking Python version..."
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
required_version="3.13"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Error: Python $required_version or higher is required. Found: $python_version"
    echo "Please install Python $required_version or higher:"
    echo "  - Ubuntu/Debian: sudo apt install python3.13"
    echo "  - macOS: brew install python@3.13"
    echo "  - Or download from: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python $python_version is compatible"

# Check if pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "📦 pipx not found. Installing pipx..."
    
    # Check if python3 is available first
    if ! command -v python3 &> /dev/null; then
        echo "❌ Error: python3 is not available."
        echo "Please install Python 3 first:"
        echo "  - Ubuntu/Debian: sudo apt install python3"
        echo "  - macOS: brew install python3"
        echo "  - Or download from: https://www.python.org/downloads/"
        exit 1
    fi
    
    # Try to install pipx using different methods
    if command -v brew &> /dev/null; then
        echo "Installing pipx via Homebrew..."
        brew install pipx
        pipx ensurepath
    elif command -v apt &> /dev/null; then
        echo "Installing pipx via apt..."
        sudo apt update && sudo apt install -y pipx
        pipx ensurepath
    elif python3 -m pip --version &> /dev/null; then
        echo "Installing pipx via pip..."
        python3 -m pip install --user pipx
        pipx ensurepath
    else
        echo "❌ Error: Could not install pipx automatically."
        echo "Please install pipx manually:"
        echo "  - Ubuntu/Debian: sudo apt install pipx"
        echo "  - macOS: brew install pipx"
        echo "  - Other: python3 -m pip install --user pipx"
        exit 1
    fi
    
    # Ensure pipx is in PATH
    export PATH="$HOME/.local/bin:$PATH"
    
    echo "✅ pipx installed successfully!"
else
    echo "📦 pipx is already installed"
fi

# Install the package in development mode with pipx
echo "📥 Installing WireGuard VPN Manager with pipx..."

# Remove existing installation if it exists
if pipx list | grep -q "wireguard-vpn-manager"; then
    echo "🔄 Removing existing installation..."
    pipx uninstall wireguard-vpn-manager
fi

# Install in editable mode with development dependencies
echo "📦 Installing in development mode..."
pipx install --editable ".[dev]"

echo ""
echo "✅ Setup complete!"
echo ""
echo "The 'vpn-manager' command is now available globally!"
echo ""
echo "Get started:"
echo "  vpn-manager --help"
echo ""
