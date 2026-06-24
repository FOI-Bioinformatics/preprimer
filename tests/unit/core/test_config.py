"""
Comprehensive tests for the enhanced configuration system.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
from pydantic import ValidationError

from preprimer.core.enhanced_config import (
    AlignmentSettings,
    EnhancedConfig,
    LoggingSettings,
    OutputSettings,
    ParserSettings,
    PluginSettings,
    SecuritySettings,
    ValidationSettings,
)
from preprimer.core.exceptions import ConfigError


class TestPydanticValidation:
    """Test pydantic validation features."""

    def test_basic_validation(self):
        """Test basic configuration validation."""
        config = EnhancedConfig()

        # Should have sensible defaults
        assert config.alignment.aligner == "blast"
        assert config.validation.enabled == True
        assert config.output.formats == ["artic"]
        assert config.parser.default_pool == 1
        assert config.plugins.enabled == True

    def test_invalid_aligner_validation(self):
        """Test validation of invalid aligner."""
        with pytest.raises(ValueError, match="Aligner must be one of"):
            AlignmentSettings(aligner="invalid_aligner")

    def test_primer_length_validation(self):
        """Test primer length validation."""
        # Valid lengths
        settings = ValidationSettings(min_length=15, max_length=35)
        assert settings.min_length == 15
        assert settings.max_length == 35

        # Invalid range - Pydantic field constraint validation occurs first
        with pytest.raises(ValidationError):
            ValidationSettings(min_length=30, max_length=25)

        # Test our model validator with values that pass field constraints
        with pytest.raises(
            ValueError, match="max_length must be greater than min_length"
        ):
            ValidationSettings(min_length=25, max_length=25)  # Equal values should fail

    def test_gc_content_validation(self):
        """Test GC content validation."""
        # Valid GC range
        settings = ValidationSettings(min_gc=0.3, max_gc=0.7)
        assert settings.min_gc == 0.3
        assert settings.max_gc == 0.7

        # Invalid range
        with pytest.raises(ValueError, match="max_gc must be greater than min_gc"):
            ValidationSettings(min_gc=0.8, max_gc=0.6)

    def test_tm_validation(self):
        """Test melting temperature validation."""
        # Valid Tm range
        settings = ValidationSettings(min_tm=50.0, max_tm=70.0)
        assert settings.min_tm == 50.0
        assert settings.max_tm == 70.0

        # Invalid range
        with pytest.raises(ValueError, match="max_tm must be greater than min_tm"):
            ValidationSettings(min_tm=75.0, max_tm=65.0)

    def test_output_format_validation(self):
        """Test output format validation."""
        # Valid formats (artic, fasta, varvamp, sts, olivar)
        settings = OutputSettings(formats=["artic", "fasta", "sts"])
        assert settings.formats == ["artic", "fasta", "sts"]

        # Invalid format
        with pytest.raises(ValueError, match="Invalid output formats"):
            OutputSettings(formats=["artic", "invalid_format"])

    def test_compression_validation(self):
        """Test compression format validation."""
        # Valid compression
        settings = OutputSettings(compression="gzip")
        assert settings.compression == "gzip"

        # Invalid compression
        with pytest.raises(ValueError, match="Compression must be one of"):
            OutputSettings(compression="invalid_compression")

    def test_naming_scheme_validation(self):
        """Test naming scheme validation."""
        # Valid scheme
        settings = ParserSettings(naming_scheme="artic")
        assert settings.naming_scheme == "artic"

        # Invalid scheme
        with pytest.raises(ValueError, match="Naming scheme must be one of"):
            ParserSettings(naming_scheme="invalid_scheme")

    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid level (case insensitive)
        settings = LoggingSettings(level="debug")
        assert settings.level == "DEBUG"

        # Invalid level
        with pytest.raises(ValueError, match="Log level must be one of"):
            LoggingSettings(level="invalid_level")

    def test_field_constraints(self):
        """Test field constraints and ranges."""
        # Test integer constraints
        alignment = AlignmentSettings(threads=16, timeout=600)
        assert alignment.threads == 16
        assert alignment.timeout == 600

        # Test constraint violations
        with pytest.raises(ValueError):
            AlignmentSettings(threads=0)  # Below minimum

        with pytest.raises(ValueError):
            AlignmentSettings(threads=100)  # Above maximum


class TestEnvironmentVariables:
    """Test environment variable support."""

    def test_from_env_basic(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            "PREPRIMER_ALIGNER": "merpcr",
            "PREPRIMER_ALIGNMENT_THREADS": "8",
            "PREPRIMER_VALIDATE_SEQUENCES": "false",
            "PREPRIMER_OUTPUT_FORMATS": "artic,fasta,sts",
            "PREPRIMER_DEBUG_MODE": "true",
            "PREPRIMER_LOG_LEVEL": "DEBUG",
        }

        with patch.dict(os.environ, env_vars):
            config = EnhancedConfig.from_env()

            assert config.alignment.aligner == "merpcr"
            assert config.alignment.threads == 8
            assert config.validation.enabled == False
            assert config.output.formats == ["artic", "fasta", "sts"]
            assert config.debug_mode == True
            assert config.logging.level == "DEBUG"

    def test_from_env_custom_prefix(self):
        """Test environment variables with custom prefix."""
        env_vars = {"MYAPP_ALIGNER": "blast", "MYAPP_DEBUG_MODE": "true"}

        with patch.dict(os.environ, env_vars):
            config = EnhancedConfig.from_env(prefix="MYAPP_")

            assert config.alignment.aligner == "blast"
            assert config.debug_mode == True

    def test_env_type_conversion(self):
        """Test environment variable type conversion."""
        env_vars = {
            "PREPRIMER_ALIGNMENT_THREADS": "4",
            "PREPRIMER_MIN_PRIMER_LENGTH": "18",
            "PREPRIMER_FORCE_OVERWRITE": "yes",
            "PREPRIMER_VALIDATE_SEQUENCES": "1",
            "PREPRIMER_DEBUG_MODE": "on",
        }

        with patch.dict(os.environ, env_vars):
            config = EnhancedConfig.from_env()

            assert config.alignment.threads == 4
            assert config.validation.min_length == 18
            assert config.output.force_overwrite == True
            assert config.validation.enabled == True
            assert config.debug_mode == True


class TestFileConfiguration:
    """Test file-based configuration."""

    def test_json_configuration(self):
        """Test loading configuration from JSON file."""
        config_data = {
            "alignment": {"aligner": "exonerate", "threads": 6},
            "validation": {"min_length": 20, "max_length": 30},
            "output": {"formats": ["fasta", "sts"], "force_overwrite": True},
            "debug_mode": True,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            config = EnhancedConfig.from_file(config_path, merge_env=False)

            assert config.alignment.aligner == "exonerate"
            assert config.alignment.threads == 6
            assert config.validation.min_length == 20
            assert config.validation.max_length == 30
            assert config.output.formats == ["fasta", "sts"]
            assert config.output.force_overwrite == True
            assert config.debug_mode == True

        finally:
            Path(config_path).unlink()

    def test_yaml_configuration(self):
        """Test loading configuration from YAML file."""
        config_data = {
            "alignment": {
                "aligner": "exonerate",
                "threads": 8,
                "params": {"preset": "sr"},
            },
            "plugins": {
                "enabled": True,
                "config": {"my_plugin": {"option1": "value1", "option2": 42}},
            },
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.safe_dump(config_data, f)
            config_path = f.name

        try:
            config = EnhancedConfig.from_file(config_path, merge_env=False)

            assert config.alignment.aligner == "exonerate"
            assert config.alignment.threads == 8
            assert config.alignment.params == {"preset": "sr"}
            assert config.plugins.enabled == True
            assert config.plugins.config["my_plugin"]["option1"] == "value1"
            assert config.plugins.config["my_plugin"]["option2"] == 42

        finally:
            Path(config_path).unlink()

    def test_file_with_env_merge(self):
        """Test merging file configuration with environment variables."""
        config_data = {
            "alignment": {"aligner": "blast", "threads": 4},
            "debug_mode": False,
        }

        env_vars = {
            "PREPRIMER_ALIGNER": "merpcr",  # Should override file
            "PREPRIMER_VALIDATE_SEQUENCES": "false",  # Should add to config
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(config_data, f)
            config_path = f.name

        try:
            with patch.dict(os.environ, env_vars):
                config = EnhancedConfig.from_file(config_path, merge_env=True)

                # File should override env for threads
                assert config.alignment.threads == 4
                # File should override env for aligner
                assert config.alignment.aligner == "blast"
                # Env should set validation.enabled
                assert config.validation.enabled == False
                # File should set debug_mode
                assert config.debug_mode == False

        finally:
            Path(config_path).unlink()

    def test_invalid_file_handling(self):
        """Test handling of invalid configuration files."""
        # Non-existent file
        with pytest.raises(ConfigError, match="Configuration file not found"):
            EnhancedConfig.from_file("/nonexistent/config.json")

        # Invalid JSON
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            config_path = f.name

        try:
            with pytest.raises(ConfigError, match="Failed to parse config file"):
                EnhancedConfig.from_file(config_path)
        finally:
            Path(config_path).unlink()

    def test_save_configuration(self):
        """Test saving configuration to file."""
        config = EnhancedConfig(
            alignment=AlignmentSettings(aligner="exonerate", threads=8), debug_mode=True
        )

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            json_path = f.name

        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            yaml_path = f.name

        try:
            # Test JSON save
            config.save(json_path, format="json")
            assert Path(json_path).exists()

            with open(json_path) as f:
                saved_data = json.load(f)
                assert saved_data["alignment"]["aligner"] == "exonerate"
                assert saved_data["debug_mode"] == True

            # Test YAML save
            config.save(yaml_path, format="yaml")
            assert Path(yaml_path).exists()

            with open(yaml_path) as f:
                saved_data = yaml.safe_load(f)
                assert saved_data["alignment"]["aligner"] == "exonerate"
                assert saved_data["debug_mode"] == True

        finally:
            Path(json_path).unlink(missing_ok=True)
            Path(yaml_path).unlink(missing_ok=True)


class TestPluginConfiguration:
    """Test plugin-specific configuration features."""

    def test_plugin_config_management(self):
        """Test plugin configuration management."""
        config = EnhancedConfig()

        # Initially no plugin config
        assert config.get_plugin_config("test_plugin") == {}

        # Set plugin config
        plugin_settings = {"option1": "value1", "option2": 42}
        config.set_plugin_config("test_plugin", plugin_settings)

        # Retrieve plugin config
        retrieved = config.get_plugin_config("test_plugin")
        assert retrieved == plugin_settings

        # Update plugin config
        config.set_plugin_config("test_plugin", {"option3": "value3"})
        updated = config.get_plugin_config("test_plugin")
        assert updated["option1"] == "value1"  # Preserved
        assert updated["option3"] == "value3"  # Added

    def test_plugin_settings_validation(self):
        """Test plugin settings validation."""
        # Valid plugin settings
        settings = PluginSettings(
            enabled=True,
            search_paths=["/path1", "/path2"],
            whitelist=["plugin1", "plugin2"],
            blacklist=["bad_plugin"],
            config={"plugin1": {"setting": "value"}},
        )

        assert settings.enabled == True
        assert settings.search_paths == ["/path1", "/path2"]
        assert settings.whitelist == ["plugin1", "plugin2"]
        assert settings.blacklist == ["bad_plugin"]
        assert settings.config["plugin1"]["setting"] == "value"


class TestSecuritySettings:
    """Test security-related configuration."""

    def test_security_settings_defaults(self):
        """Test security settings defaults."""
        settings = SecuritySettings()

        assert settings.allow_remote_files == False
        assert settings.max_file_size == 100 * 1024 * 1024  # 100MB
        assert settings.allowed_extensions == None
        assert settings.sandbox_mode == False
        assert settings.validate_paths == True

    def test_security_settings_validation(self):
        """Test security settings validation."""
        # Valid settings
        settings = SecuritySettings(
            allow_remote_files=True,
            max_file_size=50 * 1024 * 1024,
            allowed_extensions=[".tsv", ".txt", ".fasta"],
            sandbox_mode=True,
        )

        assert settings.allow_remote_files == True
        assert settings.max_file_size == 50 * 1024 * 1024
        assert settings.allowed_extensions == [".tsv", ".txt", ".fasta"]
        assert settings.sandbox_mode == True


class TestComplexScenarios:
    """Test complex configuration scenarios."""

    def test_nested_configuration_merge(self):
        """Test deep merging of nested configurations."""
        # Base configuration
        base_data = {
            "alignment": {
                "aligner": "blast",
                "threads": 4,
                "params": {"evalue": 0.001},
            },
            "validation": {"enabled": True, "min_length": 15},
        }

        # Override configuration
        override_data = {
            "alignment": {
                "threads": 8,
                "params": {"max_targets": 10},  # Should merge with evalue
            },
            "debug_mode": True,
        }

        merged = EnhancedConfig._deep_merge(base_data, override_data)

        assert merged["alignment"]["aligner"] == "blast"  # Preserved
        assert merged["alignment"]["threads"] == 8  # Overridden
        assert merged["alignment"]["params"]["evalue"] == 0.001  # Preserved
        assert merged["alignment"]["params"]["max_targets"] == 10  # Added
        assert merged["validation"]["enabled"] == True  # Preserved
        assert merged["debug_mode"] == True  # Added

    def test_configuration_validation_error_handling(self):
        """Test handling of validation errors in configuration."""
        # Test that pydantic validation errors are properly handled
        with pytest.raises(ValueError):
            EnhancedConfig(
                alignment=AlignmentSettings(aligner="invalid"),
                validation=ValidationSettings(
                    min_length=50, max_length=30
                ),  # Invalid range
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
