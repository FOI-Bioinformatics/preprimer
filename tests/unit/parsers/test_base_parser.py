"""
Abstract base class for parser tests.

All parser tests should inherit from BaseParserTest to ensure consistent
testing of the StandardizedParser interface contract.

Usage:
    class TestMyParser(BaseParserTest):
        parser_class = MyParser
        valid_test_file = Path("tests/test_data/datasets/small/myformat/file.ext")
        expected_amplicon_count = 5
        expected_format_name = "myformat"
        expected_extensions = [".ext"]

        # Optionally override or add parser-specific tests
        def test_myformat_specific_feature(self):
            # Custom test
            pass
"""

import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Type

import pytest

from preprimer.core.exceptions import InvalidFormatError, ParserError, SecurityError
from preprimer.core.standardized_parser import StandardizedParser


class BaseParserTest(ABC):
    """
    Abstract base class for testing parsers.

    Subclasses must define:
    - parser_class: The parser class to test
    - valid_test_file: Path to a valid test file
    - expected_amplicon_count: Number of amplicons in valid_test_file
    - expected_format_name: Expected format name (e.g., "varvamp", "artic")
    - expected_extensions: List of valid file extensions (e.g., [".tsv", ".txt"])
    """

    # =========================================================================
    # Subclass must define these
    # =========================================================================

    @property
    @abstractmethod
    def parser_class(self) -> Type[StandardizedParser]:
        """The parser class to test."""
        pass

    @property
    @abstractmethod
    def valid_test_file(self) -> Path:
        """Path to a valid test file for this parser."""
        pass

    @property
    @abstractmethod
    def expected_amplicon_count(self) -> int:
        """Expected number of amplicons in valid_test_file."""
        pass

    @property
    @abstractmethod
    def expected_format_name(self) -> str:
        """Expected format name (e.g., 'varvamp', 'artic')."""
        pass

    @property
    @abstractmethod
    def expected_extensions(self) -> List[str]:
        """Expected file extensions (e.g., ['.tsv', '.bed'])."""
        pass

    # =========================================================================
    # Optional: Override these for parser-specific behavior
    # =========================================================================

    def get_invalid_test_files(self) -> List[Path]:
        """Return list of paths to invalid test files (different formats)."""
        # Default: empty list, subclasses can override
        return []

    # =========================================================================
    # Fixtures
    # =========================================================================

    @pytest.fixture
    def parser(self):
        """Create parser instance."""
        return self.parser_class()

    # =========================================================================
    # Contract Tests - All parsers MUST pass these
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.parser
    @pytest.mark.contract
    def test_parser_has_required_methods(self):
        """Parser must implement all required methods."""
        required_methods = [
            "parse",
            "validate_file",
            "format_name",
            "file_extensions",
            "get_reference_file",
        ]

        for method_name in required_methods:
            assert hasattr(
                self.parser_class, method_name
            ), f"Parser missing required method: {method_name}"
            assert callable(
                getattr(self.parser_class, method_name)
            ), f"Parser method not callable: {method_name}"

    @pytest.mark.unit
    @pytest.mark.parser
    @pytest.mark.contract
    def test_format_name_returns_string(self):
        """format_name() must return a non-empty string."""
        format_name = self.parser_class.format_name()

        assert isinstance(format_name, str), "format_name must return string"
        assert len(format_name) > 0, "format_name must not be empty"
        assert (
            format_name == self.expected_format_name
        ), f"Expected format name '{self.expected_format_name}', got '{format_name}'"

    @pytest.mark.unit
    @pytest.mark.parser
    @pytest.mark.contract
    def test_file_extensions_returns_list(self):
        """file_extensions() must return a non-empty list."""
        extensions = self.parser_class.file_extensions()

        assert isinstance(extensions, list), "file_extensions must return list"
        assert len(extensions) > 0, "file_extensions must not be empty"
        assert all(
            isinstance(ext, str) for ext in extensions
        ), "All extensions must be strings"
        assert all(
            ext.startswith(".") for ext in extensions
        ), "All extensions must start with '.'"
        assert set(extensions) == set(
            self.expected_extensions
        ), f"Expected extensions {self.expected_extensions}, got {extensions}"

    # =========================================================================
    # File Validation Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.parser
    def test_validate_file_accepts_valid_file(self, parser):
        """Parser must accept valid files of its format."""
        assert (
            self.valid_test_file.exists()
        ), f"Test file does not exist: {self.valid_test_file}"

        result = parser.validate_file(self.valid_test_file)

        assert result is True, f"Parser rejected valid {self.expected_format_name} file"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_validate_file_rejects_invalid_files(self, parser):
        """Parser must reject files of other formats."""
        invalid_files = self.get_invalid_test_files()

        if not invalid_files:
            pytest.skip("No invalid test files provided")

        for invalid_file in invalid_files:
            if not invalid_file.exists():
                continue

            result = parser.validate_file(invalid_file)
            assert (
                result is False
            ), f"Parser accepted invalid file: {invalid_file.name}"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_validate_file_handles_nonexistent_file(self, parser):
        """Parser must handle nonexistent files gracefully."""
        nonexistent = Path("/nonexistent/file.txt")

        result = parser.validate_file(nonexistent)

        assert result is False, "Parser should return False for nonexistent file"

    @pytest.mark.unit
    @pytest.mark.parser
    @pytest.mark.security
    def test_validate_file_handles_malformed_utf8(self, parser):
        """Parser must handle malformed UTF-8 files gracefully."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".tmp", delete=False) as f:
            # Write invalid UTF-8 bytes
            f.write(b"\x80\x81\x82invalid utf-8\x90\x91")
            malformed_file = Path(f.name)

        try:
            result = parser.validate_file(malformed_file)
            # Should return False, not crash
            assert isinstance(result, bool), "validate_file should return bool"
        finally:
            malformed_file.unlink()

    # =========================================================================
    # Parsing Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_valid_file_returns_amplicons(self, parser):
        """Parser must successfully parse valid files."""
        amplicons = parser.parse(self.valid_test_file, prefix="test")

        assert isinstance(amplicons, list), "parse() must return list"
        assert (
            len(amplicons) == self.expected_amplicon_count
        ), f"Expected {self.expected_amplicon_count} amplicons, got {len(amplicons)}"

        # Verify amplicon structure
        for amp in amplicons:
            assert hasattr(amp, "amplicon_id"), "Amplicon missing amplicon_id"
            assert hasattr(amp, "primers"), "Amplicon missing primers"
            assert isinstance(amp.primers, list), "Amplicon.primers must be list"
            assert len(amp.primers) > 0, "Amplicon must have at least one primer"

    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_with_prefix(self, parser):
        """Parser must apply prefix (to amplicon IDs or reference IDs)."""
        prefix = "TEST_PREFIX"
        amplicons = parser.parse(self.valid_test_file, prefix=prefix)

        # Prefix should be applied somewhere - either amplicon_id or reference_id
        for amp in amplicons:
            assert (
                amp.amplicon_id.startswith(prefix) or amp.reference_id == prefix
            ), f"Prefix '{prefix}' should be in amplicon_id or reference_id"

    @pytest.mark.unit
    @pytest.mark.parser
    @pytest.mark.security
    def test_parse_nonexistent_file_raises_error(self, parser):
        """Parser must raise error for nonexistent files."""
        nonexistent = Path("/nonexistent/file.txt")

        with pytest.raises((ParserError, InvalidFormatError, SecurityError)):
            parser.parse(nonexistent, prefix="test")

    @pytest.mark.unit
    @pytest.mark.parser
    def test_parse_empty_file_raises_error(self, parser):
        """Parser must raise error for empty files."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=self.expected_extensions[0], delete=False
        ) as f:
            # Write nothing - empty file
            f.write("")
            empty_file = Path(f.name)

        try:
            with pytest.raises((ParserError, InvalidFormatError)):
                parser.parse(empty_file, prefix="test")
        finally:
            empty_file.unlink()

    # =========================================================================
    # Security Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.parser
    @pytest.mark.security
    @pytest.mark.parametrize(
        "dangerous_path",
        [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../../../../root/.ssh/id_rsa",
        ],
    )
    def test_parse_rejects_path_traversal(self, parser, dangerous_path):
        """Parser must reject path traversal attempts."""
        with pytest.raises(SecurityError, match="[Pp]ath"):
            parser.parse(dangerous_path, prefix="test")

    # =========================================================================
    # Performance Tests (optional benchmarks)
    # =========================================================================

    @pytest.mark.performance
    @pytest.mark.parser
    def test_parse_performance(self, parser, benchmark):
        """Benchmark parser performance on valid file."""
        # Only run if pytest-benchmark is available
        result = benchmark(parser.parse, self.valid_test_file, "bench")

        assert isinstance(result, list), "parse() must return list"
        assert (
            len(result) == self.expected_amplicon_count
        ), "Benchmark must return correct amplicon count"

    # =========================================================================
    # Reference File Tests
    # =========================================================================

    @pytest.mark.unit
    @pytest.mark.parser
    def test_get_reference_file_returns_path_or_none(self, parser):
        """get_reference_file() must return Path or None."""
        result = parser.get_reference_file(self.valid_test_file)

        assert result is None or isinstance(
            result, Path
        ), "get_reference_file must return Path or None"
