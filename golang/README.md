# VLP2SS - Go Implementation

A high-performance Go implementation of the VLP to ScreenSteps converter with API upload support.

**Version:** 1.0.2  
**Author:** Burke Azbill  
**License:** MIT

## Features

- Fast, concurrent processing
- Single binary with no dependencies
- ScreenSteps API upload support
- Cross-platform support (Linux, macOS, Windows)
- Beautiful colored output
- Comprehensive logging
- Progress tracking
- Rate limiting and retry logic

## Building

### Prerequisites

- Go 1.21 or higher

### Build Instructions

```bash
# Download dependencies
make deps

# Build the binary
make build

# Or simply
make
```

### Cross-Compilation

Build for multiple platforms:

```bash
make cross
```

This creates binaries for:
- Linux (amd64, arm64)
- macOS (Intel, Apple Silicon)
- Windows (amd64)

## Usage

### Basic Usage

```bash
# Convert a ZIP file
./vlp2ss -i input.zip -o output/

# Convert a directory
./vlp2ss -i extracted-dir/ -o output/

# Verbose mode
./vlp2ss -i input.zip -o output/ -v

# Keep temporary files
./vlp2ss -i input.zip -o output/ --no-cleanup

# Convert and upload to ScreenSteps
./vlp2ss -i input.zip -o output/ \
    --upload \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345
```

### Show Examples

```bash
./vlp2ss --examples
```

### Help

```bash
./vlp2ss --help
```

## Installation

Install to your `$GOPATH/bin`:

```bash
make install
```

Then you can run it from anywhere:

```bash
vlp2ss -i input.zip -o output/
```

## Development

### Run Tests

```bash
make test
```

### Clean Build Artifacts

```bash
make clean
```

## Performance

The Go implementation offers significant performance benefits:

- **Fast**: 2-3x faster than Python for large files
- **Memory Efficient**: Lower memory footprint
- **Concurrent**: Parallel processing of images and articles
- **Single Binary**: No runtime dependencies

## Output Structure

```
output/
└── HOL-2601-03-VCF-L/
    ├── <manual-id>.json          # Table of contents
    ├── articles/
    │   ├── <article-id>.json     # Article metadata
    │   └── <article-id>.html     # Article content
    └── images/
        └── <article-id>/
            └── *.png             # Article images
```

## Logging

Logs are automatically created in the `logs/` directory:

```
logs/vlp_converter_20250103_143022.log
```

## API Upload

The Go implementation includes full ScreenSteps API integration:

```bash
# Convert and upload in one command
# YOUR_SS_ACCOUNT is whatever preceeds .screenstepslive.com when accessing Screensteps
./vlp2ss -i input.zip -o output/ \
    --upload \
    --account YOUR_SS_ACCOUNT \
    --user YOUR_USERNAME \
    --token YOUR_PASSWORD \
    --site YOUR_SITE_ID \
    -v
```

### Features

- Automatic rate limit handling
- Retry logic for failed requests
- Image upload support
- Progress tracking

## Author

Burke Azbill

## License

MIT License - See main project LICENSE file.
