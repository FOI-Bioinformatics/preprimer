# Security Policy

## Supported Versions

Security updates are provided for the following versions of PrePrimer:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| 0.2.x   | :white_check_mark: |
| < 0.2.0 | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report security vulnerabilities by email to:
**preprimer-security@foi.se**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

### What to Include

Please include the following information in your report:

- Type of vulnerability
- Full paths of source file(s) related to the vulnerability
- Location of the affected source code (tag/branch/commit or direct URL)
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the vulnerability, including how an attacker might exploit it

### Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 5 business days
- **Fix Timeline**: Varies based on severity and complexity
  - **Critical**: 1-7 days
  - **High**: 7-14 days
  - **Medium**: 14-30 days
  - **Low**: 30-90 days

## Security Features

PrePrimer implements multiple security layers for safe file processing:

### 1. Path Validation

```python
from preprimer.core.security import PathValidator

# Automatic path traversal prevention
safe_path = PathValidator.sanitize_path(user_input)

# Directory validation
PathValidator.validate_output_directory(output_dir)
```

**Features:**
- Path traversal attack prevention
- Symlink validation
- Restricted path enforcement
- Directory boundary checks

### 2. Input Sanitization

```python
# File size limits (default: 50MB)
PathValidator.validate_file_size(file_path, max_size=50_000_000)

# Content validation
PathValidator.validate_file_content(file_path, allowed_extensions=['.tsv', '.bed', '.csv'])
```

**Features:**
- Configurable file size limits
- File type validation
- Content sanitization
- MIME type checking

### 3. Secure File Operations

```python
from preprimer.core.security import SecureFileHandler

# Safe temporary file handling
with SecureFileHandler.create_temp_file() as temp_file:
    # Automatic cleanup on context exit
    process_file(temp_file)
```

**Features:**
- Secure temporary file creation
- Automatic resource cleanup
- Permission validation
- Atomic file operations

### 4. Security Event Logging

```python
# Security events are automatically logged
logger.security("Path traversal attempt detected: %s", malicious_path)
```

**Logged Events:**
- Path traversal attempts
- File size violations
- Invalid input patterns
- Permission errors

## Known Security Considerations

### 1. File Processing

**Risk Level**: Low

PrePrimer processes text files (TSV, BED, CSV, FASTA) which inherently have low security risk. However:

- **File Size**: Default 50MB limit prevents resource exhaustion
- **Path Traversal**: Prevented through path validation
- **Symlinks**: Validated and restricted

**Mitigation**: Input validation is performed at multiple levels

### 2. Degenerate Primer Sequences

**Risk Level**: Minimal

IUPAC degenerate nucleotide codes (R, Y, S, W, etc.) are validated:

- Limited to valid IUPAC codes
- No code execution risk
- Pattern validation applied

**Mitigation**: Sequence validation enforced by parsers

### 3. External File References

**Risk Level**: Low

ARTIC format can reference external files (reference.fasta):

- Path validation applied
- Restricted to scheme directory
- No remote file access by default

**Mitigation**: Configurable file path restrictions

### 4. Metadata Processing

**Risk Level**: Low

JSON and YAML metadata files (info.json, config files):

- Safe parsing with pydantic validation
- Schema enforcement
- Type checking
- No code execution

**Mitigation**: Strict schema validation, no `eval()` or `exec()`

## Security Best Practices for Users

### 1. Input Validation

```python
from pathlib import Path
from preprimer.core.security import PathValidator

# Always validate user-provided paths
def safe_convert(user_input_path: str):
    # Check file exists
    input_path = Path(user_input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"File not found: {user_input_path}")

    # Validate path safety
    safe_path = PathValidator.sanitize_path(user_input_path)

    # Validate file size
    PathValidator.validate_file_size(safe_path)

    # Perform conversion
    converter.convert(input_file=str(safe_path), ...)
```

### 2. Output Directory Control

```python
# Use absolute paths for output
output_dir = Path("/absolute/path/to/output").resolve()

# Validate directory is safe
PathValidator.validate_output_directory(str(output_dir))

# Create with restricted permissions
output_dir.mkdir(parents=True, exist_ok=True, mode=0o755)
```

### 3. Configuration Security

```python
# Don't load configurations from untrusted sources
config = PrePrimerConfig.from_file("config.json")  # OK if you control file

# Validate configuration
if config.security.max_file_size > 100_000_000:  # 100MB
    raise ValueError("File size limit too high")
```

### 4. Dependency Management

```bash
# Keep dependencies updated
pip install --upgrade preprimer

# Check for known vulnerabilities
pip install safety
safety check

# Use virtual environments
python -m venv venv
source venv/bin/activate
pip install preprimer
```

## Security Testing

PrePrimer includes comprehensive security testing:

```bash
# Run security tests
python -m pytest tests/test_security.py -v

# Run security linting
bandit -r preprimer/ -ll

# Check dependencies
safety check
```

**Test Coverage:**
- 38 security-focused tests
- 100% security module coverage
- Path traversal prevention
- Input sanitization
- File size validation
- Permission checks

## Vulnerability Disclosure Process

### 1. Report Received

- Security team acknowledges receipt
- Initial severity assessment
- Assign CVE if applicable

### 2. Investigation

- Reproduce vulnerability
- Assess impact and scope
- Develop fix and test cases

### 3. Fix Development

- Implement security patch
- Add regression tests
- Verify fix effectiveness

### 4. Disclosure

- **Private disclosure** to reporter
- Allow time for users to update (typically 7-14 days)
- **Public disclosure** via:
  - GitHub Security Advisory
  - Release notes
  - Security mailing list

### 5. Release

- Tag security release
- Update CHANGELOG with security notes
- Notify users through appropriate channels

## Security Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

*No vulnerabilities reported yet. Be the first!*

## Secure Development Practices

PrePrimer follows secure coding practices:

### Code Review

- All code reviewed before merge
- Security-focused review for critical paths
- Automated security scanning in CI/CD

### Dependency Management

```toml
# pyproject.toml - Dependencies are pinned with minimum versions
dependencies = [
    "pydantic>=2.0,<3.0",
    "click>=8.0,<9.0",
]
```

### Testing

- Comprehensive test suite (611 tests)
- Security-specific test suite (38 tests)
- Property-based testing with Hypothesis
- Integration tests with real data

### Static Analysis

```bash
# Automated in CI/CD
black --check preprimer/
flake8 preprimer/
mypy preprimer/
bandit -r preprimer/
```

## Security Resources

- **Security Policy**: This document
- **Security Guide**: `docs/user-guide/security.md` (detailed usage)
- **Security Tests**: `tests/test_security*.py`
- **Security Module**: `preprimer/core/security.py`

## Contact

- **Security Issues**: preprimer-security@foi.se
- **General Issues**: https://github.com/FOI-Bioinformatics/preprimer/issues
- **Website**: https://github.com/FOI-Bioinformatics/preprimer

## Attribution

We thank the security research community for helping keep PrePrimer secure.

---

**Last Updated**: 2024-10-14
**Version**: 1.0.0
