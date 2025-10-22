"""
Test data factories for PrePrimer tests.

Provides factory functions for creating common test data scenarios.
"""

import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from preprimer.core.interfaces import AmpliconData, PrimerData
from tests.utils.builders import AmpliconDataBuilder, PrimerDataBuilder, TestDatasetBuilder


def create_minimal_dataset() -> Dict[str, AmpliconData]:
    """
    Create a minimal valid dataset with 1 amplicon.

    Returns:
        Dictionary with single amplicon
    """
    return TestDatasetBuilder().with_n_amplicons(1).build()


def create_small_dataset(amplicons: int = 5, pools: int = 2) -> Dict[str, AmpliconData]:
    """
    Create a small dataset for quick tests.

    Args:
        amplicons: Number of amplicons
        pools: Number of pools to distribute across

    Returns:
        Dictionary of amplicons
    """
    return TestDatasetBuilder().with_n_amplicons(amplicons, pools=pools).build()


def create_medium_dataset(amplicons: int = 80, pools: int = 2) -> Dict[str, AmpliconData]:
    """
    Create a medium-sized dataset for performance tests.

    Args:
        amplicons: Number of amplicons
        pools: Number of pools

    Returns:
        Dictionary of amplicons
    """
    return TestDatasetBuilder().with_n_amplicons(amplicons, pools=pools).build()


def create_circular_genome_dataset() -> Dict[str, AmpliconData]:
    """
    Create a dataset with amplicons that wrap around (circular genome).

    Returns:
        Dictionary with circular genome amplicons
    """
    # Amplicon that wraps around the origin (start > end)
    amplicon1 = (
        AmpliconDataBuilder()
        .with_id("amplicon_circular_1")
        .with_length(400)
        .build()
    )

    # Add primers with wrapped coordinates
    forward = (
        PrimerDataBuilder()
        .with_name("amplicon_circular_1_LEFT")
        .with_sequence("ATCGATCGATCGATCGATCG")
        .with_coordinates(16400, 16420)  # Near end of ref
        .forward()
        .for_amplicon("amplicon_circular_1")
        .build()
    )

    reverse = (
        PrimerDataBuilder()
        .with_name("amplicon_circular_1_RIGHT")
        .with_sequence("CGATCGATCGATCGATCGAT")
        .with_coordinates(200, 180)  # Near start of ref (wrapped)
        .reverse()
        .for_amplicon("amplicon_circular_1")
        .build()
    )

    amplicon1.primers = [forward, reverse]

    return {"amplicon_circular_1": amplicon1}


def create_degenerate_primer_dataset() -> Dict[str, AmpliconData]:
    """
    Create a dataset with IUPAC degenerate primers.

    Returns:
        Dictionary with degenerate primers
    """
    forward = (
        PrimerDataBuilder()
        .with_name("degen_primer_F")
        .with_sequence("ATCGRYSWKMBDHVNATCG")  # Contains all IUPAC codes
        .forward()
        .for_amplicon("degen_amplicon")
        .build()
    )

    reverse = (
        PrimerDataBuilder()
        .with_name("degen_primer_R")
        .with_sequence("CGATNNNNNNATCG")
        .reverse()
        .with_coordinates(300, 286)
        .for_amplicon("degen_amplicon")
        .build()
    )

    amplicon = (
        AmpliconDataBuilder()
        .with_id("degen_amplicon")
        .with_primers([forward, reverse])
        .build()
    )

    return {"degen_amplicon": amplicon}


def create_multi_pool_dataset(pools: int = 4) -> Dict[str, AmpliconData]:
    """
    Create a dataset with multiple pools.

    Args:
        pools: Number of pools

    Returns:
        Dictionary with amplicons across pools
    """
    return TestDatasetBuilder().with_n_amplicons(pools * 4, pools=pools).build()


def create_alternates_dataset() -> Dict[str, AmpliconData]:
    """
    Create a dataset with alternate primers for same amplicon.

    Returns:
        Dictionary with amplicons having multiple primer options
    """
    primers: List[PrimerData] = []

    # Add 2 forward primers
    for i in range(1, 3):
        primers.append(
            PrimerDataBuilder()
            .with_name(f"alt_amplicon_LEFT_alt{i}")
            .with_sequence(f"{'A' * i}TCGATCGATCGATCGATCG")
            .forward()
            .for_amplicon("alt_amplicon")
            .with_coordinates(100 + i * 10, 120 + i * 10)
            .build()
        )

    # Add 2 reverse primers
    for i in range(1, 3):
        primers.append(
            PrimerDataBuilder()
            .with_name(f"alt_amplicon_RIGHT_alt{i}")
            .with_sequence(f"CGATCGATCGATCGATCGA{'T' * i}")
            .reverse()
            .for_amplicon("alt_amplicon")
            .with_coordinates(300 + i * 10, 280 + i * 10)
            .build()
        )

    amplicon = (
        AmpliconDataBuilder()
        .with_id("alt_amplicon")
        .with_primers(primers)
        .build()
    )

    return {"alt_amplicon": amplicon}


def create_temp_fasta_file(
    sequence: str = "ATCGATCGATCG",
    name: str = "test_ref"
) -> Path:
    """
    Create a temporary FASTA file.

    Args:
        sequence: Reference sequence
        name: Reference name

    Returns:
        Path to temporary FASTA file
    """
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".fasta", delete=False)
    tmp.write(f">{name}\n{sequence}\n")
    tmp.close()
    return Path(tmp.name)


def create_temp_bed_file(
    primers: List[Tuple[str, int, int, str]],
    reference: str = "test_ref"
) -> Path:
    """
    Create a temporary BED file.

    Args:
        primers: List of (name, start, end, strand) tuples
        reference: Reference name

    Returns:
        Path to temporary BED file
    """
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".bed", delete=False)
    for name, start, end, strand in primers:
        tmp.write(f"{reference}\t{start}\t{end}\t{name}\t60\t{strand}\n")
    tmp.close()
    return Path(tmp.name)


def create_temp_varvamp_file(
    amplicons: Dict[str, AmpliconData]
) -> Path:
    """
    Create a temporary VarVAMP TSV file.

    Args:
        amplicons: Amplicon data to write

    Returns:
        Path to temporary TSV file
    """
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".tsv", delete=False)

    # Write header
    tmp.write(
        "amplicon_name\tamplicon_length\tprimer_name\tpool\tstart\tstop\t"
        "seq\tsize\tgc_best\ttemp_best\tmean_gc\tmean_temp\tscore\n"
    )

    # Write primers
    for amp_id, amplicon in amplicons.items():
        for primer in amplicon.primers:
            tmp.write(
                f"{amp_id}\t{amplicon.length or 200}\t{primer.name}\t{primer.pool}\t"
                f"{primer.start}\t{primer.stop}\t{primer.sequence}\t{len(primer.sequence)}\t"
                f"{primer.gc_content or 0.5}\t{primer.tm or 60.0}\t"
                f"{primer.gc_content or 0.5}\t{primer.tm or 60.0}\t{primer.score or 1.0}\n"
            )

    tmp.close()
    return Path(tmp.name)


def create_malformed_file(
    file_type: str = "varvamp",
    issue: str = "missing_columns"
) -> Path:
    """
    Create a malformed test file for error testing.

    Args:
        file_type: Format type (varvamp, artic, etc.)
        issue: Type of malformation

    Returns:
        Path to malformed file
    """
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=f".{file_type}", delete=False)

    if file_type == "varvamp":
        if issue == "missing_columns":
            tmp.write("amplicon_name\tprimer_name\n")  # Missing most columns
        elif issue == "invalid_data":
            tmp.write(
                "amplicon_name\tamplicon_length\tprimer_name\tpool\tstart\tstop\t"
                "seq\tsize\tgc_best\ttemp_best\tmean_gc\tmean_temp\tscore\n"
                "amp1\tNOT_A_NUMBER\tprimer1\t1\t100\t120\tATCG\t4\t0.5\t60\t0.5\t60\t1.0\n"
            )
        elif issue == "empty_file":
            pass  # Write nothing

    elif file_type == "artic":
        if issue == "invalid_coordinates":
            tmp.write("ref\t200\t100\tprimer_F\t60\t+\n")  # Start > end for forward

    tmp.close()
    return Path(tmp.name)


# Preset scenarios for common testing patterns

SCENARIO_MINIMAL = "minimal"  # 1 amplicon
SCENARIO_SMALL = "small"  # 5 amplicons
SCENARIO_MEDIUM = "medium"  # 80 amplicons
SCENARIO_CIRCULAR = "circular"  # Circular genome
SCENARIO_DEGENERATE = "degenerate"  # Degenerate primers
SCENARIO_MULTI_POOL = "multi_pool"  # 4 pools
SCENARIO_ALTERNATES = "alternates"  # Multiple primer options


def create_dataset_from_scenario(scenario: str) -> Dict[str, AmpliconData]:
    """
    Create a dataset from a predefined scenario.

    Args:
        scenario: Scenario name (use SCENARIO_* constants)

    Returns:
        Dictionary of amplicons for that scenario
    """
    scenarios = {
        SCENARIO_MINIMAL: create_minimal_dataset,
        SCENARIO_SMALL: create_small_dataset,
        SCENARIO_MEDIUM: create_medium_dataset,
        SCENARIO_CIRCULAR: create_circular_genome_dataset,
        SCENARIO_DEGENERATE: create_degenerate_primer_dataset,
        SCENARIO_MULTI_POOL: create_multi_pool_dataset,
        SCENARIO_ALTERNATES: create_alternates_dataset,
    }

    if scenario not in scenarios:
        raise ValueError(f"Unknown scenario: {scenario}. Available: {list(scenarios.keys())}")

    return scenarios[scenario]()
