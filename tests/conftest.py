"""
Pytest configuration and shared fixtures for PrePrimer tests.

This module provides shared test configuration, fixtures, and utilities
for harmonized testing across all parser types.
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

from preprimer.core.config import PrePrimerConfig
from preprimer.core.registry import parser_registry, writer_registry

# Add preprimer to path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import and register all components


@pytest.fixture(scope="session")
def test_data_dir():
    """Path to test data directory."""
    return Path(__file__).parent / "test_data"


@pytest.fixture(scope="session")
def varvamp_test_file(test_data_dir):
    """VarVAMP test file."""
    return test_data_dir / "ASFV_long" / "primers.tsv"


@pytest.fixture(scope="session")
def varvamp_reference_file(test_data_dir):
    """VarVAMP reference file."""
    return test_data_dir / "ASFV_long" / "ambiguous_consensus.fasta"


@pytest.fixture(scope="session")
def artic_test_file(test_data_dir):
    """ARTIC test file."""
    return test_data_dir / "ASFV.scheme.bed"


@pytest.fixture(scope="session")
def olivar_test_file(test_data_dir):
    """Olivar test file."""
    return test_data_dir / "olivar_examples" / "olivar-design.csv"


@pytest.fixture(scope="session")
def olivar_reference_file(test_data_dir):
    """Olivar reference file."""
    return test_data_dir / "olivar_examples" / "EPI_ISL_402124_ref.fasta"


@pytest.fixture
def test_config():
    """Standard test configuration."""
    return PrePrimerConfig(
        validate_sequences=True,
        force_overwrite=True,
        min_primer_length=10,
        max_primer_length=50,
    )


@pytest.fixture
def temp_output_dir():
    """Temporary output directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture(scope="session", autouse=True)
def verify_test_environment():
    """Verify test environment is properly set up."""
    # Check that parsers are registered
    expected_parsers = ["varvamp", "artic", "olivar"]
    registered_parsers = parser_registry.list_formats()

    for parser in expected_parsers:
        assert parser in registered_parsers, f"Parser '{parser}' not registered"

    # Check that writers are registered
    expected_writers = ["artic", "fasta", "sts"]
    registered_writers = writer_registry.list_formats()

    for writer in expected_writers:
        assert writer in registered_writers, f"Writer '{writer}' not registered"


@pytest.fixture(params=["varvamp", "artic", "olivar"])
def parser_test_data(request, test_data_dir):
    """Parametrized fixture providing test data for all parsers."""
    parser_files = {
        "varvamp": {
            "file": test_data_dir / "ASFV_long" / "primers.tsv",
            "reference": test_data_dir / "ASFV_long" / "ambiguous_consensus.fasta",
            "expected_amplicons": 80,
            "expected_primers": 160,
            "prefix": "ASFV",
        },
        "artic": {
            "file": test_data_dir / "ASFV.scheme.bed",
            "reference": None,
            "expected_amplicons": 80,  # Will be calculated from file
            "expected_primers": 160,  # Will be calculated from file
            "prefix": "ASFV",
        },
        "olivar": {
            "file": test_data_dir / "olivar_examples" / "olivar-design.csv",
            "reference": test_data_dir / "olivar_examples" / "EPI_ISL_402124_ref.fasta",
            "expected_amplicons": 5,
            "expected_primers": 10,
            "prefix": "COVID19",
        },
    }

    data = parser_files[request.param]
    data["format"] = request.param

    # Skip if test file doesn't exist
    if not data["file"].exists():
        pytest.skip(f"Test file not available for {request.param}: {data['file']}")

    # Calculate actual values for ARTIC
    if request.param == "artic":
        with open(data["file"]) as f:
            lines = [line for line in f if line.strip() and not line.startswith("#")]
        data["expected_primers"] = len(lines)
        data["expected_amplicons"] = len(lines) // 2

    return data


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "parser: marks tests for specific parsers")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid or "workflow" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark parser-specific tests
        if "varvamp" in item.nodeid.lower():
            item.add_marker(pytest.mark.parser)
        elif "artic" in item.nodeid.lower():
            item.add_marker(pytest.mark.parser)
        elif "olivar" in item.nodeid.lower():
            item.add_marker(pytest.mark.parser)


@pytest.fixture
def sample_primer_data():
    """Sample primer data for testing."""
    from preprimer.core.interfaces import PrimerData

    return [
        PrimerData(
            name="test_primer_F",
            sequence="ATCGATCGATCGATCGATCG",
            start=100,
            stop=120,
            strand="+",
            direction="forward",
            pool=1,
            amplicon_id="test_amplicon_1",
            reference_id="test_ref",
            gc_content=50.0,
            tm=60.0,
            score=1.0,
        ),
        PrimerData(
            name="test_primer_R",
            sequence="CGATCGATCGATCGATCGAT",
            start=300,
            stop=280,  # Reverse primer
            strand="-",
            direction="reverse",
            pool=1,
            amplicon_id="test_amplicon_1",
            reference_id="test_ref",
            gc_content=50.0,
            tm=60.0,
            score=1.0,
        ),
    ]


@pytest.fixture
def sample_amplicon_data(sample_primer_data):
    """Sample amplicon data for testing."""
    from preprimer.core.interfaces import AmpliconData

    return AmpliconData(
        amplicon_id="test_amplicon_1",
        primers=sample_primer_data,
        length=200,
        reference_id="test_ref",
    )
