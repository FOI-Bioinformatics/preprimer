#!/usr/bin/env python3
"""
Demonstration of the enhanced configuration system with environment variables,
pydantic validation, plugin settings, and runtime reconfiguration.
"""

import json
import os
import tempfile
import time
from pathlib import Path

from preprimer.core.enhanced_config import (
    AlignmentSettings,
    ConfigManager,
    EnhancedConfig,
    OutputSettings,
    ParserSettings,
    ValidationSettings,
    get_config,
    update_config_partial,
)


def demo_basic_configuration():
    """Demonstrate basic configuration creation and validation."""
    print("=== Basic Configuration Demo ===")

    # Create configuration with custom settings
    config = EnhancedConfig(
        alignment=AlignmentSettings(
            aligner="minimap2", threads=8, params={"preset": "sr", "secondary": "no"}
        ),
        validation=ValidationSettings(
            min_length=18, max_length=32, min_gc=0.35, max_gc=0.65
        ),
        output=OutputSettings(
            formats=["artic", "fasta", "bed"], force_overwrite=True, compression="gzip"
        ),
        debug_mode=True,
    )

    print(f"Aligner: {config.alignment.aligner}")
    print(f"Threads: {config.alignment.threads}")
    print(
        f"Primer length range: {config.validation.min_length}-{config.validation.max_length}"
    )
    print(f"Output formats: {config.output.formats}")
    print(f"Debug mode: {config.debug_mode}")
    print()


def demo_environment_variables():
    """Demonstrate environment variable configuration."""
    print("=== Environment Variables Demo ===")

    # Set environment variables
    env_vars = {
        "PREPRIMER_ALIGNER": "blast",
        "PREPRIMER_ALIGNMENT_THREADS": "12",
        "PREPRIMER_OUTPUT_FORMATS": "artic,fasta,tsv",
        "PREPRIMER_DEBUG_MODE": "true",
        "PREPRIMER_LOG_LEVEL": "DEBUG",
    }

    # Temporarily set environment variables
    old_env = {}
    for key, value in env_vars.items():
        old_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        # Load configuration from environment
        config = EnhancedConfig.from_env()

        print(f"Aligner from env: {config.alignment.aligner}")
        print(f"Threads from env: {config.alignment.threads}")
        print(f"Output formats from env: {config.output.formats}")
        print(f"Debug mode from env: {config.debug_mode}")
        print(f"Log level from env: {config.logging.level}")
        print()

    finally:
        # Restore environment
        for key, old_value in old_env.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value


def demo_file_configuration():
    """Demonstrate file-based configuration."""
    print("=== File Configuration Demo ===")

    # Create a configuration file
    config_data = {
        "alignment": {
            "aligner": "exonerate",
            "threads": 6,
            "timeout": 600,
            "params": {"model": "protein2dna"},
        },
        "validation": {
            "enabled": True,
            "min_length": 20,
            "max_length": 28,
            "check_tm": True,
            "min_tm": 55.0,
            "max_tm": 65.0,
        },
        "output": {
            "formats": ["artic", "bed"],
            "create_directories": True,
            "preserve_metadata": True,
        },
        "plugins": {
            "enabled": True,
            "config": {
                "quality_check": {"strict_mode": True, "min_quality": 0.8},
                "custom_formatter": {
                    "template": "custom_template.txt",
                    "options": {"include_metadata": True},
                },
            },
        },
        "custom": {
            "project_name": "COVID-19 Surveillance",
            "version": "2.1.0",
            "contact": "researcher@example.com",
        },
    }

    # Save to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f, indent=2)
        config_path = Path(f.name)

    try:
        # Load configuration from file
        config = EnhancedConfig.from_file(config_path, merge_env=False)

        print(f"Loaded from: {config_path}")
        print(f"Aligner: {config.alignment.aligner}")
        print(f"Threads: {config.alignment.threads}")
        print(f"Timeout: {config.alignment.timeout}")
        print(f"Validation enabled: {config.validation.enabled}")
        print(f"Tm range: {config.validation.min_tm}-{config.validation.max_tm}")
        print(f"Plugin config: {config.plugins.config}")
        print(f"Custom settings: {config.custom}")

        # Demonstrate plugin configuration access
        quality_config = config.get_plugin_config("quality_check")
        print(f"Quality check config: {quality_config}")
        print()

    finally:
        config_path.unlink()


def demo_runtime_reconfiguration():
    """Demonstrate runtime reconfiguration."""
    print("=== Runtime Reconfiguration Demo ===")

    # Create a configuration manager
    manager = ConfigManager()

    # Track configuration changes
    change_log = []

    def log_changes(new_config):
        change_log.append(
            f"Config changed: debug_mode={new_config.debug_mode}, threads={new_config.alignment.threads}"
        )

    manager.add_change_callback(log_changes)

    print("Initial config:")
    initial = manager.config
    print(f"  Debug mode: {initial.debug_mode}")
    print(f"  Threads: {initial.alignment.threads}")

    # Partial updates
    print("\nUpdating debug mode...")
    manager.update_partial(debug_mode=True)

    print("Updating alignment threads...")
    manager.update_partial(**{"alignment.threads": 16})

    print("Updating multiple settings...")
    manager.update_partial(
        debug_mode=False,
        **{"validation.min_length": 22, "output.force_overwrite": True},
    )

    # Show final config
    final = manager.config
    print(f"\nFinal config:")
    print(f"  Debug mode: {final.debug_mode}")
    print(f"  Threads: {final.alignment.threads}")
    print(f"  Min length: {final.validation.min_length}")
    print(f"  Force overwrite: {final.output.force_overwrite}")

    print(f"\nChange log:")
    for change in change_log:
        print(f"  {change}")
    print()


def demo_validation_features():
    """Demonstrate pydantic validation features."""
    print("=== Validation Features Demo ===")

    try:
        # This should work
        print("Creating valid configuration...")
        valid_config = EnhancedConfig(
            alignment=AlignmentSettings(aligner="blast", threads=4),
            validation=ValidationSettings(min_length=15, max_length=30),
        )
        print("✓ Valid configuration created successfully")

    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    try:
        # This should fail - invalid aligner
        print("Testing invalid aligner...")
        EnhancedConfig(alignment=AlignmentSettings(aligner="invalid_tool"))
        print("✗ Should have failed!")

    except ValueError as e:
        print(f"✓ Validation caught invalid aligner: {e}")

    try:
        # This should fail - invalid range
        print("Testing invalid primer length range...")
        EnhancedConfig(validation=ValidationSettings(min_length=25, max_length=25))
        print("✗ Should have failed!")

    except ValueError as e:
        print(f"✓ Validation caught invalid range: {e}")

    try:
        # This should fail - invalid output format
        print("Testing invalid output format...")
        EnhancedConfig(output=OutputSettings(formats=["invalid_format"]))
        print("✗ Should have failed!")

    except ValueError as e:
        print(f"✓ Validation caught invalid format: {e}")

    print()


def demo_legacy_compatibility():
    """Demonstrate backward compatibility with legacy configuration."""
    print("=== Legacy Compatibility Demo ===")

    # Create enhanced configuration
    enhanced_config = EnhancedConfig(
        alignment=AlignmentSettings(aligner="minimap2", threads=8),
        validation=ValidationSettings(min_length=18, max_length=32, enabled=True),
        output=OutputSettings(formats=["artic", "fasta"], force_overwrite=True),
        parser=ParserSettings(default_pool=2, naming_scheme="custom"),
        custom={"experiment_id": "EXP-2024-001"},
    )

    # Convert to legacy format
    legacy_config = enhanced_config.to_legacy_config()

    print("Enhanced → Legacy conversion:")
    print(f"  Aligner: {legacy_config.aligner}")
    print(
        f"  Primer length: {legacy_config.min_primer_length}-{legacy_config.max_primer_length}"
    )
    print(f"  Output formats: {legacy_config.output_formats}")
    print(f"  Force overwrite: {legacy_config.force_overwrite}")
    print(f"  Default pool: {legacy_config.default_pool}")
    print(f"  Naming scheme: {legacy_config.primer_naming_scheme}")
    print(f"  Validate sequences: {legacy_config.validate_sequences}")
    print(f"  Custom settings: {legacy_config.custom_settings}")
    print()


def main():
    """Run all configuration demos."""
    print("PrePrimer Enhanced Configuration System Demo")
    print("=" * 50)
    print()

    demo_basic_configuration()
    demo_environment_variables()
    demo_file_configuration()
    demo_runtime_reconfiguration()
    demo_validation_features()
    demo_legacy_compatibility()

    print("Demo completed successfully!")


if __name__ == "__main__":
    main()
