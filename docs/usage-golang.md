# Go Usage Guide - VLP2SS

This guide covers the Go implementation of VLP2SS, which provides a high-performance, standalone binary with no runtime dependencies.

**Version:** 1.0.1  
**Author:** Burke Azbill  
**License:** MIT

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Command-Line Options](#command-line-options)
- [Examples](#examples)
- [Building from Source](#building-from-source)
- [Cross-Compilation](#cross-compilation)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Overview

The Go implementation (`vlp2ss`) is a high-performance, compiled binary that:

- Converts VLP ZIP files or directories to ScreenSteps format
- Uploads content directly to ScreenSteps via API
- Requires no runtime dependencies (single binary)
- Provides 2-3x faster performance than Python
- Supports cross-platform compilation
- Includes colored output and progress tracking

### When to Use Go Implementation

- **Production**: Best for high-volume processing
- **Performance**: 2-3x faster than Python
- **Deployment**: Single binary, no dependencies
- **Cross-Platform**: Easy to compile for any platform

## Prerequisites

### For Using Pre-Built Binary

- No prerequisites! The binary is self-contained.

### For Building from Source

- **Go**: Version 1.21 or higher

## Installation

### Option 1: Download Pre-Built Binary

If available, download the pre-built binary for your platform:

```bash
# Linux
curl -L -o vlp2ss https://github.com/yourusername/VLP2SS/releases/latest/download/vlp2ss-linux-amd64
chmod +x vlp2ss

# macOS (Intel)
curl -L -o vlp2ss https://github.com/yourusername/VLP2SS/releases/latest/download/vlp2ss-darwin-amd64
chmod +x vlp2ss

# macOS (Apple Silicon)
curl -L -o vlp2ss https://github.com/yourusername/VLP2SS/releases/latest/download/vlp2ss-darwin-arm64
chmod +x vlp2ss

# Windows
curl -L -o vlp2ss.exe https://github.com/yourusername/VLP2SS/releases/latest/download/vlp2ss-windows-amd64.exe
```

### Option 2: Build from Source

#### Step 1: Install Go

**macOS:**

```bash
brew install go
```

**Linux:**

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

**Windows:**

Download and install from [golang.org](https://go.dev/dl/)

#### Step 2: Build the Binary

```bash
# Navigate to golang directory
cd golang

# Download dependencies
go mod download
go mod tidy

# Build the binary
go build -o vlp2ss main.go

# Or use Makefile
make build
```

#### Step 3: Install System-Wide (Optional)

```bash
# Copy to system bin directory
sudo cp vlp2ss /usr/local/bin/

# Or use Makefile
make install

# Test
vlp2ss --help
```

## Basic Usage

### Convert a VLP ZIP File

```bash
./vlp2ss -i input.zip -o output/
```

### Convert an Extracted Directory

```bash
./vlp2ss -i /path/to/extracted/vlp/ -o output/
```

### Convert and Upload

```bash
./vlp2ss -i input.zip -o output/ \
    --upload \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345
```

## Command-Line Options

### Required Arguments

- `-i, --input PATH` - Input VLP ZIP file or directory

### Optional Arguments

- `-o, --output PATH` - Output directory (default: output)
- `-v, --verbose` - Enable verbose logging
- `--no-cleanup` - Keep temporary files after conversion

### Upload Options

- `--upload` - Upload to ScreenSteps after conversion
- `--account NAME` - ScreenSteps account name
- `--user USER` - ScreenSteps user ID
- `--token TOKEN` - ScreenSteps API token
- `--site SITE_ID` - ScreenSteps site ID

### Other Options

- `-h, --help` - Show help message
- `--examples` - Show detailed usage examples

## Examples

### Example 1: Simple Conversion

Convert a VLP ZIP file:

```bash
./vlp2ss -i HOL-2601-03-VCF-L_en.zip -o output/
```

### Example 2: Verbose Mode

Enable detailed logging:

```bash
./vlp2ss -i input.zip -o output/ -v
```

### Example 3: Convert and Upload

Convert and upload in one command:

```bash
./vlp2ss -i input.zip -o output/ \
    --upload \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345 \
    -v
```

### Example 4: Keep Temporary Files

Useful for debugging:

```bash
./vlp2ss -i input.zip -o output/ --no-cleanup
```

### Example 5: Batch Processing

Process multiple files:

```bash
#!/bin/bash
for zipfile in *.zip; do
    echo "Processing $zipfile..."
    ./vlp2ss -i "$zipfile" -o "output/$(basename "$zipfile" .zip)"
done
```

### Example 6: Show Examples

Display built-in examples:

```bash
./vlp2ss --examples
```

## Building from Source

### Basic Build

```bash
cd golang
go build -o vlp2ss main.go
```

### Build with Optimization

```bash
go build -ldflags="-s -w" -o vlp2ss main.go
```

Flags:
- `-s`: Strip symbol table
- `-w`: Strip DWARF debugging information

### Using Makefile

The project includes a Makefile for common tasks:

```bash
# Build the binary
make build

# Download dependencies
make deps

# Clean build artifacts
make clean

# Run tests
make test

# Install to $GOPATH/bin
make install

# Build for multiple platforms
make cross

# Show help
make help
```

## Cross-Compilation

Go makes it easy to compile for different platforms:

### Linux (AMD64)

```bash
GOOS=linux GOARCH=amd64 go build -o vlp2ss-linux-amd64 main.go
```

### Linux (ARM64)

```bash
GOOS=linux GOARCH=arm64 go build -o vlp2ss-linux-arm64 main.go
```

### macOS (Intel)

```bash
GOOS=darwin GOARCH=amd64 go build -o vlp2ss-darwin-amd64 main.go
```

### macOS (Apple Silicon)

```bash
GOOS=darwin GOARCH=arm64 go build -o vlp2ss-darwin-arm64 main.go
```

### Windows (AMD64)

```bash
GOOS=windows GOARCH=amd64 go build -o vlp2ss-windows-amd64.exe main.go
```

### Build for All Platforms

```bash
make cross
```

This creates binaries for:
- Linux (amd64, arm64)
- macOS (Intel, Apple Silicon)
- Windows (amd64)

## Advanced Usage

### Integration with CI/CD

#### GitLab CI Example

```yaml
build:
  stage: build
  image: golang:1.21
  script:
    - cd golang
    - go mod download
    - go build -o vlp2ss main.go
  artifacts:
    paths:
      - golang/vlp2ss

convert:
  stage: convert
  dependencies:
    - build
  script:
    - chmod +x golang/vlp2ss
    - ./golang/vlp2ss -i input.zip -o output/ --upload --account $SS_ACCOUNT --user $SS_USER --token $SS_TOKEN --site $SS_SITE
  artifacts:
    paths:
      - output/
```

#### GitHub Actions Example

```yaml
name: Build and Convert

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Go
        uses: actions/setup-go@v2
        with:
          go-version: 1.21
      
      - name: Build
        run: |
          cd golang
          go build -o vlp2ss main.go
      
      - name: Convert VLP
        run: |
          chmod +x golang/vlp2ss
          ./golang/vlp2ss -i input.zip -o output/ --upload \
            --account ${{ secrets.SS_ACCOUNT }} \
            --user ${{ secrets.SS_USER }} \
            --token ${{ secrets.SS_TOKEN }} \
            --site ${{ secrets.SS_SITE }}
```

### Docker Container

#### Dockerfile

```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY golang/ .

RUN go mod download
RUN go build -ldflags="-s -w" -o vlp2ss main.go

# Runtime stage
FROM alpine:latest

RUN apk --no-cache add ca-certificates

WORKDIR /app
COPY --from=builder /app/vlp2ss .

ENTRYPOINT ["./vlp2ss"]
CMD ["--help"]
```

#### Build and Run

```bash
# Build image
docker build -t vlp2ss .

# Run conversion
docker run -v $(pwd)/input:/input -v $(pwd)/output:/output \
    vlp2ss -i /input/file.zip -o /output/

# Run with upload
docker run -v $(pwd)/input:/input -v $(pwd)/output:/output \
    vlp2ss -i /input/file.zip -o /output/ \
    --upload \
    --account myaccount \
    --user admin \
    --token YOUR_TOKEN \
    --site 12345
```

### Systemd Service

Create a systemd service for automated conversions:

```ini
# /etc/systemd/system/vlp2ss.service
[Unit]
Description=VLP2SS Converter Service
After=network.target

[Service]
Type=oneshot
User=vlp2ss
Group=vlp2ss
WorkingDirectory=/opt/vlp2ss
ExecStart=/usr/local/bin/vlp2ss -i /data/input.zip -o /data/output/ --upload --account myaccount --user admin --token TOKEN --site 12345
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable vlp2ss.service
sudo systemctl start vlp2ss.service
sudo systemctl status vlp2ss.service
```

### Cron Job

Schedule automatic conversions:

```bash
# Edit crontab
crontab -e

# Add a job to run daily at 2 AM
0 2 * * * /usr/local/bin/vlp2ss -i /data/input.zip -o /data/output/ --upload --account myaccount --user admin --token TOKEN --site 12345 >> /var/log/vlp2ss.log 2>&1
```

## Troubleshooting

### Binary Not Found

**Problem**: "command not found: vlp2ss"

**Solution**: Ensure the binary is in your PATH:

```bash
# Add current directory to PATH temporarily
export PATH=$PATH:$(pwd)

# Or copy to a directory in PATH
sudo cp vlp2ss /usr/local/bin/
```

### Permission Denied

**Problem**: "Permission denied" when running the binary

**Solution**: Make the binary executable:

```bash
chmod +x vlp2ss
```

### Build Errors

**Problem**: "go: command not found"

**Solution**: Install Go or add it to your PATH:

```bash
export PATH=$PATH:/usr/local/go/bin
```

**Problem**: "package not found"

**Solution**: Download dependencies:

```bash
go mod download
go mod tidy
```

### Runtime Errors

**Problem**: "content.xml not found"

**Solution**: Verify the ZIP file structure:

```bash
unzip -l input.zip | grep content.xml
```

If `content.xml` is in a subdirectory, extract and convert the directory:

```bash
unzip input.zip -d extracted/
./vlp2ss -i extracted/path/to/content/ -o output/
```

**Problem**: "API authentication failed"

**Solution**: Verify your credentials:

1. Check username and API token
2. Ensure token has "Full Access" permission
3. Verify account name matches your ScreenSteps URL

Test with curl:

```bash
curl -u "admin:YOUR_TOKEN" \
  https://myaccount.screenstepslive.com/api/v2/sites
```

### Debugging with Verbose Mode

Enable verbose mode for detailed output:

```bash
./vlp2ss -i input.zip -o output/ -v
```

This shows:

- Detailed progress information
- API request/response details
- Error messages with context
- File operations

### Check Logs

Logs are created in the `logs/` directory:

```bash
# List log files
ls -la logs/

# View the latest log
tail -f logs/vlp_converter_*.log
```

## Performance Tips

### Optimize Build

Use build flags for smaller, faster binaries:

```bash
go build -ldflags="-s -w" -o vlp2ss main.go
```

### Optimize Runtime

1. **Use SSD storage** for faster I/O
2. **Ensure sufficient memory** for large files
3. **Close other applications** to free resources
4. **Use verbose mode** to monitor progress

### Benchmark

Compare performance with Python:

```bash
# Go implementation
time ./vlp2ss -i large_file.zip -o output/

# Python implementation
time python3 python/vlp_converter.py -i large_file.zip -o output/
```

Typical results: Go is 2-3x faster than Python.

## Best Practices

### Security

1. **Never hardcode credentials** in scripts
2. **Use environment variables** for sensitive data
3. **Secure binaries** with proper permissions (chmod 755)
4. **Rotate API tokens** regularly
5. **Use HTTPS only** for API calls

### Deployment

1. **Test on target platform** before deployment
2. **Use cross-compilation** for different platforms
3. **Include version information** in binaries
4. **Provide checksums** for downloads
5. **Document system requirements**

### Maintenance

1. **Keep Go updated** for security patches
2. **Rebuild periodically** with latest dependencies
3. **Test with sample data** before production use
4. **Monitor logs** for issues
5. **Back up converted content**

## Additional Resources

- [Main Documentation](README.md)
- [API Guide](API_GUIDE.md)
- [Installation Guide](INSTALLATION.md)
- [Python Usage Guide](usage-python.md)
- [Go Documentation](https://golang.org/doc/)
- [Cobra CLI Framework](https://github.com/spf13/cobra)

## Support

For issues or questions:

1. Check this documentation
2. Run with `--help` or `--examples`
3. Enable verbose mode (`-v`) for debugging
4. Review log files
5. Check the [troubleshooting guide](README.md#troubleshooting)

## License

MIT License - Copyright (c) 2025 Burke Azbill

See [LICENSE](../LICENSE) for details.

