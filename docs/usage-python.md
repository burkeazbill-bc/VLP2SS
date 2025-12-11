# Python Usage Guide - VLP2SS

This guide covers the Python implementation of VLP2SS, which provides a full-featured converter and uploader with comprehensive logging and error handling.

**Version:** 1.0.2  
**Author:** Burke Azbill  
**License:** MIT

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Command-Line Options](#command-line-options)
- [Examples](#examples)
- [Python API](#python-api)
- [Advanced Usage](#advanced-usage)
- [Troubleshooting](#troubleshooting)

## Overview

The Python implementation consists of two main scripts:

1. **`vlp_converter.py`** - Converts VLP exports to ScreenSteps format
2. **`screensteps_uploader.py`** - Uploads converted content to ScreenSteps via API
3. **`vlp2ss-py.sh`** - Bash wrapper that combines both scripts

### When to Use Python Implementation

- **Development**: Easy to modify and extend
- **Full Features**: Most comprehensive implementation
- **Debugging**: Excellent error messages and logging
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Prerequisites

### Required Software

- **Python**: Version 3.7 or higher
- **pip**: Python package manager

### Required Python Packages

- **requests**: For HTTP API calls

## Installation

### Step 1: Install Python

#### macOS

```bash
brew install python3
```

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install python3 python3-pip
```

#### Windows

Download and install from [python.org](https://www.python.org/downloads/)

### Step 2: Install Dependencies

```bash
# Using requirements.txt
pip3 install -r python/requirements.txt

# Or install directly
pip3 install requests
```

### Step 3: Verify Installation

```bash
python3 python/vlp_converter.py --help
python3 python/screensteps_uploader.py --help
```

### Step 4: Make Scripts Executable (Unix/macOS)

```bash
chmod +x python/vlp_converter.py
chmod +x python/screensteps_uploader.py
chmod +x python/vlp2ss-py.sh
```

## Basic Usage

### Using the Wrapper Script (Recommended)

The wrapper script (`vlp2ss-py.sh`) provides a convenient interface:

```bash
./python/vlp2ss-py.sh -i input.zip -o output/
```

### Using Python Scripts Directly

#### Convert Only

```bash
python3 python/vlp_converter.py -i input.zip -o output/
```

#### Upload Only

```bash
python3 python/screensteps_uploader.py \
    --content output/HOL-2601-03-VCF-L \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345
```

## Command-Line Options

### VLP Converter (`vlp_converter.py`)

#### Required Arguments

- `-i, --input PATH` - Input VLP ZIP file or directory

#### Optional Arguments

- `-o, --output PATH` - Output directory (default: output)
- `-v, --verbose` - Enable verbose logging
- `--no-cleanup` - Keep temporary files
- `--examples` - Show detailed examples
- `-h, --help` - Show help message

### ScreenSteps Uploader (`screensteps_uploader.py`)

#### Required Arguments

- `--content PATH` - Path to converted content directory
- `--account NAME` - ScreenSteps account name
- `--user USER` - ScreenSteps user ID
- `--token TOKEN` - ScreenSteps API token
- `--site SITE_ID` - ScreenSteps site ID

#### Optional Arguments

- `--no-create` - Use existing manual (don't create new)
- `-v, --verbose` - Enable verbose logging
- `--examples` - Show detailed examples
- `-h, --help` - Show help message

### Wrapper Script (`vlp2ss-py.sh`)

Combines options from both scripts:

- `-i, --input PATH` - Input VLP ZIP file or directory
- `-o, --output PATH` - Output directory
- `-v, --verbose` - Enable verbose logging
- `--no-cleanup` - Keep temporary files
- `--upload` - Upload to ScreenSteps after conversion
- `--account NAME` - ScreenSteps account name
- `--user USER` - ScreenSteps user ID
- `--token TOKEN` - ScreenSteps API token
- `--site SITE_ID` - ScreenSteps site ID
- `--dry-run` - Show what would be done
- `-h, --help` - Show help message
- `--examples` - Show detailed examples

## Examples

### Example 1: Simple Conversion

Convert a VLP ZIP file:

```bash
python3 python/vlp_converter.py \
    -i HOL-2601-03-VCF-L_en.zip \
    -o output/
```

### Example 2: Convert with Verbose Output

Enable detailed logging:

```bash
python3 python/vlp_converter.py \
    -i input.zip \
    -o output/ \
    -v
```

### Example 3: Convert an Extracted Directory

Convert from an already extracted VLP directory:

```bash
python3 python/vlp_converter.py \
    -i /path/to/extracted/vlp/ \
    -o output/
```

### Example 4: Keep Temporary Files

Useful for debugging:

```bash
python3 python/vlp_converter.py \
    -i input.zip \
    -o output/ \
    --no-cleanup
```

### Example 5: Upload Converted Content

Upload to ScreenSteps:

```bash
python3 python/screensteps_uploader.py \
    --content output/HOL-2601-03-VCF-L \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345 \
    -v
```

### Example 6: Convert and Upload (Wrapper Script)

Use the wrapper for one-step conversion and upload:

```bash
./python/vlp2ss-py.sh \
    -i input.zip \
    -o output/ \
    --upload \
    --account myaccount \
    --user admin \
    --token YOUR_API_TOKEN \
    --site 12345
```

### Example 7: Batch Processing

Process multiple files:

```bash
#!/bin/bash
for zipfile in *.zip; do
    echo "Converting $zipfile..."
    python3 python/vlp_converter.py \
        -i "$zipfile" \
        -o "output/$(basename "$zipfile" .zip)" \
        -v
done
```

### Example 8: Using Environment Variables

```bash
export SS_ACCOUNT=myaccount
export SS_USER=admin
export SS_TOKEN=YOUR_API_TOKEN
export SS_SITE=12345

./python/vlp2ss-py.sh -i input.zip -o output/ --upload
```

## Python API

You can also use the converter as a Python module:

### Import the Module

```python
import sys
sys.path.append('python')

from vlp_converter import VLPConverter
from screensteps_uploader import ScreenStepsUploader
```

### Convert VLP Content

```python
# Create converter instance
converter = VLPConverter(
    input_path='input.zip',
    output_dir='output',
    verbose=True
)

# Run conversion
output_path = converter.convert()
print(f"Converted to: {output_path}")
```

### Upload to ScreenSteps

```python
# Create uploader instance
uploader = ScreenStepsUploader(
    content_dir='output/HOL-2601-03-VCF-L',
    account='myaccount',
    user='admin',
    token='YOUR_API_TOKEN',
    site_id='12345',
    verbose=True
)

# Upload content
manual_id = uploader.upload()
print(f"Created manual ID: {manual_id}")
```

### Complete Example

```python
#!/usr/bin/env python3

import sys
sys.path.append('python')

from vlp_converter import VLPConverter
from screensteps_uploader import ScreenStepsUploader

def main():
    # Convert
    converter = VLPConverter(
        input_path='input.zip',
        output_dir='output',
        verbose=True
    )
    output_path = converter.convert()
    
    # Upload
    uploader = ScreenStepsUploader(
        content_dir=output_path,
        account='myaccount',
        user='admin',
        token='YOUR_API_TOKEN',
        site_id='12345',
        verbose=True
    )
    manual_id = uploader.upload()
    
    print(f"Success! Manual ID: {manual_id}")

if __name__ == '__main__':
    main()
```

## Advanced Usage

### Integration with Django

```python
from django.core.management.base import BaseCommand
from vlp_converter import VLPConverter
from screensteps_uploader import ScreenStepsUploader

class Command(BaseCommand):
    help = 'Convert and upload VLP content'

    def add_arguments(self, parser):
        parser.add_argument('input_file', type=str)
        parser.add_argument('--upload', action='store_true')

    def handle(self, *args, **options):
        converter = VLPConverter(
            input_path=options['input_file'],
            output_dir='output',
            verbose=True
        )
        output_path = converter.convert()
        
        if options['upload']:
            uploader = ScreenStepsUploader(
                content_dir=output_path,
                account=settings.SS_ACCOUNT,
                user=settings.SS_USER,
                token=settings.SS_TOKEN,
                site_id=settings.SS_SITE,
                verbose=True
            )
            uploader.upload()
        
        self.stdout.write(self.style.SUCCESS('Conversion complete!'))
```

### Integration with Flask

```python
from flask import Flask, request, jsonify
from vlp_converter import VLPConverter
import os

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    input_path = os.path.join('uploads', file.filename)
    file.save(input_path)
    
    try:
        converter = VLPConverter(
            input_path=input_path,
            output_dir='output',
            verbose=False
        )
        output_path = converter.convert()
        
        return jsonify({
            'success': True,
            'output_path': output_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
    finally:
        os.remove(input_path)

if __name__ == '__main__':
    app.run(debug=True)
```

### Custom Logging

```python
import logging
from vlp_converter import VLPConverter

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('conversion.log'),
        logging.StreamHandler()
    ]
)

# Create converter with custom logger
converter = VLPConverter(
    input_path='input.zip',
    output_dir='output',
    verbose=True
)

# Convert
output_path = converter.convert()
```

### Error Handling

```python
from vlp_converter import VLPConverter
from screensteps_uploader import ScreenStepsUploader

def safe_convert_and_upload(input_file):
    try:
        # Convert
        converter = VLPConverter(
            input_path=input_file,
            output_dir='output',
            verbose=True
        )
        output_path = converter.convert()
        
        # Upload
        uploader = ScreenStepsUploader(
            content_dir=output_path,
            account='myaccount',
            user='admin',
            token='YOUR_API_TOKEN',
            site_id='12345',
            verbose=True
        )
        manual_id = uploader.upload()
        
        return {
            'success': True,
            'manual_id': manual_id,
            'output_path': output_path
        }
        
    except FileNotFoundError as e:
        return {
            'success': False,
            'error': f'File not found: {e}'
        }
    except ValueError as e:
        return {
            'success': False,
            'error': f'Invalid input: {e}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {e}'
        }

# Usage
result = safe_convert_and_upload('input.zip')
if result['success']:
    print(f"Success! Manual ID: {result['manual_id']}")
else:
    print(f"Error: {result['error']}")
```

## Troubleshooting

### Module Not Found

**Problem**: "ModuleNotFoundError: No module named 'requests'"

**Solution**: Install the requests module:

```bash
pip3 install requests
```

### Permission Denied

**Problem**: "Permission denied" when running scripts

**Solution**: Make scripts executable:

```bash
chmod +x python/vlp_converter.py
chmod +x python/screensteps_uploader.py
chmod +x python/vlp2ss-py.sh
```

### Python Version Issues

**Problem**: "SyntaxError" or features not working

**Solution**: Ensure you're using Python 3.7 or higher:

```bash
python3 --version
```

If needed, install a newer version:

```bash
# macOS
brew install python@3.11

# Ubuntu
sudo apt install python3.11
```

### content.xml Not Found

**Problem**: "content.xml not found in ZIP file"

**Solution**: Extract and inspect the ZIP structure:

```bash
unzip -l input.zip | grep content.xml
```

If `content.xml` is in a subdirectory, extract and convert the directory:

```bash
unzip input.zip -d extracted/
python3 python/vlp_converter.py -i extracted/path/to/content/ -o output/
```

### API Authentication Failed

**Problem**: "401 Unauthorized" when uploading

**Solution**: Verify your credentials:

1. Check username and API token
2. Ensure token has "Full Access" permission
3. Verify account name matches your ScreenSteps URL

Test credentials:

```python
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth('admin', 'YOUR_TOKEN')
response = requests.get(
    'https://myaccount.screenstepslive.com/api/v2/sites',
    auth=auth
)
print(response.status_code)
print(response.json())
```

### Rate Limit Exceeded

**Problem**: "429 Too Many Requests"

**Solution**: The uploader automatically handles rate limiting. Just wait for the retry to complete.

### Memory Issues with Large Files

**Problem**: "MemoryError" when processing large VLP exports

**Solution**: Increase available memory or process in chunks:

```python
import gc

# Force garbage collection
gc.collect()

# Process with memory optimization
converter = VLPConverter(
    input_path='large_file.zip',
    output_dir='output',
    verbose=True
)
output_path = converter.convert()

# Clean up
gc.collect()
```

### Debugging with Verbose Mode

Enable verbose mode for detailed output:

```bash
python3 python/vlp_converter.py -i input.zip -o output/ -v
```

This shows:

- Detailed progress information
- API request/response details
- Error messages with stack traces
- File operations

### Check Logs

Logs are created in the `logs/` directory:

```bash
# List log files
ls -la logs/

# View the latest converter log
tail -f logs/vlp_converter_*.log

# View the latest uploader log
tail -f logs/screensteps_upload_*.log
```

## Performance Tips

### Optimize for Large Files

1. Use verbose mode to monitor progress
2. Ensure sufficient disk space
3. Close other applications to free memory

### Parallel Processing

Process multiple files in parallel:

```python
from concurrent.futures import ThreadPoolExecutor
from vlp_converter import VLPConverter

def convert_file(input_file):
    converter = VLPConverter(
        input_path=input_file,
        output_dir='output',
        verbose=False
    )
    return converter.convert()

# Process files in parallel
files = ['file1.zip', 'file2.zip', 'file3.zip']
with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(convert_file, files)

for result in results:
    print(f"Converted: {result}")
```

## Best Practices

### Security

1. **Never hardcode credentials** in scripts
2. **Use environment variables** for sensitive data
3. **Secure configuration files** with proper permissions
4. **Rotate API tokens** regularly
5. **Use HTTPS only** for API calls

### Code Quality

1. **Use type hints** for better code documentation
2. **Add error handling** for all external operations
3. **Write unit tests** for critical functions
4. **Use logging** instead of print statements
5. **Follow PEP 8** style guidelines

### Maintenance

1. **Keep dependencies updated**: `pip3 install --upgrade requests`
2. **Test with sample data** before production use
3. **Back up converted content**
4. **Document custom modifications**
5. **Review logs regularly**

## Additional Resources

- [Main Documentation](README.md)
- [API Guide](API_GUIDE.md)
- [Installation Guide](INSTALLATION.md)
- [Python Requests Documentation](https://docs.python-requests.org/)

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

