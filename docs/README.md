# VLP2SS - Complete User Guide

A comprehensive toolset for converting VMware Lab Platform (VLP) exported content to ScreenSteps format, with API upload capabilities.

**Version:** 1.0.2  
**Author:** Burke Azbill  
**License:** MIT

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guides](#usage-guides)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

This project provides tools to convert lab manuals exported from VMware Lab Platform (VLP) into ScreenSteps-compatible format. It includes:

- **Python Implementation**: Full-featured converter with API upload capabilities
- **Comprehensive Logging**: Detailed logs for debugging and auditing
- **Beautiful CLI**: Colored output with progress tracking

## Features

### ✨ Core Features

- ✅ Convert VLP ZIP exports to ScreenSteps format
- ✅ Convert extracted VLP directories
- ✅ Preserve chapter and article hierarchy
- ✅ Copy and organize images
- ✅ Generate ScreenSteps-compatible JSON and HTML
- ✅ Upload directly to ScreenSteps via API
- ✅ Batch processing support
- ✅ Comprehensive logging
- ✅ Progress tracking with colored output

### ✨ Technical Features

- 🔧 Configurable output structure
- 🔧 Verbose and quiet modes
- 🔧 Dry-run capability
- 🔧 Environment variable support
- 🔧 Rate limiting for API calls
- 🔧 Automatic retry on failures
- 🔧 Cross-platform compatibility

## Installation

### 📦 Prerequisites

#### For Python Implementation

- Python 3.7 or higher
- pip (Python package manager)

### Installing Python Dependencies

```bash
pip3 install requests
```

### Making Scripts Executable

```bash
chmod +x python/*.py
```

## Quick Start

### 🚀 Convert a VLP ZIP File

```bash
# Using Python
cd python
python3 vlp_converter.py -i input.zip -o output/
```

### 🚀 Convert and Upload to ScreenSteps

```bash
# Using Python
cd python
./vlp2ss-py.sh \
    -i input.zip \
    -o output/ \
    --upload \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345
```

## Usage Guides

For detailed usage instructions, see:

- **[Python Usage Guide](usage-python.md)** - Python implementation with API

### Quick Reference

### 📖 Python Converter

#### Basic Conversion

```bash
python3 vlp_converter.py -i <input> -o <output>
```

#### Options

- `-i, --input PATH`: Input VLP ZIP file or directory (required)
- `-o, --output PATH`: Output directory (default: output)
- `-v, --verbose`: Enable verbose logging
- `--no-cleanup`: Keep temporary files
- `--examples`: Show detailed examples
- `-h, --help`: Show help message

#### Examples

```bash
# Convert with verbose output
python3 vlp_converter.py -i input.zip -o output/ -v

# Keep temporary files for debugging
python3 vlp_converter.py -i input.zip -o output/ --no-cleanup

# Convert an extracted directory
python3 vlp_converter.py -i VLP-Export-Samples/HOL-2601-03-VCF-L-en/ -o output/
```

### ScreenSteps Uploader

#### Upload Converted Content

```bash
python3 screensteps_uploader.py \
    --content output/HOL-2601-03-VCF-L \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345
```

#### Python Options

- `--content PATH`: Path to converted content directory (required)
- `--account NAME`: ScreenSteps account name (required)
- `--user USER`: ScreenSteps user ID (required)
- `--token TOKEN`: ScreenSteps API token (required)
- `--site SITE_ID`: ScreenSteps site ID (required)
- `--no-create`: Use existing manual (don't create new)
- `-v, --verbose`: Enable verbose logging
- `--version`: Show version number
- `--examples`: Show detailed examples

### 📖 Python Wrapper

#### Basic Usage

```bash
./vlp2ss-py.sh -i <input> -o <output> [OPTIONS]
```


#### Environment Variables

Instead of passing credentials as arguments, you can use environment variables:

```bash
export SS_ACCOUNT=myaccount
export SS_USER=admin
export SS_TOKEN=YOUR_API_TOKEN
export SS_SITE=12345

./vlp2ss-py.sh -i input.zip -o output/ --upload
```

## Architecture

### 🏗️ VLP Content Structure

VLP exports contain:

```text
VLP-Export/
├── content.xml          # Main content structure
└── images/
    └── *.png           # Screenshots and images
```

The `content.xml` file contains:

- Manual metadata (name, language, format)
- Hierarchical content nodes (chapters and articles)
- Localized content (title, body, images)

### ScreenSteps Output Structure

The converter produces:

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

### Conversion Process

1. **Extract**: Unzip VLP export (if ZIP file)
2. **Parse**: Parse `content.xml` using XML parser
3. **Flatten**: Convert hierarchical structure to chapters/articles
4. **Transform**: Generate ScreenSteps-compatible JSON and HTML
5. **Copy**: Organize images by article
6. **Write**: Save all files to output directory
7. **Upload** (optional): Upload to ScreenSteps via API

### Component Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                     User Interface                          │
│  (Python CLI)                                               │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  VLP Parser                                 │
│  - XML parsing                                              │
│  - Content node traversal                                   │
│  - Image extraction                                         │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│               Structure Flattener                           │
│  - Hierarchy to chapters/articles                           │
│  - Content cleaning                                         │
│  - Metadata extraction                                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│            ScreenSteps Converter                            │
│  - JSON generation                                          │
│  - HTML formatting                                          │
│  - Image organization                                       │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                File Writer                                  │
│  - Directory creation                                       │
│  - File output                                              │
│  - Image copying                                            │
└─────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────┐
│            ScreenSteps API Uploader                         │
│  - Authentication                                           │
│  - Manual/chapter/article creation                          │
│  - Image upload                                             │
│  - Rate limiting                                            │
└─────────────────────────────────────────────────────────────┘
```

## API Reference

### 🔌 ScreenSteps API Integration

The uploader uses ScreenSteps API v2. Key endpoints:

#### Authentication

```text
Base URL: https://{account}.screenstepslive.com/api/v2
Auth: HTTP Basic (username:token)
```

#### Endpoints Used

- `GET /sites` - List all sites
- `GET /sites/{site_id}` - Get site details
- `POST /sites/{site_id}/manuals` - Create manual
- `POST /sites/{site_id}/manuals/{manual_id}/chapters` - Create chapter
- `POST /sites/{site_id}/chapters/{chapter_id}/articles` - Create article
- `POST /sites/{site_id}/files` - Upload image
- `PUT /sites/{site_id}/articles/{article_id}` - Update article

#### Rate Limiting

The API implements automatic rate limiting:

- Detects 429 (Too Many Requests) responses
- Automatically retries after specified delay
- Default retry delay: 60 seconds

### Generating API Token

1. Log in to your ScreenSteps account
2. Navigate to **Account Settings** → **API Tokens**
3. Click **Generate New Token**
4. Select **Full Access** permission
5. Copy the token and use with `--token` parameter

## Tool Examples

### 📚 Example 1: Simple Conversion

```bash
python3 vlp_converter.py \
    -i HOL-2601-03-VCF-L_en.zip \
    -o output/
```

**Current Issue**: Need to convert VLP export to ScreenSteps format

**Recommendation**: Use the Python converter for full-featured conversion

**Benefit**:

- Automatic structure conversion
- Image organization
- Comprehensive logging

**Example Usage**:

```bash
# Python script
python3 vlp_converter.py -i input.zip -o output/

# Bash wrapper
./vlp2ss-py.sh -i input.zip -o output/
```

### 📚 Example 2: Batch Conversion

```bash
#!/bin/bash
# batch_convert.sh

for zipfile in *.zip; do
    echo "Converting $zipfile..."
    python3 vlp_converter.py \
        -i "$zipfile" \
        -o "output/$(basename "$zipfile" .zip)"
done
```

**Current Issue**: Need to convert multiple VLP exports

**Recommendation**: Use a bash loop for batch processing

**Benefit**:

- Process multiple files automatically
- Consistent output structure
- Time savings

**Example Usage**:

```bash
# Bash script
./batch_convert.sh

# Or inline
for file in *.zip; do
    ./vlp2ss-py.sh -i "$file" -o "output/$(basename "$file" .zip)"
done
```

### 📚 Example 3: Ansible Playbook

```yaml
---
- name: Convert and upload VLP content
  hosts: localhost
  gather_facts: no
  vars:
    vlp_files:
      - HOL-2601-03-VCF-L_en.zip
      - HOL-2501-08-VCF-L_en.zip
    output_dir: /opt/screensteps/output
    ss_account: myaccount
    ss_user: admin
    ss_token: "{{ lookup('env', 'SS_TOKEN') }}"
    ss_site: 12345

  tasks:
    - name: Ensure output directory exists
      file:
        path: "{{ output_dir }}"
        state: directory
        mode: '0755'

    - name: Convert VLP files
      command: >
        python3 vlp_converter.py
        -i "{{ item }}"
        -o "{{ output_dir }}/{{ item | basename | regex_replace('.zip$', '') }}"
        -v
      args:
        chdir: /opt/VLP2SS/python
      loop: "{{ vlp_files }}"
      register: conversion_results

    - name: Upload to ScreenSteps
      command: >
        python3 screensteps_uploader.py
        --content "{{ output_dir }}/{{ item.item | basename | regex_replace('.zip$', '') }}"
        --account "{{ ss_account }}"
        --user "{{ ss_user }}"
        --token "{{ ss_token }}"
        --site "{{ ss_site }}"
        -v
      args:
        chdir: /opt/VLP2SS/python
      loop: "{{ conversion_results.results }}"
      when: item.rc == 0

    - name: Display results
      debug:
        msg: "Processed {{ item.item }}: {{ 'Success' if item.rc == 0 else 'Failed' }}"
      loop: "{{ conversion_results.results }}"
```

**Current Issue**: Need automated deployment and conversion

**Recommendation**: Use Ansible for infrastructure automation

**Benefit**:

- Automated deployment
- Idempotent operations
- Error handling
- Scalable to multiple servers

**Example Usage**:

```bash
# Run the playbook
ansible-playbook convert_vlp.yml

# With extra variables
ansible-playbook convert_vlp.yml -e "ss_site=54321"

# Dry run
ansible-playbook convert_vlp.yml --check
```

### 📚 Example 4: Docker Container

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

```bash
# Build image
docker build -t vlp-converter .

# Run conversion
docker run -v $(pwd)/input:/data/input \
           -v $(pwd)/output:/data/output \
           vlp-converter \
           -i /data/input/HOL-2601-03-VCF-L_en.zip \
           -o /data/output
```

**Current Issue**: Need containerized deployment

**Recommendation**: Use Docker for consistent environments

**Benefit**:

- Isolated environment
- Reproducible builds
- Easy deployment
- No dependency conflicts

**Example Usage**:

```bash
# Build the container
docker build -t vlp-converter .

# Run conversion
docker run -v $(pwd):/data vlp-converter -i /data/input.zip -o /data/output

# Interactive mode
docker run -it -v $(pwd):/data vlp-converter bash
```

## Troubleshooting

### 🐛 Common Issues

#### Issue: "Image not found, skipping: ..."

**cause**: the extracted zip file directory structure appears to be missing an image that was referenced in the xml. This results in the image not being found and skipped.

**workaround**:

1. Review the summary at the end of the output, here's an example:
   <img src="images/summary-skipped-images.png" alt="Skipped Images Summary" width="600">
2. Log in to ScreenSteps, locate the referenced Chapter, Article, Step and replace the placeholder Alert message with the missing screenshot.
   <img src="images/error-importing-image.png" alt="Image Placeholder" width="600">

#### Issue: "content.xml not found"

**Cause**: VLP export structure is different than expected

**Solution**:

1. Extract the ZIP manually
2. Locate `content.xml`
3. Run converter on the directory containing `content.xml`

```bash
unzip input.zip -d extracted/
python3 vlp_converter.py -i extracted/ -o output/
```

#### Issue: "Failed to upload image"

**Cause**: Image file not found or API error

**Solution**:

1. Check that images exist in source directory
2. Verify API token has "Full Access" permission
3. Check network connectivity
4. Review logs for detailed error

#### Issue: "Rate limit exceeded"

**Cause**: Too many API requests

**Solution**: The uploader automatically handles rate limiting. Wait for the retry delay to complete.

#### Issue: "Python module 'requests' not found"

**Cause**: Missing Python dependency

**Solution**:

```bash
pip3 install requests
```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Python
python3 vlp_converter.py -i input.zip -o output/ -v
```

### Log Files

Logs are automatically created in the `logs/` directory:

```text
logs/
├── vlp_converter_20250103_143022.log
└── screensteps_upload_20250103_143530.log
```

## Contributing

🤝 Contributions are welcome! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed guidelines on:

- Code of conduct
- Development setup
- Coding standards
- Testing requirements
- Submitting changes
- Reporting issues

## Additional Documentation

- **[Installation Guide](INSTALLATION.md)** - Detailed installation instructions
- **[API Guide](API_GUIDE.md)** - ScreenSteps API integration details
- **[Python Usage](usage-python.md)** - Python implementation guide
- **[Contributing](../CONTRIBUTING.md)** - Contribution guidelines

## License

📄 MIT License - Copyright (c) 2025 Burke Azbill

See [LICENSE](../LICENSE) file for details.

## Support

📞 For issues, questions, or contributions:

- Create an issue in the repository
- Contact the development team
- Review the troubleshooting guide

## Acknowledgments

🙏

- VMware Lab Platform team for VLP
- ScreenSteps for their API documentation
- Open source community for tools and libraries
