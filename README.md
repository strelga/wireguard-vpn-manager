# WireGuard VPN Management System

A comprehensive WireGuard VPN management system with Docker Compose support for multiple server configurations.

## Features

- **Multi-server support**: Manage multiple local WireGuard VPN servers with different configurations
- **Client management**: Easy addition and removal of VPN clients
- **Service management**: Start, stop, restart, and monitor services
- **QR code generation**: Mobile-friendly client configuration
- **Automated IP allocation**: Automatic assignment of client IP addresses
- **Secure key management**: Automated WireGuard key pair generation

## Installation

### Quick Setup with pipx (Recommended)

Run the setup script from the project root:

```bash
./setup.sh
```

This will automatically:

- Install pipx if not already installed
- Install the WireGuard VPN Manager globally with development dependencies
- Make the `vpn-manager` command available system-wide
- Install development tools (ruff, mypy) globally

## Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.13+**
- **qrencode** (optional, for QR code generation)
- **WireGuard tools** (optional, for local key generation)

### Install system dependencies (optional)

#### Ubuntu/Debian

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install optional tools
sudo apt update
sudo apt install qrencode wireguard-tools

# Logout and login again for Docker group changes
```

#### macOS

```bash
# Install Docker Desktop from https://docker.com
# Install optional tools
brew install qrencode wireguard-tools
```

## Configuration

1. **Server configurations** are stored in `servers/<server_name>/config.yml`:
   - Each server has its own YAML configuration file
   - Contains server URL, port, subnet, DNS, allowed IPs, and peers count
   - Automatically generated when creating a new server

1. **Docker Compose** is generated from server configs:
   - Run `vpn-manager service generate` to create `servers/docker-compose.generated.yml`
   - Main `docker-compose.yml` includes the generated file

## Usage

All management is done through the unified CLI tool. After running the setup script, the `vpn-manager` command is available globally:

```bash
vpn-manager --help
```

### Shell Autocompletion

The CLI supports shell autocompletion for commands, options, and arguments. Enable it for your shell:

#### Bash

```bash
# Install completion for current session
vpn-manager --install-completion bash

# Install permanently (add to ~/.bashrc)
echo 'eval "$(vpn-manager --show-completion bash)"' >> ~/.bashrc
source ~/.bashrc
```

#### Zsh

```bash
# Install completion for current session
vpn-manager --install-completion zsh

# Install permanently (add to ~/.zshrc)
echo 'eval "$(vpn-manager --show-completion zsh)"' >> ~/.zshrc
source ~/.zshrc
```

#### Fish

```bash
# Install completion for current session
vpn-manager --install-completion fish

# Install permanently (add to ~/.config/fish/completions/vpn-manager.fish)
vpn-manager --show-completion fish > ~/.config/fish/completions/vpn-manager.fish
```

#### PowerShell

```powershell
# Install completion for current session
vpn-manager --install-completion powershell | Out-String | Invoke-Expression

# Install permanently (add to PowerShell profile)
vpn-manager --show-completion powershell >> $PROFILE
```

To uninstall completion:

```bash
vpn-manager --uninstall-completion bash  # or zsh, fish, powershell
```

### Service Management

```bash
# Start services
vpn-manager service start [server_name]

# Stop services
vpn-manager service stop [server_name]

# Restart services
vpn-manager service restart [server_name]

# Check status
vpn-manager service status [server_name]

# View logs
vpn-manager service logs [server_name]

# Follow logs in real-time
vpn-manager service logs -f [server_name]

# Show last N lines of logs
vpn-manager service logs -t 50 [server_name]

# Generate docker-compose configuration
vpn-manager service generate
```

### Server Management

```bash
# List all servers
vpn-manager server list

# Create a new server
vpn-manager server create -n myserver -u example.com -p 51822 -s 10.15.15.0/24

# Create server with custom DNS and allowed IPs
vpn-manager server create -n myserver -u example.com -p 51822 -s 10.15.15.0/24 -d "1.1.1.1,8.8.8.8" -a "0.0.0.0/0"

# Create server with custom peers count
vpn-manager server create -n myserver -u example.com -p 51822 -s 10.15.15.0/24 -P 10

# Remove server (with confirmation)
vpn-manager server remove myserver

# Force remove server (no confirmation)
vpn-manager server remove myserver --force
```

### Client Management

```bash
# Add a new client
vpn-manager client add <server_name> <client_name>

# Examples
vpn-manager client add myserver phone
vpn-manager client add myserver laptop

# Remove a client
vpn-manager client remove <server_name> <client_name>

# Examples
vpn-manager client remove myserver phone
vpn-manager client remove myserver laptop

# List clients
vpn-manager client list myserver
```

### Key Generation

```bash
# Generate key pair (print to stdout)
vpn-manager key generate

# Save to directory
vpn-manager key generate /path/to/save/keys
```

### Help

```bash
# Show all available commands
vpn-manager --help

# Show help for a specific group
vpn-manager service --help
vpn-manager client --help
vpn-manager server --help
vpn-manager key --help
```

## Client Configuration

When you add a client, the system:

1. **Generates** a unique key pair for the client
2. **Assigns** the next available IP address in the server subnet
3. **Creates** a client configuration file in `servers/<server>/clients/<client>.conf`
4. **Updates** the server configuration with the new peer
5. **Restarts** the corresponding container
6. **Displays** a QR code for mobile device setup

### Mobile Setup

1. Install WireGuard app on your mobile device
2. Scan the QR code displayed after adding a client
3. Or manually import the `.conf` file from `servers/<server>/clients/`

### Desktop Setup

1. Install WireGuard client on your computer
2. Import the `.conf` file from `servers/<server>/clients/<client_name>.conf`
3. Connect to the VPN

## Troubleshooting

### Installation Issues

#### Command not found

```bash
# Reinstall with pipx
pipx install --editable ".[dev]" --force
```

#### Import errors

```bash
# Reinstall the package
pipx install --editable ".[dev]" --force
```

### Runtime Issues

For issues and questions:

1. Check the troubleshooting section above
2. Review container logs for error messages
3. Verify your server configurations in `servers/*/config.yml`
4. Ensure all prerequisites are installed correctly
5. Open an issue on [GitHub](https://github.com/strelga/wireguard-vpn-manager/issues)

### Check container logs

Use the `vpn-manager service logs` command to view logs. See [Service Management](#service-management) for detailed usage.

### Check WireGuard status inside container

```bash
vpn-manager service status [server_name]
```

### Verify network connectivity

```bash
# Test from client
ping 10.13.13.1  # Server IP
```

### Common Issues

1. **Port conflicts**: Ensure ports 51820 and 51821 are not used by other services
2. **Firewall**: Open UDP ports 51820 and 51821 in your firewall
3. **DNS issues**: Check that DNS servers are accessible from client networks
4. **Key permissions**: Client key files should have 600 permissions (automatically set)

### Reset Configuration

To completely reset a server configuration:

```bash
# Stop services
vpn-manager service stop

# Remove server config and clients
rm -rf servers/myserver/config/*
rm -rf servers/myserver/clients/*

# Restart services (will regenerate server configs)
vpn-manager service start
```

## Security Notes

- **Private keys** are stored with 600 permissions (owner read/write only)
- **Client configurations** contain sensitive key material - protect them accordingly
- **Server configurations** are automatically generated and managed
- **Regular backups** of client configurations are recommended

## Advanced Usage

### Custom Server Configuration

To add a new server type:

1. Create directory structure: `servers/<new_server>/`
2. Create `config.yml` with server configuration
3. Run `vpn-manager service generate` to update docker-compose
4. The management scripts will automatically detect the new server

### Batch Operations

Add multiple clients:

```bash
for client in phone laptop tablet; do
    vpn-manager client add <server_name> $client
done
```

### Monitoring

View real-time logs:

```bash
# Follow logs for all servers
vpn-manager service logs -f

# Follow logs for specific server
vpn-manager service logs -f myserver
```

Monitor specific server:

```bash
# Show last 100 lines (default)
vpn-manager service logs myserver

# Show last 50 lines
vpn-manager service logs myserver -t 50
```

## Development

### Code Quality Tools

```bash
# Run linter
make lint

# Format code
make format

# Type checking
make typecheck

# Run all checks
make check-all

# Run tests
make test

# Run tests with coverage
make test-cov
```

## Uninstalling

```bash
pipx uninstall wireguard-vpn-manager
```

## Author

Grigory Streltsov - [strelga@gmail.com](mailto:strelga@gmail.com)

## License

MIT
