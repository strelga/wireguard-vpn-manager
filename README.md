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

```txt
vpn/
├── docker-compose.yml          # Main compose file with includes
├── .env                        # Environment configuration
├── servers/
│   ├── server-1/
│   │   ├── config.yml         # Server configuration file
│   │   └── clients/           # Client configuration files
│   └── ...
└── vpn-manager/               # Unified management tool
    ├── manager.py            # Main CLI interface
    ├── utils.py               # Common utilities library
    ├── services.py            # Service management
    ├── clients.py             # Client management
    ├── servers.py             # Server management
    ├── keys.py                # Key generation
    └── pyproject.toml         # Project configuration
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
vpn-manager client add internet phone
vpn-manager client add tunnel laptop

# Remove a client
vpn-manager client remove <server_name> <client_name>

# Examples
vpn-manager client remove internet phone
vpn-manager client remove tunnel laptop

# List clients
vpn-manager client list [server_name]
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
vpn-manager service stop

# Remove server config and clients
rm -rf servers/internet/config/*
rm -rf servers/internet/clients/*
rm -rf servers/tunnel/config/*
rm -rf servers/tunnel/clients/*

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
3. Verify your server configurations in `servers/*/config.yml`
4. Ensure all prerequisites are installed correctly

## License

This project is provided as-is for educational and personal use.
