# Platform Compatibility

PrePrimer compatibility requirements and platform-specific considerations.

## Supported Platforms

### Linux
- **Status**: Fully supported
- **Distributions**: Ubuntu 20.04+, CentOS 7+, Debian 10+, Fedora 30+
- **Architecture**: x86_64, ARM64
- **Python**: 3.11-3.13

### macOS  
- **Status**: Fully supported
- **Versions**: macOS 10.15 (Catalina) and later
- **Architecture**: Intel x86_64, Apple Silicon (M1/M2)
- **Python**: 3.11-3.13

### Windows
- **Status**: Not supported
- **Reason**: Unicode character encoding limitations in file processing
- **Alternative**: Windows Subsystem for Linux (WSL2)

## Windows Considerations

PrePrimer does not support native Windows execution due to:

1. **Unicode Encoding Issues**: Inconsistent handling of Unicode characters in primer sequences
2. **File Path Limitations**: Windows path separator and length restrictions
3. **Permission Model**: Different file permission handling affects security features

### WSL2 Recommendation

Windows users can run PrePrimer using Windows Subsystem for Linux:

```bash
# Install WSL2 with Ubuntu
wsl --install -d Ubuntu

# In WSL2 terminal:
sudo apt update && sudo apt install python3 python3-pip git
git clone https://github.com/FOI-Bioinformatics/preprimer.git
cd preprimer
pip3 install -e ".[dev]"
```

## Python Version Support

| Python Version | Status | Notes |
|---------------|---------|-------|
| 3.11 | ✅ Supported | Minimum required version |
| 3.12 | ✅ Supported | Recommended for development |
| 3.13 | ✅ Supported | Latest stable features |
| 3.8-3.10 | ❌ Deprecated | No longer supported as of v0.3.0 |
| <3.8 | ❌ Unsupported | Missing required language features |

## Hardware Requirements

### Minimum Requirements
- **CPU**: 1 GHz processor
- **Memory**: 512 MB RAM
- **Storage**: 100 MB free space
- **Network**: Internet connection for installation

### Recommended Requirements  
- **CPU**: Multi-core processor (2+ cores)
- **Memory**: 2 GB RAM for large datasets
- **Storage**: 1 GB free space for development
- **Network**: Stable internet for package installation

## Performance Characteristics by Platform

### Linux Performance
- **File I/O**: Optimal performance with native filesystem support
- **Memory**: Efficient memory management with glibc
- **Processing**: ~67,000 amplicons/second average

### macOS Performance
- **File I/O**: Good performance with APFS/HFS+ filesystems
- **Memory**: Comparable to Linux performance
- **Processing**: ~65,000 amplicons/second average (slight overhead)

### Performance Factors
- **Dataset size**: Linear scaling with amplicon count
- **File format**: VarVAMP parsing fastest, Olivar slowest
- **Storage type**: SSD recommended for large datasets

## Dependency Management

### System Dependencies
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3 python3-pip python3-dev build-essential

# CentOS/RHEL
sudo yum install python3 python3-pip python3-devel gcc

# macOS (via Homebrew)
brew install python
```

### Python Dependencies
All Python dependencies are managed through pip and specified in `pyproject.toml`:

```bash
# Core dependencies
pip install -e .

# Development dependencies
pip install -e ".[dev]"
```

## Testing Across Platforms

### CI/CD Testing Matrix
- **Ubuntu Latest**: Python 3.11, 3.12, 3.13
- **macOS Latest**: Python 3.11, 3.12, 3.13
- **Test Coverage**: 581 tests across all supported configurations

### Platform-Specific Tests
```bash
# Run platform compatibility tests
python -m pytest tests/test_integration.py::test_platform_specific_operations -v

# Validate file handling across filesystems
python -m pytest tests/test_security.py::test_filesystem_operations -v
```

## Known Limitations

### General Limitations
- **Large Memory Datasets**: >10,000 amplicons may require additional memory
- **Network Dependencies**: Internet required for initial package installation
- **Unicode Support**: Complex Unicode characters in primer names may need validation

### Platform-Specific Limitations

#### Linux
- **SELinux**: May require policy adjustments for file operations
- **Container Environments**: Full functionality in Docker containers

#### macOS
- **Gatekeeper**: May require security exception for unsigned binaries
- **Sandboxing**: App sandboxing may restrict file access

## Installation Troubleshooting

### Common Issues

#### Permission Errors
```bash
# Use virtual environments instead of system-wide installation
python3 -m venv preprimer-env
source preprimer-env/bin/activate
pip install -e .
```

#### Python Version Issues
```bash
# Verify Python version
python3 --version

# Use specific Python version
python3.10 -m pip install -e .
```

#### Dependency Conflicts
```bash
# Clean installation in isolated environment
python3 -m venv clean-env
source clean-env/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

## Future Compatibility

### Planned Support
- **Python 3.14**: Expected support upon release
- **Additional ARM platforms**: Extended ARM64 support
- **Container optimization**: Improved Docker/Podman support

### Windows Compatibility Research
Ongoing investigation into Windows support includes:
- Unicode handling improvements
- Path normalization enhancements  
- Cross-platform file operation abstraction

For updates on Windows compatibility, monitor the project repository and release notes.