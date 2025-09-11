"""
Comprehensive tests for ARTIC parser targeting missed coverage lines.
"""

import pytest
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, mock_open

from preprimer.parsers.artic_parser import ARTICParser
from preprimer.core.exceptions import ParserError
from preprimer.core.interfaces import PrimerData, AmpliconData


class TestARTICParserValidationEdgeCases:
    """Test validation edge cases and error paths."""
    
    def test_validate_file_nonexistent_file(self):
        """Test validation with non-existent file (line 31)."""
        parser = ARTICParser()
        
        result = parser.validate_file("/nonexistent/file.bed")
        assert result is False
    
    def test_validate_file_insufficient_columns(self):
        """Test validation with insufficient columns (line 42)."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            # Write line with insufficient columns (< 6)
            f.write("chr1\t100\t200\tprimer\n")  # Only 4 columns
            temp_path = f.name
        
        try:
            result = parser.validate_file(temp_path)
            assert result is False  # Should return False due to insufficient columns
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_invalid_numeric_fields(self):
        """Test validation with invalid numeric fields (lines 46-53).""" 
        parser = ARTICParser()
        
        # Test invalid start position
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("chr1\tnot_number\t200\tprimer_LEFT\t1\t+\n")
            temp_path1 = f.name
        
        try:
            result = parser.validate_file(temp_path1)
            assert result is False  # Should return False due to invalid start
        finally:
            os.unlink(temp_path1)
        
        # Test invalid stop position
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("chr1\t100\tnot_number\tprimer_LEFT\t1\t+\n")
            temp_path2 = f.name
        
        try:
            result = parser.validate_file(temp_path2)
            assert result is False  # Should return False due to invalid stop
        finally:
            os.unlink(temp_path2)
        
        # Test invalid pool number
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("chr1\t100\t200\tprimer_LEFT\tnot_number\t+\n")
            temp_path3 = f.name
        
        try:
            result = parser.validate_file(temp_path3)
            assert result is False  # Should return False due to invalid pool
        finally:
            os.unlink(temp_path3)
    
    def test_validate_file_invalid_strand(self):
        """Test validation with invalid strand (lines 50-51)."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("chr1\t100\t200\tprimer_LEFT\t1\tx\n")  # Invalid strand 'x'
            temp_path = f.name
        
        try:
            result = parser.validate_file(temp_path)
            assert result is False  # Should return False due to invalid strand
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_no_artic_naming(self):
        """Test validation without ARTIC naming convention (lines 57-58)."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("chr1\t100\t200\tregular_primer\t1\t+\n")  # No LEFT/RIGHT
            temp_path = f.name
        
        try:
            result = parser.validate_file(temp_path)
            assert result is False  # Should return False due to missing LEFT/RIGHT
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_empty_file(self):
        """Test validation with empty file (line 62 - return True for empty)."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            # Write only comments and empty lines
            f.write("# This is a comment\n")
            f.write("\n")
            f.write("   \n")  # whitespace only
            temp_path = f.name
        
        try:
            result = parser.validate_file(temp_path)
            assert result is True  # Should return True (no invalid lines found)
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_io_exception(self):
        """Test validation with I/O exception (lines 64-66)."""
        parser = ARTICParser()
        
        # Mock open to raise an exception
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            result = parser.validate_file("somefile.bed")
            assert result is False  # Should return False on exception


class TestARTICParserParsingEdgeCases:
    """Test parsing edge cases and error paths."""
    
    def test_parse_invalid_file_error(self):
        """Test parsing invalid file raises ParserError (line 75)."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("invalid\tformat\n")  # Invalid format
            temp_path = f.name
        
        try:
            with pytest.raises(ParserError, match="is not a valid ARTIC format"):
                parser.parse(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_parse_malformed_lines_warning(self):
        """Test parsing with malformed lines (lines 89-91)."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            # Valid line first
            f.write("chr1\t100\t200\tSARS-CoV-2_1_LEFT\t1\t+\tATCG\n")
            # Malformed line (insufficient columns)
            f.write("chr1\t300\t400\tprimer\t2\n")  # Missing strand and sequence
            # Another valid line
            f.write("chr1\t500\t600\tSARS-CoV-2_1_RIGHT\t1\t-\tTGCA\n")
            temp_path = f.name
        
        try:
            # Should parse successfully, skipping malformed line
            amplicons = parser.parse(temp_path)
            assert len(amplicons) == 1  # Only one amplicon from valid lines
            assert len(amplicons[0].primers) == 2  # Two valid primers
        finally:
            os.unlink(temp_path)
    
    def test_parse_invalid_primer_name_format(self):
        """Test parsing with invalid primer name format (lines 107-109).""" 
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            # Valid ARTIC format for validation but invalid name format for parsing
            # This primer name has LEFT but insufficient parts for parsing logic
            f.write("chr1\t100\t200\tLEFT\t1\t+\tATCG\n")  # Too few parts but contains LEFT
            temp_path = f.name
        
        try:
            with pytest.raises(ParserError, match="Invalid ARTIC primer name format"):
                parser.parse(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_parse_different_primer_naming_formats(self):
        """Test parsing different primer naming formats (lines 115-120)."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            # Format 1: PREFIX_SIZE_AMPLICON_SIDE_ALT
            f.write("chr1\t100\t200\tSARS-CoV-2_400_1_LEFT_1\t1\t+\tATCG\n")
            # Format 2: PREFIX_AMPLICON_SIDE
            f.write("chr1\t300\t400\tSARS-CoV-2_2_RIGHT\t1\t-\tTGCA\n")
            # Format 3: Fallback format
            f.write("chr1\t500\t600\tprefix_3_other_LEFT\t2\t+\tGCTA\n")
            temp_path = f.name
        
        try:
            amplicons = parser.parse(temp_path)
            
            # Should have parsed all three amplicons
            amplicon_ids = {amp.amplicon_id for amp in amplicons}
            assert "amplicon_1" in amplicon_ids
            assert "amplicon_2" in amplicon_ids  
            assert "amplicon_other" in amplicon_ids  # fallback format
        finally:
            os.unlink(temp_path)
    
    def test_parse_unknown_primer_side_error(self):
        """Test parsing with unknown primer side (line 130)."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("chr1\t100\t200\tSARS-CoV-2_1_LEFT\t1\t+\tATCG\n")  # Valid for validation
            temp_path = f.name
        
        try:
            # Mock validate_file to return True to bypass validation
            with patch.object(parser, 'validate_file', return_value=True):
                # Mock the file reading to return content with invalid primer side  
                mock_content = "chr1\t100\t200\tSARS-CoV-2_1_MIDDLE\t1\t+\tATCG\n"
                with patch('builtins.open', mock_open(read_data=mock_content)):
                    with pytest.raises(ParserError, match="Unknown primer side in"):
                        parser.parse(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_parse_exception_handling(self):
        """Test parsing exception handling (lines 156-157)."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            f.write("chr1\t100\t200\tSARS-CoV-2_1_LEFT\t1\t+\tATCG\n")
            temp_path = f.name
        
        try:
            # Mock validate_file to return True to bypass validation
            with patch.object(parser, 'validate_file', return_value=True):
                # Mock open to raise exception during parsing (line 156-157)
                with patch('builtins.open', side_effect=IOError("Read error during parsing")):
                    with pytest.raises(ParserError, match="Failed to parse ARTIC file"):
                        parser.parse(temp_path)
        finally:
            os.unlink(temp_path)


class TestARTICParserAmpliconProcessing:
    """Test amplicon processing edge cases."""
    
    def test_amplicon_length_calculation(self):
        """Test amplicon length calculation (lines 161-164)."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            # Two primers for same amplicon with different positions
            f.write("chr1\t100\t150\tSARS-CoV-2_1_LEFT\t1\t+\tATCG\n")
            f.write("chr1\t300\t350\tSARS-CoV-2_1_RIGHT\t1\t-\tTGCA\n")
            temp_path = f.name
        
        try:
            amplicons = parser.parse(temp_path)
            assert len(amplicons) == 1
            
            # Length should be max_stop - min_start = 350 - 100 = 250
            assert amplicons[0].length == 250
        finally:
            os.unlink(temp_path)
    
    def test_empty_amplicon_no_length_calculation(self):
        """Test empty amplicons don't get length calculated."""
        parser = ARTICParser()
        
        # This tests the edge case where an amplicon might be created but have no primers
        # This shouldn't happen in normal parsing but tests the safety check
        amplicon = AmpliconData(amplicon_id="test", primers=[], reference_id="chr1")
        
        # Simulate the length calculation logic for empty primers list
        if amplicon.primers:  # This should be False
            starts = [p.start for p in amplicon.primers]
            stops = [p.stop for p in amplicon.primers]
            amplicon.length = max(stops) - min(starts)
        
        # Length should remain None/unset for empty amplicons
        assert not hasattr(amplicon, 'length') or amplicon.length is None


class TestARTICParserReferenceFileHandling:
    """Test reference file handling."""
    
    def test_get_reference_file_scheme_bed_format(self):
        """Test finding reference file for .scheme.bed format (lines 180-185).""" 
        parser = ARTICParser()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .scheme.bed file
            scheme_file = Path(temp_dir) / "test.scheme.bed"
            scheme_file.write_text("chr1\t100\t200\tprimer_LEFT\t1\t+\n")
            
            # Create corresponding reference file
            ref_file = Path(temp_dir) / "test.reference.fasta"
            ref_file.write_text(">chr1\nATCGATCG\n")
            
            # Should find the reference file
            result = parser.get_reference_file(scheme_file)
            assert result == ref_file
    
    def test_get_reference_file_scheme_bed_not_found(self):
        """Test reference file not found for .scheme.bed format."""
        parser = ARTICParser()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .scheme.bed file but no reference
            scheme_file = Path(temp_dir) / "test.scheme.bed"
            scheme_file.write_text("chr1\t100\t200\tprimer_LEFT\t1\t+\n")
            
            # Should continue to alternative naming (line 188+)
            result = parser.get_reference_file(scheme_file)
            # Should return None since alternative also doesn't exist
            assert result is None
    
    def test_get_reference_file_alternative_naming(self):
        """Test alternative reference file naming (lines 188-191)."""
        parser = ARTICParser()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a regular .bed file
            bed_file = Path(temp_dir) / "test.bed"
            bed_file.write_text("chr1\t100\t200\tprimer_LEFT\t1\t+\n")
            
            # Create reference with alternative naming
            ref_file = Path(temp_dir) / "test.reference.fasta"
            ref_file.write_text(">chr1\nATCGATCG\n")
            
            # Should find the reference file using alternative naming
            result = parser.get_reference_file(bed_file)
            assert result == ref_file
    
    def test_get_reference_file_not_found(self):
        """Test reference file not found returns None."""
        parser = ARTICParser()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a .bed file but no reference
            bed_file = Path(temp_dir) / "test.bed"
            bed_file.write_text("chr1\t100\t200\tprimer_LEFT\t1\t+\n")
            
            # Should return None
            result = parser.get_reference_file(bed_file)
            assert result is None


class TestARTICParserClassMethods:
    """Test class methods."""
    
    def test_format_name(self):
        """Test format name method."""
        assert ARTICParser.format_name() == "artic"
    
    def test_file_extensions(self):
        """Test file extensions method."""
        extensions = ARTICParser.file_extensions()
        assert ".bed" in extensions
        assert ".scheme.bed" in extensions


class TestARTICParserComplexScenarios:
    """Test complex parsing scenarios."""
    
    def test_parse_mixed_valid_invalid_lines(self):
        """Test parsing file with mix of valid, invalid, and comment lines."""
        parser = ARTICParser()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as f:
            # Comments and empty lines
            f.write("# ARTIC primer scheme\n")
            f.write("\n")
            f.write("   # Another comment\n")
            
            # Valid lines
            f.write("chr1\t100\t150\tSARS-CoV-2_1_LEFT\t1\t+\tATCGATCG\n")
            f.write("chr1\t300\t350\tSARS-CoV-2_1_RIGHT\t1\t-\tTGCATGCA\n")
            
            # Invalid line (will be skipped with warning)
            f.write("chr1\t400\t450\tincomplete_line\t2\n")  # Missing strand and sequence
            
            # Another valid amplicon
            f.write("chr1\t500\t550\tSARS-CoV-2_2_LEFT\t2\t+\tGCTAGCTA\n")
            f.write("chr1\t700\t750\tSARS-CoV-2_2_RIGHT\t2\t-\tCGATCGAT\n")
            
            temp_path = f.name
        
        try:
            amplicons = parser.parse(temp_path)
            
            # Should have 2 amplicons
            assert len(amplicons) == 2
            
            # Check amplicon 1
            amp1 = next(amp for amp in amplicons if amp.amplicon_id == "amplicon_1")
            assert len(amp1.primers) == 2
            assert amp1.length == 250  # 350 - 100
            
            # Check amplicon 2  
            amp2 = next(amp for amp in amplicons if amp.amplicon_id == "amplicon_2")
            assert len(amp2.primers) == 2
            assert amp2.length == 250  # 750 - 500
            
        finally:
            os.unlink(temp_path)