# Contributing to VLP2SS

Thank you for your interest in contributing to VLP2SS - The VLP to ScreenSteps Converter! This document provides guidelines and instructions for contributing to the project.

**Version:** 1.0.1
**Author:** Burke Azbill  
**License:** MIT

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How to Contribute](#how-to-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Issues](#reporting-issues)
- [Feature Requests](#feature-requests)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

**Positive behavior includes:**

- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behavior includes:**

- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without permission
- Other conduct which could reasonably be considered inappropriate

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Git**: For version control
- **Python 3.7+**: For Python implementation
- **Go 1.21+**: For Go implementation
- **Bash 4.0+**: For Bash scripts
- **Text Editor**: VS Code, Vim, or your preferred editor

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/yourusername/VLP2SS.git
cd VLP2SS
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/burkeazbill-bc/VLP2SS.git
```

4. Create a branch for your work:

```bash
git checkout -b feature/your-feature-name
```

## How to Contribute

### Types of Contributions

We welcome various types of contributions:

1. **Bug Fixes**: Fix issues in existing code
2. **New Features**: Add new functionality
3. **Documentation**: Improve or add documentation
4. **Tests**: Add or improve test coverage
5. **Performance**: Optimize existing code
6. **Refactoring**: Improve code structure

### Areas for Improvement

Current areas where contributions are especially welcome:

- Resume capability for interrupted uploads
- Parallel processing for faster uploads
- Content validation before upload
- Image optimization
- Web-based UI
- Docker container improvements
- Additional test coverage
- Documentation improvements

## Development Setup

### Python Development

1. Install dependencies:

```bash
pip3 install -r python/requirements.txt
```

2. Install development dependencies:

```bash
pip3 install pytest pytest-cov black flake8 mypy
```

3. Set up pre-commit hooks (optional):

```bash
pip3 install pre-commit
pre-commit install
```

### Go Development

1. Install dependencies:

```bash
cd golang
go mod download
go mod tidy
```

2. Install development tools:

```bash
go install golang.org/x/tools/cmd/goimports@latest
go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
```

### Bash Development

1. Install shellcheck for linting:

```bash
# macOS
brew install shellcheck

# Ubuntu/Debian
sudo apt-get install shellcheck

# RHEL/CentOS
sudo yum install shellcheck
```

## Coding Standards

### Python

Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guidelines:

```bash
# Format code with black
black python/

# Check style with flake8
flake8 python/

# Type checking with mypy
mypy python/
```

**Key guidelines:**

- Use 4 spaces for indentation
- Maximum line length: 88 characters (black default)
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Use meaningful variable names

**Example:**

```python
def convert_vlp_to_screensteps(
    input_path: str,
    output_dir: str,
    verbose: bool = False
) -> str:
    """
    Convert VLP content to ScreenSteps format.
    
    Args:
        input_path: Path to VLP ZIP file or directory
        output_dir: Output directory for converted content
        verbose: Enable verbose logging
        
    Returns:
        Path to converted content directory
        
    Raises:
        FileNotFoundError: If input_path does not exist
        ValueError: If input_path is invalid
    """
    # Implementation here
    pass
```

### Go

Follow [Effective Go](https://golang.org/doc/effective_go) guidelines:

```bash
# Format code
go fmt ./...

# Run linter
golangci-lint run

# Organize imports
goimports -w .
```

**Key guidelines:**

- Use tabs for indentation
- Use `gofmt` to format code
- Write godoc comments for exported functions
- Use meaningful variable names
- Handle errors explicitly

**Example:**

```go
// ConvertVLPToScreenSteps converts VLP content to ScreenSteps format.
//
// Parameters:
//   - inputPath: Path to VLP ZIP file or directory
//   - outputDir: Output directory for converted content
//   - verbose: Enable verbose logging
//
// Returns the path to the converted content directory and any error encountered.
func ConvertVLPToScreenSteps(inputPath, outputDir string, verbose bool) (string, error) {
    if inputPath == "" {
        return "", fmt.Errorf("input path cannot be empty")
    }
    
    // Implementation here
    return "", nil
}
```

### Bash

Follow [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html):

```bash
# Check with shellcheck - NOTE: There is a VS Code Extension for this!
shellcheck python/vlp2ss-py.sh
```

**Key guidelines:**

- Use 4 spaces for indentation
- Quote all variables: `"$variable"`
- Use `[[ ]]` instead of `[ ]` for tests
- Add comments for complex logic
- Use `set -euo pipefail` at the beginning

**Example:**

```bash
#!/bin/bash

set -euo pipefail

# Convert VLP content to ScreenSteps format
#
# Arguments:
#   $1 - Input path (VLP ZIP file or directory)
#   $2 - Output directory
#   $3 - Verbose flag (optional)
#
# Returns:
#   0 on success, 1 on error
convert_vlp_to_screensteps() {
    local input_path="$1"
    local output_dir="$2"
    local verbose="${3:-false}"
    
    if [[ -z "$input_path" ]]; then
        echo "Error: Input path cannot be empty" >&2
        return 1
    fi
    
    # Implementation here
    return 0
}
```

### Documentation

- Use Markdown for all documentation
- Follow [markdownlint](https://github.com/DavidAnson/markdownlint) rules
- Include code examples where appropriate
- Keep line length under 100 characters
- Use proper heading hierarchy

## Testing

### Python Tests

Write tests using pytest:

```python
# tests/test_converter.py
import pytest
from vlp_converter import VLPConverter

def test_converter_initialization():
    """Test VLPConverter initialization."""
    converter = VLPConverter(
        input_path="test.zip",
        output_dir="output"
    )
    assert converter.input_path == "test.zip"
    assert converter.output_dir == "output"

def test_converter_invalid_input():
    """Test VLPConverter with invalid input."""
    with pytest.raises(FileNotFoundError):
        converter = VLPConverter(
            input_path="nonexistent.zip",
            output_dir="output"
        )
        converter.convert()
```

Run tests:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=python tests/

# Run specific test file
pytest tests/test_converter.py
```

### Go Tests

Write tests using Go's testing package:

```go
// converter_test.go
package main

import (
    "testing"
)

func TestConvertVLPToScreenSteps(t *testing.T) {
    tests := []struct {
        name      string
        inputPath string
        outputDir string
        wantErr   bool
    }{
        {
            name:      "valid input",
            inputPath: "test.zip",
            outputDir: "output",
            wantErr:   false,
        },
        {
            name:      "empty input",
            inputPath: "",
            outputDir: "output",
            wantErr:   true,
        },
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            _, err := ConvertVLPToScreenSteps(tt.inputPath, tt.outputDir, false)
            if (err != nil) != tt.wantErr {
                t.Errorf("ConvertVLPToScreenSteps() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

Run tests:

```bash
# Run all tests
go test ./...

# Run with coverage
go test -cover ./...

# Run specific test
go test -run TestConvertVLPToScreenSteps
```

### Bash Tests

Write tests using [bats](https://github.com/bats-core/bats-core):

```bash
# tests/test_vlp2ss.bats
#!/usr/bin/env bats

@test "vlp2ss.sh exists and is executable" {
    [ -x "bash/vlp2ss.sh" ]
}

@test "vlp2ss.sh shows help" {
    run bash/vlp2ss.sh --help
    [ "$status" -eq 0 ]
    [[ "$output" =~ "USAGE" ]]
}

@test "vlp2ss.sh requires input" {
    run bash/vlp2ss.sh -o output/
    [ "$status" -ne 0 ]
}
```

Run tests:

```bash
bats tests/test_vlp2ss.bats
```

## Submitting Changes

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```text
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```text
feat(converter): add support for nested chapters

Add support for converting VLP content with nested chapter structures.
This allows for more complex hierarchies to be preserved during conversion.

Closes #123
```

```text
fix(uploader): handle rate limiting correctly

Fix issue where rate limit errors were not being properly handled,
causing uploads to fail instead of retrying.

Fixes #456
```

```text
docs(readme): update installation instructions

Add detailed instructions for installing on Windows and update
the prerequisites section.
```

### Pull Request Process

1. **Update your branch** with the latest upstream changes:

```bash
git fetch upstream
git rebase upstream/main
```

2. **Run tests** and ensure they pass:

```bash
# Python
pytest

# Go
go test ./...

# Bash
shellcheck bash/vlp2ss.sh
```

3. **Update documentation** if needed:
   - Update README.md if adding features
   - Add/update usage examples
   - Update API documentation

4. **Push your changes**:

```bash
git push origin feature/your-feature-name
```

5. **Create a Pull Request** on GitHub:
   - Use a clear, descriptive title
   - Describe what changes you made and why
   - Reference any related issues
   - Include screenshots for UI changes

6. **Address review feedback**:
   - Make requested changes
   - Push updates to your branch
   - Respond to reviewer comments

### Pull Request Template

```markdown
## Description

Brief description of the changes made.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Testing

Describe the tests you ran and their results.

## Checklist

- [ ] My code follows the project's coding standards
- [ ] I have added tests for my changes
- [ ] All tests pass locally
- [ ] I have updated the documentation
- [ ] My commits follow the commit message guidelines

## Related Issues

Closes #(issue number)
```

## Reporting Issues

### Before Submitting an Issue

1. **Search existing issues** to avoid duplicates
2. **Try the latest version** to see if the issue is already fixed
3. **Gather information**:
   - VLP2SS version
   - Operating system and version
   - Python/Go version
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages and logs

### Issue Template

```markdown
## Description

Clear description of the issue.

## Steps to Reproduce

1. Step one
2. Step two
3. Step three

## Expected Behavior

What you expected to happen.

## Actual Behavior

What actually happened.

## Environment

- VLP2SS version: 1.0.1
- OS: macOS 13.0
- Python version: 3.11
- Go version: 1.21

## Logs

```text
Paste relevant log output here
```

## Additional Context

Any other relevant information.

```

## Feature Requests

We welcome feature requests! Please:

1. **Check existing requests** to avoid duplicates
2. **Describe the feature** clearly and concisely
3. **Explain the use case** and why it would be valuable
4. **Provide examples** of how it would work
5. **Consider implementation** if you have ideas

### Feature Request Template

```markdown
## Feature Description

Clear description of the proposed feature.

## Use Case

Explain why this feature would be valuable and who would benefit.

## Proposed Solution

Describe how you envision this feature working.

## Alternatives Considered

Describe alternative solutions or features you've considered.

## Additional Context

Any other relevant information, mockups, or examples.
```

## License

By contributing to VLP2SS, you agree that your contributions will be licensed under the MIT License.

## Questions?

If you have questions about contributing, please:

1. Check the [documentation](docs/)
2. Search existing issues
3. Create a new issue with the "question" label

## Thank You

Thank you for contributing to VLP2SS! Your efforts help make this project better for everyone.

---

**Project:** VLP2SS - The VLP to ScreenSteps Converter  
**Version:** 1.0.1  
**Author:** Burke Azbill  
**License:** MIT
