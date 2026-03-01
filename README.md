# WireGuard VPN Management System

A comprehensive WireGuard VPN management system with Docker Compose support for multiple server configurations.

## Features

- **Multi-server support**: Internet gateway and tunnel server configurations
- **Client management**: Easy addition and removal of VPN clients
- **Service management**: Start, stop, restart, and monitor services
- **QR code generation**: Mobile-friendly client configuration
- **Automated IP allocation**: Automatic assignment of client IP addresses
- **Secure key management**: Automated WireGuard key pair generation

## Project Structure

```
vpn/
├── docker-compose.yml          # Main compose file with includes
├── .env                        # Environment configuration
├── servers/
│   ├── server-1/
│   │   ├── docker-compose.yml
│   │   ├── config/            # Server configuration files
│   │   └── clients/           # Client configuration files
│   └── server-2/
│       ├── docker-compose.yml
│       ├── config/            # Server configuration files
│       └── clients/           # Client configuration files
└── vpn-manager/               # Unified management tool
    ├── __main__.py            # Main CLI interface
    ├── utils.py               # Common utilities library
    ├── services.py            # Service management
    ├── clients.py             # Client management
    ├── servers.py             # Server management
    ├── keys.py                # Key generation
    ├── pyproject.toml         # Project configuration
    ├── setup.sh               # Development setup script
    └── venv/                  # Virtual environment
```

## Prerequisites

- **Docker** and **Docker Compose**
- **Python 3.13+**
- **qrencode** (optional, for QR code generation)
- **WireGuard tools** (optional, for local key generation)

### Quick Setup with pipx (Recommended)

1. **Setup the management environment:**

```bash
./setup.sh
```

This will automatically:

- Install pipx if not already installed
- Install the WireGuard VPN Manager globally with development dependencies
- Make the `vpn-manager` command available system-wide
- Install development tools (ruff, mypy) globally

1. **Install system dependencies (optional):**

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

1. **Edit `.env` file** with your server details:

```bash
# Internet gateway configuration
INTERNET_SERVER_URL=your-server-ip-or-domain.com
INTERNET_PEERS=5

# Tunnel server configuration  
TUNNEL_SERVER_URL=your-tunnel-server-ip.com
TUNNEL_PEERS=3
```

1. **Server configurations** are automatically loaded from:
   - `servers/internet/docker-compose.yml` - Internet gateway (10.13.13.0/24, port 51820)
   - `servers/tunnel/docker-compose.yml` - Tunnel server (10.14.14.0/24, port 51821)

## Usage

All management is done through the unified CLI tool. After running the setup script, the `vpn-manager` command is available globally:

```bash
vpn-manager --help
```

### Service Management

```bash
# Start all services
vpn-manager start

# Start specific server
vpn-manager start internet

# Stop services
vpn-manager stop [server_name]

# Restart services
vpn-manager restart [server_name]

# Check status
vpn-manager status [server_name]
```

### Server Management

```bash
# List all servers
vpn-manager list-servers

# Create a new server
vpn-manager create-server myserver example.com 51822 10.15.15.0/24

# Create server with custom DNS and allowed IPs
vpn-manager create-server myserver example.com 51822 10.15.15.0/24 "1.1.1.1,8.8.8.8" "0.0.0.0/0"

# Remove server (with confirmation)
vpn-manager remove-server myserver

# Force remove server (no confirmation)
vpn-manager remove-server myserver --force
```

### Client Management

```bash
# Add a new client
vpn-manager add-client <server_name> <client_name>

# Examples
vpn-manager add-client internet phone
vpn-manager add-client tunnel laptop

# Remove a client
vpn-manager remove-client <server_name> <client_name>

# Examples
vpn-manager remove-client internet phone
vpn-manager remove-client tunnel laptop

# List clients
vpn-manager list-clients [server_name]
```

### Key Generation

```bash
# Generate key pair (print to stdout)
vpn-manager generate-keys

# Save to directory
vpn-manager generate-keys /path/to/save/keys
```

### Help

```bash
# Show all available commands
vpn-manager --help
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

### Check container logs

```bash
docker-compose logs -f [container_name]
```

### Check WireGuard status inside container

```bash
docker-compose exec wireguard-internet wg show
docker-compose exec wireguard-tunnel wg show
```

### Verify network connectivity

```bash
# Test from client
ping 10.13.13.1  # Internet gateway
ping 10.14.14.1  # Tunnel server
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
vpn-manager stop

# Remove server config and clients
rm -rf servers/internet/config/*
rm -rf servers/internet/clients/*
rm -rf servers/tunnel/config/*
rm -rf servers/tunnel/clients/*

# Restart services (will regenerate server configs)
vpn-manager start
```

## Development

The project includes modern Python development tools for code quality and maintainability.

### Code Quality Tools

```bash
# Development tools are available globally after setup
cd manager

# Run linter
ruff check .

# Format code
ruff format .

# Type checking
mypy .

# Run all checks
ruff check . && mypy .
```

### Project Configuration

- **pyproject.toml**: Modern Python project configuration with dependencies and tool settings
- **ruff**: Fast Python linter and formatter (installed globally via pipx)
- **mypy**: Static type checker (installed globally via pipx)
- **pipx**: Package manager for isolated Python applications

### Adding New Features

1. Make changes to the code
2. Run code quality checks: `ruff check . && mypy .`
3. Test the functionality
4. Update documentation if needed

## Security Notes

- **Private keys** are stored with 600 permissions (owner read/write only)
- **Client configurations** contain sensitive key material - protect them accordingly
- **Server configurations** are automatically generated and managed
- **Regular backups** of client configurations are recommended

## Advanced Usage

### Custom Server Configuration

To add a new server type:

1. Create directory structure: `servers/<new_server>/`
2. Add `docker-compose.yml` with WireGuard service configuration
3. Update main `docker-compose.yml` to include the new server
4. The management scripts will automatically detect the new server

### Batch Operations

Add multiple clients:

```bash
for client in phone laptop tablet; do
    vpn-manager add-client internet $client
done
```

### Monitoring

View real-time logs:

```bash
docker-compose logs -f
```

Monitor specific container:

```bash
docker-compose logs -f wireguard-internet
```

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review container logs for error messages
3. Verify your `.env` configuration
4. Ensure all prerequisites are installed correctly

## License

This project is provided as-is for educational and personal use.
