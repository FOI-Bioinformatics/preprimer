"""
Comprehensive tests for STS writer targeting missed coverage lines.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from preprimer.writers.sts_writer import STSWriter
from preprimer.core.exceptions import OutputError
from preprimer.core.interfaces import AmpliconData, PrimerData


class TestSTSWriterMissedLines:
    """Test specific missed coverage lines in STSWriter."""
    
    def test_write_missing_primers_warning(self):
        """Test missing forward or reverse primer warning (lines 53-57)."""
        writer = STSWriter()
        
        # Create amplicons with missing primers
        amplicons = [
            # Amplicon with only forward primer (missing reverse)
            AmpliconData(
                amplicon_id="amp1",
                primers=[
                    PrimerData("amp1_F", "ATCGATCG", 100, 120, "+", "forward", 1, "amp1")
                ],
                reference_id="chr1"
            ),
            # Amplicon with only reverse primer (missing forward)  
            AmpliconData(
                amplicon_id="amp2",
                primers=[
                    PrimerData("amp2_R", "CGATCGAT", 300, 320, "-", "reverse", 1, "amp2")
                ],
                reference_id="chr1"
            ),
            # Complete amplicon for comparison
            AmpliconData(
                amplicon_id="amp3",
                primers=[
                    PrimerData("amp3_F", "GCTAGCTA", 500, 520, "+", "forward", 1, "amp3"),
                    PrimerData("amp3_R", "TAGCTAG", 700, 720, "-", "reverse", 1, "amp3")
                ],
                reference_id="chr1"
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sts.tsv', delete=False) as f:
            temp_path = f.name
        
        try:
            # Should skip incomplete amplicons and log warnings
            result = writer.write(amplicons, temp_path)
            assert result == Path(temp_path)
            
            # Check file contents - should only have complete amplicon
            with open(temp_path, 'r') as f:
                content = f.read()
                
            lines = content.strip().split('\n')
            assert len(lines) == 2  # Header + 1 complete amplicon
            assert lines[0] == "NAME\tFORWARD\tREVERSE"
            assert "amp3" in lines[1]  # Only complete amplicon written
            assert "GCTAGCTA" in lines[1]
            assert "TAGCTAG" in lines[1]
            
        finally:
            os.unlink(temp_path)
    
    def test_write_reference_id_processing(self):
        """Test reference_id processing in name generation (lines 66->72)."""
        writer = STSWriter()
        
        # Test amplicon WITH reference_id attribute
        amplicons = [
            AmpliconData(
                amplicon_id="test_amplicon",
                primers=[
                    PrimerData("test_F", "ATCGATCG", 100, 120, "+", "forward", 1, "test_amplicon"),
                    PrimerData("test_R", "CGATCGAT", 300, 320, "-", "reverse", 1, "test_amplicon")
                ],
                reference_id="chr1"  # This should trigger line 66->72 logic
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sts.tsv', delete=False) as f:
            temp_path = f.name
        
        try:
            writer.write(amplicons, temp_path)
            
            # Check that reference_id was included in name
            with open(temp_path, 'r') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            assert len(lines) == 2  # Header + 1 amplicon
            
            # Should have format: chr1_test_amplicon
            amplicon_line = lines[1]
            name_part = amplicon_line.split('\t')[0]
            assert name_part == "chr1_test_amplicon"
            
        finally:
            os.unlink(temp_path)
    
    def test_write_amplicon_id_duplication_prevention(self):
        """Test prevention of amplicon_id duplication in naming (lines 68->72)."""
        writer = STSWriter()
        
        # Test amplicon where amplicon_id already starts with reference_id
        amplicons = [
            AmpliconData(
                amplicon_id="chr1_amplicon_1",  # Already contains reference_id
                primers=[
                    PrimerData("test_F", "ATCGATCG", 100, 120, "+", "forward", 1, "chr1_amplicon_1"),
                    PrimerData("test_R", "CGATCGAT", 300, 320, "-", "reverse", 1, "chr1_amplicon_1")
                ],
                reference_id="chr1"
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sts.tsv', delete=False) as f:
            temp_path = f.name
        
        try:
            writer.write(amplicons, temp_path)
            
            # Check that reference_id was NOT duplicated
            with open(temp_path, 'r') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            amplicon_line = lines[1]
            name_part = amplicon_line.split('\t')[0]
            
            # Should NOT be "chr1_chr1_amplicon_1", just "chr1_amplicon_1"
            assert name_part == "chr1_amplicon_1"
            assert name_part.count("chr1") == 1  # Only appears once
            
        finally:
            os.unlink(temp_path)
    
    def test_write_multiple_primers_warning(self):
        """Test multiple primers per direction warning (line 82)."""
        writer = STSWriter()
        
        # Create amplicon with multiple primers per direction
        amplicons = [
            AmpliconData(
                amplicon_id="multi_primer_amp",
                primers=[
                    # Multiple forward primers
                    PrimerData("amp_F1", "ATCGATCG", 100, 120, "+", "forward", 1, "multi_primer_amp"),
                    PrimerData("amp_F2", "GCTAGCTA", 110, 130, "+", "forward", 1, "multi_primer_amp"),
                    
                    # Multiple reverse primers
                    PrimerData("amp_R1", "CGATCGAT", 300, 320, "-", "reverse", 1, "multi_primer_amp"),
                    PrimerData("amp_R2", "TAGCTAG", 310, 330, "-", "reverse", 1, "multi_primer_amp"),
                ],
                reference_id="chr1"
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sts.tsv', delete=False) as f:
            temp_path = f.name
        
        try:
            # Should use first primer of each direction and log info
            writer.write(amplicons, temp_path)
            
            # Check file contents - should use first primers only
            with open(temp_path, 'r') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            amplicon_line = lines[1]
            parts = amplicon_line.split('\t')
            
            # Should use first forward (ATCGATCG) and first reverse (CGATCGAT)
            assert parts[1] == "ATCGATCG"  # First forward primer sequence
            assert parts[2] == "CGATCGAT"  # First reverse primer sequence
            
        finally:
            os.unlink(temp_path)
    
    def test_write_exception_handling(self):
        """Test exception handling during write (lines 101-102)."""
        writer = STSWriter()
        
        amplicons = [
            AmpliconData(
                amplicon_id="test_amp",
                primers=[
                    PrimerData("test_F", "ATCGATCG", 100, 120, "+", "forward", 1, "test_amp"),
                    PrimerData("test_R", "CGATCGAT", 300, 320, "-", "reverse", 1, "test_amp")
                ],
                reference_id="chr1"
            )
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.sts.tsv', delete=False) as f:
            temp_path = f.name
            
        try:
            # Mock validate_output_path to return path but then mock open to fail
            with patch.object(writer, 'validate_output_path', return_value=Path(temp_path)):
                with patch('builtins.open', side_effect=IOError("Permission denied")):
                    with pytest.raises(OutputError, match="Failed to write STS format"):
                        writer.write(amplicons, temp_path)
        finally:
            # Clean up if file was created
            if os.path.exists(temp_path):
                os.unlink(temp_path)


class TestSTSWriterComprehensiveFeatures:
    """Test comprehensive STS writer features."""
    
    def test_format_properties(self):
        """Test class methods."""
        assert STSWriter.format_name() == "sts"
        assert STSWriter.file_extension() == ".sts.tsv"
    
    def test_write_empty_amplicons_list(self):
        """Test writing empty amplicons list."""
        writer = STSWriter()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sts.tsv', delete=False) as f:
            temp_path = f.name
        
        try:
            result = writer.write([], temp_path)
            assert result == Path(temp_path)
            
            # Check file contains only header
            with open(temp_path, 'r') as f:
                content = f.read()
            
            assert content.strip() == "NAME\tFORWARD\tREVERSE"
            
        finally:
            os.unlink(temp_path)
    
    def test_write_with_reference_path_logging(self):
        """Test reference path logging (lines 90-97)."""
        writer = STSWriter()
        
        amplicons = [
            AmpliconData(
                amplicon_id="test_amp",
                primers=[
                    PrimerData("test_F", "ATCGATCG", 100, 120, "+", "forward", 1, "test_amp"),
                    PrimerData("test_R", "CGATCGAT", 300, 320, "-", "reverse", 1, "test_amp")
                ],
                reference_id="chr1"
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sts.tsv', delete=False) as f:
            temp_path = f.name
        
        try:
            # Write with reference_path kwarg - should trigger reference logging
            reference_path = "/path/to/reference.fasta"
            result = writer.write(amplicons, temp_path, reference_path=reference_path)
            
            assert result == Path(temp_path)
            
            # Check file was created with correct content
            with open(temp_path, 'r') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            assert len(lines) == 2  # Header + 1 amplicon
            assert lines[0] == "NAME\tFORWARD\tREVERSE"
            assert "chr1_test_amp" in lines[1]
            
        finally:
            os.unlink(temp_path)
    
    def test_write_amplicon_without_reference_id(self):
        """Test amplicon without reference_id attribute."""
        writer = STSWriter()
        
        # Create amplicon without reference_id
        amplicons = [
            AmpliconData(
                amplicon_id="simple_amp",
                primers=[
                    PrimerData("simple_F", "AAATTTCCC", 50, 70, "+", "forward", 1, "simple_amp"),
                    PrimerData("simple_R", "GGGAAATTT", 250, 270, "-", "reverse", 1, "simple_amp")
                ]
                # No reference_id attribute
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sts.tsv', delete=False) as f:
            temp_path = f.name
        
        try:
            writer.write(amplicons, temp_path)
            
            # Check that amplicon_id is used as-is for name
            with open(temp_path, 'r') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            amplicon_line = lines[1]
            name_part = amplicon_line.split('\t')[0]
            
            # Should just be the amplicon_id
            assert name_part == "simple_amp"
            
        finally:
            os.unlink(temp_path)
    
    def test_write_complex_amplicon_naming(self):
        """Test complex amplicon naming scenarios."""
        writer = STSWriter()
        
        # Test various naming scenarios
        amplicons = [
            # Case 1: Empty reference_id
            AmpliconData(
                amplicon_id="amp1",
                primers=[
                    PrimerData("amp1_F", "ATCG", 100, 120, "+", "forward", 1, "amp1"),
                    PrimerData("amp1_R", "CGAT", 300, 320, "-", "reverse", 1, "amp1")
                ],
                reference_id=""  # Empty reference_id
            ),
            # Case 2: None reference_id  
            AmpliconData(
                amplicon_id="amp2",
                primers=[
                    PrimerData("amp2_F", "GCTA", 100, 120, "+", "forward", 1, "amp2"),
                    PrimerData("amp2_R", "TAGC", 300, 320, "-", "reverse", 1, "amp2")
                ],
                reference_id=None
            ),
            # Case 3: Normal reference_id
            AmpliconData(
                amplicon_id="amp3",
                primers=[
                    PrimerData("amp3_F", "AAAA", 100, 120, "+", "forward", 1, "amp3"),
                    PrimerData("amp3_R", "TTTT", 300, 320, "-", "reverse", 1, "amp3")
                ],
                reference_id="scaffold1"
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sts.tsv', delete=False) as f:
            temp_path = f.name
        
        try:
            writer.write(amplicons, temp_path)
            
            with open(temp_path, 'r') as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            assert len(lines) == 4  # Header + 3 amplicons
            
            # Check naming for each case
            amp1_line = [line for line in lines[1:] if "amp1" in line][0]
            amp2_line = [line for line in lines[1:] if "amp2" in line][0]
            amp3_line = [line for line in lines[1:] if "amp3" in line][0]
            
            # Case 1: Empty reference_id should just use amplicon_id
            assert amp1_line.startswith("amp1\t")
            
            # Case 2: None reference_id should just use amplicon_id
            assert amp2_line.startswith("amp2\t")
            
            # Case 3: Normal reference_id should be prefixed
            assert amp3_line.startswith("scaffold1_amp3\t")
            
        finally:
            os.unlink(temp_path)


class TestSTSWriterValidation:
    """Test STS writer validation methods."""
    
    def test_validate_output_path(self):
        """Test output path validation."""
        writer = STSWriter()
        
        # Test with string path
        result = writer.validate_output_path("test.sts.tsv")
        assert isinstance(result, Path)
        assert str(result).endswith("test.sts.tsv")
        
        # Test with Path object
        path_obj = Path("another.sts.tsv")
        result = writer.validate_output_path(path_obj)
        assert result == path_obj


class TestSTSWriterIntegration:
    """Test STS writer integration scenarios."""
    
    def test_write_realistic_dataset(self):
        """Test writing a realistic multi-amplicon dataset."""
        writer = STSWriter()
        
        # Create realistic amplicon data
        amplicons = [
            AmpliconData(
                amplicon_id="amplicon_1",
                primers=[
                    PrimerData("COVID_1_LEFT", "ACCAACCAACTTTCGATCTCTTGT", 266, 289, "+", "forward", 1, "amplicon_1"),
                    PrimerData("COVID_1_RIGHT", "CATCTTTAAGATGTTGACGTGCCTC", 635, 658, "-", "reverse", 1, "amplicon_1")
                ],
                reference_id="NC_045512.2"
            ),
            AmpliconData(
                amplicon_id="amplicon_2", 
                primers=[
                    PrimerData("COVID_2_LEFT", "CTGTTTTACAGGTTCGCGACG", 600, 620, "+", "forward", 2, "amplicon_2"),
                    PrimerData("COVID_2_RIGHT", "TAAGGATCAGTGCCAAGCTCGT", 950, 971, "-", "reverse", 2, "amplicon_2")
                ],
                reference_id="NC_045512.2"
            )
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sts.tsv', delete=False) as f:
            temp_path = f.name
        
        try:
            result = writer.write(amplicons, temp_path, reference_path="/ref/covid.fasta")
            
            # Verify file structure
            with open(temp_path, 'r') as f:
                lines = f.readlines()
            
            assert len(lines) == 3  # Header + 2 amplicons
            assert lines[0].strip() == "NAME\tFORWARD\tREVERSE"
            
            # Check amplicon 1
            amp1_parts = lines[1].strip().split('\t')
            assert amp1_parts[0] == "NC_045512.2_amplicon_1"
            assert amp1_parts[1] == "ACCAACCAACTTTCGATCTCTTGT"
            assert amp1_parts[2] == "CATCTTTAAGATGTTGACGTGCCTC"
            
            # Check amplicon 2
            amp2_parts = lines[2].strip().split('\t')
            assert amp2_parts[0] == "NC_045512.2_amplicon_2"
            assert amp2_parts[1] == "CTGTTTTACAGGTTCGCGACG"
            assert amp2_parts[2] == "TAAGGATCAGTGCCAAGCTCGT"
            
        finally:
            os.unlink(temp_path)