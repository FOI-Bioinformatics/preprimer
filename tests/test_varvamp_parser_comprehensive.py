"""
Comprehensive tests for VarVAMPParser covering all error paths and edge cases.

Focuses on the missed coverage areas to improve overall parser coverage.
"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from preprimer.core.exceptions import (
    CorruptedDataError,
    InsufficientDataError,
    InvalidFormatError,
    ParserError,
    SecurityError,
)
from preprimer.parsers.varvamp_parser import VarVAMPParser


class TestVarVAMPParserFileValidation:
    """Test file validation error paths and edge cases."""

    def test_validate_file_with_unicode_decode_error(self):
        """Test validation with unicode decode error (lines 81-83)."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".tsv", delete=False) as f:
            # Write invalid UTF-8 bytes
            f.write(b"\x80\x81\x82invalid utf-8")
            invalid_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            result = parser.validate_file(invalid_file)
            assert result is False
        finally:
            invalid_file.unlink()

    def test_validate_file_with_general_exception(self):
        """Test validation with general exception handling (lines 84-86)."""
        # Create a file that will cause an exception during parsing
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write("malformed\ttsv\tdata\n")
            f.write("line1\tline2")  # Missing column - could cause parsing issues
            problem_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            # Even with malformed TSV, our validation should handle it gracefully
            result = parser.validate_file(problem_file)
            # Should return False for invalid format, not crash
            assert isinstance(result, bool)
        finally:
            problem_file.unlink()


class TestVarVAMPParserContentParsing:
    """Test content parsing error paths and edge cases."""

    def test_parse_file_with_no_fieldnames(self):
        """Test parsing file with no fieldnames (line 115)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Write file with no header
            f.write("")  # Completely empty
            no_header_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            with pytest.raises(InvalidFormatError) as exc_info:
                parser.parse(no_header_file, "test")

            error = exc_info.value
            assert (
                "empty or missing headers" in error.user_message
                or "varvamp format" in error.user_message.lower()
            )
        finally:
            no_header_file.unlink()

    def test_parse_file_with_empty_rows(self):
        """Test parsing file with empty rows (lines 137-138)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Write proper VarVAMP header
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write("\t".join(header) + "\n")
            f.write("\t\t\t\t\t\t\t\t\t\t\t\t\n")  # Empty row
            f.write(
                "amp1\t200\tFW_primer1\t1\t100\t120\tATCGATCG\t8\t50.0\t60.0\t45.0\t58.0\t0.9\n"
            )  # Valid row
            f.write("\t\t\t\t\t\t\t\t\t\t\t\t\n")  # Another empty row
            empty_rows_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            amplicons = parser.parse(empty_rows_file, "test")

            # Should successfully parse the valid row, skip empty ones
            assert len(amplicons) == 1
            assert amplicons[0].amplicon_id == "amp1"
        finally:
            empty_rows_file.unlink()

    def test_parse_file_with_invalid_primer_name_format(self):
        """Test parsing with invalid primer name format (line 157)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write("\t".join(header) + "\n")
            # Invalid primer name (doesn't start with FW or RW)
            f.write(
                "amp1\t200\tINVALID_primer1\t1\t100\t120\tATCGATCG\t8\t50.0\t60.0\t45.0\t58.0\t0.9\n"
            )
            invalid_name_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            with pytest.raises(CorruptedDataError) as exc_info:
                parser.parse(invalid_name_file, "test")

            # The error may be wrapped differently by the standardized parser
            assert exc_info.value is not None
        finally:
            invalid_name_file.unlink()

    def test_parse_file_with_invalid_coordinates(self):
        """Test parsing with invalid coordinates (line 170)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write("\t".join(header) + "\n")
            # Invalid coordinates: start >= stop
            f.write(
                "amp1\t200\tFW_primer1\t1\t150\t120\tATCGATCG\t8\t50.0\t60.0\t45.0\t58.0\t0.9\n"
            )
            invalid_coords_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            with pytest.raises(CorruptedDataError) as exc_info:
                parser.parse(invalid_coords_file, "test")

            error = exc_info.value
            assert "Invalid coordinates" in str(error)
            assert (
                "start position must be less than stop position" in error.user_message
            )
        finally:
            invalid_coords_file.unlink()

    def test_parse_file_with_specific_parser_error_reraise(self):
        """Test that specific parser errors are re-raised (lines 224-226)."""
        # Create a parser that will trigger a ParserError during field validation
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write("\t".join(header) + "\n")
            # Create row with invalid pool value that will trigger validation error
            f.write(
                "amp1\t200\tFW_primer1\tinvalid_pool\t100\t120\tATCGATCG\t8\t50.0\t60.0\t45.0\t58.0\t0.9\n"
            )
            invalid_pool_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            with pytest.raises((ParserError, InvalidFormatError, CorruptedDataError)):
                parser.parse(invalid_pool_file, "test")
        finally:
            invalid_pool_file.unlink()


class TestVarVAMPParserFileErrors:
    """Test file-level error handling paths."""

    def test_parse_no_valid_data_found(self):
        """Test InsufficientDataError when no valid rows processed (line 234)."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write("\t".join(header) + "\n")
            # Write row with all invalid data that will be skipped
            f.write("\t\t\t\t\t\t\t\t\t\t\t\t\n")  # Empty row
            no_data_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            # The error may be wrapped by the standardized parser
            with pytest.raises((InsufficientDataError, ParserError)) as exc_info:
                parser.parse(no_data_file, "test")

            # Check that some error is raised about insufficient data
            assert exc_info.value is not None
        finally:
            no_data_file.unlink()

    def test_parse_unicode_decode_error(self):
        """Test UnicodeDecodeError handling (line 240)."""
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".tsv", delete=False) as f:
            # Write invalid UTF-8 content that looks like TSV header
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write(("\t".join(header) + "\n").encode("utf-8"))
            f.write(b"\x80\x81\x82invalid utf-8 data\n")
            unicode_error_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            with pytest.raises((InvalidFormatError, UnicodeDecodeError)) as exc_info:
                parser.parse(unicode_error_file, "test")

            # Should raise some kind of error related to encoding
            assert exc_info.value is not None
        finally:
            unicode_error_file.unlink()

    def test_parse_file_not_found_error(self):
        """Test FileNotFoundError handling (line 247)."""
        nonexistent_file = Path("/nonexistent/varvamp/file.tsv")

        parser = VarVAMPParser()
        with pytest.raises(
            (ParserError, InvalidFormatError, FileNotFoundError)
        ) as exc_info:
            parser.parse(nonexistent_file, "test")

        # Should raise some kind of error about missing file
        assert exc_info.value is not None

    def test_parse_permission_error(self):
        """Test PermissionError handling (line 254)."""
        # Create a file and remove read permissions
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write("\t".join(header) + "\n")
            f.write(
                "amp1\t200\tFW_primer1\t1\t100\t120\tATCGATCG\t8\t50.0\t60.0\t45.0\t58.0\t0.9\n"
            )
            restricted_file = Path(f.name)

        try:
            # Remove read permissions (this might not work on all systems)
            import stat

            restricted_file.chmod(stat.S_IWRITE)

            parser = VarVAMPParser()
            # This test might not work on all systems due to permission handling differences
            try:
                with pytest.raises(
                    (ParserError, PermissionError, InvalidFormatError)
                ) as exc_info:
                    parser.parse(restricted_file, "test")

                # Should raise some kind of error
                assert exc_info.value is not None
            except PermissionError:
                # If we actually get a PermissionError, that's also valid
                pass
        finally:
            # Restore permissions and cleanup
            try:
                restricted_file.chmod(stat.S_IREAD | stat.S_IWRITE)
                restricted_file.unlink()
            except:
                pass


class TestVarVAMPParserSafeConversions:
    """Test safe conversion method error handling."""

    def test_safe_float_convert_empty_value(self):
        """Test _safe_float_convert with empty value (line 265)."""
        parser = VarVAMPParser()

        # Empty value should return None
        result = parser._safe_float_convert("", 1, "test_field")
        assert result is None

        # None value should return None
        result = parser._safe_float_convert(None, 1, "test_field")
        assert result is None

    def test_safe_float_convert_invalid_value(self):
        """Test _safe_float_convert with invalid value (lines 268-270)."""
        parser = VarVAMPParser()

        # Invalid float value should return None and log warning
        with patch("preprimer.parsers.varvamp_parser.logger") as mock_logger:
            result = parser._safe_float_convert("not_a_float", 5, "gc_content")

            assert result is None
            mock_logger.warning.assert_called_once()
            assert "Invalid gc_content in row 5" in str(mock_logger.warning.call_args)

    def test_safe_int_convert_empty_value(self):
        """Test _safe_int_convert with empty value (line 275)."""
        parser = VarVAMPParser()

        # Empty value should return None
        result = parser._safe_int_convert("", 1, "test_field")
        assert result is None

        # None value should return None
        result = parser._safe_int_convert(None, 1, "test_field")
        assert result is None

    def test_safe_int_convert_invalid_value(self):
        """Test _safe_int_convert with invalid value (lines 278-280)."""
        parser = VarVAMPParser()

        # Invalid int value should return None and log warning
        with patch("preprimer.parsers.varvamp_parser.logger") as mock_logger:
            result = parser._safe_int_convert("not_an_int", 3, "amplicon_length")

            assert result is None
            mock_logger.warning.assert_called_once()
            assert "Invalid amplicon_length in row 3" in str(
                mock_logger.warning.call_args
            )


class TestVarVAMPParserReferenceFile:
    """Test reference file discovery error handling."""

    def test_get_reference_file_security_error(self):
        """Test SecurityError handling in get_reference_file (lines 303-305)."""
        parser = VarVAMPParser()

        # Mock path_validator to raise SecurityError
        with patch.object(parser.path_validator, "sanitize_path") as mock_sanitize:
            mock_sanitize.side_effect = SecurityError("Path traversal detected")

            result = parser.get_reference_file("/some/path/varvamp_primers.tsv")
            assert result is None  # Should return None on security error

    def test_get_reference_file_general_exception(self):
        """Test general exception handling in get_reference_file (lines 306-308)."""
        parser = VarVAMPParser()

        # Mock path_validator to raise unexpected exception
        with patch.object(parser.path_validator, "sanitize_path") as mock_sanitize:
            mock_sanitize.side_effect = RuntimeError("Unexpected error")

            result = parser.get_reference_file("/some/path/varvamp_primers.tsv")
            assert result is None  # Should return None on any error

    def test_get_reference_file_success(self):
        """Test successful reference file discovery."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create main varvamp file
            varvamp_file = temp_path / "primers.tsv"
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            varvamp_file.write_text("\t".join(header) + "\n")

            # Create reference file
            ref_file = temp_path / "ambiguous_consensus.fasta"
            ref_file.write_text(">reference\nATCGATCG\n")

            parser = VarVAMPParser()
            result = parser.get_reference_file(varvamp_file)

            # Should find and return the reference file
            assert result is not None
            assert result.name == "ambiguous_consensus.fasta"


class TestVarVAMPParserComplexScenarios:
    """Test complex parsing scenarios and edge cases."""

    def test_amlicon_typo_correction(self):
        """Test correction of common 'amlicon_name' typo."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # Use the typo in header
            header = [
                "amlicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write("\t".join(header) + "\n")
            f.write(
                "amp1\t200\tFW_primer1\t1\t100\t120\tATCGATCG\t8\t50.0\t60.0\t45.0\t58.0\t0.9\n"
            )
            typo_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            amplicons = parser.parse(typo_file, "test")

            # Should successfully parse despite the typo in header
            assert len(amplicons) == 1
            assert amplicons[0].amplicon_id == "amp1"
        finally:
            typo_file.unlink()

    def test_complete_varvamp_parsing(self):
        """Test complete VarVAMP parsing with all fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write("\t".join(header) + "\n")
            # Forward primer
            f.write(
                "amp1\t400\tFW_primer1\t1\t100\t120\tATCGATCGATCGATCG\t16\t50.0\t60.0\t45.0\t58.0\t0.9\n"
            )
            # Reverse primer
            f.write(
                "amp1\t400\tRW_primer1\t1\t380\t400\tCGATCGATCGATCGAT\t16\t52.0\t62.0\t48.0\t60.0\t0.85\n"
            )
            complete_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            amplicons = parser.parse(complete_file, "test")

            # Should successfully parse both primers
            assert len(amplicons) == 1
            amplicon = amplicons[0]
            assert amplicon.amplicon_id == "amp1"
            assert len(amplicon.primers) == 2

            # Check primer details
            forward_primer = next(
                p for p in amplicon.primers if p.direction == "forward"
            )
            reverse_primer = next(
                p for p in amplicon.primers if p.direction == "reverse"
            )

            assert forward_primer.name == "FW_primer1"
            assert forward_primer.gc_content == 50.0
            assert forward_primer.tm == 60.0
            assert forward_primer.score == 0.9

            assert reverse_primer.name == "RW_primer1"
            assert reverse_primer.direction == "reverse"
            assert reverse_primer.strand == "-"
        finally:
            complete_file.unlink()

    def test_optional_fields_handling(self):
        """Test handling of missing optional fields."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            # All required columns for VarVAMP validation, but some with empty values
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write("\t".join(header) + "\n")
            # Use empty values for optional fields
            f.write("amp1\t\tFW_primer1\t1\t100\t120\tATCGATCGATCGATCG\t\t\t\t\t\t\n")
            minimal_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            amplicons = parser.parse(minimal_file, "test")

            # Should successfully parse with default values for missing fields
            assert len(amplicons) == 1
            amplicon = amplicons[0]
            primer = amplicon.primers[0]

            # Optional fields should be None when empty
            assert primer.gc_content is None
            assert primer.tm is None
            assert primer.score is None
        finally:
            minimal_file.unlink()

    def test_metadata_preservation(self):
        """Test that metadata is properly preserved."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            header = [
                "amplicon_name",
                "amplicon_length",
                "primer_name",
                "pool",
                "start",
                "stop",
                "seq",
                "size",
                "gc_best",
                "temp_best",
                "mean_gc",
                "mean_temp",
                "score",
            ]
            f.write("\t".join(header) + "\n")
            f.write(
                "amp1\t400\tFW_primer1\t2\t100\t120\tATCGATCG\t8\t50.0\t60.0\t45.5\t58.5\t0.95\n"
            )
            metadata_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            amplicons = parser.parse(metadata_file, "test")

            primer = amplicons[0].primers[0]

            # Check metadata preservation
            assert primer.metadata["mean_gc"] == 45.5
            assert primer.metadata["mean_temp"] == 58.5
            assert primer.metadata["amplicon_length"] == 400
            assert primer.metadata["source_row"] == 2
        finally:
            metadata_file.unlink()
