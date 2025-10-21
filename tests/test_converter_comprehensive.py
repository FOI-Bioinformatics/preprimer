"""
Comprehensive tests for PrimerConverter error handling and edge cases.

Focuses on covering the missing error handling paths and edge cases
that aren't covered by existing integration tests.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from preprimer.core.converter import PrimerConverter
from preprimer.core.enhanced_config import EnhancedConfig
from preprimer.core.exceptions import (
    InvalidFormatError,
    OutputError,
    ParserError,
    ValidationError,
)
from preprimer.core.interfaces import AmpliconData, PrimerData


class TestPrimerConverterErrorHandling:
    """Test error handling paths in PrimerConverter."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = EnhancedConfig()
        self.converter = PrimerConverter(self.config)

        # Create test data with both forward and reverse primers
        self.forward_primer = PrimerData(
            name="test_primer_F",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amplicon",
        )

        self.reverse_primer = PrimerData(
            name="test_primer_R",
            sequence="CGATCGATCGATCGAT",
            start=300,
            stop=316,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="test_amplicon",
        )

        self.test_amplicon = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[self.forward_primer, self.reverse_primer],
            length=200,
            reference_id="test_ref",
        )

    @patch("preprimer.core.converter.parser_registry")
    def test_convert_parser_error_reraise(self, mock_registry):
        """Test that ParserError is re-raised as-is during parsing."""
        with tempfile.NamedTemporaryFile(suffix=".bed") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                # Setup mock parser that raises ParserError
                mock_parser = Mock()
                mock_parser.parse.side_effect = ParserError("Test parser error")
                mock_registry.detect_format.return_value = "artic"
                mock_registry.get_parser.return_value = mock_parser

                # Should re-raise ParserError as-is
                with pytest.raises(ParserError, match="Test parser error"):
                    self.converter.convert(
                        input_file=input_file.name,
                        output_dir=output_dir,
                        output_formats=["artic"],
                    )

    @patch("preprimer.core.converter.parser_registry")
    def test_convert_unexpected_parse_error_wrapped(self, mock_registry):
        """Test that unexpected parsing errors are wrapped in ParserError."""
        with tempfile.NamedTemporaryFile(suffix=".bed") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                # Setup mock parser that raises unexpected error
                mock_parser = Mock()
                mock_parser.parse.side_effect = ValueError("Unexpected parsing issue")
                mock_registry.detect_format.return_value = "artic"
                mock_registry.get_parser.return_value = mock_parser

                # Should wrap in ParserError
                with pytest.raises(ParserError) as exc_info:
                    self.converter.convert(
                        input_file=input_file.name,
                        output_dir=output_dir,
                        output_formats=["artic"],
                    )

                # Check error details
                error = exc_info.value
                assert "Unexpected error parsing artic file" in str(error)
                assert "Failed to parse" in error.user_message
                assert "Verify that" in str(error.suggestions[0])

    @patch("preprimer.core.converter.parser_registry")
    def test_convert_validation_error_reraise(self, mock_registry):
        """Test that ValidationError is re-raised as-is during validation."""
        with tempfile.NamedTemporaryFile(suffix=".bed") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                # Setup mock parser
                mock_parser = Mock()
                mock_parser.parse.return_value = [self.test_amplicon]
                mock_registry.detect_format.return_value = "artic"
                mock_registry.get_parser.return_value = mock_parser

                # Mock _validate_amplicons to raise ValidationError
                with patch.object(
                    self.converter, "_validate_amplicons"
                ) as mock_validate:
                    mock_validate.side_effect = ValidationError("Test validation error")

                    # Should re-raise ValidationError as-is
                    with pytest.raises(ValidationError, match="Test validation error"):
                        self.converter.convert(
                            input_file=input_file.name,
                            output_dir=output_dir,
                            output_formats=["artic"],
                        )

    @patch("preprimer.core.converter.parser_registry")
    def test_convert_unexpected_validation_error_wrapped(self, mock_registry):
        """Test that unexpected validation errors are wrapped in ValidationError."""
        with tempfile.NamedTemporaryFile(suffix=".bed") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                # Setup mock parser
                mock_parser = Mock()
                mock_parser.parse.return_value = [self.test_amplicon]
                mock_registry.detect_format.return_value = "artic"
                mock_registry.get_parser.return_value = mock_parser

                # Mock _validate_amplicons to raise unexpected error
                with patch.object(
                    self.converter, "_validate_amplicons"
                ) as mock_validate:
                    mock_validate.side_effect = RuntimeError(
                        "Unexpected validation issue"
                    )

                    # Should wrap in ValidationError
                    with pytest.raises(ValidationError) as exc_info:
                        self.converter.convert(
                            input_file=input_file.name,
                            output_dir=output_dir,
                            output_formats=["artic"],
                        )

                    # Check error details
                    error = exc_info.value
                    assert "Unexpected error during amplicon validation" in str(error)
                    assert "Error validating parsed amplicon data" in error.user_message
                    assert "Check that the input data is complete and valid" in str(
                        error.suggestions[0]
                    )

    @patch("preprimer.core.converter.parser_registry")
    def test_convert_missing_reference_file_resolution(self, mock_registry):
        """Test reference file resolution when None is provided."""
        with tempfile.NamedTemporaryFile(suffix=".bed") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                # Create a mock reference file
                with tempfile.NamedTemporaryFile(
                    suffix=".fasta", delete=False
                ) as ref_file:
                    ref_file_path = Path(ref_file.name)

                try:
                    # Setup mock parser that can provide reference file
                    mock_parser = Mock()
                    mock_parser.parse.return_value = [self.test_amplicon]
                    mock_parser.get_reference_file.return_value = ref_file_path
                    mock_registry.detect_format.return_value = "artic"
                    mock_registry.get_parser.return_value = mock_parser

                    # Mock writer registry
                    with patch(
                        "preprimer.core.converter.writer_registry"
                    ) as mock_writer_reg:
                        mock_writer = Mock()
                        mock_writer.write.return_value = Path(output_dir) / "output.bed"
                        mock_writer_reg.get_writer.return_value = mock_writer

                        # Convert without providing reference file
                        result = self.converter.convert(
                            input_file=input_file.name,
                            output_dir=output_dir,
                            output_formats=["artic"],
                            reference_file=None,  # Should trigger resolution
                        )

                        # Should have resolved reference file
                        mock_parser.get_reference_file.assert_called_once_with(
                            Path(input_file.name)
                        )
                        # Writer should be called with resolved reference
                        mock_writer.write.assert_called()
                        write_call = mock_writer.write.call_args
                        assert write_call.kwargs.get("reference_path") == ref_file_path

                finally:
                    ref_file_path.unlink(missing_ok=True)

    @patch("preprimer.core.converter.parser_registry")
    @patch("preprimer.core.converter.writer_registry")
    def test_convert_file_exists_no_force_error(self, mock_writer_reg, mock_registry):
        """Test OutputError when output file exists and force=False."""
        with tempfile.NamedTemporaryFile(suffix=".bed") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                # Create existing output file with ARTIC format structure
                existing_output = (
                    Path(output_dir) / "artic" / "primers" / "V1" / "primers.scheme.bed"
                )
                existing_output.parent.mkdir(parents=True, exist_ok=True)
                existing_output.write_text("existing content")

                # Setup mocks
                mock_parser = Mock()
                mock_parser.parse.return_value = [self.test_amplicon]
                mock_parser.get_reference_file.return_value = None
                mock_registry.detect_format.return_value = "artic"
                mock_registry.get_parser.return_value = mock_parser

                mock_writer = Mock()
                mock_writer_reg.get_writer.return_value = mock_writer

                # Setup config to not force overwrite
                self.config.output.force_overwrite = False

                # Mock writer to use the existing output path structure
                mock_writer.file_extension.return_value = ".bed"

                # Should raise OutputError
                with pytest.raises(OutputError) as exc_info:
                    self.converter.convert(
                        input_file=input_file.name,
                        output_dir=output_dir,
                        output_formats=["artic"],
                        force=False,
                    )

                error = exc_info.value
                assert "Output file exists" in str(error)
                assert "Use --force to overwrite" in str(error)

    @patch("preprimer.core.converter.parser_registry")
    @patch("preprimer.core.converter.writer_registry")
    def test_convert_file_exists_force_override_config(
        self, mock_writer_reg, mock_registry
    ):
        """Test that force parameter overrides config.output.force_overwrite=False."""
        with tempfile.NamedTemporaryFile(suffix=".bed") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                # Create existing output file with ARTIC format structure
                existing_output = (
                    Path(output_dir) / "artic" / "primers" / "V1" / "primers.scheme.bed"
                )
                existing_output.parent.mkdir(parents=True, exist_ok=True)
                existing_output.write_text("existing content")

                # Set config to not force overwrite
                self.config.output.force_overwrite = False

                # Setup mocks
                mock_parser = Mock()
                mock_parser.parse.return_value = [self.test_amplicon]
                mock_parser.get_reference_file.return_value = None
                mock_registry.detect_format.return_value = "artic"
                mock_registry.get_parser.return_value = mock_parser

                mock_writer = Mock()
                mock_writer.write.return_value = existing_output
                mock_writer_reg.get_writer.return_value = mock_writer

                # Mock writer to use the existing output path structure
                mock_writer.file_extension.return_value = ".bed"

                # Should succeed with force=True parameter
                result = self.converter.convert(
                    input_file=input_file.name,
                    output_dir=output_dir,
                    output_formats=["artic"],
                    force=True,  # Should override config
                )

                # Should complete successfully
                assert result is not None
                mock_writer.write.assert_called()

    @patch("preprimer.core.converter.parser_registry")
    @patch("preprimer.core.converter.writer_registry")
    def test_convert_writer_error_handling(self, mock_writer_reg, mock_registry):
        """Test error handling when writer fails."""
        with tempfile.NamedTemporaryFile(suffix=".bed") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                # Setup mocks
                mock_parser = Mock()
                mock_parser.parse.return_value = [self.test_amplicon]
                mock_parser.get_reference_file.return_value = None
                mock_registry.detect_format.return_value = "artic"
                mock_registry.get_parser.return_value = mock_parser

                # Mock writer that fails
                mock_writer = Mock()
                mock_writer.write.side_effect = OutputError("Test writer error")
                mock_writer.file_extension.return_value = ".bed"
                mock_writer_reg.get_writer.return_value = mock_writer

                # Should propagate OutputError
                with pytest.raises(OutputError, match="Test writer error"):
                    self.converter.convert(
                        input_file=input_file.name,
                        output_dir=output_dir,
                        output_formats=["artic"],
                    )

    @patch("preprimer.core.converter.parser_registry")
    def test_convert_format_detection_failure(self, mock_registry):
        """Test error when format cannot be detected."""
        with tempfile.NamedTemporaryFile(suffix=".unknown") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                # Mock failed format detection
                mock_registry.detect_format.return_value = None
                mock_registry.list_formats.return_value = ["artic", "varvamp", "olivar"]

                # Should raise InvalidFormatError
                with pytest.raises(InvalidFormatError) as exc_info:
                    self.converter.convert(
                        input_file=input_file.name,
                        output_dir=output_dir,
                        output_formats=["artic"],
                        input_format=None,  # Trigger auto-detection
                    )

                error = exc_info.value
                assert "Could not detect the format of" in error.user_message

    def test_validate_amplicons_empty_list(self):
        """Test validation error for empty amplicon list."""
        with pytest.raises(ValidationError) as exc_info:
            self.converter._validate_amplicons([])

        error = exc_info.value
        assert "No amplicons found in input file" in str(error)

    def test_validate_amplicons_no_primers(self):
        """Test validation error for amplicon with no primers."""
        # Create amplicon with no primers
        empty_amplicon = AmpliconData(
            amplicon_id="empty_amplicon",
            primers=[],
            length=200,
            reference_id="test_ref",
        )

        with pytest.raises(ValidationError) as exc_info:
            self.converter._validate_amplicons([empty_amplicon])

        error = exc_info.value
        assert "empty_amplicon has no primers" in str(error)

    def test_validate_amplicons_no_forward_primers(self):
        """Test validation error for amplicon with no forward primers."""
        # Create reverse primer only
        reverse_primer = PrimerData(
            name="reverse_only",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="test_amplicon",
        )

        reverse_only_amplicon = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[reverse_primer],
            length=200,
            reference_id="test_ref",
        )

        with pytest.raises(ValidationError) as exc_info:
            self.converter._validate_amplicons([reverse_only_amplicon])

        error = exc_info.value
        assert "test_amplicon has no forward primers" in str(error)

    def test_validate_amplicons_no_reverse_primers(self):
        """Test validation error for amplicon with no reverse primers."""
        # Create forward primer only
        forward_primer = PrimerData(
            name="forward_only",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amplicon",
        )

        forward_only_amplicon = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[forward_primer],
            length=200,
            reference_id="test_ref",
        )

        with pytest.raises(ValidationError) as exc_info:
            self.converter._validate_amplicons([forward_only_amplicon])

        error = exc_info.value
        assert "test_amplicon has no reverse primers" in str(error)

    def test_validate_amplicons_invalid_sequence_validation_disabled(self):
        """Test that invalid sequences are ignored when validation is disabled."""
        # Disable sequence validation in config
        self.config.validation.enabled = False

        # Create primer with invalid sequence
        invalid_primer = PrimerData(
            name="invalid_seq",
            sequence="ATCGXYZ",  # Invalid nucleotides
            start=100,
            stop=107,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amplicon",
        )

        valid_reverse = PrimerData(
            name="valid_reverse",
            sequence="ATCGATCG",
            start=200,
            stop=208,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="test_amplicon",
        )

        mixed_amplicon = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[invalid_primer, valid_reverse],
            length=200,
            reference_id="test_ref",
        )

        # Should not raise error when validation is disabled
        try:
            self.converter._validate_amplicons([mixed_amplicon])
        except ValidationError:
            pytest.fail(
                "Should not raise ValidationError when sequence validation is disabled"
            )

    @patch("preprimer.core.converter.writer_registry")
    def test_convert_single_format_successful(self, mock_writer_reg):
        """Test successful single format conversion (covering success paths)."""
        with tempfile.NamedTemporaryFile(suffix=".bed") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                output_file = Path(output_dir) / "output.bed"

                # Setup mocks
                with patch(
                    "preprimer.core.converter.parser_registry"
                ) as mock_parser_reg:
                    mock_parser = Mock()
                    mock_parser.parse.return_value = [self.test_amplicon]
                    mock_parser.get_reference_file.return_value = None
                    mock_parser_reg.detect_format.return_value = "artic"
                    mock_parser_reg.get_parser.return_value = mock_parser

                    mock_writer = Mock()
                    mock_writer.write.return_value = output_file
                    mock_writer_reg.get_writer.return_value = mock_writer

                    # Mock writer extension method
                    mock_writer.file_extension.return_value = ".bed"

                    # Should succeed
                    result = self.converter.convert(
                        input_file=input_file.name,
                        output_dir=output_dir,
                        output_formats=["artic"],
                    )

                    assert result == {"artic": output_file}
                    mock_parser.parse.assert_called_once()
                    mock_writer.write.assert_called_once()


class TestPrimerConverterEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = EnhancedConfig()
        self.converter = PrimerConverter(self.config)

        # Create valid amplicon with both forward and reverse primers
        forward_primer = PrimerData(
            name="test_forward",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amplicon",
        )

        reverse_primer = PrimerData(
            name="test_reverse",
            sequence="CGATCGATCGATCGAT",
            start=300,
            stop=316,
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="test_amplicon",
        )

        self.valid_amplicon = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[forward_primer, reverse_primer],
            length=200,
            reference_id="test_ref",
        )

    def test_validate_amplicons_mixed_issues(self):
        """Test validation with multiple types of issues."""
        # Create various problematic amplicons
        empty_amplicon = AmpliconData(
            amplicon_id="empty", primers=[], length=200, reference_id="test_ref"
        )

        forward_only_primer = PrimerData(
            name="forward_only",
            sequence="ATCGATCG",
            start=100,
            stop=108,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="forward_only_amp",
        )

        forward_only_amplicon = AmpliconData(
            amplicon_id="forward_only_amp",
            primers=[forward_only_primer],
            length=200,
            reference_id="test_ref",
        )

        # Should collect all issues
        with pytest.raises(ValidationError) as exc_info:
            self.converter._validate_amplicons([empty_amplicon, forward_only_amplicon])

        error = exc_info.value
        error_str = str(error)
        assert "empty has no primers" in error_str
        assert "forward_only_amp has no reverse primers" in error_str

    def test_format_detection_with_explicit_format(self):
        """Test that explicit format bypasses detection."""
        with tempfile.NamedTemporaryFile(suffix=".bed") as input_file:
            with tempfile.TemporaryDirectory() as output_dir:
                with patch("preprimer.core.converter.parser_registry") as mock_registry:
                    mock_parser = Mock()
                    mock_parser.parse.return_value = [
                        self.valid_amplicon
                    ]  # Use valid amplicon to avoid validation error
                    mock_parser.get_reference_file.return_value = None
                    mock_registry.get_parser.return_value = mock_parser

                    with patch(
                        "preprimer.core.converter.writer_registry"
                    ) as mock_writer_reg:
                        mock_writer = Mock()
                        mock_writer.write.return_value = Path(output_dir) / "output.tsv"
                        mock_writer.file_extension.return_value = ".tsv"
                        mock_writer_reg.get_writer.return_value = mock_writer

                        # Should not call detect_format when format is explicit
                        result = self.converter.convert(
                            input_file=input_file.name,
                            output_dir=output_dir,
                            output_formats=["varvamp"],
                            input_format="varvamp",  # Explicit format
                        )

                        # Should not have called detect_format
                        mock_registry.detect_format.assert_not_called()
                        # Should have called get_parser with explicit format
                        mock_registry.get_parser.assert_called_with("varvamp")
                        # Should have succeeded
                        assert "varvamp" in result
