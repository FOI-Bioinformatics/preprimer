"""
Comprehensive tests for PrimerschemeInfo module covering all error paths and edge cases.

Focuses on the missed coverage areas to improve overall module coverage.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from preprimer.core.primerscheme_info import (
    PrimerschemeInfo,
    calculate_md5,
    generate_info_json,
    validate_primerscheme_directory,
)


class TestPrimerschemeInfoValidation:
    """Test validation error paths in PrimerschemeInfo."""

    def test_empty_schemename_validation(self):
        """Test validation error for empty schemename."""
        with pytest.raises(ValueError, match="schemename cannot be empty"):
            PrimerschemeInfo(
                schemename="",  # Empty name should fail
                schemeversion="v1.0.0",
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )

    def test_invalid_schemename_characters(self):
        """Test validation error for invalid characters in schemename."""
        with pytest.raises(
            ValueError,
            match="schemename must be lowercase alphanumeric with hyphens only",
        ):
            PrimerschemeInfo(
                schemename="Invalid_Name!",  # Contains invalid characters
                schemeversion="v1.0.0",
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )

    def test_schemename_starts_with_hyphen(self):
        """Test validation error for schemename starting with hyphen."""
        with pytest.raises(
            ValueError, match="schemename cannot start or end with hyphen"
        ):
            PrimerschemeInfo(
                schemename="-invalid-name",  # Starts with hyphen
                schemeversion="v1.0.0",
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )

    def test_schemename_ends_with_hyphen(self):
        """Test validation error for schemename ending with hyphen."""
        with pytest.raises(
            ValueError, match="schemename cannot start or end with hyphen"
        ):
            PrimerschemeInfo(
                schemename="invalid-name-",  # Ends with hyphen
                schemeversion="v1.0.0",
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )

    def test_invalid_schemeversion_format(self):
        """Test validation error for invalid schemeversion format."""
        with pytest.raises(ValueError, match="schemeversion must follow format"):
            PrimerschemeInfo(
                schemename="valid-name",
                schemeversion="1.0.0",  # Missing 'v' prefix
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )

    def test_negative_ampliconsize(self):
        """Test validation error for negative ampliconsize."""
        with pytest.raises(ValueError, match="ampliconsize must be a positive integer"):
            PrimerschemeInfo(
                schemename="valid-name",
                schemeversion="v1.0.0",
                ampliconsize=-100,  # Negative size
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )

    def test_zero_ampliconsize(self):
        """Test validation error for zero ampliconsize."""
        with pytest.raises(ValueError, match="ampliconsize must be a positive integer"):
            PrimerschemeInfo(
                schemename="valid-name",
                schemeversion="v1.0.0",
                ampliconsize=0,  # Zero size
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )

    def test_non_integer_ampliconsize(self):
        """Test validation error for non-integer ampliconsize."""
        with pytest.raises(ValueError, match="ampliconsize must be a positive integer"):
            PrimerschemeInfo(
                schemename="valid-name",
                schemeversion="v1.0.0",
                ampliconsize="200",  # String instead of int
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )


class TestPrimerschemeInfoFactoryMethods:
    """Test factory method edge cases and error handling."""

    def test_from_dict_missing_default_factory_fields(self):
        """Test from_dict handles missing default factory fields."""
        data = {
            "schemename": "test-scheme",
            "schemeversion": "v1.0.0",
            "ampliconsize": 200,
            "species": "SARS-CoV-2",
            "primer_bed_md5": "abc123",
            "reference_fasta_md5": "def456",
            # Missing: authors, citations, collections
        }

        info = PrimerschemeInfo.from_dict(data)

        # Should have empty lists for default factory fields
        assert info.authors == []
        assert info.citations == []
        assert info.collections == []

    def test_from_dict_missing_preprimer_fields(self):
        """Test from_dict handles missing PrePrimer-specific fields."""
        data = {
            "schemename": "test-scheme",
            "schemeversion": "v1.0.0",
            "ampliconsize": 200,
            "species": "SARS-CoV-2",
            "primer_bed_md5": "abc123",
            "reference_fasta_md5": "def456",
            # Missing: created_by, created_date
        }

        info = PrimerschemeInfo.from_dict(data)

        # Should have default values
        assert info.created_by == "External"
        assert info.created_date is not None  # Should be auto-generated

    def test_from_json_invalid_json(self):
        """Test from_json with invalid JSON string."""
        invalid_json = '{"schemename": "test", invalid json'

        with pytest.raises(json.JSONDecodeError):
            PrimerschemeInfo.from_json(invalid_json)

    def test_from_file_nonexistent_file(self):
        """Test from_file with non-existent file."""
        with pytest.raises(FileNotFoundError):
            PrimerschemeInfo.from_file("/nonexistent/path/info.json")

    def test_from_file_invalid_json_content(self):
        """Test from_file with file containing invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write('{"invalid": json content}')
            temp_path = Path(f.name)

        try:
            with pytest.raises(json.JSONDecodeError):
                PrimerschemeInfo.from_file(temp_path)
        finally:
            temp_path.unlink()


class TestCalculateMD5:
    """Test MD5 calculation function error handling."""

    def test_calculate_md5_file_not_found(self):
        """Test calculate_md5 with non-existent file."""
        with pytest.raises(FileNotFoundError, match="File not found"):
            calculate_md5("/nonexistent/file.txt")

    def test_calculate_md5_valid_file(self):
        """Test calculate_md5 with valid file."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("test content for MD5 calculation")
            temp_path = Path(f.name)

        try:
            md5_hash = calculate_md5(temp_path)
            # Should return a valid MD5 hash (32 hex characters)
            assert len(md5_hash) == 32
            assert all(c in "0123456789abcdef" for c in md5_hash)
        finally:
            temp_path.unlink()


class TestGenerateInfoJson:
    """Test generate_info_json function with various scenarios."""

    def test_generate_info_json_with_all_files(self):
        """Test generate_info_json with all required files present."""
        # Create temporary files for testing
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".bed", delete=False
        ) as primer_file:
            primer_file.write("chr1\t100\t120\tprimer1\t1\t+\n")
            primer_path = Path(primer_file.name)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".fasta", delete=False
        ) as ref_file:
            ref_file.write(">reference\nACTGACTGACTG\n")
            ref_path = Path(ref_file.name)

        try:
            info = generate_info_json(
                schemename="test-scheme",
                schemeversion="v1.0.0",
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_path=primer_path,
                reference_fasta_path=ref_path,
                authors=["Test Author"],
                description="Test description",
                collections=["TEST"],
            )

            assert info.schemename == "test-scheme"
            assert info.schemeversion == "v1.0.0"
            assert info.ampliconsize == 200
            assert info.species == "SARS-CoV-2"
            assert info.authors == ["Test Author"]
            assert info.description == "Test description"
            assert info.collections == ["TEST"]
            assert len(info.primer_bed_md5) == 32  # Valid MD5
            assert len(info.reference_fasta_md5) == 32  # Valid MD5

        finally:
            primer_path.unlink()
            ref_path.unlink()


class TestValidatePrimerschemeDirectory:
    """Test directory validation function - mostly uncovered area."""

    def test_validate_nonexistent_directory(self):
        """Test validation of non-existent directory."""
        result = validate_primerscheme_directory("/nonexistent/directory")

        expected = {
            "directory_exists": False,
            "primer_bed_exists": False,
            "reference_fasta_exists": False,
            "info_json_exists": False,
            "info_json_valid": False,
            "md5_hashes_match": False,
        }

        assert result == expected

    def test_validate_empty_directory(self):
        """Test validation of empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = validate_primerscheme_directory(temp_dir)

            expected = {
                "directory_exists": True,
                "primer_bed_exists": False,
                "reference_fasta_exists": False,
                "info_json_exists": False,
                "info_json_valid": False,
                "md5_hashes_match": False,
            }

            assert result == expected

    def test_validate_directory_with_invalid_info_json(self):
        """Test validation with invalid info.json file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create invalid info.json
            info_file = temp_path / "info.json"
            info_file.write_text('{"invalid": json content}')

            result = validate_primerscheme_directory(temp_path)

            assert result["directory_exists"] is True
            assert result["info_json_exists"] is True
            assert result["info_json_valid"] is False  # Invalid JSON
            assert result["md5_hashes_match"] is False

    def test_validate_directory_with_valid_info_json_no_files(self):
        """Test validation with valid info.json but missing bed/fasta files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create valid info.json
            info = PrimerschemeInfo(
                schemename="test-scheme",
                schemeversion="v1.0.0",
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )
            info.save(temp_path / "info.json")

            result = validate_primerscheme_directory(temp_path)

            assert result["directory_exists"] is True
            assert result["info_json_exists"] is True
            assert result["info_json_valid"] is True
            assert result["primer_bed_exists"] is False
            assert result["reference_fasta_exists"] is False
            assert result["md5_hashes_match"] is False

    def test_validate_complete_valid_directory(self):
        """Test validation of complete valid primerscheme directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create primer.bed file
            primer_file = temp_path / "primer.bed"
            primer_file.write_text("chr1\t100\t120\tprimer1\t1\t+\n")

            # Create reference.fasta file
            ref_file = temp_path / "reference.fasta"
            ref_file.write_text(">reference\nACTGACTGACTG\n")

            # Calculate actual MD5 hashes
            primer_md5 = calculate_md5(primer_file)
            ref_md5 = calculate_md5(ref_file)

            # Create info.json with correct hashes
            info = PrimerschemeInfo(
                schemename="test-scheme",
                schemeversion="v1.0.0",
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5=primer_md5,
                reference_fasta_md5=ref_md5,
            )
            info.save(temp_path / "info.json")

            result = validate_primerscheme_directory(temp_path)

            # All validations should pass
            assert result["directory_exists"] is True
            assert result["primer_bed_exists"] is True
            assert result["reference_fasta_exists"] is True
            assert result["info_json_exists"] is True
            assert result["info_json_valid"] is True
            assert result["md5_hashes_match"] is True

    def test_validate_directory_with_mismatched_md5(self):
        """Test validation with MD5 hash mismatch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create primer.bed and reference.fasta files
            primer_file = temp_path / "primer.bed"
            primer_file.write_text("chr1\t100\t120\tprimer1\t1\t+\n")

            ref_file = temp_path / "reference.fasta"
            ref_file.write_text(">reference\nACTGACTGACTG\n")

            # Create info.json with WRONG MD5 hashes
            info = PrimerschemeInfo(
                schemename="test-scheme",
                schemeversion="v1.0.0",
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5="wrong_hash_123",
                reference_fasta_md5="wrong_hash_456",
            )
            info.save(temp_path / "info.json")

            result = validate_primerscheme_directory(temp_path)

            assert result["directory_exists"] is True
            assert result["primer_bed_exists"] is True
            assert result["reference_fasta_exists"] is True
            assert result["info_json_exists"] is True
            assert result["info_json_valid"] is True
            assert result["md5_hashes_match"] is False  # Mismatched hashes


class TestPrimerschemeInfoSerialization:
    """Test serialization and deserialization edge cases."""

    def test_to_dict_filters_none_values(self):
        """Test that to_dict filters out None values."""
        info = PrimerschemeInfo(
            schemename="test-scheme",
            schemeversion="v1.0.0",
            ampliconsize=200,
            species="SARS-CoV-2",
            primer_bed_md5="abc123",
            reference_fasta_md5="def456",
            description=None,  # None value should be filtered
            algorithmversion=None,  # None value should be filtered
        )

        result = info.to_dict()

        # None values should not be in the dictionary
        assert "description" not in result
        assert "algorithmversion" not in result

        # Required values should be present
        assert result["schemename"] == "test-scheme"
        assert result["ampliconsize"] == 200

    def test_save_and_load_roundtrip(self):
        """Test complete save/load roundtrip."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            # Create original info
            original = PrimerschemeInfo(
                schemename="test-scheme",
                schemeversion="v1.0.0",
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
                authors=["Test Author"],
                collections=["TEST", "VALIDATION"],
            )

            # Save to file
            original.save(temp_path)

            # Load from file
            loaded = PrimerschemeInfo.from_file(temp_path)

            # Should be equivalent
            assert loaded.schemename == original.schemename
            assert loaded.schemeversion == original.schemeversion
            assert loaded.ampliconsize == original.ampliconsize
            assert loaded.species == original.species
            assert loaded.primer_bed_md5 == original.primer_bed_md5
            assert loaded.reference_fasta_md5 == original.reference_fasta_md5
            assert loaded.authors == original.authors
            assert loaded.collections == original.collections

        finally:
            temp_path.unlink(missing_ok=True)


class TestSchemeVersionValidationEdgeCases:
    """Test additional edge cases for scheme version validation."""

    def test_valid_schemeversion_with_suffix(self):
        """Test that version with suffix is accepted."""
        # Should not raise error
        info = PrimerschemeInfo(
            schemename="test-scheme",
            schemeversion="v1.0.0-beta",  # With suffix
            ampliconsize=200,
            species="SARS-CoV-2",
            primer_bed_md5="abc123",
            reference_fasta_md5="def456",
        )
        assert info.schemeversion == "v1.0.0-beta"

    def test_invalid_schemeversion_missing_v(self):
        """Test version validation without 'v' prefix."""
        with pytest.raises(ValueError, match="schemeversion must follow format"):
            PrimerschemeInfo(
                schemename="test-scheme",
                schemeversion="1.0.0",  # Missing v prefix
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )

    def test_invalid_schemeversion_wrong_pattern(self):
        """Test version validation with wrong pattern."""
        with pytest.raises(ValueError, match="schemeversion must follow format"):
            PrimerschemeInfo(
                schemename="test-scheme",
                schemeversion="v1.0",  # Missing patch version
                ampliconsize=200,
                species="SARS-CoV-2",
                primer_bed_md5="abc123",
                reference_fasta_md5="def456",
            )
