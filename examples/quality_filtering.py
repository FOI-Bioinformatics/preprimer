#!/usr/bin/env python3
"""
Quality Filtering Example

Demonstrates how to filter primers based on quality metrics such as
GC content, melting temperature, primer length, and other characteristics.
"""

from pathlib import Path
from typing import List

from preprimer.core.interfaces import AmpliconData, PrimerData
from preprimer.parsers import VarVAMPParser
from preprimer.writers import ARTICWriter


def filter_primers_by_gc(primers: List[PrimerData], min_gc: float, max_gc: float) -> List[PrimerData]:
    """Filter primers by GC content."""
    return [
        p
        for p in primers
        if p.gc_content is not None and min_gc <= p.gc_content <= max_gc
    ]


def filter_primers_by_tm(primers: List[PrimerData], min_tm: float, max_tm: float) -> List[PrimerData]:
    """Filter primers by melting temperature."""
    return [p for p in primers if p.tm is not None and min_tm <= p.tm <= max_tm]


def filter_primers_by_length(primers: List[PrimerData], min_len: int, max_len: int) -> List[PrimerData]:
    """Filter primers by sequence length."""
    return [p for p in primers if min_len <= p.length <= max_len]


def has_degenerate_bases(sequence: str) -> bool:
    """Check if sequence contains degenerate IUPAC bases."""
    degenerate = set("RYSWKMBDHVN")
    return any(base in degenerate for base in sequence.upper())


def analyze_primer_quality(amplicons: List[AmpliconData]):
    """
    Analyze primer quality metrics.

    Args:
        amplicons: List of AmpliconData objects

    Returns:
        dict: Quality statistics
    """
    all_primers = []
    for amplicon in amplicons:
        all_primers.extend(amplicon.primers)

    stats = {
        "total_primers": len(all_primers),
        "gc_content": [],
        "tm": [],
        "length": [],
        "degenerate_count": 0,
    }

    for primer in all_primers:
        if primer.gc_content is not None:
            stats["gc_content"].append(primer.gc_content)
        if primer.tm is not None:
            stats["tm"].append(primer.tm)
        if primer.length:
            stats["length"].append(primer.length)
        if has_degenerate_bases(primer.sequence):
            stats["degenerate_count"] += 1

    return stats


def filter_amplicons_by_quality(
    amplicons: List[AmpliconData],
    min_gc: float = 30.0,
    max_gc: float = 70.0,
    min_tm: float = 55.0,
    max_tm: float = 65.0,
    min_length: int = 18,
    max_length: int = 30,
) -> List[AmpliconData]:
    """
    Filter amplicons to keep only those with primers meeting quality criteria.

    Args:
        amplicons: List of amplicons to filter
        min_gc: Minimum GC content (%)
        max_gc: Maximum GC content (%)
        min_tm: Minimum melting temperature (°C)
        max_tm: Maximum melting temperature (°C)
        min_length: Minimum primer length
        max_length: Maximum primer length

    Returns:
        List of filtered amplicons
    """
    filtered_amplicons = []

    for amplicon in amplicons:
        # Filter primers by all criteria
        filtered_primers = amplicon.primers

        # Apply GC filter
        filtered_primers = filter_primers_by_gc(filtered_primers, min_gc, max_gc)

        # Apply Tm filter
        filtered_primers = filter_primers_by_tm(filtered_primers, min_tm, max_tm)

        # Apply length filter
        filtered_primers = filter_primers_by_length(
            filtered_primers, min_length, max_length
        )

        # Keep amplicon only if it has both forward and reverse primers
        forward_primers = [p for p in filtered_primers if p.direction == "forward"]
        reverse_primers = [p for p in filtered_primers if p.direction == "reverse"]

        if forward_primers and reverse_primers:
            # Create new amplicon with filtered primers
            filtered_amplicon = AmpliconData(
                amplicon_id=amplicon.amplicon_id,
                primers=filtered_primers,
                length=amplicon.length,
                reference_id=amplicon.reference_id,
                start=amplicon.start,
                end=amplicon.end,
                pool=amplicon.pool,
                metadata=amplicon.metadata,
            )
            filtered_amplicons.append(filtered_amplicon)

    return filtered_amplicons


def main():
    """Filter primers based on quality metrics."""

    print("=" * 70)
    print("PrePrimer Quality Filtering Example")
    print("=" * 70)
    print()

    # Input file
    input_file = "path/to/primers.tsv"

    if not Path(input_file).exists():
        print(f"Input file not found: {input_file}")
        print()
        print("To use this example:")
        print("1. Update 'input_file' with your primer scheme file")
        print("2. Adjust quality thresholds as needed")
        print()
        print("Example: input_file = 'tests/test_data/datasets/small/primers.tsv'")
        return

    # Quality criteria
    quality_criteria = {
        "min_gc": 35.0,  # Minimum GC content (%)
        "max_gc": 65.0,  # Maximum GC content (%)
        "min_tm": 57.0,  # Minimum Tm (°C)
        "max_tm": 63.0,  # Maximum Tm (°C)
        "min_length": 20,  # Minimum primer length
        "max_length": 28,  # Maximum primer length
    }

    print(f"Input file: {input_file}")
    print()
    print("Quality Criteria:")
    print(f"  GC content:  {quality_criteria['min_gc']:.1f}% - {quality_criteria['max_gc']:.1f}%")
    print(f"  Tm:          {quality_criteria['min_tm']:.1f}°C - {quality_criteria['max_tm']:.1f}°C")
    print(f"  Length:      {quality_criteria['min_length']}-{quality_criteria['max_length']} bp")
    print()

    # Parse input
    parser = VarVAMPParser()
    amplicons = parser.parse(input_file, prefix="ref")

    print(f"Original amplicons: {len(amplicons)}")
    print()

    # Analyze original quality
    print("Original Quality Statistics:")
    print("-" * 70)
    original_stats = analyze_primer_quality(amplicons)

    if original_stats["gc_content"]:
        gc_values = original_stats["gc_content"]
        print(f"GC Content:  {min(gc_values):.1f}% - {max(gc_values):.1f}% ", end="")
        print(f"(mean: {sum(gc_values) / len(gc_values):.1f}%)")

    if original_stats["tm"]:
        tm_values = original_stats["tm"]
        print(f"Tm:          {min(tm_values):.1f}°C - {max(tm_values):.1f}°C ", end="")
        print(f"(mean: {sum(tm_values) / len(tm_values):.1f}°C)")

    if original_stats["length"]:
        length_values = original_stats["length"]
        print(f"Length:      {min(length_values)}-{max(length_values)} bp ", end="")
        print(f"(mean: {sum(length_values) / len(length_values):.1f} bp)")

    print(f"Degenerate:  {original_stats['degenerate_count']} primers")
    print()

    # Apply filters
    print("Applying quality filters...")
    filtered_amplicons = filter_amplicons_by_quality(amplicons, **quality_criteria)

    print(f"Filtered amplicons: {len(filtered_amplicons)}")
    print()

    # Analyze filtered quality
    if filtered_amplicons:
        print("Filtered Quality Statistics:")
        print("-" * 70)
        filtered_stats = analyze_primer_quality(filtered_amplicons)

        if filtered_stats["gc_content"]:
            gc_values = filtered_stats["gc_content"]
            print(
                f"GC Content:  {min(gc_values):.1f}% - {max(gc_values):.1f}% ",
                end="",
            )
            print(f"(mean: {sum(gc_values) / len(gc_values):.1f}%)")

        if filtered_stats["tm"]:
            tm_values = filtered_stats["tm"]
            print(
                f"Tm:          {min(tm_values):.1f}°C - {max(tm_values):.1f}°C ",
                end="",
            )
            print(f"(mean: {sum(tm_values) / len(tm_values):.1f}°C)")

        if filtered_stats["length"]:
            length_values = filtered_stats["length"]
            print(
                f"Length:      {min(length_values)}-{max(length_values)} bp ",
                end="",
            )
            print(f"(mean: {sum(length_values) / len(length_values):.1f} bp)")

        print(f"Degenerate:  {filtered_stats['degenerate_count']} primers")
        print()

        # Summary
        print("Summary:")
        print("-" * 70)
        removed = len(amplicons) - len(filtered_amplicons)
        retention = len(filtered_amplicons) / len(amplicons) * 100 if amplicons else 0

        print(f"Original:   {len(amplicons)} amplicons")
        print(f"Filtered:   {len(filtered_amplicons)} amplicons")
        print(f"Removed:    {removed} amplicons")
        print(f"Retention:  {retention:.1f}%")
        print()

        # Save filtered results
        output_dir = "output/quality_filtered"
        print(f"Saving filtered primers to: {output_dir}")

        writer = ARTICWriter()
        writer.write(
            amplicons=filtered_amplicons,
            output_path=output_dir,
            prefix="filtered",
        )

        print(f"✓ Filtered primers saved")

    else:
        print("⚠ No amplicons passed quality filters!")
        print("Consider relaxing the quality criteria.")


if __name__ == "__main__":
    main()
