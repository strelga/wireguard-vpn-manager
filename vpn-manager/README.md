# WireGuard VPN Manager

Unified command-line interface for WireGuard VPN management.

## Setup

### Quick Setup with pipx (Recommended)

Run the setup script to install the manager globally using pipx:

```bash
cd ..
./setup.sh
```

This will automatically:

- Install pipx if not already installed
- Install the WireGuard VPN Manager globally with development dependencies
- Make the `vpn-manager` command available system-wide
- Install development tools (ruff, mypy) globally

### Manual Installation

If you prefer to install manually:

```bash
# Install pipx if not installed
pip install --user pipx
pipx ensurepath

# Install the manager (from project root)
cd ..
pipx install --editable "manager/.[dev]"
```

## Usage

After installation, the `vpn-manager` command is available globally:

```bash
vpn-manager --help
```

### Basic Commands

```bash
# Service management
vpn-manager start                    # Start all services
vpn-manager start internet          # Start specific server
vpn-manager stop                     # Stop all services
vpn-manager restart                  # Restart all services
vpn-manager status                   # Check status

# Client management
vpn-manager add-client internet phone    # Add client to server
vpn-manager remove-client internet phone # Remove client
vpn-manager list-clients                 # List all clients

# Server management
vpn-manager list-servers                 # List all servers
vpn-manager create-server myserver example.com 51822 10.15.15.0/24
vpn-manager remove-server myserver      # Remove server

# Key generation
vpn-manager generate-keys               # Generate key pair
```

## Development

### Code Quality Tools

The development tools are installed globally with pipx:

```bash
# Run linter
ruff check .

# Format code
ruff format .

# Type checking
mypy .

# Run all checks
ruff check . && mypy .
```

### Project Structure

- **pyproject.toml**: Modern Python project configuration
- **setup.sh**: Automated setup script using pipx
- **No virtual environment needed**: pipx manages isolation automatically

## Benefits of pipx

- **Global installation**: The `vpn-manager` command works from any directory
- **Isolated environment**: Each package has its own virtual environment
- **Easy management**: Simple install/uninstall with `pipx`
- **Development tools**: Linting and type checking tools available globally
- **No activation needed**: No need to activate virtual environments

## Uninstalling

To remove the manager:

```bash
pipx uninstall wireguard-vpn-manager
```

## Troubleshooting

### pipx not found

If pipx is not in your PATH after installation:

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export PATH="$HOME/.local/bin:$PATH"

# Or run
pipx ensurepath
```

### Command not found

If the `vpn-manager` command is not found:

```bash
# Reinstall with pipx
pipx install --editable ".[dev]" --force
