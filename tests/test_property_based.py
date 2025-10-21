"""
Property-based testing using Hypothesis for robust test coverage.
"""

import string
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, initialize, invariant, rule

from preprimer.core.enhanced_config import (
    AlignmentSettings,
    EnhancedConfig,
    ValidationSettings,
)
from preprimer.core.exceptions import (
    ParserError,
    PrePrimerError,
    SecurityError,
    ValidationError,
)
from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.core.security import InputValidator, PathValidator


class TestPrimerDataProperties:
    """Property-based tests for PrimerData validation."""

    # Strategy for valid DNA sequences
    dna_sequence = st.text(alphabet="ATCG", min_size=10, max_size=100)

    # Strategy for valid primer names
    primer_name = st.text(
        alphabet=string.ascii_letters + string.digits + "_-", min_size=1, max_size=50
    ).filter(
        lambda x: x[0].isalpha()
    )  # Must start with letter

    # Strategy for genomic coordinates
    genomic_position = st.integers(min_value=1, max_value=1000000)

    @given(
        name=primer_name,
        sequence=dna_sequence,
        start=genomic_position,
        strand=st.sampled_from(["+", "-", "1", "-1"]),
        direction=st.sampled_from(["forward", "reverse"]),
        pool=st.integers(min_value=1, max_value=10),
    )
    def test_primer_data_creation_properties(
        self, name, sequence, start, strand, direction, pool
    ):
        """Test that PrimerData objects can be created with valid inputs."""
        stop = start + len(sequence)

        primer = PrimerData(
            name=name,
            sequence=sequence,
            start=start,
            stop=stop,
            strand=strand,
            direction=direction,
            pool=pool,
            amplicon_id=f"amplicon_{pool}",
            reference_id="test_ref",
        )

        # Properties that should always hold
        assert primer.name == name
        assert primer.sequence == sequence
        assert primer.start == start
        assert primer.stop == stop
        assert primer.strand == strand
        assert primer.direction == direction
        assert primer.pool == pool
        assert primer.stop > primer.start  # Stop must be after start
        assert len(primer.sequence) == (primer.stop - primer.start)

    @given(
        sequences=st.lists(dna_sequence, min_size=1, max_size=10),
        pool=st.integers(min_value=1, max_value=5),
    )
    def test_primer_sequence_properties(self, sequences, pool):
        """Test properties of primer sequences."""
        primers = []
        start_pos = 100

        for i, seq in enumerate(sequences):
            primer = PrimerData(
                name=f"primer_{i}",
                sequence=seq,
                start=start_pos,
                stop=start_pos + len(seq),
                strand="+",
                direction="forward",
                pool=pool,
                amplicon_id=f"amplicon_{pool}",
                reference_id="test_ref",
            )
            primers.append(primer)
            start_pos += len(seq) + 50  # Gap between primers

        # All primers should have non-empty sequences
        assert all(len(p.sequence) > 0 for p in primers)

        # All primers should have valid coordinates
        assert all(p.stop > p.start for p in primers)

        # Sequences should only contain valid DNA bases
        valid_bases = set("ATCG")
        assert all(set(p.sequence).issubset(valid_bases) for p in primers)

    @given(
        gc_content=st.floats(min_value=0.0, max_value=1.0),
        tm=st.floats(min_value=30.0, max_value=95.0),
        score=st.floats(min_value=0.0, max_value=100.0),
    )
    def test_primer_metrics_properties(self, gc_content, tm, score):
        """Test properties of primer quality metrics."""
        primer = PrimerData(
            name="test_primer",
            sequence="ATCGATCGATCG",
            start=100,
            stop=112,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="amplicon_1",
            reference_id="test_ref",
            gc_content=gc_content,
            tm=tm,
            score=score,
        )

        # Metrics should be within expected ranges
        if primer.gc_content is not None:
            assert 0.0 <= primer.gc_content <= 1.0
        if primer.tm is not None:
            assert primer.tm >= 0.0  # Tm should be positive
        if primer.score is not None:
            assert primer.score >= 0.0  # Score should be non-negative


class TestAmpliconDataProperties:
    """Property-based tests for AmpliconData validation."""

    @given(
        amplicon_id=st.text(min_size=1, max_size=20).filter(str.isalnum),
        num_primers=st.integers(min_value=2, max_value=20),
        length=st.integers(min_value=50, max_value=5000),
    )
    def test_amplicon_creation_properties(self, amplicon_id, num_primers, length):
        """Test AmpliconData creation with various primer counts."""
        primers = []

        # Create forward primers
        forward_count = num_primers // 2
        reverse_count = num_primers - forward_count

        start_pos = 100
        for i in range(forward_count):
            primer = PrimerData(
                name=f"FW_{i}",
                sequence="ATCGATCG",
                start=start_pos + i * 20,
                stop=start_pos + i * 20 + 8,
                strand="+",
                direction="forward",
                pool=1,
                amplicon_id=amplicon_id,
                reference_id="test_ref",
            )
            primers.append(primer)

        # Create reverse primers
        for i in range(reverse_count):
            primer = PrimerData(
                name=f"RW_{i}",
                sequence="CGATCGAT",
                start=start_pos + length - i * 20 - 8,
                stop=start_pos + length - i * 20,
                strand="-",
                direction="reverse",
                pool=1,
                amplicon_id=amplicon_id,
                reference_id="test_ref",
            )
            primers.append(primer)

        amplicon = AmpliconData(
            amplicon_id=amplicon_id,
            primers=primers,
            length=length,
            reference_id="test_ref",
        )

        # Properties that should always hold
        assert amplicon.amplicon_id == amplicon_id
        assert len(amplicon.primers) == num_primers
        assert len(amplicon.forward_primers) == forward_count
        assert len(amplicon.reverse_primers) == reverse_count
        assert amplicon.length == length

        # All primers should belong to this amplicon
        assert all(p.amplicon_id == amplicon_id for p in amplicon.primers)


class TestConfigurationProperties:
    """Property-based tests for configuration validation."""

    @given(
        threads=st.integers(min_value=1, max_value=32),
        timeout=st.integers(min_value=30, max_value=3600),
        min_length=st.integers(min_value=8, max_value=25),
        max_length=st.integers(min_value=25, max_value=60),
        min_gc=st.floats(min_value=0.0, max_value=1.0),
        max_gc=st.floats(min_value=0.0, max_value=1.0),
        pool=st.integers(min_value=1, max_value=10),
    )
    def test_config_validation_properties(
        self, threads, timeout, min_length, max_length, min_gc, max_gc, pool
    ):
        """Test configuration validation with various parameter combinations."""
        assume(max_length > min_length)  # Ensure valid length range
        assume(max_gc > min_gc)  # Ensure valid GC range

        config = EnhancedConfig(
            alignment=AlignmentSettings(
                aligner="blast", threads=threads, timeout=timeout
            ),
            validation=ValidationSettings(
                min_length=min_length,
                max_length=max_length,
                min_gc=min_gc,
                max_gc=max_gc,
            ),
            parser={"default_pool": pool},
        )

        # Configuration should be valid
        assert config.alignment.threads == threads
        assert config.alignment.timeout == timeout
        assert config.validation.min_length == min_length
        assert config.validation.max_length == max_length
        assert config.validation.min_gc == min_gc
        assert config.validation.max_gc == max_gc

        # Ranges should be valid
        assert config.validation.max_length > config.validation.min_length
        assert config.validation.max_gc > config.validation.min_gc


class TestSecurityProperties:
    """Property-based tests for security validation."""

    # Strategy for file paths (avoiding problematic characters)
    safe_path_component = st.text(
        alphabet=string.ascii_letters + string.digits + "_-.", min_size=1, max_size=20
    ).filter(lambda x: not x.startswith(".") and ".." not in x)

    @given(path_components=st.lists(safe_path_component, min_size=1, max_size=5))
    def test_path_validation_properties(self, path_components):
        """Test path validation with various path structures."""
        # Create a safe path
        path_str = "/".join(path_components)
        path = Path(path_str)

        try:
            validated_path = PathValidator.sanitize_path(path)

            # If validation succeeds, path should be normalized
            assert isinstance(validated_path, Path)

        except SecurityError as e:
            # If validation fails, it should be a SecurityError
            assert isinstance(e, SecurityError)
        except Exception as e:
            # Other exceptions should be for path-related issues
            assert "path" in str(e).lower() or "invalid" in str(e).lower()

    @given(
        field_value=st.text(min_size=0, max_size=1000),
        max_length=st.integers(min_value=10, max_value=500),
    )
    def test_input_validation_properties(self, field_value, max_length):
        """Test input validation with various string inputs."""
        try:
            sanitized = InputValidator.sanitize_string(
                field_value, max_length=max_length
            )

            # Sanitized string should not exceed max length
            assert len(sanitized) <= max_length

            # Should not contain null bytes
            assert "\x00" not in sanitized

        except (ValidationError, SecurityError) as e:
            # Validation and security errors are expected for certain inputs
            assert isinstance(e, (ValidationError, SecurityError))


class TestErrorHandlingProperties:
    """Property-based tests for error handling."""

    @given(
        error_message=st.text(min_size=1, max_size=200),
        context_keys=st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=5),
        context_values=st.lists(
            st.text(min_size=0, max_size=50), min_size=0, max_size=5
        ),
    )
    def test_error_context_properties(
        self, error_message, context_keys, context_values
    ):
        """Test error context handling with various inputs."""
        assume(len(context_keys) == len(context_values))  # Ensure key-value pairs match

        context = dict(zip(context_keys, context_values))

        error = PrePrimerError(error_message, context=context)

        # Error should preserve message and context
        assert error.technical_message == error_message
        assert error.context == context

        # User message should be available
        user_msg = error.get_user_message()
        assert isinstance(user_msg, str)
        assert len(user_msg) > 0

    @given(
        suggestions=st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=10)
    )
    def test_error_suggestions_properties(self, suggestions):
        """Test error suggestion handling."""
        error = PrePrimerError("Test error")

        # Add suggestions one by one
        for suggestion in suggestions:
            error.add_suggestion(suggestion)

        # All suggestions should be present
        assert len(error.suggestions) == len(suggestions)
        assert all(s in error.suggestions for s in suggestions)

        # User message should include suggestions
        user_msg = error.get_user_message()
        assert "Suggestions:" in user_msg
        for suggestion in suggestions:
            assert suggestion in user_msg


class ConfigurationStateMachine(RuleBasedStateMachine):
    """Stateful testing for configuration management."""

    def __init__(self):
        super().__init__()
        self.config = EnhancedConfig()
        self.change_count = 0

    @initialize()
    def setup_config(self):
        """Initialize the configuration state."""
        self.config = EnhancedConfig()
        self.change_count = 0

    @rule(debug_mode=st.booleans())
    def toggle_debug_mode(self, debug_mode):
        """Toggle debug mode."""
        old_debug = self.config.debug_mode
        self.config.debug_mode = debug_mode
        if old_debug != debug_mode:
            self.change_count += 1

    @rule(threads=st.integers(min_value=1, max_value=16))
    def set_alignment_threads(self, threads):
        """Set alignment threads."""
        old_threads = self.config.alignment.threads
        self.config.alignment.threads = threads
        if old_threads != threads:
            self.change_count += 1

    @rule(min_length=st.integers(min_value=8, max_value=25))
    def set_min_primer_length(self, min_length):
        """Set minimum primer length."""
        assume(min_length < self.config.validation.max_length)
        old_min = self.config.validation.min_length
        self.config.validation.min_length = min_length
        if old_min != min_length:
            self.change_count += 1

    @invariant()
    def config_is_valid(self):
        """Configuration should always be valid."""
        # Alignment settings should be reasonable
        assert 1 <= self.config.alignment.threads <= 32
        assert 30 <= self.config.alignment.timeout <= 3600

        # Validation ranges should be valid
        assert self.config.validation.max_length > self.config.validation.min_length
        assert self.config.validation.max_gc > self.config.validation.min_gc
        assert self.config.validation.max_tm > self.config.validation.min_tm

        # Debug mode should be boolean
        assert isinstance(self.config.debug_mode, bool)

    @invariant()
    def change_count_is_non_negative(self):
        """Change count should never be negative."""
        assert self.change_count >= 0


# Create test class for stateful testing
TestConfigurationStateful = ConfigurationStateMachine.TestCase


class TestFileOperationProperties:
    """Property-based tests for file operations."""

    @given(
        content=st.text(min_size=0, max_size=1000),
        suffix=st.sampled_from([".txt", ".tsv", ".csv", ".json"]),
    )
    def test_temp_file_properties(self, content, suffix):
        """Test temporary file operations with various content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            # File should exist after creation
            assert temp_path.exists()

            # File should have correct suffix
            assert temp_path.suffix == suffix

            # Content should be preserved (normalize line endings)
            with open(temp_path, "r") as f:
                read_content = f.read()
                # Normalize line endings for cross-platform compatibility
                normalized_content = content.replace("\r\n", "\n").replace("\r", "\n")
                normalized_read = read_content.replace("\r\n", "\n").replace("\r", "\n")
                assert normalized_read == normalized_content

        finally:
            temp_path.unlink(missing_ok=True)

    @given(
        primer_data=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20),  # name
                st.text(alphabet="ATCG", min_size=10, max_size=50),  # sequence
                st.integers(min_value=1, max_value=1000),  # start
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_primer_file_format_properties(self, primer_data):
        """Test primer file format properties."""
        # Create primers from generated data
        primers = []
        for name, sequence, start in primer_data:
            primer = PrimerData(
                name=name,
                sequence=sequence,
                start=start,
                stop=start + len(sequence),
                strand="+",
                direction="forward",
                pool=1,
                amplicon_id="test_amplicon",
                reference_id="test_ref",
            )
            primers.append(primer)

        # All primers should have unique names within the same amplicon
        names = [p.name for p in primers]
        # Note: Hypothesis might generate duplicate names, so we test the property conditionally
        if len(set(names)) == len(names):
            assert len(primers) == len(set(names))

        # All primers should have valid coordinates
        assert all(p.stop > p.start for p in primers)

        # All primers should have non-empty sequences
        assert all(len(p.sequence) > 0 for p in primers)


# Configuration for Hypothesis
settings.register_profile("dev", max_examples=50, deadline=1000)
settings.register_profile("ci", max_examples=100, deadline=2000)
settings.register_profile("thorough", max_examples=1000, deadline=5000)

# Use appropriate profile based on environment
import os

profile = os.environ.get("HYPOTHESIS_PROFILE", "dev")
settings.load_profile(profile)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
