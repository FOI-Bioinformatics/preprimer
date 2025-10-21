#!/usr/bin/env python3
"""
Batch Processing Example

Demonstrates how to process multiple primer scheme files in batch,
converting them all to multiple output formats with progress tracking
and error handling.
"""

from pathlib import Path

from preprimer.core.converter import Converter
from preprimer.core.exceptions import PrePrimerError


def process_single_file(converter, input_file, output_base_dir):
    """
    Process a single primer scheme file.

    Args:
        converter: Converter instance
        input_file: Path to input file
        output_base_dir: Base output directory

    Returns:
        tuple: (success: bool, amplicon_count: int, error_message: str)
    """
    try:
        # Create output directory based on input filename
        scheme_name = input_file.stem
        output_dir = output_base_dir / scheme_name

        # Convert to multiple formats
        amplicons = converter.convert(
            input_file=str(input_file),
            output_dir=str(output_dir),
            output_formats=["artic", "fasta", "sts"],
            prefix=scheme_name,
        )

        return True, len(amplicons), None

    except PrePrimerError as e:
        return False, 0, f"{type(e).__name__}: {e}"

    except Exception as e:
        return False, 0, f"Unexpected error: {e}"


def main():
    """Process multiple primer scheme files in batch."""

    print("=" * 70)
    print("PrePrimer Batch Processing Example")
    print("=" * 70)
    print()

    # Configuration
    input_directory = Path("input_schemes")
    output_directory = Path("output/batch_conversion")
    file_pattern = "*.tsv"  # Process all TSV files

    # Create directories if they don't exist
    output_directory.mkdir(parents=True, exist_ok=True)

    # Find input files
    input_files = list(input_directory.glob(file_pattern))

    if not input_files:
        print(f"No files found matching pattern '{file_pattern}' in {input_directory}")
        print()
        print("To use this example:")
        print(f"1. Create directory: {input_directory}")
        print(f"2. Place primer scheme files (.tsv) in {input_directory}")
        print("3. Run this script again")
        return

    print(f"Found {len(input_files)} files to process")
    print(f"Input directory:  {input_directory}")
    print(f"Output directory: {output_directory}")
    print(f"Output formats:   ARTIC, FASTA, STS")
    print()

    # Initialize converter
    converter = Converter()

    # Process files
    results = {
        "success": [],
        "failed": [],
        "total_amplicons": 0,
    }

    print("Processing files...")
    print("-" * 70)

    for i, input_file in enumerate(input_files, 1):
        print(f"\n[{i}/{len(input_files)}] {input_file.name}")

        success, amplicon_count, error = process_single_file(
            converter, input_file, output_directory
        )

        if success:
            results["success"].append(input_file.name)
            results["total_amplicons"] += amplicon_count
            print(f"  ✓ Success: {amplicon_count} amplicons converted")
        else:
            results["failed"].append((input_file.name, error))
            print(f"  ✗ Failed: {error}")

    # Summary
    print()
    print("=" * 70)
    print("Batch Processing Summary")
    print("=" * 70)
    print()
    print(f"Total files:       {len(input_files)}")
    print(f"Successful:        {len(results['success'])}")
    print(f"Failed:            {len(results['failed'])}")
    print(f"Total amplicons:   {results['total_amplicons']}")
    print()

    if results["success"]:
        print("Successfully processed files:")
        for filename in results["success"]:
            print(f"  ✓ {filename}")
        print()

    if results["failed"]:
        print("Failed files:")
        for filename, error in results["failed"]:
            print(f"  ✗ {filename}")
            print(f"    Error: {error}")
        print()

    # Success rate
    success_rate = (
        len(results["success"]) / len(input_files) * 100 if input_files else 0
    )
    print(f"Success rate: {success_rate:.1f}%")
    print()

    print(f"Output location: {output_directory.absolute()}")


if __name__ == "__main__":
    main()
