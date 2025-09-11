"""
Comprehensive tests for the error handling system.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from preprimer.core.exceptions import (
    AlignmentError,
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


class TestPrePrimerErrorBase:
    """Test the base PrePrimerError functionality."""

    def test_basic_error_creation(self):
        """Test creating a basic PrePrimerError."""
        error = PrePrimerError("Test technical message")

        assert error.technical_message == "Test technical message"
        assert error.user_message == "Test technical message"  # Default fallback
        assert error.context == {}
        assert error.suggestions == []

    def test_error_with_custom_user_message(self):
        """Test error with custom user message."""
        error = PrePrimerError(
            "Technical details about the error",
            user_message="User-friendly error message",
        )

        assert error.technical_message == "Technical details about the error"
        assert error.user_message == "User-friendly error message"

    def test_error_with_context_and_suggestions(self):
        """Test error with context and suggestions."""
        context = {"file": "test.txt", "line": 42}
        suggestions = ["Try fixing the file", "Check the documentation"]

        error = PrePrimerError(
            "Error message", context=context, suggestions=suggestions
        )

        assert error.context == context
        assert error.suggestions == suggestions

    def test_add_context_method(self):
        """Test adding context dynamically."""
        error = PrePrimerError("Test message")
        error.add_context(file="test.txt", line=42)

        assert error.context["file"] == "test.txt"
        assert error.context["line"] == 42

    def test_add_suggestion_method(self):
        """Test adding suggestions dynamically."""
        error = PrePrimerError("Test message")
        error.add_suggestion("First suggestion")
        error.add_suggestion("Second suggestion")

        assert len(error.suggestions) == 2
        assert "First suggestion" in error.suggestions
        assert "Second suggestion" in error.suggestions

    def test_get_user_message_with_suggestions(self):
        """Test user message formatting with suggestions."""
        error = PrePrimerError(
            "Technical message",
            user_message="User message",
            suggestions=["Suggestion 1", "Suggestion 2"],
        )

        user_msg = error.get_user_message()
        assert "User message" in user_msg
        assert "Suggestions:" in user_msg
        assert "• Suggestion 1" in user_msg
        assert "• Suggestion 2" in user_msg

    def test_error_logging(self):
        """Test that errors are properly logged."""
        with patch("preprimer.core.exceptions.logger") as mock_logger:
            error = PrePrimerError("Test error")

            # Check that error was logged
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "PrePrimerError: Test error" in call_args[0][0]

    def test_method_chaining(self):
        """Test that methods return self for chaining."""
        error = PrePrimerError("Test message")
        result = error.add_context(file="test.txt").add_suggestion("Try this")

        assert result is error
        assert error.context["file"] == "test.txt"
        assert "Try this" in error.suggestions


class TestSpecificErrorTypes:
    """Test specific error type implementations."""

    def test_parser_error_defaults(self):
        """Test ParserError default behavior."""
        error = ParserError("Parse failed", file_path="test.txt")

        assert "Parse failed" in error.technical_message
        assert "Failed to parse primer file test.txt" in error.user_message
        assert error.context["file_path"] == "test.txt"

    def test_parser_error_custom_message(self):
        """Test ParserError with custom user message."""
        error = ParserError(
            "Parse failed",
            file_path="test.txt",
            user_message="Custom parse error message",
        )

        assert error.user_message == "Custom parse error message"

    def test_validation_error_with_field(self):
        """Test ValidationError with field context."""
        error = ValidationError("Invalid value", field="primer_name", value="ABC123")

        assert error.context["field"] == "primer_name"
        assert error.context["value"] == "ABC123"
        assert "Validation failed for primer_name" in error.user_message

    def test_security_error_special_logging(self):
        """Test SecurityError uses warning level logging."""
        with patch("preprimer.core.exceptions.logger") as mock_logger:
            error = SecurityError(
                "Path traversal detected", violation_type="path_traversal"
            )

            # Check that security error was logged as warning
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args
            assert "SECURITY:" in call_args[0][0]
            assert error.context["violation_type"] == "path_traversal"

    def test_file_not_found_error(self):
        """Test FileNotFoundError convenience class."""
        error = FileNotFoundError("/path/to/missing/file.txt")

        assert "Required file not found" in error.technical_message
        assert "File not found: /path/to/missing/file.txt" in error.user_message
        assert error.context["file_path"] == "/path/to/missing/file.txt"
        assert len(error.suggestions) > 0

    def test_invalid_format_error(self):
        """Test InvalidFormatError with expected format."""
        error = InvalidFormatError("test.txt", expected_format="VarVAMP")

        assert error.context["expected_format"] == "VarVAMP"
        assert "Expected VarVAMP format" in error.user_message
        assert error.context["file_path"] == "test.txt"

    def test_corrupted_data_error_with_details(self):
        """Test CorruptedDataError with details."""
        error = CorruptedDataError("data.txt", details="Invalid header format")

        assert "Invalid header format" in error.technical_message
        assert "corrupted or malformed" in error.user_message
        assert len(error.suggestions) > 0

    def test_insufficient_data_error_with_counts(self):
        """Test InsufficientDataError with count context."""
        error = InsufficientDataError(
            "Not enough primers", required_count=10, actual_count=3
        )

        assert error.context["required_count"] == 10
        assert error.context["actual_count"] == 3
        assert "Not enough primers" in error.user_message

    def test_alignment_error_with_tool(self):
        """Test AlignmentError with tool context."""
        error = AlignmentError("BLAST failed", tool="blast")

        assert error.context["alignment_tool"] == "blast"
        assert "Alignment failed with blast" in error.user_message
        assert any("BLAST" in suggestion for suggestion in error.suggestions)

    def test_output_error_with_path(self):
        """Test OutputError with output path."""
        error = OutputError(
            "Write failed", output_path="/tmp/output.txt", format_name="FASTA"
        )

        assert error.context["output_path"] == "/tmp/output.txt"
        assert error.context["format"] == "FASTA"
        assert "/tmp/output.txt" in error.user_message
        assert "write permissions" in " ".join(error.suggestions).lower()

    def test_config_error_with_file_and_setting(self):
        """Test ConfigError with file and setting context."""
        error = ConfigError(
            "Invalid setting", config_file="config.yaml", setting="max_primers"
        )

        assert error.context["config_file"] == "config.yaml"
        assert error.context["setting"] == "max_primers"
        assert "config.yaml" in error.user_message


class TestErrorContext:
    """Test the ErrorContext context manager."""

    def test_successful_operation(self):
        """Test ErrorContext with successful operation."""
        with patch("preprimer.core.exceptions.logging") as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            with ErrorContext("test operation"):
                # Successful operation
                pass

            # Should log start and completion
            mock_logger.debug.assert_any_call("Starting test operation")
            mock_logger.debug.assert_any_call("Completed test operation")

    def test_preprimer_error_passthrough(self):
        """Test ErrorContext passes through PrePrimerError."""
        with patch("preprimer.core.exceptions.logging") as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            with pytest.raises(ParserError):
                with ErrorContext("test operation"):
                    raise ParserError("Test parser error")

            # Should not log the PrePrimerError (it logs itself)
            mock_logger.error.assert_not_called()

    def test_unexpected_error_logging(self):
        """Test ErrorContext logs unexpected errors."""
        with patch("preprimer.core.exceptions.logging") as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            with pytest.raises(ValueError):
                with ErrorContext("test operation"):
                    raise ValueError("Unexpected error")

            # Should log the unexpected error
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Unexpected error in test operation" in call_args[0][0]


class TestErrorHandlingDecorator:
    """Test the error handling decorator."""

    def test_decorator_successful_operation(self):
        """Test decorator with successful operation."""

        @handle_common_exceptions("test function")
        def successful_function():
            return "success"

        result = successful_function()
        assert result == "success"

    def test_decorator_with_error(self):
        """Test decorator with error."""

        @handle_common_exceptions("test function")
        def failing_function():
            raise ValueError("Test error")

        with patch("preprimer.core.exceptions.logging") as mock_logging:
            mock_logger = Mock()
            mock_logging.getLogger.return_value = mock_logger

            with pytest.raises(ValueError):
                failing_function()

            # Should log the error
            mock_logger.error.assert_called_once()


class TestErrorHandlingIntegration:
    """Integration tests for error handling in real scenarios."""

    def test_parser_error_chain(self):
        """Test error chaining from parser to converter."""
        from preprimer.core.config import PrePrimerConfig
        from preprimer.core.converter import PrimerConverter

        converter = PrimerConverter()

        # Test with non-existent file
        with pytest.raises(FileNotFoundError) as exc_info:
            converter.convert(
                "/nonexistent/file.txt", "/tmp/output", output_formats=["fasta"]
            )

        error = exc_info.value
        assert isinstance(error, FileNotFoundError)
        assert "/nonexistent/file.txt" in error.technical_message
        assert "File not found" in error.user_message
        assert len(error.suggestions) > 0

    def test_format_detection_error(self):
        """Test format detection error with user-friendly message."""
        from preprimer.core.converter import PrimerConverter

        # Create a file that doesn't match any format
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".unknown", delete=False
        ) as f:
            f.write("This is not a valid primer file format\n")
            temp_path = f.name

        try:
            converter = PrimerConverter()
            with pytest.raises(InvalidFormatError) as exc_info:
                converter.convert(temp_path, "/tmp/output", output_formats=["fasta"])

            error = exc_info.value
            assert isinstance(error, InvalidFormatError)
            assert temp_path in error.technical_message
            assert "Could not detect the format" in error.user_message
            assert "Available formats:" in error.user_message
            assert len(error.suggestions) > 0

        finally:
            Path(temp_path).unlink()

    def test_varvamp_parser_enhanced_errors(self):
        """Test VarVAMP parser enhanced error messages."""
        from preprimer.parsers.varvamp_parser import VarVAMPParser

        # Create invalid VarVAMP file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Write invalid content
            f.write("invalid_header\tother_header\n")
            f.write("some_data\tmore_data\n")
            temp_path = f.name

        try:
            parser = VarVAMPParser()

            # Should reject during validation
            assert not parser.validate_file(temp_path)

            # Should raise detailed error during parsing
            with pytest.raises(InvalidFormatError) as exc_info:
                parser.parse(temp_path)

            error = exc_info.value
            assert "not in valid varvamp format" in error.user_message.lower()

        finally:
            Path(temp_path).unlink()

    def test_error_user_message_formatting(self):
        """Test that user messages are properly formatted and helpful."""
        # Test various error types for user-friendly messages
        errors_to_test = [
            ParserError("Technical error", file_path="test.txt"),
            ValidationError("Invalid data", field="primer_sequence"),
            SecurityError("Path traversal", violation_type="directory_traversal"),
            InvalidFormatError("test.txt", expected_format="ARTIC"),
            CorruptedDataError("test.txt", details="Malformed row"),
            InsufficientDataError("No primers found", required_count=1, actual_count=0),
        ]

        for error in errors_to_test:
            user_msg = error.get_user_message()

            # User message should be helpful
            assert len(user_msg) > 20  # Not too short
            assert not user_msg.startswith("Traceback")  # Not a stack trace
            assert "." in user_msg  # Proper sentence structure

            # Should have suggestions
            if error.suggestions:
                assert "Suggestions:" in user_msg
                assert "•" in user_msg  # Bullet points

    def test_context_preservation_through_error_chain(self):
        """Test that context is preserved when errors are wrapped."""
        original_error = ParserError("Original parsing error", file_path="test.txt")
        original_error.add_context(line_number=42, column=5)

        # Simulate error wrapping
        try:
            raise original_error
        except ParserError as e:
            wrapped_error = ValidationError(
                "Validation failed due to parsing error", context=e.context
            )
            wrapped_error.add_context(validation_stage="primer_check")

            # Should preserve original context and add new context
            assert wrapped_error.context["file_path"] == "test.txt"
            assert wrapped_error.context["line_number"] == 42
            assert wrapped_error.context["column"] == 5
            assert wrapped_error.context["validation_stage"] == "primer_check"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
