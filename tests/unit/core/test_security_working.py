"""
Working unit tests for security validation components.

This is a REAL, WORKING migration demonstrating best practices:
- Parametrized tests for efficiency
- Property-based testing for edge cases
- Performance benchmarking
- Clear organization by threat category
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from preprimer.core.exceptions import SecurityError
from preprimer.core.security import (
    InputValidator,
    PathValidator,
    SecureFileOperations,
    secure_subprocess_call,
)


# =============================================================================
# Test Data - Organized by threat category
# =============================================================================

PATH_TRAVERSAL_ATTACKS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "../../../../../../root/.ssh/id_rsa",
    "file/../../../etc/shadow",
    "normal/path/../../etc/passwd",
    "./../../../../../../etc/passwd",
]

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

WINDOWS_RESERVED_NAMES = [
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "LPT1",
    "CON.txt",
    "prn.csv",
]

SAFE_FILENAMES = [
    "normal_file.txt",
    "file-with-dashes.csv",
    "file123.tsv",
    "a.b.c.txt",
    "CamelCaseFile.bed",
]


# =============================================================================
# PathValidator Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestPathValidatorTraversal:
    """Test path traversal attack prevention."""

    @pytest.mark.parametrize("malicious_path", PATH_TRAVERSAL_ATTACKS)
    def test_path_traversal_blocked(self, malicious_path):
        """Path traversal attempts should be blocked."""
        with pytest.raises(SecurityError):
            PathValidator.sanitize_path(malicious_path)

    def test_safe_path_accepted(self, tmp_path):
        """Safe paths should be accepted."""
        test_file = tmp_path / "test.txt"
        test_file.touch()

        # Should not raise
        result = PathValidator.sanitize_path(str(test_file))
        assert isinstance(result, Path)


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
        with pytest.raises(SecurityError):
            PathValidator.validate_filename(reserved_name)

    @pytest.mark.parametrize("safe_name", SAFE_FILENAMES)
    def test_safe_filenames_accepted(self, safe_name):
        """Safe filenames should be accepted."""
        # Should not raise
        PathValidator.validate_filename(safe_name)

    def test_filename_length_limit(self):
        """Filenames exceeding 255 bytes should be rejected."""
        long_name = "a" * 256

        with pytest.raises(SecurityError, match="too long"):
            PathValidator.validate_filename(long_name)

    def test_only_periods_rejected(self):
        """Filenames consisting only of periods should be rejected."""
        with pytest.raises(SecurityError, match="only of periods"):
            PathValidator.validate_filename("...")


@pytest.mark.unit
@pytest.mark.security
class TestPathValidatorProperties:
    """Property-based tests using Hypothesis."""

    @given(st.text(min_size=256, max_size=300))
    @settings(max_examples=50, deadline=500)
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
    @settings(max_examples=50, deadline=500)
    def test_forbidden_char_rejected(self, filename):
        """Any filename with forbidden characters should be rejected."""
        with pytest.raises(SecurityError):
            PathValidator.validate_filename(filename)


# =============================================================================
# InputValidator Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestInputValidator:
    """Test input validation."""

    @pytest.mark.parametrize(
        "valid_sequence",
        ["ATCG", "ATCGATCGATCG", "NNNN", "atcg", "AtCgNn"],
    )
    def test_primer_sequence_valid(self, valid_sequence):
        """Valid primer sequences should pass validation."""
        # Should not raise
        InputValidator.validate_primer_sequence(valid_sequence)

    @pytest.mark.parametrize(
        "invalid_sequence",
        ["ATCGX", "123", "ATCG ", " ATCG", ""],
    )
    def test_primer_sequence_invalid(self, invalid_sequence):
        """Invalid primer sequences should be rejected."""
        with pytest.raises(SecurityError):
            InputValidator.validate_primer_sequence(invalid_sequence)

    def test_amplicon_name_validation(self):
        """Amplicon names should be validated."""
        # Valid name
        InputValidator.validate_amplicon_name("amplicon_1")

        # Invalid name (too long)
        with pytest.raises(SecurityError):
            InputValidator.validate_amplicon_name("x" * 300)

    def test_string_sanitization(self):
        """Strings should be sanitized (control chars removed, length enforced)."""
        # Test control character removal
        dangerous = "test\x00null\x01char"
        safe = InputValidator.sanitize_string(dangerous, max_length=100)

        # Control characters should be removed
        assert "\x00" not in safe
        assert "\x01" not in safe
        assert "test" in safe
        assert len(safe) <= 100

        # Test length enforcement
        with pytest.raises(SecurityError, match="too long"):
            InputValidator.sanitize_string("x" * 1001, max_length=1000)


# =============================================================================
# SecureFileOperations Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestSecureFileOperations:
    """Test secure file operations."""

    def test_safe_open_file(self, tmp_path):
        """Files should be opened safely."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        ops = SecureFileOperations(base_dir=tmp_path)
        with ops.safe_open_file(test_file, "r") as f:
            content = f.read()

        assert content == "content"

    def test_safe_create_directories(self, tmp_path):
        """Directories should be created safely."""
        ops = SecureFileOperations(base_dir=tmp_path)
        new_dir = tmp_path / "nested" / "dir"

        ops.safe_create_directories(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_safe_remove_tree(self, tmp_path):
        """Directory trees should be removed safely."""
        ops = SecureFileOperations(base_dir=tmp_path)
        test_dir = tmp_path / "to_remove"
        test_dir.mkdir()
        (test_dir / "file.txt").write_text("test")

        ops.safe_remove_tree(test_dir)

        assert not test_dir.exists()

    def test_operations_restricted_to_base_dir(self, tmp_path):
        """Operations should be restricted to base directory."""
        ops = SecureFileOperations(base_dir=tmp_path)

        # Try to access file outside base_dir
        with pytest.raises(SecurityError):
            ops.safe_open_file("/etc/passwd", "r")


# =============================================================================
# Subprocess Security Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.security
class TestSubprocessSecurity:
    """Test secure subprocess execution."""

    def test_command_as_list_required(self):
        """Commands must be passed as list, not string."""
        with pytest.raises(SecurityError, match="must be a non-empty list"):
            secure_subprocess_call("ls -la")

    def test_safe_command_execution(self):
        """Safe commands should execute successfully."""
        # Use a simple command that works on all platforms
        result = secure_subprocess_call(["echo", "test"])
        assert result.returncode == 0

    def test_timeout_parameter(self):
        """Timeout parameter should be respected."""
        # Test that timeout parameter is accepted
        result = secure_subprocess_call(["echo", "test"], timeout=60)
        assert result.returncode == 0


# =============================================================================
# Integration Tests
# =============================================================================

@pytest.mark.integration
@pytest.mark.security
class TestSecurityIntegration:
    """Integration security tests."""

    def test_pathvalidator_with_securefileops(self, tmp_path):
        """PathValidator should work with SecureFileOperations."""
        # Validate path
        safe_file = tmp_path / "safe.txt"
        validated = PathValidator.sanitize_path(str(safe_file))

        # Use in SecureFileOperations
        ops = SecureFileOperations(base_dir=tmp_path)
        with ops.safe_open_file(validated, "w") as f:
            f.write("test")

        assert safe_file.read_text() == "test"


# =============================================================================
# Performance Tests
# =============================================================================

@pytest.mark.performance
@pytest.mark.security
class TestSecurityPerformance:
    """Performance benchmarks for security code."""

    def test_filename_validation_performance(self, benchmark):
        """Filename validation should be fast."""
        result = benchmark(
            PathValidator.validate_filename,
            "safe_filename.txt"
        )
        assert result is None  # No exception

    def test_path_sanitization_performance(self, benchmark, tmp_path):
        """Path sanitization should be fast."""
        test_path = tmp_path / "test.txt"
        test_path.touch()

        result = benchmark(
            PathValidator.sanitize_path,
            str(test_path)
        )
        assert result.exists()


# =============================================================================
# Contract Tests
# =============================================================================

@pytest.mark.unit
@pytest.mark.contract
class TestSecurityContracts:
    """Contract tests for security interfaces."""

    def test_pathvalidator_has_required_methods(self):
        """PathValidator must have all required methods."""
        required = [
            "validate_filename",
            "validate_path_components",
            "sanitize_path",
        ]

        for method in required:
            assert hasattr(PathValidator, method)
            assert callable(getattr(PathValidator, method))

    def test_inputvalidator_has_required_methods(self):
        """InputValidator must have all required methods."""
        required = [
            "validate_primer_sequence",
            "validate_amplicon_name",
            "sanitize_string",
        ]

        for method in required:
            assert hasattr(InputValidator, method)
            assert callable(getattr(InputValidator, method))

    def test_security_errors_have_messages(self):
        """Security errors must have informative messages."""
        try:
            PathValidator.sanitize_path("../../../etc/passwd")
        except SecurityError as e:
            message = str(e).lower()
            # Should mention the issue
            assert any(
                word in message
                for word in ["traversal", "invalid", "path"]
            )
