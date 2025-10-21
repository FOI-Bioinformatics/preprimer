#!/usr/bin/env python3
"""
Basic Format Conversion Example

Demonstrates simple conversion between primer design formats using PrePrimer.
This example shows the most common use case: converting a VarVAMP TSV file
to ARTIC BED format.
"""

from pathlib import Path

from preprimer.core.converter import Converter


def main():
    """Convert a VarVAMP primer scheme to ARTIC format."""

    # Initialize converter
    converter = Converter()

    # Input file (replace with your actual file path)
    input_file = "path/to/primers.tsv"

    # Check if input file exists
    if not Path(input_file).exists():
        print(f"Error: Input file not found: {input_file}")
        print("\nPlease update the 'input_file' variable with your file path.")
        print("Example: input_file = 'tests/test_data/datasets/small/primers.tsv'")
        return

    # Output directory
    output_dir = "output/basic_conversion"

    print("=" * 70)
    print("PrePrimer Basic Conversion Example")
    print("=" * 70)
    print()

    print(f"Input file:  {input_file}")
    print(f"Output dir:  {output_dir}")
    print(f"Format:      VarVAMP → ARTIC")
    print()

    try:
        # Perform conversion
        print("Converting...")
        amplicons = converter.convert(
            input_file=input_file,
            output_dir=output_dir,
            output_formats=["artic"],
            prefix="MyVirus",
        )

        # Print results
        print(f"\n✓ Conversion successful!")
        print(f"  Amplicons converted: {len(amplicons)}")
        print()
        print("Output files:")
        print(f"  {output_dir}/artic/primer.bed")
        print(f"  {output_dir}/artic/reference.fasta")
        print(f"  {output_dir}/artic/info.json")
        print()

        # Print amplicon summary
        print("Amplicon Summary:")
        print("-" * 70)
        for i, amplicon in enumerate(amplicons[:5], 1):  # Show first 5
            print(f"{i}. {amplicon.amplicon_id}")
            print(f"   Length: {amplicon.length} bp")
            print(f"   Primers: {len(amplicon.primers)}")

        if len(amplicons) > 5:
            print(f"... and {len(amplicons) - 5} more amplicons")

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("Please check the input file path.")

    except Exception as e:
        print(f"\n✗ Conversion failed: {e}")
        print(f"Error type: {type(e).__name__}")


if __name__ == "__main__":
    main()
