# VLP2SS - The VLP to ScreenSteps Converter

> Convert VMware Lab Platform (VLP) exported lab manuals to ScreenSteps format with API upload capabilities.

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/) [![Go](https://img.shields.io/badge/Go-1.21+-00ADD8.svg)](https://golang.org/) [![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Version:** 1.0  
**Author:** Burke Azbill  
**License:** MIT

## 🎯 Overview

VLP2SS provides a complete toolset for converting VLP (VMware Lab Platform) exported content into ScreenSteps-compatible format. It includes two implementations (Python, Go) and comprehensive documentation.

### What It Does

- ✅ Converts VLP ZIP exports to ScreenSteps JSON/HTML format
- ✅ Preserves chapter and article hierarchy
- ✅ Organizes images by article
- ✅ Uploads content directly to ScreenSteps via API
- ✅ Provides CLI with progress tracking
- ✅ Generates comprehensive logs

## 🚀 Quick Start

### Option 1: Python (Recommended for most users)

```bash
# Install dependencies
pip3 install -r python/requirements.txt

# Convert a VLP export (using the Python launcher script)
./python/vlp2ss-py.sh \
    -i HOL-2601-03-VCF-L_en.zip \
    -o output/
```

### Option 2: Go (Best for performance)

```bash
# Build
cd golang
make build

# Convert
./vlp2ss -i input.zip -o output/
```

## 📁 Project Structure

```text
VLP2SS/
├── python/                     # Python scripts
│   ├── vlp_converter.py        # Main converter
│   ├── screensteps_uploader.py # API uploader
│   ├── vlp2ss-py.sh            # Python launcher script
│   └── requirements.txt        # Dependencies
├── golang/                     # Go implementation
│   ├── main.go                 # Go converter
│   ├── go.mod                  # Go modules
│   ├── Makefile                # Build automation
│   └── README.md               # Go-specific docs
├── docs/                       # Documentation
│   ├── README.md               # Complete user guide
│   ├── INSTALLATION.md         # Installation guide
│   ├── API_GUIDE.md            # API integration guide
│   ├── usage-bash.md           # Bash usage guide
│   ├── usage-python.md         # Python usage guide
│   └── usage-golang.md         # Go usage guide
├── LICENSE                     # MIT License
├── README.md                   # This file
└── CONTRIBUTING.md             # Contribution guidelines
```

## 📚 Documentation

Comprehensive documentation is available:

- **[Complete User Guide](docs/README.md)** - Full documentation with examples
- **[Installation Guide](docs/INSTALLATION.md)** - Step-by-step installation
- **[API Integration Guide](docs/API_GUIDE.md)** - ScreenSteps API details
- **[Python Usage Guide](docs/usage-python.md)** - Python implementation guide
- **[Go Usage Guide](docs/usage-golang.md)** - Go implementation guide
- **[Contributing Guide](CONTRIBUTING.md)** - How to contribute

## ✨ Features

### Core Capabilities

- Convert VLP ZIP files or directories
- Parse complex XML structure
- Flatten hierarchical content
- Generate ScreenSteps JSON/HTML
- Organize images by article
- Upload via ScreenSteps API

### User Experience

- Colored CLI output
- Progress tracking with step indicators
- Comprehensive logging
- Helpful error messages
- Built-in usage examples

### Advanced Features

- Batch processing support
- Rate limit handling
- Automatic retry on failures
- Environment variable support
- Dry-run capability
- Cross-platform compatibility

## 🔧 Installation

### Prerequisites

- **Python**: 3.7 or higher (for Python implementation)
- **Go**: 1.21 or higher (for Go implementation)

### Quick Install

```bash
# Install Python dependencies
pip3 install requests

# Make scripts executable
chmod +x python/vlp2ss-py.sh
chmod +x python/*.py

# Build Go binary (optional)
cd golang && make build
```

For detailed installation instructions, see [INSTALLATION.md](docs/INSTALLATION.md).

## 📖 Usage Examples

### Example 1: Simple Conversion (Python)

```bash
./python/vlp2ss-py.sh \
    -i HOL-2601-03-VCF-L_en.zip \
    -o output/
```

### Example 2: Convert with Verbose Output

```bash
./python/vlp2ss-py.sh \
    -i input.zip \
    -o output/ \
    -v
```

### Example 3: Batch Processing

```bash
for file in *.zip; do
    python3 python/vlp_converter.py \
        -i "$file" \
        -o "output/$(basename "$file" .zip)"
done
```

### Example 4: Go Implementation

```bash
cd golang
./vlp2ss -i input.zip -o output/ --upload \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345
```

## 🏗️ Output Structure

The converter produces the following structure:

```text
output/
└── <Manual-Name>/
    ├── <manual-id>.json          # Table of contents
    ├── articles/
    │   ├── <article-id>.json     # Article metadata
    │   └── <article-id>.html     # Article HTML content
    └── images/
        └── <article-id>/
            └── *.png             # Article images
```

## 🔌 ScreenSteps API Integration

### Endpoints Used

- **Create Manual**: `POST /sites/{site_id}/manuals`
- **Create Chapter**: `POST /sites/{site_id}/manuals/{manual_id}/chapters`
- **Create Article**: `POST /sites/{site_id}/chapters/{chapter_id}/articles`
- **Upload Image**: `POST /sites/{site_id}/files`
- **Update Article**: `PUT /sites/{site_id}/articles/{article_id}`

### Generating an API Token

1. Log in to your ScreenSteps account
2. Go to **Account Settings** → **API Tokens**
3. Click **Generate New Token**
4. Select **Full Access** permission
5. Copy the token

### Upload Converted Content

```bash
python3 python/screensteps_uploader.py \
    --content output/HOL-2601-03-VCF-L \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345
```

For detailed API documentation, see [API_GUIDE.md](docs/API_GUIDE.md).

## 🎨 Implementation Comparison

| Feature | Python | Go |
|---------|--------|-----|
| **Speed** | Moderate | Fast (2-3x) |
| **Dependencies** | Python 3.7+, requests | None |
| **API Upload** | ✅ Yes | ✅ Yes |
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Flexibility** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Performance** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Portability** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Best For** | Development | Production |

## 🐛 Troubleshooting

### Common Issues

**Problem**: "content.xml not found"

```bash
# Solution: Extract ZIP and run on directory
unzip input.zip -d extracted/
python3 vlp_converter.py -i extracted/ -o output/
```

**Problem**: "Module 'requests' not found"

```bash
# Solution: Install Python dependencies
pip3 install requests
```

**Problem**: "Permission denied"

```bash
# Solution: Make scripts executable
chmod +x bash/vlp2ss.sh
chmod +x python/*.py
```

**Problem**: "Rate limit exceeded"

```text
# Solution: The uploader automatically handles this
# Just wait for the retry delay to complete
```

For more troubleshooting help, see the [Complete User Guide](docs/README.md#troubleshooting).

## 📊 Test Results

Successfully tested with sample VLP exports:

- ✅ Almost all images copied and organized
- ✅ Strong text maintained
- ✅ Embedded Youtube Videos maintained
- ✅ JSON and HTML files generated correctly
- ✅ Comprehensive logs created

## 🔒 Security

### Best Practices

- ✅ Store credentials in environment variables
- ✅ Use HTTPS only for API calls

### Secure Credential Storage

```bash
# Create config file
cat > ~/.vlp2ss/config.env << EOF
export SS_ACCOUNT=myaccount
export SS_USER=admin
export SS_TOKEN=your_token_here
export SS_SITE=12345
EOF

# Secure the file
chmod 600 ~/.vlp2ss/config.env

# Load credentials
source ~/.vlp2ss/config.env
```

## 📈 Performance

### Upload Times

Upload times depend on:

- Number of articles
- Number of images
- Image sizes
- Network speed
- API rate limits (no more than 8 image uploads within 10 seconds)

Actual Example Timing:

| Articles | Images | Conversion time |Import Time |
|:---------:|:--------:|:----------:|:-----:|
| **36** | 472 | 1s | 17m 58s  |
| **21** | 107 | 0s | 4m 17s  |
| **25** | 132 | 0s | 5m 13s  |
| **34** | 133 | 0s | 6m 9s  |

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Areas for improvement:

- Content validation before upload
- Web-based UI
- Docker container

## 📞 Support

### Known Issues

- Not all ScreenSteps accounts are enabled for image/file upload

### Getting Help

1. Check the [documentation](docs/)
2. Run scripts with `--help` or `--examples`
3. Review log files in `logs/` directory
4. Check the [troubleshooting guide](docs/README.md#troubleshooting)

### External Resources

- [ScreenSteps API Documentation](https://help.screensteps.com/m/integration/c/301068)
- [ScreenSteps: Creating images or file attachments via the Public API](https://help.screensteps.com/a/1540764-creating-images-or-file-attachments-via-the-public-api)
- [VMware Lab Platform Documentation](https://techdocs.broadcom.com/us/en/vmware-cis/other/vmware-lab-platform.html)

## 📄 License

MIT License - Copyright (c) 2025 Burke Azbill

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Dependencies

This project uses the following open-source libraries:

- **Python**: `requests` library (Apache 2.0 License)
- **Go**: `github.com/fatih/color` (MIT License), `github.com/spf13/cobra` (Apache 2.0 License)

All dependencies are used in compliance with their respective licenses.

## 🙏 Acknowledgments

- VMware Lab Platform team for VLP
- ScreenSteps for their API and documentation
- Open source community for tools and libraries

## 📝 Version History

- **v1.0.1** (2025-11-11)
  - Fix double encoded xml export translation
  - Fix Youtube embedded videos
  
- **v1.0** (2025-11-07)
  - Initial release
  - Python and Go implementations
  - Full API upload support
  - Comprehensive documentation
  - Tested with real VLP data
  - MIT License
  - Rate limiting and retry logic

---

## 🚀 Getting Started with Git

This project uses Git for version control. To get started:

Create a fork of the Repository.

### Clone your fork of the Repository

```bash
git clone https://github.com/yourusername/VLP2SS.git
cd VLP2SS
```

### Keep Your Fork Updated

```bash
git remote add upstream https://github.com/burkeazbill-bc/VLP2SS.git
git fetch upstream
git merge upstream/main
```

### Create a Branch for Your Work

```bash
git checkout -b feature/your-feature-name
```

### Commit Your Changes

```bash
git add .
git commit -m "Description of your changes"
git push origin feature/your-feature-name
```

For more details, see [CONTRIBUTING.md](CONTRIBUTING.md).

---

**Status**: ✅ Production Ready

**Last Updated**: November 7, 2025

**Author**: Burke Azbill

**License**: MIT

For detailed technical information, see the [documentation](docs/).
