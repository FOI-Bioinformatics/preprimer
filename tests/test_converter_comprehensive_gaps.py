"""
Comprehensive tests for PrimerConverter targeting missed coverage lines.

This targets the 7 missed statements in preprimer/core/converter.py which are
critical for core conversion functionality.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from preprimer.core.converter import PrimerConverter
from preprimer.core.config import PrePrimerConfig
from preprimer.core.exceptions import ValidationError, OutputError
from preprimer.core.interfaces import AmpliconData, PrimerData


class TestConverterReferenceFileHandling:
    """Test reference file detection and logging (lines 105->111)."""
    
    def test_converter_with_reference_file_detection(self):
        """Test reference file detection when not provided (lines 105-108)."""
        
        # Mock parser that returns a reference file
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            AmpliconData(
                amplicon_id="test_amp",
                primers=[
                    PrimerData("test_F", "ATCGATCGATCGATCGATCGAT", 100, 120, "+", "forward", 1, "test_amp"),
                    PrimerData("test_R", "CGATCGATCGATCGATCGAT", 300, 320, "-", "reverse", 1, "test_amp")
                ]
            )
        ]
        # This should trigger line 106-108 - reference file detection
        mock_parser.get_reference_file.return_value = Path("/found/reference.fasta")
        
        mock_writer = MagicMock()
        mock_writer.write.return_value = Path("/output/test.txt")
        mock_writer.file_extension.return_value = ".txt"
        
        with patch('preprimer.core.converter.parser_registry') as mock_parser_reg:
            with patch('preprimer.core.converter.writer_registry') as mock_writer_reg:
                mock_parser_reg.detect_format.return_value = "test_format"
                mock_parser_reg.get_parser.return_value = mock_parser
                mock_writer_reg.get_writer.return_value = mock_writer
                
                # Disable validation for this test since it's not the focus
                config = PrePrimerConfig(validate_sequences=False)
                converter = PrimerConverter(config)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_input = Path(temp_dir) / "input.txt"
                    test_input.write_text("test data")
                    
                    # Call without reference_file to trigger detection
                    result = converter.convert(
                        input_file=test_input,
                        output_dir=temp_dir,
                        output_formats=["test_format"],
                        reference_file=None  # Should trigger detection at line 106
                    )
                    
                    # Should have found reference file and logged it
                    mock_parser.get_reference_file.assert_called_once_with(test_input)
                    assert isinstance(result, dict)


class TestConverterOutputFileAssignment:
    """Test output file assignment after writing (lines 127->129)."""
    
    def test_converter_output_file_assignment_when_writer_returns_none(self):
        """Test output file assignment when writer returns None (lines 127-128)."""
        
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            AmpliconData(
                amplicon_id="test_amp",
                primers=[
                    PrimerData("test_F", "ATCGATCGATCGATCGATCGAT", 100, 120, "+", "forward", 1, "test_amp"),
                    PrimerData("test_R", "CGATCGATCGATCGATCGAT", 300, 320, "-", "reverse", 1, "test_amp")
                ]
            )
        ]
        mock_parser.get_reference_file.return_value = None
        
        # Mock writer that returns None (some writers may do this)
        mock_writer = MagicMock()
        mock_writer.write.return_value = None  # This should trigger line 127-128
        mock_writer.file_extension.return_value = ".txt"
        
        with patch('preprimer.core.converter.parser_registry') as mock_parser_reg:
            with patch('preprimer.core.converter.writer_registry') as mock_writer_reg:
                mock_parser_reg.detect_format.return_value = "test_format"
                mock_parser_reg.get_parser.return_value = mock_parser
                mock_writer_reg.get_writer.return_value = mock_writer
                
                # Disable validation for this test since it's not the focus
                config = PrePrimerConfig(validate_sequences=False)
                converter = PrimerConverter(config)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_input = Path(temp_dir) / "input.txt"
                    test_input.write_text("test data")
                    
                    result = converter.convert(
                        input_file=test_input,
                        output_dir=temp_dir,
                        output_formats=["test_format"]
                    )
                    
                    # When writer returns None, should still assign output file
                    assert "test_format" in result
                    # Should have assigned the expected output path
                    expected_path = Path(temp_dir) / "test_format" / "primers.txt"
                    assert result["test_format"] == expected_path


class TestConverterContinueOnError:
    """Test continue on error logic (line 135)."""
    
    def test_converter_continue_on_error_flag(self):
        """Test continue_on_error flag behavior (line 135)."""
        
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            AmpliconData(
                amplicon_id="test_amp",
                primers=[
                    PrimerData("test_F", "ATCGATCGATCGATCGATCGAT", 100, 120, "+", "forward", 1, "test_amp"),
                    PrimerData("test_R", "CGATCGATCGATCGATCGAT", 300, 320, "-", "reverse", 1, "test_amp")
                ]
            )
        ]
        mock_parser.get_reference_file.return_value = None
        
        # Mock writer that raises an exception
        mock_writer = MagicMock()
        mock_writer.write.side_effect = Exception("Writer failed")
        mock_writer.file_extension.return_value = ".txt"
        
        with patch('preprimer.core.converter.parser_registry') as mock_parser_reg:
            with patch('preprimer.core.converter.writer_registry') as mock_writer_reg:
                mock_parser_reg.detect_format.return_value = "test_format"
                mock_parser_reg.get_parser.return_value = mock_parser
                mock_writer_reg.get_writer.return_value = mock_writer
                
                # Disable validation for this test since it's not the focus
                config = PrePrimerConfig(validate_sequences=False)
                converter = PrimerConverter(config)
                
                with tempfile.TemporaryDirectory() as temp_dir:
                    test_input = Path(temp_dir) / "input.txt"
                    test_input.write_text("test data")
                    
                    # Test with continue_on_error=True - should not raise
                    result = converter.convert(
                        input_file=test_input,
                        output_dir=temp_dir,
                        output_formats=["test_format"],
                        continue_on_error=True  # Should trigger line 135 logic
                    )
                    
                    # Should return empty dict since writer failed but continued
                    assert result == {}
                    
                    # Test with continue_on_error=False (default) - should raise
                    with pytest.raises(Exception, match="Writer failed"):
                        converter.convert(
                            input_file=test_input,
                            output_dir=temp_dir,
                            output_formats=["test_format"],
                            continue_on_error=False
                        )


class TestConverterPrimerValidationEdgeCases:
    """Test specific primer validation edge cases (lines 204-205, 214, 223, 231)."""
    
    def test_validation_empty_primer_sequence(self):
        """Test validation with empty primer sequence (lines 204-205)."""
        
        # Create amplicon with empty primer sequence
        amplicons = [
            AmpliconData(
                amplicon_id="test_amp",
                primers=[
                    PrimerData("empty_seq", "", 100, 120, "+", "forward", 1, "test_amp"),  # Empty sequence
                    PrimerData("test_R", "CGAT", 300, 320, "-", "reverse", 1, "test_amp")
                ]
            )
        ]
        
        config = PrePrimerConfig(validate_sequences=True)
        converter = PrimerConverter(config)
        
        with pytest.raises(ValidationError, match="has empty sequence"):
            converter._validate_amplicons(amplicons)
    
    def test_validation_primer_too_long(self):
        """Test validation with primer too long (line 214)."""
        
        # Create amplicon with very long primer
        long_sequence = "A" * 100  # Assuming max_primer_length is less than 100
        
        amplicons = [
            AmpliconData(
                amplicon_id="test_amp",
                primers=[
                    PrimerData("long_primer", long_sequence, 100, 120, "+", "forward", 1, "test_amp"),
                    PrimerData("test_R", "CGAT", 300, 320, "-", "reverse", 1, "test_amp")
                ]
            )
        ]
        
        config = PrePrimerConfig(
            validate_sequences=True,
            max_primer_length=50  # Set lower than our test sequence
        )
        converter = PrimerConverter(config)
        
        with pytest.raises(ValidationError, match="is too long"):
            converter._validate_amplicons(amplicons)
    
    def test_validation_invalid_sequence_characters(self):
        """Test validation with invalid sequence characters (line 223)."""
        
        # Create amplicon with invalid characters in sequence
        amplicons = [
            AmpliconData(
                amplicon_id="test_amp",
                primers=[
                    PrimerData("invalid_seq", "ATCGXYZ123", 100, 120, "+", "forward", 1, "test_amp"),  # Invalid chars
                    PrimerData("test_R", "CGAT", 300, 320, "-", "reverse", 1, "test_amp")
                ]
            )
        ]
        
        config = PrePrimerConfig(validate_sequences=True)
        converter = PrimerConverter(config)
        
        with pytest.raises(ValidationError, match="contains invalid characters"):
            converter._validate_amplicons(amplicons)
    
    def test_validation_many_issues_truncation(self):
        """Test validation issue summary truncation (line 231)."""
        
        # Create many amplicons with validation issues to trigger truncation
        amplicons = []
        
        for i in range(15):  # Create more than 10 issues
            amplicons.append(
                AmpliconData(
                    amplicon_id=f"bad_amp_{i}",
                    primers=[
                        PrimerData(f"bad_primer_{i}", "ATCGXYZ", 100, 120, "+", "forward", 1, f"bad_amp_{i}")
                        # Missing reverse primer and has invalid characters
                    ]
                )
            )
        
        config = PrePrimerConfig(validate_sequences=True)
        converter = PrimerConverter(config)
        
        with pytest.raises(ValidationError) as exc_info:
            converter._validate_amplicons(amplicons)
        
        # Should truncate and show "... and X more issues"
        error_message = str(exc_info.value)
        assert "... and" in error_message
        assert "more issues" in error_message


class TestConverterComplexScenarios:
    """Test complex converter scenarios."""
    
    def test_converter_all_validation_paths(self):
        """Test converter with all validation edge cases."""
        
        # Create complex amplicon set with various issues
        amplicons = [
            # Good amplicon
            AmpliconData(
                amplicon_id="good_amp",
                primers=[
                    PrimerData("good_F", "ATCGATCG", 100, 120, "+", "forward", 1, "good_amp"),
                    PrimerData("good_R", "CGATCGAT", 300, 320, "-", "reverse", 1, "good_amp")
                ]
            ),
            # Amplicon with empty sequence
            AmpliconData(
                amplicon_id="empty_seq_amp",
                primers=[
                    PrimerData("empty_F", "", 100, 120, "+", "forward", 1, "empty_seq_amp"),  # Empty
                    PrimerData("empty_R", "CGAT", 300, 320, "-", "reverse", 1, "empty_seq_amp")
                ]
            ),
            # Amplicon with long primer
            AmpliconData(
                amplicon_id="long_amp",
                primers=[
                    PrimerData("long_F", "A" * 100, 100, 120, "+", "forward", 1, "long_amp"),  # Too long
                    PrimerData("long_R", "CGAT", 300, 320, "-", "reverse", 1, "long_amp")
                ]
            ),
            # Amplicon with invalid characters
            AmpliconData(
                amplicon_id="invalid_amp",
                primers=[
                    PrimerData("invalid_F", "ATCGXYZ", 100, 120, "+", "forward", 1, "invalid_amp"),  # Invalid chars
                    PrimerData("invalid_R", "CGAT", 300, 320, "-", "reverse", 1, "invalid_amp")
                ]
            )
        ]
        
        config = PrePrimerConfig(
            validate_sequences=True,
            max_primer_length=50
        )
        converter = PrimerConverter(config)
        
        with pytest.raises(ValidationError) as exc_info:
            converter._validate_amplicons(amplicons)
        
        error_message = str(exc_info.value)
        
        # Should have all types of validation errors
        assert "empty sequence" in error_message
        assert "too long" in error_message
        assert "invalid characters" in error_message
    
    def test_converter_with_file_exists_error_handling(self):
        """Test converter file exists error handling."""
        
        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            AmpliconData(
                amplicon_id="test_amp",
                primers=[
                    PrimerData("test_F", "ATCGATCGATCGATCGATCGAT", 100, 120, "+", "forward", 1, "test_amp"),
                    PrimerData("test_R", "CGATCGATCGATCGATCGAT", 300, 320, "-", "reverse", 1, "test_amp")
                ]
            )
        ]
        mock_parser.get_reference_file.return_value = None
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing output file
            output_subdir = Path(temp_dir) / "test_format" 
            output_subdir.mkdir()
            existing_file = output_subdir / "primers.txt"
            existing_file.write_text("existing content")
            
            mock_writer = MagicMock()
            mock_writer.file_extension.return_value = ".txt"
            
            with patch('preprimer.core.converter.parser_registry') as mock_parser_reg:
                with patch('preprimer.core.converter.writer_registry') as mock_writer_reg:
                    mock_parser_reg.detect_format.return_value = "test_format"
                    mock_parser_reg.get_parser.return_value = mock_parser
                    mock_writer_reg.get_writer.return_value = mock_writer
                    
                    config = PrePrimerConfig(force_overwrite=False, validate_sequences=False)
                    converter = PrimerConverter(config)
                    
                    test_input = Path(temp_dir) / "input.txt"
                    test_input.write_text("test data")
                    
                    # Should raise OutputError when file exists and no force
                    with pytest.raises(OutputError, match="Output file exists"):
                        converter.convert(
                            input_file=test_input,
                            output_dir=temp_dir,
                            output_formats=["test_format"]
                        )
                    
                    # Should work with force=True in kwargs
                    mock_writer.write.return_value = existing_file
                    result = converter.convert(
                        input_file=test_input,
                        output_dir=temp_dir,
                        output_formats=["test_format"],
                        force=True  # Should override config
                    )
                    
                    assert "test_format" in result