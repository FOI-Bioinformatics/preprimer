#!/usr/bin/env python3
"""
Topology Handling Example

Demonstrates how to handle circular genome topologies (mitochondrial DNA,
plasmids, viral episomes) where amplicons may wrap around the genome origin.
"""

from pathlib import Path

from preprimer.core.topology import GenomeTopology, TopologyDetector
from preprimer.parsers import VarVAMPParser


def analyze_amplicon_topology(amplicon, topology_detector, reference_length):
    """
    Analyze an amplicon for circular genome characteristics.

    Args:
        amplicon: AmpliconData object
        topology_detector: TopologyDetector instance
        reference_length: Reference genome length

    Returns:
        dict: Analysis results
    """
    analysis = {
        "amplicon_id": amplicon.amplicon_id,
        "reported_length": amplicon.length,
        "start": amplicon.start,
        "end": amplicon.end,
        "wraps_origin": False,
        "actual_length": amplicon.length,
    }

    # Check if amplicon wraps around origin (start > end)
    if amplicon.start and amplicon.end:
        if amplicon.start > amplicon.end:
            analysis["wraps_origin"] = True

            # Calculate true length for circular genome
            actual_length = topology_detector.calculate_amplicon_length(
                start=amplicon.start,
                end=amplicon.end,
                reference_length=reference_length,
                is_circular=True,
            )

            analysis["actual_length"] = actual_length
            analysis["calculation"] = (
                f"({reference_length} - {amplicon.start}) + {amplicon.end} + 1 "
                f"= {actual_length}"
            )

    return analysis


def main():
    """Analyze circular genome topology and cross-origin amplicons."""

    print("=" * 70)
    print("PrePrimer Topology Handling Example")
    print("=" * 70)
    print()

    # Example: Human mitochondrial DNA (circular, 16,569 bp)
    input_file = "path/to/mitochondrial_primers.tsv"
    reference_length = 16569  # Human mtDNA length

    if not Path(input_file).exists():
        print(f"Input file not found: {input_file}")
        print()
        print("This example demonstrates circular genome handling.")
        print()
        print("To use this example with real data:")
        print("1. Prepare a mitochondrial primer scheme file")
        print("2. Update the 'input_file' variable")
        print("3. Set correct 'reference_length' (e.g., 16569 for human mtDNA)")
        print()
        print("Example with test data:")
        print("  input_file = 'tests/test_data/datasets/mitochondrial/primers.tsv'")
        print("  reference_length = 16569")
        return

    # Parse primers
    parser = VarVAMPParser()
    amplicons = parser.parse(input_file, prefix="NC_012920.1")

    print(f"Input file:         {input_file}")
    print(f"Reference length:   {reference_length:,} bp")
    print(f"Total amplicons:    {len(amplicons)}")
    print()

    # Detect topology
    print("Detecting genome topology...")
    detector = TopologyDetector()
    topology = detector.detect_topology(amplicons, reference_length=reference_length)

    print(f"Detected topology:  {topology.value}")
    print()

    if topology == GenomeTopology.CIRCULAR:
        print("✓ Circular genome detected")
        print()
        print("Characteristics of circular genomes:")
        print("  • Amplicons can wrap around the origin (position 0/end)")
        print("  • start > end coordinates are valid")
        print("  • Length calculations must account for wrapping")
        print()

        # Analyze each amplicon
        print("Amplicon Analysis:")
        print("-" * 70)

        wrapped_amplicons = []
        standard_amplicons = []

        for amplicon in amplicons:
            analysis = analyze_amplicon_topology(amplicon, detector, reference_length)

            if analysis["wraps_origin"]:
                wrapped_amplicons.append(analysis)
            else:
                standard_amplicons.append(analysis)

        # Report wrapped amplicons (these are the interesting ones)
        if wrapped_amplicons:
            print(f"\nCross-Origin Amplicons ({len(wrapped_amplicons)}):")
            print("-" * 70)

            for analysis in wrapped_amplicons:
                print(f"\n{analysis['amplicon_id']}:")
                print(f"  Coordinates:      {analysis['start']:,} → {analysis['end']:,}")
                print(f"  Wraps origin:     YES ⟲")
                print(f"  Reported length:  {analysis['reported_length']} bp")
                print(f"  Actual length:    {analysis['actual_length']} bp")
                print(f"  Calculation:      {analysis['calculation']}")

        # Report standard amplicons
        if standard_amplicons:
            print(f"\nStandard Amplicons ({len(standard_amplicons)}):")
            print("-" * 70)

            for analysis in standard_amplicons[:3]:  # Show first 3
                print(f"{analysis['amplicon_id']}: ", end="")
                print(f"{analysis['start']:,} → {analysis['end']:,} ", end="")
                print(f"({analysis['actual_length']} bp)")

            if len(standard_amplicons) > 3:
                print(f"... and {len(standard_amplicons) - 3} more")

        # Summary
        print()
        print("Summary:")
        print(f"  Total amplicons:       {len(amplicons)}")
        print(f"  Cross-origin:          {len(wrapped_amplicons)}")
        print(f"  Standard:              {len(standard_amplicons)}")

        if wrapped_amplicons:
            avg_wrapped_length = sum(a["actual_length"] for a in wrapped_amplicons) / len(
                wrapped_amplicons
            )
            print(f"  Avg wrapped length:    {avg_wrapped_length:.0f} bp")

    else:
        print("Linear genome detected")
        print()
        print("All amplicons use standard coordinate system.")
        print("No special topology handling required.")
        print()

        # Show amplicon distribution
        if amplicons:
            print("Amplicon Distribution:")
            print("-" * 70)

            lengths = [amp.length for amp in amplicons if amp.length]
            if lengths:
                print(f"  Min length:  {min(lengths)} bp")
                print(f"  Max length:  {max(lengths)} bp")
                print(f"  Mean length: {sum(lengths) / len(lengths):.0f} bp")


if __name__ == "__main__":
    main()
