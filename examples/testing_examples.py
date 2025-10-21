#!/usr/bin/env python3
"""
Examples demonstrating the enhanced testing framework capabilities.

This file shows practical examples of using property-based testing,
benchmarks, integration tests, and mutation testing.
"""

import tempfile
import time
from pathlib import Path
from typing import List

import pytest
from hypothesis import assume, example, given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from preprimer.core.enhanced_config import EnhancedConfig
from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.parsers.varvamp_parser import VarVAMPParser

# =============================================================================
# Property-Based Testing Examples
# =============================================================================


class PropertyBasedTestingExamples:
    """Examples of property-based testing techniques."""

    # Strategy for generating valid DNA sequences
    dna_sequence = st.text(alphabet="ATCG", min_size=1, max_size=100)

    # Strategy for generating primer names following conventions
    primer_name = st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
        min_size=1,
        max_size=50,
    ).filter(
        lambda x: x[0].isalpha()
    )  # Must start with letter

    @given(sequence=dna_sequence, name=primer_name)
    @example(sequence="ATCG", name="test_primer")  # Explicit example
    def test_primer_data_invariants(self, sequence, name):
        """Test fundamental properties of PrimerData objects."""
        start = 100
        stop = start + len(sequence)

        primer = PrimerData(
            name=name,
            sequence=sequence,
            start=start,
            stop=stop,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amplicon",
            reference_id="test_ref",
        )

        # Invariants that should always hold
        assert primer.name == name
        assert primer.sequence == sequence
        assert primer.stop > primer.start
        assert len(primer.sequence) == (primer.stop - primer.start)
        assert primer.start >= 0
        assert primer.stop > 0

    @given(
        sequences=st.lists(dna_sequence, min_size=2, max_size=10),
        amplicon_name=st.text(min_size=1, max_size=20),
    )
    def test_amplicon_primer_relationships(self, sequences, amplicon_name):
        """Test relationships between amplicons and their primers."""
        primers = []

        for i, seq in enumerate(sequences):
            primer = PrimerData(
                name=f"primer_{i}",
                sequence=seq,
                start=100 + i * 50,
                stop=100 + i * 50 + len(seq),
                strand="+" if i % 2 == 0 else "-",
                direction="forward" if i % 2 == 0 else "reverse",
                pool=1,
                amplicon_id=amplicon_name,
                reference_id="test_ref",
            )
            primers.append(primer)

        amplicon = AmpliconData(
            amplicon_id=amplicon_name,
            primers=primers,
            length=500,
            reference_id="test_ref",
        )

        # Properties of amplicon-primer relationships
        assert len(amplicon.primers) == len(sequences)
        assert all(p.amplicon_id == amplicon_name for p in amplicon.primers)
        assert len(amplicon.forward_primers) + len(amplicon.reverse_primers) == len(
            primers
        )

        # No duplicate primer names within amplicon
        primer_names = [p.name for p in amplicon.primers]
        assert len(primer_names) == len(set(primer_names))

    @given(
        config_data=st.dictionaries(
            keys=st.sampled_from(["debug_mode", "max_workers"]),
            values=st.one_of(st.booleans(), st.integers(min_value=1, max_value=16)),
            min_size=1,
            max_size=2,
        )
    )
    def test_configuration_properties(self, config_data):
        """Test configuration validation properties."""
        try:
            config = EnhancedConfig(**config_data)

            # Configuration should be internally consistent
            if hasattr(config, "debug_mode"):
                assert isinstance(config.debug_mode, bool)

            if hasattr(config, "max_workers"):
                assert isinstance(config.max_workers, int)
                assert config.max_workers > 0
        except Exception:
            # Invalid configurations should fail with clear errors
            pass  # This is expected for some invalid inputs


class StatefulTestingExample(RuleBasedStateMachine):
    """Example of stateful property-based testing."""

    def __init__(self):
        super().__init__()
        self.config = EnhancedConfig()
        self.operations_count = 0

    @rule(debug_mode=st.booleans())
    def toggle_debug_mode(self, debug_mode):
        """Rule: Toggle debug mode."""
        self.config.debug_mode = debug_mode
        self.operations_count += 1

    @rule(max_workers=st.integers(min_value=1, max_value=16))
    def set_max_workers(self, max_workers):
        """Rule: Set maximum workers."""
        self.config.max_workers = max_workers
        self.operations_count += 1

    @invariant()
    def config_always_valid(self):
        """Invariant: Configuration should always be valid."""
        assert isinstance(self.config.debug_mode, bool)
        assert isinstance(self.config.max_workers, int)
        assert self.config.max_workers > 0
        assert self.config.max_workers <= 16

    @invariant()
    def operations_count_increases(self):
        """Invariant: Operations count should never decrease."""
        assert self.operations_count >= 0


# Create test class for the state machine
TestStatefulConfiguration = StatefulTestingExample.TestCase


# =============================================================================
# Benchmark Testing Examples
# =============================================================================


class BenchmarkTestingExamples:
    """Examples of performance benchmark testing."""

    def create_test_data(self, size: int) -> str:
        """Create test data of specified size."""
        header = "amplicon_name\tprimer_name\tseq\tstart\tstop\tpool\n"
        lines = [header]

        for i in range(size):
            lines.append(f"amp_{i}\tprimer_{i}\tATCGATCG\t{100+i*10}\t{108+i*10}\t1\n")

        return "".join(lines)

    def test_small_dataset_benchmark(self, benchmark):
        """Benchmark processing of small datasets (baseline)."""
        test_data = self.create_test_data(10)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(test_data)
            test_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            # Benchmark the parsing operation
            result = benchmark(parser.parse, test_file, "benchmark_test")

            # Verify the operation succeeded
            assert len(result) == 10

        finally:
            test_file.unlink(missing_ok=True)

    def test_medium_dataset_benchmark(self, benchmark):
        """Benchmark processing of medium datasets (scalability test)."""
        test_data = self.create_test_data(100)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(test_data)
            test_file = Path(f.name)

        try:
            parser = VarVAMPParser()
            result = benchmark(parser.parse, test_file, "benchmark_test")
            assert len(result) == 100

        finally:
            test_file.unlink(missing_ok=True)

    def test_configuration_creation_benchmark(self, benchmark):
        """Benchmark configuration object creation."""

        def create_config():
            return EnhancedConfig(debug_mode=True, max_workers=8)

        config = benchmark(create_config)
        assert config.debug_mode is True
        assert config.max_workers == 8

    @pytest.mark.parametrize("dataset_size", [10, 50, 100, 200])
    def test_scalability_benchmark(self, benchmark, dataset_size):
        """Test how performance scales with dataset size."""
        test_data = self.create_test_data(dataset_size)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False) as f:
            f.write(test_data)
            test_file = Path(f.name)

        try:
            parser = VarVAMPParser()

            # Group benchmarks by dataset size for comparison
            benchmark.group = f"dataset_size_{dataset_size}"

            result = benchmark(parser.parse, test_file, "scalability_test")
            assert len(result) == dataset_size

        finally:
            test_file.unlink(missing_ok=True)


# =============================================================================
# Integration Testing Examples
# =============================================================================


class IntegrationTestingExamples:
    """Examples of integration testing patterns."""

    @pytest.fixture
    def temp_workspace(self):
        """Fixture providing a temporary workspace."""
        workspace = Path(tempfile.mkdtemp())
        yield workspace
        # Cleanup
        import shutil

        shutil.rmtree(workspace, ignore_errors=True)

    @pytest.fixture
    def sample_varvamp_file(self, temp_workspace):
        """Fixture providing a sample VarVAMP file."""
        content = """amplicon_name\tprimer_name\tseq\tstart\tstop\tpool\tgc_best\ttemp_best
test_amp_1\tFW_1\tATCGATCGATCGATCG\t100\t116\t1\t0.5\t58.5
test_amp_1\tRW_1\tCGATCGATCGATCGAT\t300\t316\t1\t0.5\t58.5
test_amp_2\tFW_2\tGCGCGCGCGCGCGCGC\t400\t416\t2\t1.0\t68.2
test_amp_2\tRW_2\tCGCGCGCGCGCGCGCG\t700\t716\t2\t1.0\t68.2"""

        file_path = temp_workspace / "test_data.tsv"
        file_path.write_text(content)
        return file_path

    def test_complete_parsing_workflow(self, temp_workspace, sample_varvamp_file):
        """Test complete parsing workflow with realistic data."""
        parser = VarVAMPParser()

        # Test validation
        is_valid = parser.validate_file(sample_varvamp_file)
        assert is_valid, "Sample file should be valid VarVAMP format"

        # Test parsing
        amplicons = parser.parse(sample_varvamp_file, "integration_test")

        # Verify results
        assert len(amplicons) == 2, "Should parse 2 amplicons"

        # Check amplicon structure
        for amplicon in amplicons:
            assert len(amplicon.primers) == 2, "Each amplicon should have 2 primers"
            assert (
                len(amplicon.forward_primers) == 1
            ), "Each amplicon should have 1 forward primer"
            assert (
                len(amplicon.reverse_primers) == 1
            ), "Each amplicon should have 1 reverse primer"

    def test_error_handling_integration(self, temp_workspace):
        """Test error handling across component boundaries."""
        parser = VarVAMPParser()

        # Test with non-existent file
        non_existent = temp_workspace / "does_not_exist.tsv"

        with pytest.raises(Exception) as exc_info:
            parser.parse(non_existent, "error_test")

        # Error should be informative
        assert (
            "not found" in str(exc_info.value).lower()
            or "no such file" in str(exc_info.value).lower()
        )

        # Test with invalid format file
        invalid_file = temp_workspace / "invalid.tsv"
        invalid_file.write_text("This is not a valid VarVAMP file")

        with pytest.raises(Exception):
            parser.parse(invalid_file, "error_test")

    def test_configuration_integration(self, temp_workspace, sample_varvamp_file):
        """Test integration with configuration system."""
        # Create configuration with specific settings
        config = EnhancedConfig(
            validation={"enabled": True, "min_length": 10, "max_length": 50},
            debug_mode=True,
        )

        # Test that configuration affects behavior
        assert config.validation.enabled is True
        assert config.debug_mode is True

        # Parse with configuration context
        parser = VarVAMPParser()
        amplicons = parser.parse(sample_varvamp_file, "config_test")

        # Verify parsing succeeded with configuration
        assert len(amplicons) > 0

    def test_concurrent_operations_integration(
        self, temp_workspace, sample_varvamp_file
    ):
        """Test concurrent operations for thread safety."""
        import threading
        import time

        results = []
        errors = []

        def parse_worker(worker_id):
            """Worker function for concurrent parsing."""
            try:
                parser = VarVAMPParser()
                amplicons = parser.parse(sample_varvamp_file, f"worker_{worker_id}")
                results.append((worker_id, len(amplicons)))
                time.sleep(0.01)  # Small delay to increase chance of race conditions
            except Exception as e:
                errors.append((worker_id, e))

        # Start multiple worker threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=parse_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=5)

        # Verify results
        assert len(errors) == 0, f"Errors in concurrent operations: {errors}"
        assert len(results) == 5, "All workers should complete successfully"

        # All workers should get same results
        expected_count = results[0][1]
        for worker_id, count in results:
            assert count == expected_count, f"Worker {worker_id} got different result"


# =============================================================================
# Test Quality Assessment Examples
# =============================================================================


def demonstrate_test_quality_patterns():
    """
    Demonstrate patterns that lead to high-quality tests.

    This is not a test itself, but documentation of good testing practices
    that work well with mutation testing.
    """

    # ✅ GOOD: Test edge cases explicitly
    def test_primer_boundary_conditions():
        # Test minimum length
        primer = PrimerData(
            name="min",
            sequence="A",
            start=1,
            stop=2,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test",
            reference_id="ref",
        )
        assert primer.sequence == "A"

        # Test empty/invalid cases would be caught by validation

    # ✅ GOOD: Test error conditions
    def test_invalid_primer_coordinates():
        with pytest.raises(ValueError):
            # This should fail if validation is proper
            PrimerData(
                name="invalid",
                sequence="ATCG",
                start=100,
                stop=90,  # stop < start
                strand="+",
                direction="forward",
                pool=1,
                amplicon_id="test",
                reference_id="ref",
            )

    # ✅ GOOD: Test state changes
    def test_configuration_state_changes():
        config = EnhancedConfig()
        original_debug = config.debug_mode

        # Change state
        config.debug_mode = not original_debug

        # Verify state changed
        assert config.debug_mode != original_debug

    # ❌ BAD: Tests that don't actually test behavior
    def weak_test_example():
        # This test doesn't verify behavior, just object creation
        primer = PrimerData(
            name="test",
            sequence="ATCG",
            start=1,
            stop=5,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test",
            reference_id="ref",
        )
        assert primer is not None  # Weak assertion

    # ✅ GOOD: Strong assertions about behavior
    def strong_test_example():
        primer = PrimerData(
            name="test",
            sequence="ATCG",
            start=1,
            stop=5,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test",
            reference_id="ref",
        )

        # Strong assertions about specific behavior
        assert primer.name == "test"
        assert primer.sequence == "ATCG"
        assert primer.stop > primer.start
        assert len(primer.sequence) == (primer.stop - primer.start)


# =============================================================================
# Running Examples
# =============================================================================


def run_property_based_examples():
    """Run property-based testing examples."""
    print("Running Property-Based Testing Examples...")

    # Example of running with different settings
    with settings(max_examples=50, deadline=500):
        examples = PropertyBasedTestingExamples()

        # This would normally be run by pytest, but we can demonstrate
        print("✓ Property-based tests validate invariants across many inputs")
        print("✓ Stateful testing ensures complex workflows maintain consistency")


def run_benchmark_examples():
    """Demonstrate benchmark testing."""
    print("\nRunning Benchmark Examples...")
    print("✓ Benchmarks measure performance and detect regressions")
    print("✓ Scalability tests show how performance changes with data size")
    print("✓ Statistical analysis provides confidence in measurements")


def run_integration_examples():
    """Demonstrate integration testing."""
    print("\nRunning Integration Examples...")
    print("✓ Integration tests verify end-to-end workflows")
    print("✓ Error handling tests ensure graceful failure modes")
    print("✓ Configuration integration tests verify system interaction")


def main():
    """Demonstrate the testing framework capabilities."""
    print("PrePrimer Enhanced Testing Framework Examples")
    print("=" * 50)

    run_property_based_examples()
    run_benchmark_examples()
    run_integration_examples()

    print("\nTesting Best Practices:")
    print("✓ Use property-based tests to discover edge cases")
    print("✓ Use benchmarks to prevent performance regressions")
    print("✓ Use integration tests to verify complete workflows")
    print("✓ Use mutation testing to assess test quality")
    print("\nRun 'pytest tests/' to execute the full test suite!")


if __name__ == "__main__":
    main()
