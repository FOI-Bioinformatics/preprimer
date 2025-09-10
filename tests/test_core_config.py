"""
Unit tests for configuration management.

Tests the PrePrimerConfig class including validation, serialization,
and configuration management functionality.
"""

import json
import tempfile
from pathlib import Path

import pytest

from preprimer.core.config import PrePrimerConfig
from preprimer.core.exceptions import ConfigError


class TestPrePrimerConfig:
    """Test the PrePrimerConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PrePrimerConfig()

        assert config.aligner == "blast"
        assert config.alignment_params == {}
        assert config.output_formats == ["artic"]
        assert config.force_overwrite is False
        assert config.default_pool == 1
        assert config.primer_naming_scheme == "artic"
        assert config.validate_sequences is True
        assert config.min_primer_length == 15
        assert config.max_primer_length == 35
        assert config.custom_settings == {}

    def test_config_creation_with_values(self):
        """Test configuration creation with custom values."""
        config = PrePrimerConfig(
            aligner="exonerate",
            output_formats=["fasta", "sts"],
            force_overwrite=True,
            min_primer_length=20,
            max_primer_length=30,
            validate_sequences=False,
            custom_settings={"test": "value"}
        )

        assert config.aligner == "exonerate"
        assert config.output_formats == ["fasta", "sts"]
        assert config.force_overwrite is True
        assert config.min_primer_length == 20
        assert config.max_primer_length == 30
        assert config.validate_sequences is False
        assert config.custom_settings == {"test": "value"}

    def test_config_validation_valid(self):
        """Test configuration validation with valid settings."""
        config = PrePrimerConfig()
        issues = config.validate()
        assert len(issues) == 0

    def test_config_validation_invalid_aligner(self):
        """Test configuration validation with invalid aligner."""
        config = PrePrimerConfig(aligner="invalid_aligner")
        issues = config.validate()
        assert len(issues) > 0
        assert any("Invalid aligner" in issue for issue in issues)

    def test_config_validation_invalid_primer_lengths(self):
        """Test configuration validation with invalid primer lengths."""
        # Minimum too small
        config = PrePrimerConfig(min_primer_length=5)
        issues = config.validate()
        assert any("Minimum primer length should be at least 10" in issue for issue in issues)

        # Maximum too large
        config = PrePrimerConfig(max_primer_length=60)
        issues = config.validate()
        assert any("Maximum primer length should be at most 50" in issue for issue in issues)

        # Min >= Max
        config = PrePrimerConfig(min_primer_length=30, max_primer_length=25)
        issues = config.validate()
        assert any("Minimum primer length must be less than maximum" in issue for issue in issues)

    def test_config_validation_invalid_naming_scheme(self):
        """Test configuration validation with invalid naming scheme."""
        config = PrePrimerConfig(primer_naming_scheme="invalid")
        issues = config.validate()
        assert any("Invalid naming scheme" in issue for issue in issues)

    def test_config_from_dict(self):
        """Test configuration creation from dictionary."""
        data = {
            "aligner": "exonerate",
            "output_formats": ["fasta", "sts"],
            "force_overwrite": True,
            "min_primer_length": 18,
            "max_primer_length": 32,
            "custom_settings": {"key": "value"}
        }

        config = PrePrimerConfig.from_dict(data)
        assert config.aligner == "exonerate"
        assert config.output_formats == ["fasta", "sts"]
        assert config.force_overwrite is True
        assert config.min_primer_length == 18
        assert config.max_primer_length == 32
        assert config.custom_settings == {"key": "value"}

    def test_config_from_dict_with_invalid_keys(self):
        """Test configuration creation from dictionary with invalid keys."""
        data = {
            "aligner": "blast",
            "invalid_key": "should_be_ignored",
            "another_invalid": 123
        }

        config = PrePrimerConfig.from_dict(data)
        assert config.aligner == "blast"
        # Invalid keys should be ignored
        assert not hasattr(config, "invalid_key")
        assert not hasattr(config, "another_invalid")

    def test_config_to_dict(self):
        """Test configuration serialization to dictionary."""
        config = PrePrimerConfig(
            aligner="exonerate",
            output_formats=["fasta"],
            force_overwrite=True,
            custom_settings={"test": "data"}
        )

        data = config.to_dict()
        expected_keys = {
            "aligner", "alignment_params", "output_formats", "force_overwrite",
            "default_pool", "primer_naming_scheme", "validate_sequences",
            "min_primer_length", "max_primer_length", "custom_settings"
        }

        assert set(data.keys()) == expected_keys
        assert data["aligner"] == "exonerate"
        assert data["output_formats"] == ["fasta"]
        assert data["force_overwrite"] is True
        assert data["custom_settings"] == {"test": "data"}


class TestConfigFileSerialization:
    """Test configuration file operations."""

    def test_config_save_and_load(self):
        """Test saving and loading configuration to/from file."""
        config = PrePrimerConfig(
            aligner="exonerate",
            output_formats=["fasta", "sts"],
            force_overwrite=True,
            min_primer_length=18,
            custom_settings={"key": "value"}
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)

        try:
            # Save configuration
            config.save(config_path)
            assert config_path.exists()

            # Load configuration
            loaded_config = PrePrimerConfig.from_file(config_path)

            # Verify loaded configuration matches original
            assert loaded_config.aligner == config.aligner
            assert loaded_config.output_formats == config.output_formats
            assert loaded_config.force_overwrite == config.force_overwrite
            assert loaded_config.min_primer_length == config.min_primer_length
            assert loaded_config.custom_settings == config.custom_settings

        finally:
            if config_path.exists():
                config_path.unlink()

    def test_config_save_creates_directory(self):
        """Test that saving configuration creates necessary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "subdir" / "config.json"
            
            config = PrePrimerConfig()
            config.save(config_path)

            assert config_path.exists()
            assert config_path.parent.exists()

    def test_config_from_file_not_found(self):
        """Test loading configuration from non-existent file."""
        with pytest.raises(ConfigError, match="Configuration file not found"):
            PrePrimerConfig.from_file("non_existent_file.json")

    def test_config_from_file_invalid_json(self):
        """Test loading configuration from file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content {")
            config_path = Path(f.name)

        try:
            with pytest.raises(ConfigError, match="Invalid JSON"):
                PrePrimerConfig.from_file(config_path)
        finally:
            config_path.unlink()

    def test_config_file_roundtrip(self):
        """Test complete roundtrip: create -> save -> load -> compare."""
        original_config = PrePrimerConfig(
            aligner="exonerate",
            alignment_params={"param1": "value1"},
            output_formats=["fasta", "sts", "varvamp"],
            force_overwrite=True,
            default_pool=2,
            primer_naming_scheme="custom",
            validate_sequences=False,
            min_primer_length=18,
            max_primer_length=32,
            custom_settings={"custom": "data", "number": 42}
        )

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_path = Path(f.name)

        try:
            # Save and reload
            original_config.save(config_path)
            loaded_config = PrePrimerConfig.from_file(config_path)

            # Compare all fields
            assert loaded_config.aligner == original_config.aligner
            assert loaded_config.alignment_params == original_config.alignment_params
            assert loaded_config.output_formats == original_config.output_formats
            assert loaded_config.force_overwrite == original_config.force_overwrite
            assert loaded_config.default_pool == original_config.default_pool
            assert loaded_config.primer_naming_scheme == original_config.primer_naming_scheme
            assert loaded_config.validate_sequences == original_config.validate_sequences
            assert loaded_config.min_primer_length == original_config.min_primer_length
            assert loaded_config.max_primer_length == original_config.max_primer_length
            assert loaded_config.custom_settings == original_config.custom_settings

        finally:
            if config_path.exists():
                config_path.unlink()


class TestConfigValidationComprehensive:
    """Comprehensive configuration validation tests."""

    def test_all_valid_aligners(self):
        """Test all valid aligner options."""
        valid_aligners = ["blast", "exonerate"]
        
        for aligner in valid_aligners:
            config = PrePrimerConfig(aligner=aligner)
            issues = config.validate()
            assert len(issues) == 0, f"Aligner {aligner} should be valid"

    def test_all_valid_naming_schemes(self):
        """Test all valid naming scheme options."""
        valid_schemes = ["artic", "custom"]
        
        for scheme in valid_schemes:
            config = PrePrimerConfig(primer_naming_scheme=scheme)
            issues = config.validate()
            assert len(issues) == 0, f"Naming scheme {scheme} should be valid"

    def test_primer_length_boundary_values(self):
        """Test primer length validation with boundary values."""
        # Valid boundary values
        config = PrePrimerConfig(min_primer_length=10, max_primer_length=50)
        issues = config.validate()
        assert len(issues) == 0

        # Valid range
        config = PrePrimerConfig(min_primer_length=15, max_primer_length=35)
        issues = config.validate()
        assert len(issues) == 0

        # Invalid boundaries
        config = PrePrimerConfig(min_primer_length=9, max_primer_length=51)
        issues = config.validate()
        assert len(issues) >= 2  # Both min and max should be invalid

    def test_complex_validation_scenario(self):
        """Test configuration with multiple validation issues."""
        config = PrePrimerConfig(
            aligner="invalid_aligner",
            min_primer_length=5,  # Too small
            max_primer_length=60,  # Too large
            primer_naming_scheme="invalid_scheme"
        )

        issues = config.validate()
        assert len(issues) >= 4  # Should have multiple issues
        
        issue_text = " ".join(issues)
        assert "Invalid aligner" in issue_text
        assert "Minimum primer length" in issue_text
        assert "Maximum primer length" in issue_text
        assert "Invalid naming scheme" in issue_text


class TestConfigDefaults:
    """Test configuration default behavior."""

    def test_default_config_is_valid(self):
        """Ensure default configuration passes validation."""
        config = PrePrimerConfig()
        issues = config.validate()
        assert len(issues) == 0, f"Default config should be valid, but has issues: {issues}"

    def test_default_config_serialization(self):
        """Test that default configuration can be serialized."""
        config = PrePrimerConfig()
        data = config.to_dict()
        
        # Should be able to recreate from dict
        new_config = PrePrimerConfig.from_dict(data)
        
        # Should match original
        assert new_config.to_dict() == data