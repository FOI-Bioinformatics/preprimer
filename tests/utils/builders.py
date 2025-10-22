"""
Test data builders for PrePrimer tests.

Provides fluent builder APIs for creating test data objects.
"""

from pathlib import Path
from typing import Dict, List, Optional

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
from preprimer.core.interfaces import AmpliconData, PrimerData


class PrimerDataBuilder:
    """Builder for creating PrimerData objects in tests."""

    def __init__(self):
        """Initialize with default values."""
        self._name = "test_primer"
        self._sequence = "ATCGATCGATCGATCGATCG"  # 20bp
        self._start = 100
        self._stop = 120
        self._strand = "+"
        self._direction = "forward"
        self._pool = 1
        self._amplicon_id = "test_amplicon"
        self._reference_id = "test_ref"
        self._gc_content = 0.5
        self._tm = 60.0
        self._score = 1.0
        self._penalty = None
        self._metadata = {}

    def with_name(self, name: str) -> "PrimerDataBuilder":
        """Set primer name."""
        self._name = name
        return self

    def with_sequence(self, sequence: str) -> "PrimerDataBuilder":
        """Set primer sequence."""
        self._sequence = sequence
        # Auto-update stop based on sequence length if start is set
        if self._start is not None:
            if self._direction == "forward":
                self._stop = self._start + len(sequence)
            else:
                self._stop = self._start - len(sequence)
        return self

    def with_coordinates(self, start: int, stop: int) -> "PrimerDataBuilder":
        """Set primer coordinates."""
        self._start = start
        self._stop = stop
        return self

    def forward(self) -> "PrimerDataBuilder":
        """Make this a forward primer."""
        self._direction = "forward"
        self._strand = "+"
        return self

    def reverse(self) -> "PrimerDataBuilder":
        """Make this a reverse primer."""
        self._direction = "reverse"
        self._strand = "-"
        return self

    def in_pool(self, pool: int) -> "PrimerDataBuilder":
        """Set primer pool."""
        self._pool = pool
        return self

    def for_amplicon(self, amplicon_id: str) -> "PrimerDataBuilder":
        """Set amplicon ID."""
        self._amplicon_id = amplicon_id
        return self

    def with_gc(self, gc_content: float) -> "PrimerDataBuilder":
        """Set GC content."""
        self._gc_content = gc_content
        return self

    def with_tm(self, tm: float) -> "PrimerDataBuilder":
        """Set melting temperature."""
        self._tm = tm
        return self

    def build(self) -> PrimerData:
        """Build the PrimerData object."""
        return PrimerData(
            name=self._name,
            sequence=self._sequence,
            start=self._start,
            stop=self._stop,
            strand=self._strand,
            direction=self._direction,
            pool=self._pool,
            amplicon_id=self._amplicon_id,
            reference_id=self._reference_id,
            gc_content=self._gc_content,
            tm=self._tm,
            score=self._score,
            penalty=self._penalty,
            metadata=self._metadata,
        )


class AmpliconDataBuilder:
    """Builder for creating AmpliconData objects in tests."""

    def __init__(self):
        """Initialize with default values."""
        self._amplicon_id = "test_amplicon_1"
        self._primers: List[PrimerData] = []
        self._length = 200
        self._reference_id = "test_ref"
        self._start = None
        self._end = None
        self._insert_start = None
        self._insert_end = None
        self._pool = None
        self._scheme_prefix = "test"
        self._metadata = {}

    def with_id(self, amplicon_id: str) -> "AmpliconDataBuilder":
        """Set amplicon ID."""
        self._amplicon_id = amplicon_id
        return self

    def with_length(self, length: int) -> "AmpliconDataBuilder":
        """Set amplicon length."""
        self._length = length
        return self

    def with_primers(self, primers: List[PrimerData]) -> "AmpliconDataBuilder":
        """Set primers."""
        self._primers = primers
        return self

    def add_primer(self, primer: PrimerData) -> "AmpliconDataBuilder":
        """Add a single primer."""
        self._primers.append(primer)
        return self

    def add_primer_pair(
        self,
        forward_seq: str = "ATCGATCGATCGATCGATCG",
        reverse_seq: str = "CGATCGATCGATCGATCGAT",
        pool: int = 1
    ) -> "AmpliconDataBuilder":
        """Add a forward/reverse primer pair."""
        forward = (
            PrimerDataBuilder()
            .with_name(f"{self._amplicon_id}_LEFT")
            .with_sequence(forward_seq)
            .forward()
            .in_pool(pool)
            .for_amplicon(self._amplicon_id)
            .build()
        )

        reverse = (
            PrimerDataBuilder()
            .with_name(f"{self._amplicon_id}_RIGHT")
            .with_sequence(reverse_seq)
            .reverse()
            .in_pool(pool)
            .for_amplicon(self._amplicon_id)
            .with_coordinates(300, 280)  # Reverse coordinates
            .build()
        )

        self._primers.extend([forward, reverse])
        return self

    def in_pool(self, pool: int) -> "AmpliconDataBuilder":
        """Set amplicon pool."""
        self._pool = pool
        return self

    def build(self) -> AmpliconData:
        """Build the AmpliconData object."""
        return AmpliconData(
            amplicon_id=self._amplicon_id,
            primers=self._primers,
            length=self._length,
            reference_id=self._reference_id,
            start=self._start,
            end=self._end,
            insert_start=self._insert_start,
            insert_end=self._insert_end,
            pool=self._pool,
            scheme_prefix=self._scheme_prefix,
            metadata=self._metadata,
        )


class ConfigBuilder:
    """Builder for creating EnhancedConfig objects in tests."""

    def __init__(self):
        """Initialize with default test-friendly values."""
        self._validation = ValidationSettings()
        self._output = OutputSettings(force_overwrite=True)  # Default to True for tests
        self._parser = ParserSettings()
        self._alignment = AlignmentSettings()
        self._plugins = PluginSettings()
        self._security = SecuritySettings()
        self._logging = LoggingSettings()
        self._debug_mode = False
        self._profile_performance = False
        self._parallel_processing = True
        self._max_workers = 4
        self._environment = "test"  # Default to test environment

    def with_validation(
        self,
        enabled: bool = True,
        min_length: int = 15,
        max_length: int = 35
    ) -> "ConfigBuilder":
        """Set validation settings."""
        self._validation = ValidationSettings(
            enabled=enabled,
            min_length=min_length,
            max_length=max_length,
        )
        return self

    def with_output(
        self,
        formats: Optional[List[str]] = None,
        force_overwrite: bool = True
    ) -> "ConfigBuilder":
        """Set output settings."""
        self._output = OutputSettings(
            formats=formats or ["artic"],
            force_overwrite=force_overwrite,
        )
        return self

    def with_formats(self, *formats: str) -> "ConfigBuilder":
        """Set output formats (convenience method)."""
        self._output = OutputSettings(
            formats=list(formats),
            force_overwrite=self._output.force_overwrite,
        )
        return self

    def with_aligner(self, aligner: str) -> "ConfigBuilder":
        """Set alignment tool."""
        self._alignment = AlignmentSettings(aligner=aligner)
        return self

    def enable_debug(self) -> "ConfigBuilder":
        """Enable debug mode."""
        self._debug_mode = True
        return self

    def enable_profiling(self) -> "ConfigBuilder":
        """Enable performance profiling."""
        self._profile_performance = True
        return self

    def disable_parallel(self) -> "ConfigBuilder":
        """Disable parallel processing (for deterministic tests)."""
        self._parallel_processing = False
        return self

    def build(self) -> EnhancedConfig:
        """Build the EnhancedConfig object."""
        return EnhancedConfig(
            validation=self._validation,
            output=self._output,
            parser=self._parser,
            alignment=self._alignment,
            plugins=self._plugins,
            security=self._security,
            logging=self._logging,
            debug_mode=self._debug_mode,
            profile_performance=self._profile_performance,
            parallel_processing=self._parallel_processing,
            max_workers=self._max_workers,
            environment=self._environment,
        )


class TestDatasetBuilder:
    """Builder for creating test datasets with multiple amplicons."""

    def __init__(self):
        """Initialize empty dataset."""
        self._amplicons: Dict[str, AmpliconData] = {}
        self._reference_id = "test_ref"
        self._prefix = "test"

    def add_amplicon(
        self,
        amplicon_id: str,
        pool: int = 1,
        length: int = 200
    ) -> "TestDatasetBuilder":
        """Add an amplicon with default primer pair."""
        amplicon = (
            AmpliconDataBuilder()
            .with_id(amplicon_id)
            .with_length(length)
            .in_pool(pool)
            .add_primer_pair(pool=pool)
            .build()
        )
        self._amplicons[amplicon_id] = amplicon
        return self

    def add_custom_amplicon(self, amplicon: AmpliconData) -> "TestDatasetBuilder":
        """Add a custom amplicon."""
        self._amplicons[amplicon.amplicon_id] = amplicon
        return self

    def with_n_amplicons(self, n: int, pools: int = 2) -> "TestDatasetBuilder":
        """Add n amplicons distributed across pools."""
        for i in range(1, n + 1):
            pool = ((i - 1) % pools) + 1
            self.add_amplicon(f"amplicon_{i}", pool=pool)
        return self

    def build(self) -> Dict[str, AmpliconData]:
        """Build the dataset."""
        return self._amplicons


# Convenience functions for common test scenarios

def build_primer(
    name: str = "test_primer",
    sequence: str = "ATCGATCGATCGATCGATCG",
    direction: str = "forward",
    **kwargs
) -> PrimerData:
    """Quick primer builder."""
    builder = PrimerDataBuilder().with_name(name).with_sequence(sequence)
    if direction == "forward":
        builder.forward()
    else:
        builder.reverse()

    for key, value in kwargs.items():
        if hasattr(builder, f"with_{key}"):
            getattr(builder, f"with_{key}")(value)

    return builder.build()


def build_amplicon(
    amplicon_id: str = "test_amplicon",
    with_primers: bool = True,
    **kwargs
) -> AmpliconData:
    """Quick amplicon builder."""
    builder = AmpliconDataBuilder().with_id(amplicon_id)

    if with_primers:
        builder.add_primer_pair()

    for key, value in kwargs.items():
        if hasattr(builder, f"with_{key}"):
            getattr(builder, f"with_{key}")(value)

    return builder.build()


def build_config(**kwargs) -> EnhancedConfig:
    """Quick config builder."""
    builder = ConfigBuilder()

    for key, value in kwargs.items():
        method_name = f"with_{key}"
        if hasattr(builder, method_name):
            getattr(builder, method_name)(value)
        elif key == "debug":
            builder.enable_debug()
        elif key == "profiling":
            builder.enable_profiling()

    return builder.build()
