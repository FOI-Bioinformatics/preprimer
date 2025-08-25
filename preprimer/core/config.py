"""
Configuration management for preprimer.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Union

from .exceptions import ConfigError


@dataclass
class PrePrimerConfig:
    """Configuration for preprimer operations."""

    # Alignment settings
    aligner: str = "blast"
    alignment_params: Dict[str, Any] = field(default_factory=dict)

    # Output settings
    output_formats: List[str] = field(default_factory=lambda: ["artic"])
    force_overwrite: bool = False

    # Parser settings
    default_pool: int = 1
    primer_naming_scheme: str = "artic"  # artic, custom

    # Validation settings
    validate_sequences: bool = True
    min_primer_length: int = 15
    max_primer_length: int = 35

    # Additional configuration
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_file(cls, config_path: Union[str, Path]) -> "PrePrimerConfig":
        """Load configuration from JSON file."""
        config_path = Path(config_path)
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path) as f:
                data = json.load(f)
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            raise ConfigError(f"Invalid JSON in config file: {e}")
        except Exception as e:
            raise ConfigError(f"Failed to load config: {e}")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PrePrimerConfig":
        """Create configuration from dictionary."""
        # Filter out any keys not in the dataclass
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_keys}

        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "aligner": self.aligner,
            "alignment_params": self.alignment_params,
            "output_formats": self.output_formats,
            "force_overwrite": self.force_overwrite,
            "default_pool": self.default_pool,
            "primer_naming_scheme": self.primer_naming_scheme,
            "validate_sequences": self.validate_sequences,
            "min_primer_length": self.min_primer_length,
            "max_primer_length": self.max_primer_length,
            "custom_settings": self.custom_settings,
        }

    def save(self, config_path: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Validate aligner
        valid_aligners = ["blast", "exonerate"]
        if self.aligner not in valid_aligners:
            issues.append(
                f"Invalid aligner '{self.aligner}'. "
                f"Must be one of: {valid_aligners}"
            )

        # Validate primer length constraints
        if self.min_primer_length < 10:
            issues.append("Minimum primer length should be at least 10")
        if self.max_primer_length > 50:
            issues.append("Maximum primer length should be at most 50")
        if self.min_primer_length >= self.max_primer_length:
            issues.append("Minimum primer length must be less than maximum")

        # Validate naming scheme
        valid_schemes = ["artic", "custom"]
        if self.primer_naming_scheme not in valid_schemes:
            issues.append(
                f"Invalid naming scheme '{self.primer_naming_scheme}'. "
                f"Must be one of: {valid_schemes}"
            )

        return issues


# Default configuration instance
DefaultConfig = PrePrimerConfig()
