"""
Comprehensive tests for exception handling targeting missed coverage lines.

This targets the 15 missed statements in preprimer/core/exceptions.py which are
critical for user experience and error handling.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from preprimer.core.exceptions import (  # AlignmentError,  # Removed in v0.2.0 (no alignment providers implemented)
    ConfigError,
    CorruptedDataError,
    ErrorContext,
    FileNotFoundError,
    InsufficientDataError,
    InvalidFormatError,
    OutputError,
    ParserError,
    PrePrimerError,
    SecurityError,
    ValidationError,
    handle_common_exceptions,
)

# TestAlignmentErrorMissedLines class commented out - AlignmentError removed in v0.2.0


class TestOutputErrorMissedLines:
    """Test OutputError default message and suggestion generation."""

    def test_output_error_default_user_message(self):
        """Test OutputError default user_message generation (lines 156->162)."""

        # Test without user_message - should generate default
        error = OutputError("Test output error", output_path="/path/to/output.txt")

        # Should generate default user message with output path
        expected_message = "Failed to write output to /path/to/output.txt. Please check file permissions and disk space."
        assert error.user_message == expected_message

    def test_output_error_default_suggestions(self):
        """Test OutputError default suggestions generation (lines 162->169)."""

        # Test without suggestions - should generate defaults
        error = OutputError("Test output error")

        # Should generate default suggestions
        suggestions = error.suggestions
        assert len(suggestions) == 3
        assert any("write permissions" in suggestion for suggestion in suggestions)
        assert any("disk space" in suggestion for suggestion in suggestions)
        assert any("directory exists" in suggestion for suggestion in suggestions)


class TestConfigErrorMissedLines:
    """Test ConfigError default message generation."""

    def test_config_error_default_user_message(self):
        """Test ConfigError default user_message generation (lines 183->189)."""

        # Test without user_message - should generate default
        error = ConfigError("Test config error", config_file="config.yaml")

        # Should generate default user message with config file
        expected_message = "Configuration error in config.yaml. Please check your configuration settings."
        assert error.user_message == expected_message


class TestSecurityErrorMissedLines:
    """Test SecurityError default message and suggestion generation."""

    def test_security_error_default_user_message(self):
        """Test SecurityError default user_message generation (lines 201->204)."""

        # Test without user_message - should generate default
        error = SecurityError("Test security error", violation_type="path_traversal")

        # Should generate default security user message
        expected_message = (
            "Security violation detected. The operation was blocked for safety."
        )
        assert error.user_message == expected_message

    def test_security_error_default_suggestions(self):
        """Test SecurityError default suggestions generation (lines 204->211)."""

        # Test without suggestions - should generate defaults
        error = SecurityError("Test security error")

        # Should generate default security suggestions
        suggestions = error.suggestions
        assert len(suggestions) == 3
        assert any("trusted input files" in suggestion for suggestion in suggestions)
        assert any(
            "'..' or suspicious characters" in suggestion for suggestion in suggestions
        )
        assert any("file permissions" in suggestion for suggestion in suggestions)


class TestFileNotFoundErrorMissedLines:
    """Test FileNotFoundError default message and suggestion generation."""

    def test_file_not_found_error_default_user_message(self):
        """Test FileNotFoundError default user_message generation (lines 229->231)."""

        # Test without user_message - should generate default
        error = FileNotFoundError("/path/to/missing/file.txt")

        # Should generate default user message with file path
        expected_message = "File not found: /path/to/missing/file.txt"
        assert error.user_message == expected_message

    def test_file_not_found_error_default_suggestions(self):
        """Test FileNotFoundError default suggestions generation (lines 231->237)."""

        # Test without suggestions - should generate defaults
        error = FileNotFoundError("/path/to/missing/file.txt")

        # Should generate default suggestions
        suggestions = error.suggestions
        assert len(suggestions) == 3
        assert any("file path is correct" in suggestion for suggestion in suggestions)
        assert any(
            "file exists and is readable" in suggestion for suggestion in suggestions
        )
        assert any("absolute paths" in suggestion for suggestion in suggestions)


class TestInvalidFormatErrorMissedLines:
    """Test InvalidFormatError default suggestion generation."""

    def test_invalid_format_error_default_suggestions(self):
        """Test InvalidFormatError default suggestions generation (lines 259->266)."""

        # Test without suggestions - should generate defaults
        error = InvalidFormatError("/path/to/file.txt", expected_format="TSV")

        # Should generate default suggestions
        suggestions = error.suggestions
        assert len(suggestions) == 3
        assert any("correct format" in suggestion for suggestion in suggestions)
        assert any("file headers" in suggestion for suggestion in suggestions)
        assert any("converting the file" in suggestion for suggestion in suggestions)


class TestCorruptedDataErrorMissedLines:
    """Test CorruptedDataError details handling and suggestion generation."""

    def test_corrupted_data_error_with_details(self):
        """Test CorruptedDataError details handling (lines 279->282)."""

        # Test with details parameter - should append to technical message
        error = CorruptedDataError(
            "/path/to/file.txt", details="Invalid line format at line 5"
        )

        # Should include details in technical message
        assert "Invalid line format at line 5" in error.technical_message
        assert (
            "Corrupted data in /path/to/file.txt: Invalid line format at line 5"
            == error.technical_message
        )

    def test_corrupted_data_error_default_suggestions(self):
        """Test CorruptedDataError default suggestions generation (lines 285->292)."""

        # Test without suggestions - should generate defaults
        error = CorruptedDataError("/path/to/file.txt")

        # Should generate default suggestions
        suggestions = error.suggestions
        assert len(suggestions) == 3
        assert any(
            "re-downloading or re-creating" in suggestion for suggestion in suggestions
        )
        assert any("file corruption" in suggestion for suggestion in suggestions)
        assert any("original source" in suggestion for suggestion in suggestions)


class TestInsufficientDataErrorMissedLines:
    """Test InsufficientDataError default suggestion generation."""

    def test_insufficient_data_error_default_suggestions(self):
        """Test InsufficientDataError default suggestions generation (lines 312->319)."""

        # Test without suggestions - should generate defaults
        error = InsufficientDataError(
            "Not enough primers found", required_count=5, actual_count=2
        )

        # Should generate default suggestions
        suggestions = error.suggestions
        assert len(suggestions) == 3
        assert any("input file contains" in suggestion for suggestion in suggestions)
        assert any("necessary fields" in suggestion for suggestion in suggestions)
        assert any(
            "complete and not truncated" in suggestion for suggestion in suggestions
        )


class TestExceptionEdgeCaseScenarios:
    """Test edge case scenarios for comprehensive coverage."""

    # test_alignment_error_with_custom_user_message - removed (AlignmentError removed in v0.2.0)
    # test_alignment_error_with_custom_suggestions - removed (AlignmentError removed in v0.2.0)

    def test_output_error_without_output_path(self):
        """Test OutputError without output_path (should generate generic message)."""

        error = OutputError("Generic output error")

        # Should generate generic message without path
        expected_message = (
            "Failed to write output. Please check file permissions and disk space."
        )
        assert error.user_message == expected_message

    def test_config_error_without_config_file(self):
        """Test ConfigError without config_file (should generate generic message)."""

        error = ConfigError("Generic config error")

        # Should generate generic message without file
        expected_message = (
            "Configuration error. Please check your configuration settings."
        )
        assert error.user_message == expected_message

    def test_invalid_format_error_without_expected_format(self):
        """Test InvalidFormatError without expected_format (should generate generic message)."""

        error = InvalidFormatError("/path/to/file.txt")

        # Should generate message without expected format
        expected_message = "Invalid file format: /path/to/file.txt"
        assert error.user_message == expected_message

    def test_corrupted_data_error_without_details(self):
        """Test CorruptedDataError without details (should not append)."""

        error = CorruptedDataError("/path/to/file.txt")

        # Should not append details to technical message
        assert error.technical_message == "Corrupted data in /path/to/file.txt"
        assert ":" not in error.technical_message.split("file.txt", 1)[-1]


class TestExceptionIntegration:
    """Test exception integration scenarios."""

    # test_exception_chaining_with_defaults - removed (AlignmentError removed in v0.2.0)

    # test_context_preservation_with_defaults - removed (AlignmentError removed in v0.2.0)

    def test_all_exception_types_instantiation(self):
        """Test all exception types can be instantiated with defaults."""

        # Test all exception types with minimal parameters to trigger defaults
        exceptions = [
            # AlignmentError("Alignment failed"),  # Removed in v0.2.0
            OutputError("Output failed"),
            ConfigError("Config failed"),
            SecurityError("Security failed"),
            FileNotFoundError("/missing/file.txt"),
            InvalidFormatError("/bad/file.txt"),
            CorruptedDataError("/corrupt/file.txt"),
            InsufficientDataError("Not enough data"),
        ]

        # All should have user messages and appropriate suggestions
        for exc in exceptions:
            assert exc.user_message is not None
            assert len(exc.user_message) > 0
            if hasattr(exc, "suggestions"):
                assert isinstance(exc.suggestions, list)

    # test_complex_scenario_with_all_defaults - removed (AlignmentError removed in v0.2.0)
