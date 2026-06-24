"""
Tests for the StandardizedParser base class and interface.
"""

import tempfile
from pathlib import Path
from typing import Dict, List
from unittest.mock import patch

import pytest

from preprimer.core.exceptions import InvalidFormatError, ParserError, SecurityError
from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.core.standardized_parser import StandardizedParser


class MockStandardizedParser(StandardizedParser):
    """Mock implementation of StandardizedParser for testing."""

    @classmethod
    def format_name(cls) -> str:
        return "mock"

    @classmethod
    def file_extensions(cls) -> List[str]:
        return [".mock"]

    def validate_file(self, file_path) -> bool:
        """Mock validation - always returns True for testing."""
        return True

    def _parse_file_content(
        self, file_path: Path, prefix: str
    ) -> Dict[str, AmpliconData]:
        """Mock file content parsing for testing."""
        # Create mock amplicon data using standardized methods
        primer1 = self._create_primer_data(
            name="TEST_1_F",
            sequence="ATCG",
            start=1,
            stop=5,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amp_1",
            reference_id=prefix or "mock_ref",
        )

        primer2 = self._create_primer_data(
            name="TEST_1_R",
            sequence="CGAT",
            start=100,
            stop=104,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="test_amp_1",
            reference_id=prefix or "mock_ref",
        )

        amplicon = AmpliconData(
            amplicon_id="test_amp_1",
            primers=[primer1, primer2],
            reference_id=prefix or "mock_ref",
        )

        return {"test_amp_1": amplicon}


class TestStandardizedParserInterface:
    """Test the StandardizedParser interface functionality."""

    def test_initialization(self):
        """Test StandardizedParser initialization."""
        parser = MockStandardizedParser()

        # Check that validators are initialized
        assert hasattr(parser, "path_validator")
        assert hasattr(parser, "input_validator")
        assert parser.format_name() == "mock"
        assert parser.file_extensions() == [".mock"]

    def test_successful_parse(self):
        """Test successful parsing with standardized interface."""
        parser = MockStandardizedParser()

        # Create a temporary mock file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mock", delete=False) as f:
            f.write("mock content")
            temp_path = f.name

        try:
            # Test parsing
            amplicons = parser.parse(temp_path, "test_prefix")

            # Verify results
            assert len(amplicons) == 1
            assert amplicons[0].amplicon_id == "test_amp_1"
            assert amplicons[0].reference_id == "test_prefix"
            assert len(amplicons[0].primers) == 2

            # Verify metadata was added
            for primer in amplicons[0].primers:
                assert primer.metadata["parser"] == "mock"
                assert primer.metadata["validated"] is True

        finally:
            Path(temp_path).unlink()

    def test_input_validation(self):
        """Test input validation in standardized interface."""
        parser = MockStandardizedParser()

        # Test with invalid prefix by mocking the validator
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mock", delete=False) as f:
            f.write("mock content")
            temp_path = f.name

        try:
            with patch.object(
                parser.input_validator,
                "validate_amplicon_name",
                side_effect=SecurityError("Invalid amplicon name"),
            ):
                with pytest.raises(SecurityError):
                    parser.parse(temp_path, "invalid_prefix")

            # Test with obviously malicious path
            with patch.object(
                parser.path_validator,
                "sanitize_path",
                side_effect=SecurityError("Path traversal detected"),
            ):
                with pytest.raises(SecurityError):
                    parser.parse("../../../etc/passwd")

        finally:
            Path(temp_path).unlink()

    def test_file_validation_failure(self):
        """Test behavior when file validation fails."""
        parser = MockStandardizedParser()

        # Mock validate_file to return False
        with patch.object(parser, "validate_file", return_value=False):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mock", delete=False
            ) as f:
                f.write("invalid content")
                temp_path = f.name

            try:
                with pytest.raises(InvalidFormatError, match="Invalid format for file"):
                    parser.parse(temp_path)

            finally:
                Path(temp_path).unlink()

    def test_validate_required_fields(self):
        """Test required field validation."""
        parser = MockStandardizedParser()

        # Test with all fields present
        row = {"field1": "value1", "field2": "value2", "field3": "value3"}
        required_fields = ["field1", "field2", "field3"]

        # Should not raise exception
        parser._validate_required_fields(row, required_fields, 1)

        # Test with missing field
        incomplete_row = {"field1": "value1", "field2": ""}
        with pytest.raises(ParserError, match="Missing required field 'field2'"):
            parser._validate_required_fields(incomplete_row, required_fields, 2)

        # Test with completely missing field
        incomplete_row2 = {"field1": "value1"}
        with pytest.raises(ParserError, match="Missing required field 'field2'"):
            parser._validate_required_fields(incomplete_row2, required_fields, 3)

    def test_sanitize_string_field(self):
        """Test string field sanitization."""
        parser = MockStandardizedParser()

        # Test normal string
        result = parser._sanitize_string_field("normal_string", "test_field", 1)
        assert result == "normal_string"

        # Test string that's too long
        long_string = "A" * 2000
        with pytest.raises(SecurityError, match="String too long"):
            parser._sanitize_string_field(long_string, "test_field", 1, max_length=1000)

    def test_validate_numeric_field(self):
        """Test numeric field validation."""
        parser = MockStandardizedParser()

        # Test valid integer
        result = parser._validate_numeric_field("42", "test_int", 1, int)
        assert result == 42

        # Test valid float
        result = parser._validate_numeric_field("3.14", "test_float", 1, float)
        assert result == 3.14

        # Test invalid numeric value
        with pytest.raises(ParserError, match="Invalid test_int in row 1"):
            parser._validate_numeric_field("not_a_number", "test_int", 1, int)

        # Test with range validation
        result = parser._validate_numeric_field(
            "50", "test_field", 1, int, min_value=0, max_value=100
        )
        assert result == 50

        # Test below minimum
        with pytest.raises(ParserError, match="cannot be less than 10"):
            parser._validate_numeric_field("5", "test_field", 1, int, min_value=10)

        # Test above maximum
        with pytest.raises(ParserError, match="cannot be greater than 100"):
            parser._validate_numeric_field("150", "test_field", 1, int, max_value=100)

    def test_validate_primer_data(self):
        """Test primer data validation."""
        parser = MockStandardizedParser()

        # Test valid primer data
        parser._validate_primer_data("TEST_F", "ATCG", 1, 5, 1)

        # Test negative coordinates
        with pytest.raises(ParserError, match="Negative coordinates"):
            parser._validate_primer_data("TEST_F", "ATCG", -1, 5, 1)

        # Test invalid coordinate order
        with pytest.raises(
            ParserError, match="Start position must be less than stop position"
        ):
            parser._validate_primer_data("TEST_F", "ATCG", 5, 1, 1)

        # Test invalid sequence (sequence with invalid characters)
        with patch.object(
            parser.input_validator,
            "validate_primer_sequence",
            side_effect=SecurityError("Invalid sequence"),
        ):
            with pytest.raises(ParserError, match="Invalid primer data"):
                parser._validate_primer_data("TEST_F", "INVALID", 1, 5, 1)

    def test_create_primer_data(self):
        """Test primer data creation with standardized metadata."""
        parser = MockStandardizedParser()

        primer = parser._create_primer_data(
            name="TEST_F",
            sequence="ATCG",
            start=1,
            stop=5,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amp",
            reference_id="test_ref",
            metadata={"custom": "value"},
        )

        # Check basic fields
        assert primer.name == "TEST_F"
        assert primer.sequence == "ATCG"
        assert primer.start == 1
        assert primer.stop == 5

        # Check standardized metadata was added
        assert primer.metadata["parser"] == "mock"
        assert primer.metadata["validated"] is True
        assert primer.metadata["custom"] == "value"  # Custom metadata preserved

    def test_finalize_amplicons(self):
        """Test amplicon finalization with validation."""
        parser = MockStandardizedParser()

        # Create test primers
        primer1 = PrimerData(
            name="TEST_F",
            sequence="ATCG",
            start=1,
            stop=5,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amp",
            reference_id="test_ref",
        )
        primer2 = PrimerData(
            name="TEST_R",
            sequence="CGAT",
            start=100,
            stop=104,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="test_amp",
            reference_id="test_ref",
        )

        amplicon = AmpliconData(
            amplicon_id="test_amp", primers=[primer1, primer2], reference_id="test_ref"
        )

        amplicons_dict = {"test_amp": amplicon}

        # Create mock genome info for testing
        from preprimer.core.topology import GenomeInfo, GenomeTopology

        genome_info = GenomeInfo("test", GenomeTopology.LINEAR, 30000)

        # Test finalization
        result = parser._finalize_amplicons(amplicons_dict, genome_info)

        assert len(result) == 1
        assert result[0].amplicon_id == "test_amp"
        assert result[0].length == 103  # max(104) - min(1) = 103

    def test_finalize_amplicons_empty(self):
        """Test finalization with empty amplicons dict."""
        parser = MockStandardizedParser()

        # Create mock genome info for testing
        from preprimer.core.topology import GenomeInfo, GenomeTopology

        genome_info = GenomeInfo("test", GenomeTopology.LINEAR, 30000)

        with pytest.raises(ParserError, match="No valid amplicons found"):
            parser._finalize_amplicons({}, genome_info)

    def test_logging_functionality(self):
        """Test standardized logging."""
        parser = MockStandardizedParser()

        # Create test data
        primer = PrimerData(
            name="TEST_F",
            sequence="ATCG",
            start=1,
            stop=5,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amp",
            reference_id="test_ref",
        )
        amplicon = AmpliconData(
            amplicon_id="test_amp", primers=[primer], reference_id="test_ref"
        )

        # Test logging (should not raise exception)
        with patch("preprimer.core.standardized_parser.logger") as mock_logger:
            parser._log_parse_results([amplicon])

            # Verify logging was called
            assert mock_logger.info.called

            # Check log message content
            log_calls = mock_logger.info.call_args_list
            assert any("Successfully parsed" in str(call) for call in log_calls)

    def test_error_handling_chain(self):
        """Test that errors are properly chained and contextualized."""
        parser = MockStandardizedParser()

        # Mock _parse_file_content to raise an exception
        with patch.object(
            parser, "_parse_file_content", side_effect=ValueError("Mock error")
        ):
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mock", delete=False
            ) as f:
                f.write("content")
                temp_path = f.name

            try:
                with pytest.raises(ParserError, match="Failed to parse mock file"):
                    parser.parse(temp_path)

            finally:
                Path(temp_path).unlink()

    def test_security_error_passthrough(self):
        """Test that SecurityErrors are properly passed through."""
        parser = MockStandardizedParser()

        # Test that SecurityError from sanitization passes through unchanged
        with patch.object(
            parser.input_validator,
            "sanitize_string",
            side_effect=SecurityError("Security violation"),
        ):
            with pytest.raises(SecurityError, match="Security violation"):
                parser._sanitize_string_field("test", "field", 1)


class TestStandardizedParserIntegration:
    """Integration tests for StandardizedParser with real parser implementations."""

    def test_varvamp_uses_standardized_interface(self):
        """Test that VarVAMP parser uses standardized interface correctly."""
        from preprimer.parsers.varvamp_parser import VarVAMPParser

        parser = VarVAMPParser()

        # Check that it inherits from StandardizedParser
        assert isinstance(parser, StandardizedParser)

        # Check that it has the required validators
        assert hasattr(parser, "path_validator")
        assert hasattr(parser, "input_validator")

        # Check that it implements the required methods
        assert hasattr(parser, "_parse_file_content")
        assert callable(parser._parse_file_content)

    def test_standardized_metadata_addition(self):
        """Test that standardized metadata is added to parsed data."""
        from preprimer.parsers.varvamp_parser import VarVAMPParser

        parser = VarVAMPParser()

        # Get test data path - use legacy ASFV_long data
        test_data_path = Path(__file__).parent / "test_data" / "legacy" / "ASFV_long"
        if not test_data_path.exists():
            pytest.skip("Legacy ASFV_long test data not available")
            return

        varvamp_files = list(test_data_path.glob("*.tsv"))
        if not varvamp_files:
            pytest.skip("No VarVAMP TSV files found in legacy data")
            return

        # Parse first available file
        amplicons = parser.parse(varvamp_files[0])

        # Check that standardized metadata was added
        assert len(amplicons) > 0
        for amplicon in amplicons:
            for primer in amplicon.primers:
                assert "parser" in primer.metadata
                assert primer.metadata["parser"] == "varvamp"
                assert "validated" in primer.metadata
                assert primer.metadata["validated"] is True
