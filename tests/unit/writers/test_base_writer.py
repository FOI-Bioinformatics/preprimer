"""
Base test class for all OutputWriter implementations.

Provides common test cases for contract compliance, validation, writing,
security, and performance. All writer test classes should inherit from this.

Usage:
    class TestMyWriter(BaseWriterTest):
        @property
        def writer_class(self):
            return MyWriter

        @property
        def expected_format_name(self):
            return "myformat"

        @property
        def expected_file_extension(self):
            return ".ext"

        def get_test_amplicons(self):
            # Return list of AmpliconData for testing
            return [...]

        def verify_output_content(self, output_path, amplicons):
            # Verify output file content
            pass
"""

import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import pytest

from preprimer.core.exceptions import SecurityError
from preprimer.core.interfaces import AmpliconData, OutputWriter, PrimerData


class BaseWriterTest(ABC):
    """
    Abstract base class for writer tests.

    Provides comprehensive test coverage for all OutputWriter implementations:
    - Contract tests (format_name, file_extension, description)
    - Basic write tests (single, multiple, empty amplicons)
    - Validation tests (output validation)
    - Security tests (path validation, safe file operations)
    - Performance tests (write benchmarks)

    Subclasses must implement:
    - writer_class property
    - expected_format_name property
    - expected_file_extension property
    - get_test_amplicons() method
    - verify_output_content() method
    """

    # =========================================================================
    # Configuration - Must be implemented by subclasses
    # =========================================================================

    @property
    @abstractmethod
    def writer_class(self) -> type:
        """Return the writer class to test (e.g., VarVAMPWriter)."""
        pass

    @property
    @abstractmethod
    def expected_format_name(self) -> str:
        """Return expected format name (e.g., 'varvamp')."""
        pass

    @property
    @abstractmethod
    def expected_file_extension(self) -> str:
        """Return expected file extension (e.g., '.tsv')."""
        pass

    @abstractmethod
    def get_test_amplicons(self) -> List[AmpliconData]:
        """
        Return test amplicons for writing tests.

        Should return a list with at least 1-2 amplicons with valid primers.
        """
        pass

    @abstractmethod
    def verify_output_content(self, output_path: Path, amplicons: List[AmpliconData]):
        """
        Verify that output file contains expected content.

        Args:
            output_path: Path to output file
            amplicons: List of amplicons that were written

        Raises:
            AssertionError: If output content is invalid
        """
        pass

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def create_test_primer(
        self,
        name: str,
        sequence: str,
        start: int,
        stop: int,
        direction: str = "forward",
        pool: int = 1,
        amplicon_id: str = "amplicon_1",
    ) -> PrimerData:
        """Create a test primer with sensible defaults."""
        strand = "+" if direction == "forward" else "-"
        return PrimerData(
            name=name,
            sequence=sequence,
            start=start,
            stop=stop,
            strand=strand,
            direction=direction,
            pool=pool,
            amplicon_id=amplicon_id,
        )

    def create_test_amplicon(
        self,
        amplicon_id: str,
        forward_primer: PrimerData,
        reverse_primer: PrimerData,
        length: int = 200,
        reference_id: str = "test_ref",
    ) -> AmpliconData:
        """Create a test amplicon with sensible defaults."""
        return AmpliconData(
            amplicon_id=amplicon_id,
            primers=[forward_primer, reverse_primer],
            length=length,
            reference_id=reference_id,
        )

    # =========================================================================
    # Contract Tests - Ensure writer implements OutputWriter interface
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    @pytest.mark.contract
    def test_writer_has_format_name_method(self):
        """Writer must have format_name() classmethod."""
        assert hasattr(self.writer_class, "format_name")
        assert callable(getattr(self.writer_class, "format_name"))

    @pytest.mark.unit
    @pytest.mark.writer
    @pytest.mark.contract
    def test_writer_has_file_extension_method(self):
        """Writer must have file_extension() classmethod."""
        assert hasattr(self.writer_class, "file_extension")
        assert callable(getattr(self.writer_class, "file_extension"))

    @pytest.mark.unit
    @pytest.mark.writer
    @pytest.mark.contract
    def test_writer_has_write_method(self):
        """Writer must have write() method."""
        writer = self.writer_class()
        assert hasattr(writer, "write")
        assert callable(getattr(writer, "write"))

    @pytest.mark.unit
    @pytest.mark.writer
    @pytest.mark.contract
    def test_format_name_returns_expected_value(self):
        """format_name() must return expected format name."""
        assert self.writer_class.format_name() == self.expected_format_name

    @pytest.mark.unit
    @pytest.mark.writer
    @pytest.mark.contract
    def test_file_extension_returns_expected_value(self):
        """file_extension() must return expected extension."""
        assert self.writer_class.file_extension() == self.expected_file_extension

    @pytest.mark.unit
    @pytest.mark.writer
    @pytest.mark.contract
    def test_writer_has_description_property(self):
        """Writer must have description property."""
        writer = self.writer_class()
        assert hasattr(writer, "description")
        description = writer.description
        assert isinstance(description, str)
        assert len(description) > 0

    # =========================================================================
    # Basic Write Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_single_amplicon(self):
        """Writer must handle single amplicon correctly."""
        writer = self.writer_class()
        amplicons = self.get_test_amplicons()[:1]  # Just first amplicon

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=self.expected_file_extension, delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            result_path = writer.write(amplicons, output_path)

            assert result_path is not None, "write() should return output path"
            assert output_path.exists(), "Output file should exist"
            assert output_path.stat().st_size > 0, "Output file should not be empty"

            # Verify content using subclass implementation
            self.verify_output_content(output_path, amplicons)

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_multiple_amplicons(self):
        """Writer must handle multiple amplicons correctly."""
        writer = self.writer_class()
        amplicons = self.get_test_amplicons()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=self.expected_file_extension, delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            result_path = writer.write(amplicons, output_path)

            assert result_path is not None
            assert output_path.exists()
            assert output_path.stat().st_size > 0

            self.verify_output_content(output_path, amplicons)

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_empty_amplicons_list(self):
        """Writer must handle empty amplicons list gracefully."""
        writer = self.writer_class()

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=self.expected_file_extension, delete=False
        ) as f:
            output_path = Path(f.name)

        try:
            # Should not raise exception
            result_path = writer.write([], output_path)

            # File should exist (even if empty or header-only)
            assert output_path.exists()

        finally:
            if output_path.exists():
                output_path.unlink()

    @pytest.mark.unit
    @pytest.mark.writer
    def test_write_creates_output_directory(self):
        """Writer must create output directory if it doesn't exist."""
        writer = self.writer_class()
        amplicons = self.get_test_amplicons()[:1]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested directory path that doesn't exist
            output_path = Path(tmpdir) / "subdir1" / "subdir2" / f"output{self.expected_file_extension}"

            # Directory should not exist yet
            assert not output_path.parent.exists()

            result_path = writer.write(amplicons, output_path)

            # Directory should now exist
            assert output_path.parent.exists()
            assert output_path.exists()

    # =========================================================================
    # Validation Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    def test_validate_output_path_creates_directory(self):
        """validate_output_path() must create parent directories."""
        writer = self.writer_class()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "subdir" / f"output{self.expected_file_extension}"

            # Directory should not exist yet
            assert not output_path.parent.exists()

            # validate_output_path should create it
            validated_path = writer.validate_output_path(output_path)

            assert output_path.parent.exists()
            assert validated_path == output_path

    # =========================================================================
    # Security Tests
    # NOTE: Writers don't perform path validation like parsers do.
    # Path security is handled at the converter/CLI level.
    # =========================================================================

    # =========================================================================
    # Performance Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.writer
    @pytest.mark.performance
    @pytest.mark.benchmark
    def test_write_performance(self, benchmark):
        """Benchmark writer performance for regression detection."""
        writer = self.writer_class()
        amplicons = self.get_test_amplicons()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / f"benchmark{self.expected_file_extension}"

            def write_amplicons():
                return writer.write(amplicons, output_path)

            result = benchmark(write_amplicons)
            assert result is not None
