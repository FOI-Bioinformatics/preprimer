#!/usr/bin/env python3
"""
Demonstration of Olivar primer scheme conversion with PrePrimer.

This example shows how to convert Olivar primer design output to various formats
using both the CLI and Python API.
"""

import tempfile
from pathlib import Path
import sys

# Add preprimer to path if running directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from preprimer import convert_primers
from preprimer.core.registry import parser_registry

# Ensure parsers are registered
import preprimer.parsers
import preprimer.writers


def main():
    """Run the Olivar conversion demonstration."""
    
    print("🧬 PrePrimer - Olivar Integration Demonstration")
    print("=" * 50)
    
    # Path to test data
    test_data_dir = Path(__file__).parent.parent / "tests" / "test_data" / "olivar_examples"
    olivar_file = test_data_dir / "olivar-design.csv"
    reference_file = test_data_dir / "EPI_ISL_402124_ref.fasta"
    
    if not olivar_file.exists():
        print("❌ Test data not found!")
        print(f"   Expected: {olivar_file}")
        print("   Please run the test data generation first.")
        return 1
    
    print(f"📁 Input file: {olivar_file}")
    print(f"📏 File size: {olivar_file.stat().st_size:,} bytes")
    
    # Detect format
    detected_format = parser_registry.detect_format(olivar_file)
    print(f"🔍 Detected format: {detected_format}")
    
    # Parse and show info
    parser = parser_registry.get_parser(detected_format)
    amplicons = parser.parse(olivar_file, "COVID19")
    
    print(f"🧬 Parsed amplicons: {len(amplicons)}")
    print(f"🔬 Total primers: {sum(len(a.primers) for a in amplicons)}")
    
    # Show amplicon details
    print("\n📊 Amplicon Details:")
    for amplicon in amplicons:
        fwd_count = len(amplicon.forward_primers)
        rev_count = len(amplicon.reverse_primers)
        pools = set(p.pool for p in amplicon.primers)
        print(f"   {amplicon.amplicon_id}: {fwd_count}F + {rev_count}R (Pool: {', '.join(map(str, pools))})")
    
    # Convert to multiple formats
    print("\n🔄 Converting to multiple formats...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        output_files = convert_primers(
            input_file=olivar_file,
            output_dir=temp_dir,
            output_formats=["artic", "fasta", "sts"],
            prefix="COVID19_Olivar",
            reference_file=reference_file
        )
        
        print("✅ Conversion successful!")
        
        for format_name, output_file in output_files.items():
            file_size = output_file.stat().st_size
            print(f"   📤 {format_name.upper()}: {file_size:,} bytes")
            
            # Show sample content
            print(f"      Sample content:")
            with open(output_file) as f:
                lines = f.readlines()[:3]  # First 3 lines
                for line in lines:
                    print(f"      {line.rstrip()}")
                if len(lines) >= 3:
                    print("      ...")
            print()
    
    # Show CLI usage
    print("🖥️  CLI Usage Examples:")
    print()
    print("   # Get info about Olivar file")
    print(f"   preprimer info {olivar_file}")
    print()
    print("   # Convert to ARTIC format")
    print(f"   preprimer convert --input {olivar_file} \\")
    print("                    --output-dir schemes/ \\")
    print("                    --output-formats artic \\")
    print("                    --prefix COVID19")
    print()
    print("   # Convert to multiple formats with reference")
    print(f"   preprimer convert --input {olivar_file} \\")
    print("                    --output-dir schemes/ \\")
    print("                    --output-formats artic fasta sts \\")
    print("                    --prefix COVID19 \\")
    print(f"                    --reference {reference_file}")
    print()
    
    # Show Python API usage
    print("🐍 Python API Usage:")
    print("""
    from preprimer import convert_primers
    
    # Simple conversion
    output_files = convert_primers(
        input_file="olivar-design.csv",
        output_dir="schemes/",
        output_formats=["artic", "fasta"],
        prefix="COVID19"
    )
    
    # Access output files
    artic_file = output_files["artic"]
    fasta_file = output_files["fasta"]
    """)
    
    print("🎉 Olivar integration demonstration complete!")
    print("\nPrePrimer now supports:")
    print("   • VarVAMP primer schemes (.tsv)")
    print("   • ARTIC primer schemes (.bed)")  
    print("   • Olivar primer designs (.csv)")
    print("\n   Ready for your viral genomics workflows! 🧬✨")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())