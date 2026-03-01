# WireGuard VPN Manager

Unified command-line interface for WireGuard VPN management.

For detailed usage and configuration, see the main [README.md](../README.md).

## Installation

### Quick Setup with pipx (Recommended)

Run the setup script from the project root:

```bash
cd ..
./setup.sh
```

This will automatically install pipx, the manager, and development tools globally.

### Manual Installation

```bash
# Install pipx if not installed
pip install --user pipx
pipx ensurepath

# Install the manager (from project root)
cd ..
pipx install --editable "vpn-manager/.[dev]"
```

## Development

### Code Quality Tools

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

## Uninstalling

```bash
pipx uninstall wireguard-vpn-manager
```

## Troubleshooting

### Command not found

```bash
# Reinstall with pipx
pipx install --editable ".[dev]" --force
```

### Import errors

```bash
# Reinstall the package
pipx install --editable ".[dev]" --force
```
