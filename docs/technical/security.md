# Security Implementation

PrePrimer implements comprehensive security measures to protect against common vulnerabilities in file processing applications.

## Security Features

### Path Validation and Sanitization
PrePrimer prevents directory traversal attacks through comprehensive path validation:

```python
from preprimer.core.security import PathValidator, SecurityError

# Safe path operations
try:
    safe_path = PathValidator.sanitize_path(user_input)
    PathValidator.validate_output_directory(output_dir)
except SecurityError as e:
    print(f"Security violation: {e}")
```

**Protection Against:**
- Path traversal attacks (`../`, `~`, absolute paths)
- Symlink attacks and race conditions
- Hidden file access attempts
- System directory access

### Input Validation
Comprehensive input sanitization with configurable limits:

```python
from preprimer.core.security import InputValidator

# File content validation with size limits
validated_content = InputValidator.validate_file_content(
    content, 
    max_size_mb=10,
    allowed_extensions=['.tsv', '.bed', '.csv']
)

# File size validation
InputValidator.validate_file_size(file_path, max_size_mb=50)
```

**Features:**
- Configurable file size limits (default: 50MB)
- File extension validation
- Content sanitization and encoding validation
- Protection against malformed input

### Safe File Operations
Automatic resource cleanup and secure temporary file handling:

```python
from preprimer.core.security import SecurityUtils

# Secure temporary files with automatic cleanup
with SecurityUtils.create_temp_file(suffix='.tsv') as tmp_file:
    process_data(tmp_file)  # Automatic cleanup on exit

# Safe directory creation with proper permissions
safe_dir = SecurityUtils.create_safe_directory(base_path, "output")
```

**Security Measures:**
- Automatic temporary file cleanup
- Secure file permissions (600 for files, 700 for directories)
- Atomic file operations to prevent race conditions
- Memory-mapped file handling for large datasets

### Configuration and Monitoring
Security settings can be configured globally:

```python
from preprimer.core.enhanced_config import EnhancedConfigManager

config = EnhancedConfigManager.from_dict({
    "security": {
        "max_file_size_mb": 100,
        "allowed_extensions": [".tsv", ".bed", ".csv", ".fasta"],
        "strict_path_validation": True,
        "enable_symlink_protection": True,
        "log_security_events": True
    }
})
```

### Environment Variables
```bash
export PREPRIMER_MAX_FILE_SIZE_MB=100
export PREPRIMER_STRICT_PATH_VALIDATION=true
export PREPRIMER_LOG_SECURITY_EVENTS=true
```

## Security Testing

PrePrimer includes 18 security validation tests covering:

```bash
# Run security test suite
python -m pytest tests/test_security.py -v
```

**Test Coverage:**
- Path traversal prevention and validation
- Input sanitization and size limit enforcement
- File permission and access control validation
- Symlink protection and race condition prevention
- Resource exhaustion protection

## Best Practices

### For Users
1. Use the latest version for current security fixes
2. Configure appropriate file size limits for your environment
3. Validate primer data from untrusted sources
4. Enable security logging in production environments
5. Use virtual environments to isolate dependencies

### For Developers
1. Always use provided security utilities for file operations
2. Validate all user inputs with `InputValidator`
3. Use `PathValidator.sanitize_path()` for all path operations
4. Handle `SecurityError` exceptions appropriately
5. Add security tests for new functionality

## Threat Model

PrePrimer security implementation addresses:

- **File-based attacks**: Path traversal, symlink exploitation
- **Resource exhaustion**: Large file attacks, memory exhaustion
- **Data injection**: Malformed input files, encoding attacks
- **Local privilege escalation**: Directory traversal, unauthorized file access

## Security Reporting

For security vulnerabilities:
1. Do not create public GitHub issues
2. Email security concerns to project maintainers
3. Include detailed reproduction steps
4. Allow responsible disclosure timeline

**Response Timeline:**
- 24 hours: Initial acknowledgment
- 72 hours: Preliminary assessment  
- 30 days: Security fix release (if confirmed)
- Public disclosure after fix availability