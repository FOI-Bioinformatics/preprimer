"""
Enhanced configuration management for preprimer with environment variable support,
pydantic validation, plugin settings, and runtime reconfiguration.
"""

import json
import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, Set
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError, ConfigDict

from .exceptions import ConfigError


class AlignmentSettings(BaseModel):
    """Alignment-specific settings."""
    
    aligner: str = Field(default="blast", description="Alignment tool to use")
    params: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific parameters")
    threads: int = Field(default=1, ge=1, le=32, description="Number of threads for alignment")
    timeout: int = Field(default=300, ge=30, le=3600, description="Timeout in seconds")
    
    @field_validator('aligner')
    @classmethod
    def validate_aligner(cls, v):
        valid_aligners = {"blast", "exonerate", "minimap2", "bwa"}
        if v not in valid_aligners:
            raise ValueError(f"Aligner must be one of: {valid_aligners}")
        return v


class ValidationSettings(BaseModel):
    """Primer validation settings."""
    
    enabled: bool = Field(default=True, description="Enable sequence validation")
    min_length: int = Field(default=15, ge=8, le=25, description="Minimum primer length")
    max_length: int = Field(default=35, ge=25, le=60, description="Maximum primer length")
    check_gc_content: bool = Field(default=True, description="Check GC content")
    min_gc: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum GC content")
    max_gc: float = Field(default=0.7, ge=0.0, le=1.0, description="Maximum GC content")
    check_tm: bool = Field(default=True, description="Check melting temperature")
    min_tm: float = Field(default=50.0, ge=30.0, le=80.0, description="Minimum Tm")
    max_tm: float = Field(default=70.0, ge=50.0, le=90.0, description="Maximum Tm")
    
    @model_validator(mode='after')
    def validate_ranges(self):
        if self.max_length <= self.min_length:
            raise ValueError("max_length must be greater than min_length")
        if self.max_gc <= self.min_gc:
            raise ValueError("max_gc must be greater than min_gc")
        if self.max_tm <= self.min_tm:
            raise ValueError("max_tm must be greater than min_tm")
        return self


class OutputSettings(BaseModel):
    """Output generation settings."""
    
    formats: List[str] = Field(default_factory=lambda: ["artic"], description="Output formats to generate")
    force_overwrite: bool = Field(default=False, description="Overwrite existing files")
    create_directories: bool = Field(default=True, description="Create output directories if missing")
    preserve_metadata: bool = Field(default=True, description="Preserve metadata in output")
    compression: Optional[str] = Field(default=None, description="Compression format (gzip, bz2)")
    
    @field_validator('formats')
    @classmethod
    def validate_formats(cls, v):
        valid_formats = {"artic", "fasta", "bed", "tsv", "json", "yaml", "csv"}
        invalid_formats = set(v) - valid_formats
        if invalid_formats:
            raise ValueError(f"Invalid output formats: {invalid_formats}")
        return v
    
    @field_validator('compression')
    @classmethod
    def validate_compression(cls, v):
        if v is not None and v not in {"gzip", "bz2", "xz"}:
            raise ValueError("Compression must be one of: gzip, bz2, xz")
        return v


class ParserSettings(BaseModel):
    """Parser-specific settings."""
    
    default_pool: int = Field(default=1, ge=1, le=10, description="Default pool number")
    naming_scheme: str = Field(default="artic", description="Primer naming scheme")
    strict_validation: bool = Field(default=True, description="Enable strict format validation")
    skip_empty_rows: bool = Field(default=True, description="Skip empty rows during parsing")
    max_errors: int = Field(default=10, ge=0, le=100, description="Maximum parsing errors before abort")
    
    @field_validator('naming_scheme')
    @classmethod
    def validate_naming_scheme(cls, v):
        valid_schemes = {"artic", "custom", "sequential", "varvamp"}
        if v not in valid_schemes:
            raise ValueError(f"Naming scheme must be one of: {valid_schemes}")
        return v


class PluginSettings(BaseModel):
    """Plugin-specific configuration."""
    
    enabled: bool = Field(default=True, description="Enable plugin system")
    search_paths: List[str] = Field(default_factory=list, description="Plugin search paths")
    whitelist: Optional[List[str]] = Field(default=None, description="Allowed plugins (None = all)")
    blacklist: List[str] = Field(default_factory=list, description="Disabled plugins")
    config: Dict[str, Any] = Field(default_factory=dict, description="Plugin-specific configuration")


class SecuritySettings(BaseModel):
    """Security and safety settings."""
    
    allow_remote_files: bool = Field(default=False, description="Allow remote file access")
    max_file_size: int = Field(default=100*1024*1024, ge=1024, description="Maximum file size in bytes")
    allowed_extensions: Optional[List[str]] = Field(default=None, description="Allowed file extensions")
    sandbox_mode: bool = Field(default=False, description="Enable sandbox mode")
    validate_paths: bool = Field(default=True, description="Validate file paths for security")


class LoggingSettings(BaseModel):
    """Logging configuration."""
    
    level: str = Field(default="INFO", description="Log level")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
                       description="Log format")
    file: Optional[str] = Field(default=None, description="Log file path")
    max_size: int = Field(default=10*1024*1024, ge=1024, description="Max log file size")
    backup_count: int = Field(default=5, ge=1, le=10, description="Number of backup files")
    
    @field_validator('level')
    @classmethod
    def validate_level(cls, v):
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class EnhancedConfig(BaseModel):
    """
    Enhanced configuration with environment variable support, pydantic validation,
    plugin settings, and runtime reconfiguration.
    """
    
    # Core settings
    alignment: AlignmentSettings = Field(default_factory=AlignmentSettings)
    validation: ValidationSettings = Field(default_factory=ValidationSettings) 
    output: OutputSettings = Field(default_factory=OutputSettings)
    parser: ParserSettings = Field(default_factory=ParserSettings)
    plugins: PluginSettings = Field(default_factory=PluginSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    # Runtime settings
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    profile_performance: bool = Field(default=False, description="Profile performance")
    parallel_processing: bool = Field(default=True, description="Enable parallel processing")
    max_workers: int = Field(default=4, ge=1, le=16, description="Maximum worker threads")
    
    # Environment-specific settings
    environment: str = Field(default="production", description="Environment name")
    config_version: str = Field(default="1.0", description="Configuration version")
    
    # Custom settings for extensibility
    custom: Dict[str, Any] = Field(default_factory=dict, description="Custom configuration")
    
    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True
    )
    
    @classmethod
    def from_env(cls, prefix: str = "PREPRIMER_") -> "EnhancedConfig":
        """
        Create configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix
            
        Returns:
            Configuration instance
        """
        config_data = {}
        
        # Environment variable mapping
        env_mappings = {
            f"{prefix}ALIGNER": "alignment.aligner",
            f"{prefix}ALIGNMENT_THREADS": "alignment.threads",
            f"{prefix}ALIGNMENT_TIMEOUT": "alignment.timeout",
            f"{prefix}VALIDATE_SEQUENCES": "validation.enabled",
            f"{prefix}MIN_PRIMER_LENGTH": "validation.min_length",
            f"{prefix}MAX_PRIMER_LENGTH": "validation.max_length",
            f"{prefix}OUTPUT_FORMATS": "output.formats",
            f"{prefix}FORCE_OVERWRITE": "output.force_overwrite",
            f"{prefix}DEFAULT_POOL": "parser.default_pool",
            f"{prefix}NAMING_SCHEME": "parser.naming_scheme",
            f"{prefix}DEBUG_MODE": "debug_mode",
            f"{prefix}MAX_WORKERS": "max_workers",
            f"{prefix}LOG_LEVEL": "logging.level",
            f"{prefix}LOG_FILE": "logging.file",
            f"{prefix}ENVIRONMENT": "environment",
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_path.endswith(('.enabled', '.force_overwrite', '.debug_mode')):
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif config_path.endswith(('.threads', '.timeout', '.min_length', '.max_length', 
                                         '.default_pool', '.max_workers')):
                    value = int(value)
                elif config_path == 'output.formats':
                    value = [fmt.strip() for fmt in value.split(',')]
                
                # Set nested configuration value
                cls._set_nested_value(config_data, config_path, value)
        
        return cls(**config_data)
    
    @staticmethod
    def _set_nested_value(data: Dict, path: str, value: Any) -> None:
        """Set a nested dictionary value using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    @classmethod
    def from_file(cls, config_path: Union[str, Path], 
                  merge_env: bool = True, env_prefix: str = "PREPRIMER_") -> "EnhancedConfig":
        """
        Load configuration from file with optional environment variable merging.
        
        Args:
            config_path: Path to configuration file
            merge_env: Merge environment variables
            env_prefix: Environment variable prefix
            
        Returns:
            Configuration instance
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path) as f:
                if config_path.suffix.lower() == '.json':
                    file_data = json.load(f)
                elif config_path.suffix.lower() in ('.yaml', '.yml'):
                    import yaml
                    file_data = yaml.safe_load(f)
                else:
                    raise ConfigError(f"Unsupported config file format: {config_path.suffix}")
        
        except (json.JSONDecodeError, Exception) as e:
            raise ConfigError(f"Failed to parse config file {config_path}: {e}")
        
        if merge_env:
            # Start with environment config and override with file config
            env_config = cls.from_env(env_prefix)
            env_data = env_config.model_dump()
            
            # Deep merge file data into env data
            merged_data = cls._deep_merge(env_data, file_data)
            return cls(**merged_data)
        else:
            return cls(**file_data)
    
    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = EnhancedConfig._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def save(self, config_path: Union[str, Path], format: str = "json") -> None:
        """
        Save configuration to file.
        
        Args:
            config_path: Output file path
            format: Output format (json, yaml)
        """
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.model_dump(exclude_none=True)
        
        with open(config_path, 'w') as f:
            if format.lower() == 'json':
                json.dump(data, f, indent=2, default=str)
            elif format.lower() in ('yaml', 'yml'):
                import yaml
                yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)
            else:
                raise ConfigError(f"Unsupported output format: {format}")
    
    def get_plugin_config(self, plugin_name: str) -> Dict[str, Any]:
        """Get configuration for a specific plugin."""
        return self.plugins.config.get(plugin_name, {})
    
    def set_plugin_config(self, plugin_name: str, config: Dict[str, Any]) -> None:
        """Set configuration for a specific plugin."""
        if plugin_name not in self.plugins.config:
            self.plugins.config[plugin_name] = {}
        self.plugins.config[plugin_name].update(config)
    
    def to_legacy_config(self) -> "PrePrimerConfig":
        """Convert to legacy configuration format for backward compatibility."""
        from .config import PrePrimerConfig
        
        return PrePrimerConfig(
            aligner=self.alignment.aligner,
            alignment_params=self.alignment.params,
            output_formats=self.output.formats,
            force_overwrite=self.output.force_overwrite,
            default_pool=self.parser.default_pool,
            primer_naming_scheme=self.parser.naming_scheme,
            validate_sequences=self.validation.enabled,
            min_primer_length=self.validation.min_length,
            max_primer_length=self.validation.max_length,
            custom_settings=self.custom
        )


@dataclass
class ConfigWatcher:
    """Watches configuration files for changes and triggers reloads."""
    
    config_path: Path
    callback: Callable[[EnhancedConfig], None]
    _stop_event: threading.Event = field(default_factory=threading.Event)
    _thread: Optional[threading.Thread] = None
    
    def start(self) -> None:
        """Start watching for configuration changes."""
        if self._thread and self._thread.is_alive():
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop watching for configuration changes."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
    
    def _watch_loop(self) -> None:
        """Main watch loop."""
        import time
        last_mtime = self.config_path.stat().st_mtime if self.config_path.exists() else 0
        
        while not self._stop_event.wait(1.0):  # Check every second
            try:
                if self.config_path.exists():
                    current_mtime = self.config_path.stat().st_mtime
                    if current_mtime > last_mtime:
                        last_mtime = current_mtime
                        # Reload configuration
                        new_config = EnhancedConfig.from_file(self.config_path)
                        self.callback(new_config)
            except Exception:
                # Ignore errors during watching
                pass


class ConfigManager:
    """
    Manages configuration with runtime reconfiguration support.
    """
    
    def __init__(self, initial_config: Optional[EnhancedConfig] = None):
        self._config = initial_config or EnhancedConfig()
        self._watchers: List[ConfigWatcher] = []
        self._change_callbacks: List[Callable[[EnhancedConfig], None]] = []
        self._lock = threading.RLock()
    
    @property
    def config(self) -> EnhancedConfig:
        """Get current configuration (thread-safe)."""
        with self._lock:
            return self._config.model_copy(deep=True)
    
    def update_config(self, new_config: EnhancedConfig) -> None:
        """
        Update configuration and notify callbacks.
        
        Args:
            new_config: New configuration
        """
        with self._lock:
            old_config = self._config
            self._config = new_config
            
            # Notify change callbacks
            for callback in self._change_callbacks:
                try:
                    callback(new_config)
                except Exception:
                    # Don't let callback errors break config updates
                    pass
    
    def update_partial(self, **updates) -> None:
        """
        Partially update configuration.
        
        Args:
            **updates: Configuration updates
        """
        with self._lock:
            current_data = self._config.model_dump()
            
            # Apply updates
            for key, value in updates.items():
                if '.' in key:
                    # Handle nested updates
                    EnhancedConfig._set_nested_value(current_data, key, value)
                else:
                    current_data[key] = value
            
            # Create new config and update
            new_config = EnhancedConfig(**current_data)
            self.update_config(new_config)
    
    def add_change_callback(self, callback: Callable[[EnhancedConfig], None]) -> None:
        """Add a callback for configuration changes."""
        with self._lock:
            self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[EnhancedConfig], None]) -> None:
        """Remove a configuration change callback."""
        with self._lock:
            if callback in self._change_callbacks:
                self._change_callbacks.remove(callback)
    
    def watch_file(self, config_path: Union[str, Path]) -> None:
        """
        Start watching a configuration file for changes.
        
        Args:
            config_path: Path to configuration file
        """
        config_path = Path(config_path)
        
        def reload_callback(new_config: EnhancedConfig) -> None:
            self.update_config(new_config)
        
        watcher = ConfigWatcher(config_path, reload_callback)
        watcher.start()
        
        with self._lock:
            self._watchers.append(watcher)
    
    def stop_watching(self) -> None:
        """Stop all file watchers."""
        with self._lock:
            for watcher in self._watchers:
                watcher.stop()
            self._watchers.clear()


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> EnhancedConfig:
    """Get the current global configuration."""
    return config_manager.config


def update_config(new_config: EnhancedConfig) -> None:
    """Update the global configuration."""
    config_manager.update_config(new_config)


def update_config_partial(**updates) -> None:
    """Partially update the global configuration."""
    config_manager.update_partial(**updates)