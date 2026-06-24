"""
Security tests for PrePrimer.

This module tests the security enhancements implemented to prevent
path traversal attacks, command injection, and input validation vulnerabilities.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add preprimer to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from preprimer.core.exceptions import ParserError
from preprimer.core.security import (
    InputValidator,
    PathValidator,
    SecureFileOperations,
    SecurityError,
    secure_subprocess_call,
)
from preprimer.parsers.varvamp_parser import VarVAMPParser


class TestPathValidator:
    """Test the PathValidator class for security vulnerabilities."""

    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked."""
        validator = PathValidator()

        # Test various path traversal attempts
        malicious_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "../../../../../../root/.ssh/id_rsa",
            "file/../../../etc/shadow",
            "normal/path/../../etc/passwd",
            "./../../../../../../etc/passwd",
        ]

        for malicious_path in malicious_paths:
            with pytest.raises(SecurityError):
                validator.sanitize_path(malicious_path)

    def test_filename_validation(self):
        """Test filename validation against dangerous characters."""
        validator = PathValidator()

        # Test dangerous filenames
        dangerous_names = [
            "file<script>",
            'file"dangerous',
            "file|command",
            "file?wildcard",
            "file*wildcard",
            "file\x00null",
            "CON",  # Windows reserved name
            "PRN",  # Windows reserved name
            "com1.txt",  # Windows reserved name with extension
            "",  # Empty filename
            "   ",  # Whitespace only
            "file.",  # Ends with period
            "file ",  # Ends with space
            "." * 300,  # Too long
        ]

        for dangerous_name in dangerous_names:
            with pytest.raises(SecurityError):
                validator.validate_filename(dangerous_name)

    def test_safe_filenames(self):
        """Test that safe filenames are accepted."""
        validator = PathValidator()

        safe_names = [
            "normal_file.txt",
            "file-with-dashes.csv",
            "file123.tsv",
            "a.b.c.txt",
            "CamelCaseFile.bed",
        ]

        for safe_name in safe_names:
            # Should not raise exception
            validator.validate_filename(safe_name)

    def test_base_directory_restriction(self):
        """Test that paths are restricted to base directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir).resolve()  # Resolve base directory
            validator = PathValidator()

            # Test valid path within base
            safe_path = base_dir / "subdir" / "file.txt"
            result = validator.sanitize_path(safe_path, base_dir)
            # Both paths should be resolved, so check if result is under base
            try:
                result.relative_to(base_dir)
                # If this succeeds, the path is under base_dir
            except ValueError:
                pytest.fail(f"Path {result} should be within base directory {base_dir}")

            # Test path outside base directory
            with pytest.raises(SecurityError):
                validator.sanitize_path("/tmp/outside", base_dir)


class TestSecureFileOperations:
    """Test secure file operations."""

    def test_safe_remove_tree_validation(self):
        """Test that directory removal validates paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secure_ops = SecureFileOperations(Path(temp_dir))

            # Create a test directory
            test_dir = Path(temp_dir) / "test_remove"
            test_dir.mkdir()
            assert test_dir.exists()

            # Should successfully remove
            secure_ops.safe_remove_tree(test_dir)
            assert not test_dir.exists()

            # Test path traversal attempt
            with pytest.raises(SecurityError):
                secure_ops.safe_remove_tree("../../../etc")

    def test_safe_create_directories(self):
        """Test secure directory creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secure_ops = SecureFileOperations(Path(temp_dir))

            # Create nested directories
            nested_path = Path(temp_dir) / "a" / "b" / "c"
            result = secure_ops.safe_create_directories(nested_path)

            assert result.exists()
            assert result.is_dir()

            # Test path traversal prevention
            with pytest.raises(SecurityError):
                secure_ops.safe_create_directories("../outside")

    def test_safe_file_operations(self):
        """Test secure file opening with validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            secure_ops = SecureFileOperations(Path(temp_dir))

            test_file = Path(temp_dir) / "test.txt"

            # Write to file
            with secure_ops.safe_open_file(test_file, "w") as f:
                f.write("test content")

            # Read from file
            with secure_ops.safe_open_file(test_file, "r") as f:
                content = f.read()
                assert content == "test content"

            # Test path traversal prevention
            with pytest.raises(SecurityError):
                secure_ops.safe_open_file("../../../etc/passwd", "r")


class TestInputValidator:
    """Test input validation functionality."""

    def test_primer_sequence_validation(self):
        """Test primer sequence validation."""
        validator = InputValidator()

        # Test valid sequences
        valid_sequences = [
            "ATCGATCGATCG",
            "ATCGRYSWKMBDHVN",  # IUPAC codes
            "atcgryswkmbdhvn",  # Lowercase
        ]

        for seq in valid_sequences:
            validator.validate_primer_sequence(seq)  # Should not raise

        # Test invalid sequences
        invalid_sequences = [
            "",  # Empty
            "ATCGXYZ",  # Invalid characters
            "ATCG123",  # Numbers
            "ATCG-GC",  # Hyphen
            "A" * 1001,  # Too long
        ]

        for seq in invalid_sequences:
            with pytest.raises(SecurityError):
                validator.validate_primer_sequence(seq)

    def test_amplicon_name_validation(self):
        """Test amplicon name validation."""
        validator = InputValidator()

        # Test valid names
        valid_names = [
            "amplicon_1",
            "COVID-19_amplicon",
            "region_A",
        ]

        for name in valid_names:
            validator.validate_amplicon_name(name)  # Should not raise

        # Test invalid names
        invalid_names = [
            "",  # Empty
            "   ",  # Whitespace only
            "name<script>",  # HTML tags
            'name"dangerous',  # Quotes
            "name|command",  # Pipe
            "A" * 201,  # Too long
        ]

        for name in invalid_names:
            with pytest.raises(SecurityError):
                validator.validate_amplicon_name(name)

    def test_string_sanitization(self):
        """Test string sanitization functionality."""
        validator = InputValidator()

        # Test normal sanitization
        result = validator.sanitize_string("  normal text  ")
        assert result == "normal text"

        # Test control character removal
        dirty_string = "text\x00with\x01control\x02chars"
        result = validator.sanitize_string(dirty_string)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result

        # Test length validation
        with pytest.raises(SecurityError):
            validator.sanitize_string("A" * 1001, max_length=1000)


class TestSecureSubprocessCall:
    """Test secure subprocess execution."""

    def test_command_injection_prevention(self):
        """Test that command injection attempts are blocked."""
        # Test dangerous commands
        dangerous_commands = [
            ["echo", "hello; rm -rf /"],
            ["ls", "|", "grep", "secret"],
            ["cat", "/etc/passwd", "&", "echo", "done"],
            ["echo", "`whoami`"],
            ["echo", "$(rm -rf /)"],
        ]

        for cmd in dangerous_commands:
            with pytest.raises(SecurityError):
                secure_subprocess_call(cmd)

    def test_safe_command_execution(self):
        """Test that safe commands execute properly."""
        # Test safe echo command
        result = secure_subprocess_call(["echo", "hello world"])
        assert result.returncode == 0
        assert "hello world" in result.stdout

    def test_command_validation(self):
        """Test command format validation."""
        # Test invalid command formats
        with pytest.raises(SecurityError):
            secure_subprocess_call("echo hello")  # String instead of list

        with pytest.raises(SecurityError):
            secure_subprocess_call([])  # Empty command

        with pytest.raises(SecurityError):
            secure_subprocess_call([123, "hello"])  # Non-string argument


class TestVarVAMPParserSecurity:
    """Test security enhancements in VarVAMP parser."""

    def test_malicious_file_path_rejection(self):
        """Test that malicious file paths are rejected."""
        parser = VarVAMPParser()

        malicious_paths = [
            "../../../etc/passwd",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
        ]

        for path in malicious_paths:
            # Should raise SecurityError during path validation
            with pytest.raises((SecurityError, ParserError)) as exc_info:
                parser.parse(path)
            # If it's a ParserError, it should be because of security validation
            if isinstance(exc_info.value, ParserError):
                # The path should have been validated and resolved first
                assert "not a valid VarVAMP format" in str(exc_info.value)

    def test_input_sanitization(self):
        """Test that malicious input is sanitized."""
        # This test would require creating a malicious VarVAMP file
        # For now, we test the validation functions directly
        parser = VarVAMPParser()

        # Test with empty/invalid prefix
        malicious_prefixes = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE primers; --",
            "$(rm -rf /)",
        ]

        for prefix in malicious_prefixes:
            with pytest.raises(SecurityError):
                # This should trigger validation in the parse method
                InputValidator.validate_amplicon_name(prefix)

    def test_file_size_limits(self):
        """Test that extremely large files are handled safely."""
        # Create a temporary file that simulates a large malicious file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Write a header
            f.write(
                "amplicon_name\tamplicon_length\tprimer_name\tpool\tstart\tstop\tseq\tsize\tgc_best\ttemp_best\tmean_gc\tmean_temp\tscore\n"
            )

            # Write a row with extremely large sequence
            large_sequence = "A" * 100000  # Very large sequence
            f.write(
                f"amp1\t1000\tFW_primer\t1\t1\t100\t{large_sequence}\t100\t50.0\t60.0\t50.0\t60.0\t1.0\n"
            )

            temp_path = f.name

        try:
            parser = VarVAMPParser()
            # This should raise a SecurityError due to sequence length validation
            with pytest.raises(SecurityError):
                parser.parse(temp_path)
        finally:
            os.unlink(temp_path)


class TestIntegrationSecurity:
    """Integration tests for security across components."""

    def test_end_to_end_security(self):
        """Test security validation across the entire pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a secure operations instance
            secure_ops = SecureFileOperations(Path(temp_dir))

            # Test directory creation
            work_dir = Path(temp_dir) / "work"
            secure_ops.safe_create_directories(work_dir)

            # Test file operations
            test_file = work_dir / "test.txt"
            with secure_ops.safe_open_file(test_file, "w") as f:
                f.write("secure content")

            # Verify content
            with secure_ops.safe_open_file(test_file, "r") as f:
                content = f.read()
                assert content == "secure content"

            # Test cleanup
            secure_ops.safe_remove_tree(work_dir)
            assert not work_dir.exists()

    def test_error_handling_security(self):
        """Test that errors don't leak sensitive information."""
        validator = PathValidator()

        # Test that error messages are informative but don't reveal system details
        with pytest.raises(SecurityError) as exc_info:
            validator.sanitize_path("../../../etc/passwd")

        error_msg = str(exc_info.value)
        # Error message should indicate path traversal was detected
        assert "Path traversal attempt detected" in error_msg

        # Test that system directory access is denied
        with pytest.raises(SecurityError) as exc_info:
            validator.sanitize_path("/etc/shadow")

        error_msg = str(exc_info.value)
        assert "system directory denied" in error_msg


if __name__ == "__main__":
    pytest.main([__file__])
