"""
Comprehensive tests for the VarVAMPWriter class.

Tests all functionality of the VarVAMP TSV format writer including
basic writing, validation, GC content calculation, and edge cases.
"""

import csv
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.writers.varvamp_writer import VarVAMPWriter


class TestVarVAMPWriter:
    """Test the VarVAMPWriter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.writer = VarVAMPWriter()
        
        # Create realistic test data
        self.forward_primer = PrimerData(
            name="test_1_LEFT",
            sequence="ATCGATCGATCGATCG",  # 50% GC content
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amplicon_1",
            gc_content=0.5,
            tm=58.5,
            score=95.2
        )
        
        self.reverse_primer = PrimerData(
            name="test_1_RIGHT", 
            sequence="GGCCGGCCGGCCGGCC",  # 100% GC content
            start=200,
            stop=216,
            strand="-",
            direction="reverse", 
            pool=1,
            amplicon_id="amplicon_1",
            gc_content=1.0,
            tm=72.1,
            score=88.7
        )
        
        self.amplicon = AmpliconData(
            amplicon_id="amplicon_1",
            primers=[self.forward_primer, self.reverse_primer],
            length=116,
            reference_id="test_ref"
        )
        
        # Create amplicon with missing length for default testing
        self.amplicon_no_length = AmpliconData(
            amplicon_id="amplicon_2", 
            primers=[self.forward_primer, self.reverse_primer],
            length=None,
            reference_id="test_ref"
        )

    def test_format_name(self):
        """Test format_name class method."""
        assert VarVAMPWriter.format_name() == "varvamp"

    def test_file_extension(self):
        """Test file_extension class method.""" 
        assert VarVAMPWriter.file_extension() == ".tsv"

    def test_description_property(self):
        """Test description property."""
        description = self.writer.description
        assert isinstance(description, str)
        assert "VarVAMP" in description
        assert "tab-separated" in description

    def test_write_single_amplicon(self):
        """Test writing a single amplicon with multiple primers."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result_path = self.writer.write([self.amplicon], output_path)
            
            assert result_path == output_path
            assert output_path.exists()
            
            # Verify TSV content
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                rows = list(reader)
                
                assert len(rows) == 2  # Two primers
                
                # Check forward primer row
                forward_row = rows[0]
                assert forward_row['amplicon_name'] == 'amplicon_1'
                assert forward_row['amplicon_length'] == '116'
                assert forward_row['primer_name'] == 'test_1_LEFT'
                assert forward_row['pool'] == '1'
                assert forward_row['start'] == '100'
                assert forward_row['stop'] == '116'
                assert forward_row['seq'] == 'ATCGATCGATCGATCG'
                assert forward_row['size'] == '16'
                assert float(forward_row['gc_best']) == 50.0  # 50% GC
                assert float(forward_row['temp_best']) == 58.5
                assert float(forward_row['mean_gc']) == 50.0
                assert float(forward_row['mean_temp']) == 58.5
                assert float(forward_row['score']) == 95.2
                
                # Check reverse primer row
                reverse_row = rows[1]
                assert reverse_row['amplicon_name'] == 'amplicon_1'
                assert reverse_row['seq'] == 'GGCCGGCCGGCCGGCC'
                assert float(reverse_row['gc_best']) == 100.0  # 100% GC
                
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_amplicon_with_no_length(self):
        """Test writing amplicon where length is None (uses default)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result_path = self.writer.write([self.amplicon_no_length], output_path)
            
            # Verify default amplicon length is used
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                rows = list(reader)
                
                assert len(rows) == 2
                assert rows[0]['amplicon_length'] == '400'  # default
                assert rows[1]['amplicon_length'] == '400'  # default
                
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_primers_with_no_pool(self):
        """Test writing primers where pool is None (uses default)."""
        # Create primers with None pools
        primer_no_pool = PrimerData(
            name="test_no_pool",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+", 
            direction="forward",
            pool=None,
            amplicon_id="test_amplicon"
        )
        
        amplicon_no_pool = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[primer_no_pool],
            length=116,
            reference_id="test_ref"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result_path = self.writer.write([amplicon_no_pool], output_path)
            
            # Verify default pool is used
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                rows = list(reader)
                
                assert len(rows) == 1
                assert rows[0]['pool'] == '1'  # default pool
                
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_primers_with_missing_optional_attributes(self):
        """Test writing primers that lack tm and score attributes."""
        # Create primer without optional attributes
        basic_primer = PrimerData(
            name="basic_primer",
            sequence="ATCGATCGATCGATCG",
            start=100,
            stop=116,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amplicon"
        )
        
        amplicon_basic = AmpliconData(
            amplicon_id="test_amplicon",
            primers=[basic_primer],
            length=116,
            reference_id="test_ref"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result_path = self.writer.write([amplicon_basic], output_path)
            
            # Verify default values are used for missing attributes
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                rows = list(reader)
                
                assert len(rows) == 1
                row = rows[0]
                assert float(row['temp_best']) == 60.0  # default tm
                assert float(row['mean_temp']) == 60.0
                assert float(row['score']) == 90.0  # default score
                
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_write_creates_output_directory(self):
        """Test that write creates output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "subdir" / "output.tsv"
            
            # Directory shouldn't exist initially
            assert not output_path.parent.exists()
            
            result_path = self.writer.write([self.amplicon], output_path)
            
            # Directory should be created
            assert output_path.parent.exists()
            assert output_path.exists()

    def test_write_empty_amplicons_list(self):
        """Test writing empty amplicons list."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            result_path = self.writer.write([], output_path)
            
            assert result_path == output_path
            assert output_path.exists()
            
            # File should exist but be empty (no header or rows)
            with open(output_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert content == ""
                
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_calculate_gc_content_normal_sequence(self):
        """Test GC content calculation with normal sequences."""
        # Test 50% GC content
        gc_content = self.writer._calculate_gc_content("ATCGATCGATCGATCG")
        assert gc_content == 0.5
        
        # Test 100% GC content  
        gc_content = self.writer._calculate_gc_content("GGCCGGCCGGCCGGCC")
        assert gc_content == 1.0
        
        # Test 0% GC content
        gc_content = self.writer._calculate_gc_content("ATATATATATATATAT")
        assert gc_content == 0.0
        
        # Test mixed case
        gc_content = self.writer._calculate_gc_content("atcgATCG")
        assert gc_content == 0.5

    def test_calculate_gc_content_empty_sequence(self):
        """Test GC content calculation with empty sequence."""
        gc_content = self.writer._calculate_gc_content("")
        assert gc_content == 0.0

    def test_calculate_gc_content_precision(self):
        """Test GC content calculation precision."""
        # Test rounding to 3 decimal places
        gc_content = self.writer._calculate_gc_content("ATCGATCG")  # 4/8 = 0.5
        assert gc_content == 0.5
        
        # Test with longer sequence that would need rounding
        gc_content = self.writer._calculate_gc_content("ATCGATCGATC")  # 5/11 = 0.45454...
        assert gc_content == 0.455  # rounded to 3 decimal places

    def test_validate_output_valid_file(self):
        """Test validate_output with valid VarVAMP file.""" 
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # First create a valid file
            self.writer.write([self.amplicon], output_path)
            
            # Then validate it
            is_valid = self.writer.validate_output(output_path)
            assert is_valid is True
            
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_validate_output_missing_file(self):
        """Test validate_output with non-existent file."""
        non_existent_path = Path("/non/existent/file.tsv")
        is_valid = self.writer.validate_output(non_existent_path)
        assert is_valid is False

    def test_validate_output_missing_required_columns(self):
        """Test validate_output with missing required columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # Create TSV with missing required columns
            with open(output_path, 'w', newline='', encoding='utf-8') as tsvfile:
                writer = csv.DictWriter(tsvfile, fieldnames=['start', 'stop'], delimiter='\t')
                writer.writeheader()
                writer.writerow({'start': '100', 'stop': '200'})
            
            is_valid = self.writer.validate_output(output_path)
            assert is_valid is False
            
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_validate_output_empty_file(self):
        """Test validate_output with empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # Create empty file
            with open(output_path, 'w', encoding='utf-8') as f:
                pass  # Empty file
            
            is_valid = self.writer.validate_output(output_path)
            assert is_valid is False
            
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_validate_output_no_data_rows(self):
        """Test validate_output with file that has headers but no data rows."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # Create TSV with all required headers but no data
            fieldnames = [
                "amplicon_name", "amplicon_length", "primer_name", "pool",
                "start", "stop", "seq", "size", "gc_best", "temp_best",
                "mean_gc", "mean_temp", "score"
            ]
            with open(output_path, 'w', newline='', encoding='utf-8') as tsvfile:
                writer = csv.DictWriter(tsvfile, fieldnames=fieldnames, delimiter='\t')
                writer.writeheader()
                # No data rows
            
            is_valid = self.writer.validate_output(output_path)
            assert is_valid is False
            
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_validate_output_malformed_tsv(self):
        """Test validate_output with malformed TSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # Create malformed TSV
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("this is not a valid TSV file\nwith random content")
            
            is_valid = self.writer.validate_output(output_path)
            assert is_valid is False
            
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_get_output_info(self):
        """Test get_output_info method."""
        info = self.writer.get_output_info()
        
        assert isinstance(info, dict)
        assert 'format' in info
        assert 'extension' in info  
        assert 'description' in info
        assert 'use_case' in info
        assert 'columns' in info
        assert 'separator' in info
        assert 'coordinate_system' in info
        
        # Check specific content
        assert 'VarVAMP' in info['use_case']
        assert 'tab' in info['separator']
        assert '1-based' in info['coordinate_system']
        assert 'amplicon_name' in info['columns']
        assert 'seq' in info['columns']


class TestVarVAMPWriterIntegration:
    """Integration tests for VarVAMPWriter with complex scenarios."""

    def test_write_multiple_amplicons_multiple_primers(self):
        """Test writing multiple amplicons with multiple primers each."""
        writer = VarVAMPWriter()
        
        # Create complex test data
        amplicons = []
        
        for amp_i in range(2):
            primers = []
            
            # Create multiple primers per amplicon
            for primer_i in range(3):
                primer = PrimerData(
                    name=f"amp_{amp_i}_primer_{primer_i}",
                    sequence=f"{'ATCG' * (4 + primer_i)}",
                    start=100 + amp_i * 300 + primer_i * 50,
                    stop=116 + amp_i * 300 + primer_i * 50,
                    strand="+" if primer_i % 2 == 0 else "-",
                    direction="forward" if primer_i % 2 == 0 else "reverse",
                    pool=(amp_i % 2) + 1,
                    amplicon_id=f"amplicon_{amp_i}",
                    gc_content=0.5 + primer_i * 0.1,
                    tm=55.0 + primer_i * 2.5,
                    score=85.0 + primer_i * 3.0
                )
                primers.append(primer)
            
            amplicon = AmpliconData(
                amplicon_id=f"amplicon_{amp_i}",
                primers=primers,
                length=250 + amp_i * 50,
                reference_id="test_genome"
            )
            amplicons.append(amplicon)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # Write data
            result_path = writer.write(amplicons, output_path)
            
            # Verify comprehensive output
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                rows = list(reader)
                
                # Should have 6 total primers (2 amplicons * 3 primers each)
                assert len(rows) == 6
                
                # Check amplicon grouping
                amp_0_rows = [r for r in rows if r['amplicon_name'] == 'amplicon_0']
                amp_1_rows = [r for r in rows if r['amplicon_name'] == 'amplicon_1']
                
                assert len(amp_0_rows) == 3
                assert len(amp_1_rows) == 3
                
                # Check specific values for first amplicon's first primer
                first_row = amp_0_rows[0]
                assert first_row['amplicon_length'] == '250'
                assert first_row['pool'] == '1'
                assert first_row['size'] == '16'  # 4 * 4 = 16 chars
                
                # Check GC content calculation
                # "ATCGATCGATCGATCG" = 8 GC out of 16 = 50%
                assert float(first_row['gc_best']) == 50.0
                assert float(first_row['mean_gc']) == 50.0
                
            # Validate output
            assert writer.validate_output(output_path) is True
            
        finally:
            if output_path.exists():
                output_path.unlink()

    def test_round_trip_data_integrity(self):
        """Test that all data is preserved correctly in output."""
        writer = VarVAMPWriter()
        
        # Create test data with specific values to verify
        primer_data = [
            {
                "name": "test_primer_1",
                "sequence": "GCGCGCGCGCGCGCGC",  # 100% GC
                "start": 1000,
                "stop": 1016,
                "pool": 3,
                "tm": 68.5,
                "score": 92.3
            },
            {
                "name": "test_primer_2", 
                "sequence": "ATATATATATATATATAT",  # 0% GC, 18 chars
                "start": 2000,
                "stop": 2018,
                "pool": 4,
                "tm": 45.2,
                "score": 78.9
            }
        ]
        
        primers = []
        for data in primer_data:
            primer = PrimerData(
                name=data["name"],
                sequence=data["sequence"],
                start=data["start"],
                stop=data["stop"],
                strand="+",
                direction="forward",
                pool=data["pool"],
                amplicon_id="test_amplicon",
                tm=data["tm"],
                score=data["score"]
            )
            primers.append(primer)
        
        amplicon = AmpliconData(
            amplicon_id="test_amplicon",
            primers=primers,
            length=500,
            reference_id="test_ref"
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tsv', delete=False) as f:
            output_path = Path(f.name)
        
        try:
            # Write data
            result_path = writer.write([amplicon], output_path)
            
            # Verify all values are preserved correctly
            with open(output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter='\t')
                rows = list(reader)
                
                assert len(rows) == 2
                
                # Check first primer (100% GC)
                row1 = rows[0]
                assert row1['primer_name'] == 'test_primer_1'
                assert row1['seq'] == 'GCGCGCGCGCGCGCGC'
                assert row1['start'] == '1000'
                assert row1['stop'] == '1016'
                assert row1['size'] == '16'
                assert row1['pool'] == '3'
                assert float(row1['gc_best']) == 100.0
                assert float(row1['temp_best']) == 68.5
                assert float(row1['score']) == 92.3
                
                # Check second primer (0% GC)
                row2 = rows[1]
                assert row2['primer_name'] == 'test_primer_2'
                assert row2['seq'] == 'ATATATATATATATATAT'
                assert row2['size'] == '18'
                assert row2['pool'] == '4'
                assert float(row2['gc_best']) == 0.0
                assert float(row2['temp_best']) == 45.2
                assert float(row2['score']) == 78.9
                
        finally:
            if output_path.exists():
                output_path.unlink()