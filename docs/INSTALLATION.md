# Installation Guide - VLP2SS

This guide provides detailed installation instructions for VLP2SS - The VLP to ScreenSteps Converter.

**Version:** 1.0.2  
**Author:** Burke Azbill  
**License:** MIT

## Table of Contents

- [System Requirements](#system-requirements)
- [Python Installation](#python-installation)
- [Go Installation](#go-installation)
- [Docker Installation](#docker-installation)
- [Verification](#verification)

## System Requirements

### Minimum Requirements

- **OS**: Linux, macOS, or Windows (with WSL)
- **RAM**: 2GB minimum, 4GB recommended
- **Disk Space**: 500MB for tools, additional space for conversions
- **Network**: Required for API uploads

### Software Requirements

#### For Python Implementation

- Python 3.7 or higher
- pip (Python package manager)

#### For Go Implementation

- Go 1.21 or higher

## Python Installation

### Step 1: Install Python

#### On macOS

```bash
# Using Homebrew
brew install python3

# Verify installation
python3 --version
```

#### On Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python 3
sudo apt install python3 python3-pip

# Verify installation
python3 --version
pip3 --version
```

#### On Linux (RHEL/CentOS)

```bash
# Install Python 3
sudo yum install python3 python3-pip

# Verify installation
python3 --version
pip3 --version
```

#### On Windows (WSL)

```bash
# Update package list
sudo apt update

# Install Python 3
sudo apt install python3 python3-pip

# Verify installation
python3 --version
```

### Step 2: Install Python Dependencies

```bash
# Install requests library
pip3 install requests

# Verify installation
python3 -c "import requests; print('requests version:', requests.__version__)"
```

### Step 3: Install Converter Scripts

```bash
# Clone or download the repository
cd /path/to/VLP2SS

# Make scripts executable
chmod +x python/*.py

# Test installation
python3 python/vlp_converter.py --help
```

## Go Installation

### Step 1: Install Go

#### Go On macOS

```bash
# Using Homebrew
brew install go

# Verify installation
go version
```

#### On Linux

```bash
# Download Go (check for latest version at golang.org)
wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz

# Extract to /usr/local
sudo rm -rf /usr/local/go
sudo tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH=$PATH:/usr/local/go/bin

# Verify installation
go version
```

#### On Windows

Download and install from: <https://go.dev/dl/>

### Step 2: Build Go Converter

```bash
# Navigate to Go directory
cd /path/to/VLP2SS/golang

# Download dependencies
go mod download
go mod tidy

# Build the binary
go build -o vlp2ss main.go

# Or use Makefile
make build

# Test installation
./vlp2ss --help
```

### Step 3: Install System-Wide (Optional)

```bash
# Copy to system bin directory
sudo cp vlp2ss /usr/local/bin/

# Or use Makefile
make install

# Test
vlp2ss --help
```

## Docker Installation

### Step 1: Install Docker

Follow instructions at: <https://docs.docker.com/get-docker/>

### Step 2: Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install requests

# Copy converter scripts
COPY python/*.py /app/

# Create directories
RUN mkdir -p /data/input /data/output /app/logs

# Set entrypoint
ENTRYPOINT ["python3", "/app/vlp_converter.py"]
CMD ["-h"]
```

### Step 3: Build Docker Image

```bash
# Build image
docker build -t vlp-converter .

# Test installation
docker run vlp-converter --help
```

### Step 4: Create Docker Compose (Optional)

```yaml
# docker-compose.yml
version: '3.8'

services:
  vlp-converter:
    build: .
    volumes:
      - ./input:/data/input
      - ./output:/data/output
      - ./logs:/app/logs
    environment:
      - SS_ACCOUNT=${SS_ACCOUNT}
      - SS_USER=${SS_USER}
      - SS_TOKEN=${SS_TOKEN}
      - SS_SITE=${SS_SITE}
```

## Verification

### Verify Python Installation

```bash
# Check Python version
python3 --version

# Check pip
pip3 --version

# Check requests module
python3 -c "import requests; print('OK')"

# Test converter
python3 python/vlp_converter.py --examples
```

### Verify Go Installation

```bash
# Check Go version
go version

# Check binary
./golang/vlp2ss --version

# Test converter
./golang/vlp2ss --examples
```

### Verify Docker Installation

```bash
# Check Docker version
docker --version

# Test container
docker run vlp-converter --help
```

## Post-Installation Setup

### 1. Create Configuration File (Optional)

```bash
# Create config directory
mkdir -p ~/.vlp-converter

# Create config file
cat > ~/.vlp-converter/config.env << EOF
# ScreenSteps Configuration
export SS_ACCOUNT=myaccount
export SS_USER=admin
export SS_TOKEN=your_api_token_here
export SS_SITE=12345

# Converter Settings
export VLP_OUTPUT_DIR=~/vlp-output
export VLP_VERBOSE=false
EOF

# Load configuration
source ~/.vlp-converter/config.env
```

### 2. Set Up Aliases (Optional)

```bash
# Add to ~/.bashrc or ~/.zshrc
alias vlp-convert='python3 /path/to/vlp_converter.py'
alias vlp-upload='python3 /path/to/screensteps_uploader.py'
alias vlp='bash /path/to/vlp2ss-py.sh'
```

### 3. Create Output Directories

```bash
# Create standard output directories
mkdir -p ~/vlp-output
mkdir -p ~/vlp-output/converted
mkdir -p ~/vlp-output/logs
```

## Troubleshooting Installation

### Python: Module Not Found

```bash
# Ensure pip is up to date
pip3 install --upgrade pip

# Install requests with user flag
pip3 install --user requests

# Check installation location
pip3 show requests
```

### Go: Command Not Found

```bash
# Add Go to PATH
export PATH=$PATH:/usr/local/go/bin

# Add to shell configuration
echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
source ~/.bashrc
```

### Docker: Permission Denied

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and log back in, or run:
newgrp docker
```

## Uninstallation

### Remove Python Installation

```bash
# Remove Python dependencies
pip3 uninstall requests

# Remove scripts
rm -rf /path/to/VLP2SS/python
```

### Remove Go Installation

```bash
# Remove binary
rm /usr/local/bin/vlp2ss

# Remove source
rm -rf /path/to/VLP2SS/golang
```

### Remove Docker Installation

```bash
# Remove Docker image
docker rmi vlp2ss

# Remove Docker container
docker rm -f vlp2ss
```

## Next Steps

After installation:

1. Review the [Complete User Guide](README.md) for usage instructions
2. Check the usage guides:
   - [Python Usage Guide](usage-python.md)
   - [Go Usage Guide](usage-golang.md)
3. Read [API_GUIDE.md](API_GUIDE.md) for API integration
4. See the [troubleshooting section](README.md#troubleshooting) for common issues

## Support

If you encounter installation issues:

1. Check the [Troubleshooting](#troubleshooting-installation) section
2. Review system requirements
3. Check logs in the `logs/` directory
4. Create an issue in the repository
