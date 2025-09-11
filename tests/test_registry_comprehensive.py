"""
Comprehensive tests for registry module targeting missed coverage lines.
"""

from pathlib import Path
from typing import List
from unittest.mock import MagicMock, Mock, patch

import pytest

from preprimer.core.exceptions import OutputError, ParserError
from preprimer.core.interfaces import AlignmentProvider, OutputWriter, PrimerParser
from preprimer.core.registry import (
    AlignmentRegistry,
    ParserRegistry,
    WriterRegistry,
    alignment_registry,
    parser_registry,
    writer_registry,
)


class TestParserRegistryEdgeCases:
    """Test error paths and edge cases in ParserRegistry."""

    def test_get_parser_nonexistent_format_error(self):
        """Test ParserError for nonexistent format (line 36)."""
        registry = ParserRegistry()

        with pytest.raises(
            ParserError, match="No parser registered for format: nonexistent"
        ):
            registry.get_parser("nonexistent")

    def test_detect_format_no_matching_parser(self):
        """Test format detection when no parser matches (line 56)."""
        registry = ParserRegistry()

        # Register a mock parser that always fails validation
        class FailingParser(PrimerParser):
            @classmethod
            def format_name(cls) -> str:
                return "failing"

            @classmethod
            def file_extensions(cls) -> List[str]:
                return [".fail"]

            def validate_file(self, file_path) -> bool:
                return False  # Always fails validation

            def parse(self, file_path, prefix=""):
                return []

        registry.register(FailingParser)

        # Create a test file that matches extension but fails validation
        test_file = Path("/tmp/test.fail")

        # Should return None when no parser validates the file
        result = registry.detect_format(test_file)
        assert result is None

    def test_detect_format_optimized_no_match(self):
        """Test optimized format detection when no format matches (lines 87-92)."""
        registry = ParserRegistry()

        # Register parsers that fail validation
        class FailingParser1(PrimerParser):
            @classmethod
            def format_name(cls) -> str:
                return "failing1"

            @classmethod
            def file_extensions(cls) -> List[str]:
                return [".fail1"]

            def validate_file(self, file_path) -> bool:
                return False

            def parse(self, file_path, prefix=""):
                return []

        class FailingParser2(PrimerParser):
            @classmethod
            def format_name(cls) -> str:
                return "failing2"

            @classmethod
            def file_extensions(cls) -> List[str]:
                return [".fail2"]

            def validate_file(self, file_path) -> bool:
                return False

            def parse(self, file_path, prefix=""):
                return []

        registry.register(FailingParser1)
        registry.register(FailingParser2)

        # Test file that doesn't match any extension
        test_file = Path("/tmp/test.unknown")

        # Should return None when no parser validates
        result = registry.detect_format_optimized(test_file)
        assert result is None

        # Test file that matches extension but fails validation
        test_file2 = Path("/tmp/test.fail1")
        result2 = registry.detect_format_optimized(test_file2)
        assert result2 is None


class TestWriterRegistryEdgeCases:
    """Test error paths and edge cases in WriterRegistry."""

    def test_get_writer_nonexistent_format_error(self):
        """Test OutputError for nonexistent format (line 125)."""
        registry = WriterRegistry()

        with pytest.raises(
            OutputError, match="No writer registered for format: nonexistent"
        ):
            registry.get_writer("nonexistent")

    def test_get_extension_nonexistent_format(self):
        """Test get_extension for nonexistent format returns empty string (lines 135-136)."""
        registry = WriterRegistry()

        # Should return empty string for nonexistent format
        extension = registry.get_extension("nonexistent")
        assert extension == ""


class TestAlignmentRegistryEdgeCases:
    """Test error paths and edge cases in AlignmentRegistry."""

    def test_get_provider_nonexistent_tool_error(self):
        """Test ParserError for nonexistent alignment tool (lines 156-163)."""
        registry = AlignmentRegistry()

        # Register some providers first to test the "Available" message
        class MockProvider1(AlignmentProvider):
            @classmethod
            def tool_name(cls) -> str:
                return "mock1"

            def is_available(self) -> bool:
                return True

            def align_primers(self, primers, reference_file):
                return []

            def create_amplicons(self, primers_file, reference_path, output_path):
                return None

        class MockProvider2(AlignmentProvider):
            @classmethod
            def tool_name(cls) -> str:
                return "mock2"

            def is_available(self) -> bool:
                return True

            def align_primers(self, primers, reference_file):
                return []

            def create_amplicons(self, primers_file, reference_path, output_path):
                return None

        registry.register(MockProvider1)
        registry.register(MockProvider2)

        with pytest.raises(ParserError) as exc_info:
            registry.get_provider("nonexistent")

        error_msg = str(exc_info.value)
        assert "No alignment provider for: nonexistent" in error_msg
        assert "Available:" in error_msg
        assert "mock1" in error_msg
        assert "mock2" in error_msg

    def test_list_providers_empty_registry(self):
        """Test list_providers with empty registry (line 167)."""
        registry = AlignmentRegistry()

        providers = registry.list_providers()
        assert providers == []

    def test_list_available_providers(self):
        """Test list_available_providers functionality (lines 171-176)."""
        registry = AlignmentRegistry()

        # Register providers with different availability
        class AvailableProvider(AlignmentProvider):
            @classmethod
            def tool_name(cls) -> str:
                return "available"

            def is_available(self) -> bool:
                return True

            def align_primers(self, primers, reference_file):
                return []

            def create_amplicons(self, primers_file, reference_path, output_path):
                return None

        class UnavailableProvider(AlignmentProvider):
            @classmethod
            def tool_name(cls) -> str:
                return "unavailable"

            def is_available(self) -> bool:
                return False

            def align_primers(self, primers, reference_file):
                return []

            def create_amplicons(self, primers_file, reference_path, output_path):
                return None

        registry.register(AvailableProvider)
        registry.register(UnavailableProvider)

        # Should only return available providers
        available = registry.list_available_providers()
        assert "available" in available
        assert "unavailable" not in available
        assert len(available) == 1


class TestGlobalRegistryInstances:
    """Test global registry instances functionality."""

    def test_global_registries_exist(self):
        """Test that global registry instances exist and are correct types."""
        # Test that global instances exist
        assert isinstance(parser_registry, ParserRegistry)
        assert isinstance(writer_registry, WriterRegistry)
        assert isinstance(alignment_registry, AlignmentRegistry)

    def test_global_parser_registry_functionality(self):
        """Test global parser registry basic functionality."""
        # Should have some parsers registered (from imports in __init__.py)
        formats = parser_registry.list_formats()
        assert isinstance(formats, list)
        # At least some formats should be registered
        assert len(formats) > 0

    def test_global_writer_registry_functionality(self):
        """Test global writer registry basic functionality."""
        # Should have some writers registered
        formats = writer_registry.list_formats()
        assert isinstance(formats, list)
        # At least some formats should be registered
        assert len(formats) > 0


class TestRegistryErrorHandling:
    """Test various error handling scenarios."""

    def test_parser_registry_with_invalid_parser_class(self):
        """Test registry behavior with edge cases."""
        registry = ParserRegistry()

        # Test case sensitivity in format names
        class TestParser(PrimerParser):
            @classmethod
            def format_name(cls) -> str:
                return "TEST"  # Uppercase

            @classmethod
            def file_extensions(cls) -> List[str]:
                return [".test"]

            def validate_file(self, file_path) -> bool:
                return True

            def parse(self, file_path, prefix=""):
                return []

        registry.register(TestParser)

        # Should be accessible by lowercase name due to normalization
        parser = registry.get_parser("test")
        assert isinstance(parser, TestParser)

        # Should also work with original case
        parser2 = registry.get_parser("TEST")
        assert isinstance(parser2, TestParser)

    def test_writer_registry_case_handling(self):
        """Test writer registry case normalization."""
        registry = WriterRegistry()

        class TestWriter(OutputWriter):
            @classmethod
            def format_name(cls) -> str:
                return "TEST"  # Uppercase

            @classmethod
            def file_extension(cls) -> str:
                return ".test"

            def write(self, primers, output_path, reference_file=None):
                pass

        registry.register(TestWriter)

        # Should be accessible by lowercase name
        writer = registry.get_writer("test")
        assert isinstance(writer, TestWriter)

        # Extension lookup should also work
        ext = registry.get_extension("test")
        assert ext == ".test"

        # Uppercase should also work
        ext2 = registry.get_extension("TEST")
        assert ext2 == ".test"

    def test_alignment_registry_case_handling(self):
        """Test alignment registry case normalization."""
        registry = AlignmentRegistry()

        class TestProvider(AlignmentProvider):
            @classmethod
            def tool_name(cls) -> str:
                return "TEST"  # Uppercase

            def is_available(self) -> bool:
                return True

            def align_primers(self, primers, reference_file):
                return []

            def create_amplicons(self, primers_file, reference_path, output_path):
                return None

        registry.register(TestProvider)

        # Should be accessible by lowercase name
        provider = registry.get_provider("test")
        assert isinstance(provider, TestProvider)

        # Should also work with original case
        provider2 = registry.get_provider("TEST")
        assert isinstance(provider2, TestProvider)


class TestRegistryEdgeCaseScenarios:
    """Test complex edge case scenarios."""

    def test_detect_format_with_file_validation_exception(self):
        """Test format detection when parser validation throws exception."""
        registry = ParserRegistry()

        class ExceptionParser(PrimerParser):
            @classmethod
            def format_name(cls) -> str:
                return "exception"

            @classmethod
            def file_extensions(cls) -> List[str]:
                return [".exc"]

            def validate_file(self, file_path) -> bool:
                # This could happen with file I/O errors, permission issues, etc.
                raise OSError("File validation failed")

            def parse(self, file_path, prefix=""):
                return []

        class WorkingParser(PrimerParser):
            @classmethod
            def format_name(cls) -> str:
                return "working"

            @classmethod
            def file_extensions(cls) -> List[str]:
                return [".work"]

            def validate_file(self, file_path) -> bool:
                return True

            def parse(self, file_path, prefix=""):
                return []

        registry.register(ExceptionParser)
        registry.register(WorkingParser)

        # Test with file that matches exception parser extension
        test_file = Path("/tmp/test.exc")

        # Format detection should handle the exception gracefully and continue
        # This tests the robustness of the detection logic
        # The current implementation lets exceptions propagate, so we expect OSError
        with patch.object(
            ExceptionParser, "validate_file", side_effect=OSError("Test error")
        ):
            with pytest.raises(OSError, match="Test error"):
                registry.detect_format(test_file)

    def test_empty_registries_behavior(self):
        """Test behavior of empty registries."""
        # Test empty parser registry
        empty_parser_registry = ParserRegistry()

        assert empty_parser_registry.list_formats() == []
        assert empty_parser_registry.list_extensions("any") == []
        assert empty_parser_registry.detect_format(Path("/tmp/test.txt")) is None
        assert (
            empty_parser_registry.detect_format_optimized(Path("/tmp/test.txt")) is None
        )

        # Test empty writer registry
        empty_writer_registry = WriterRegistry()

        assert empty_writer_registry.list_formats() == []
        assert empty_writer_registry.get_extension("any") == ""

        # Test empty alignment registry
        empty_alignment_registry = AlignmentRegistry()

        assert empty_alignment_registry.list_providers() == []
        assert empty_alignment_registry.list_available_providers() == []
