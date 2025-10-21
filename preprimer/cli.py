"""
Modern CLI interface for preprimer.
"""

import argparse
import logging
import sys
from pathlib import Path

from .align import align_primers
from .core.converter import PrimerConverter
from .core.enhanced_config import EnhancedConfig
from .core.exceptions import PrePrimerError
from .core.registry import alignment_registry, parser_registry, writer_registry

# Import parsers and writers to register them

logger = logging.getLogger(__name__)


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""

    parser = argparse.ArgumentParser(
        description="PrePrimer - Convert and analyze tiled primer schemes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert VarVAMP to ARTIC format
  preprimer convert --input primers.tsv --output-dir schemes/ --output-formats artic

  # Convert with custom reference
  preprimer convert --input primers.tsv --output-dir schemes/ \\
                   --output-formats artic fasta sts --reference new_ref.fasta

  # Auto-detect input format
  preprimer convert --input primers.bed --output-dir schemes/ --output-formats fasta
        """,
    )

    parser.add_argument("--version", action="version", version="PrePrimer 0.2.0")
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level",
    )
    parser.add_argument("--config", type=Path, help="Configuration file (JSON)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Convert command
    convert_parser = subparsers.add_parser(
        "convert",
        help="Convert primer schemes between formats",
        description=(
            "Convert primer schemes between different formats "
            "(VarVAMP, ARTIC, Olivar)"
        ),
    )

    convert_parser.add_argument(
        "--input", "--primer-info", type=Path, required=True, help="Input primer file"
    )

    convert_parser.add_argument(
        "--output-dir",
        "--output-folder",
        type=Path,
        required=True,
        help="Output directory",
    )

    convert_parser.add_argument(
        "--input-format",
        choices=parser_registry.list_formats(),
        help="Input format (auto-detected if not specified)",
    )

    convert_parser.add_argument(
        "--output-formats",
        "--output-format",
        choices=writer_registry.list_formats(),
        nargs="+",
        default=["artic"],
        help="Output format(s)",
    )

    convert_parser.add_argument(
        "--prefix", default="primers", help="Prefix for output files"
    )

    convert_parser.add_argument(
        "--reference", type=Path, help="Reference genome FASTA file"
    )

    convert_parser.add_argument(
        "--force", action="store_true", help="Overwrite existing output files"
    )

    convert_parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate input file, don't generate output",
    )

    # List formats command
    list_parser = subparsers.add_parser("list", help="List available formats")
    list_parser.add_argument(
        "--parsers", action="store_true", help="List input formats"
    )
    list_parser.add_argument(
        "--writers", action="store_true", help="List output formats"
    )
    list_parser.add_argument("--all", action="store_true", help="List all formats")

    # Info command
    info_parser = subparsers.add_parser("info", help="Show information about a file")
    info_parser.add_argument("file", type=Path, help="File to analyze")

    # Align command
    align_parser = subparsers.add_parser(
        "align",
        help="Align primers to a reference genome",
        description=(
            "Align primers to a reference genome using BLAST, Exonerate, or me-PCR"
        ),
    )

    align_parser.add_argument(
        "--sts-file",
        type=Path,
        required=True,
        help="Input primer file in STS format",
    )

    align_parser.add_argument(
        "--reference",
        type=Path,
        required=True,
        help="Reference genome FASTA file",
    )

    align_parser.add_argument(
        "--output-dir",
        "--output-folder",
        type=Path,
        required=True,
        help="Output directory for alignment results",
    )

    align_parser.add_argument(
        "--output-formats",
        "--output-format",
        choices=["primers", "me-pcr", "merpcr"],
        nargs="+",
        required=True,
        help="Alignment output format(s): 'primers' (BLAST/Exonerate), 'me-pcr', or 'merpcr'",
    )

    align_parser.add_argument(
        "--aligner",
        choices=["blast", "exonerate"],
        default="blast",
        help="Alignment tool for primers format (default: blast)",
    )

    align_parser.add_argument(
        "--prefix",
        default="primers",
        help="Prefix for output files (default: primers)",
    )

    align_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing output files",
    )

    return parser


def cmd_convert(args: argparse.Namespace, config: EnhancedConfig) -> int:
    """Handle convert command."""
    try:
        # Update config with command line args
        if args.force:
            config.output.force_overwrite = True

        converter = PrimerConverter(config)

        if args.validate_only:
            # Just parse and validate
            logger.info("Validation mode - no output will be generated")
            parser = (
                parser_registry.get_parser(args.input_format)
                if args.input_format
                else None
            )

            if parser is None:
                input_format = parser_registry.detect_format(args.input)
                if input_format is None:
                    logger.error("Could not detect input format")
                    return 1
                parser = parser_registry.get_parser(input_format)

            amplicons = parser.parse(args.input, args.prefix)
            converter._validate_amplicons(amplicons)
            logger.info(
                f"✅ Validation successful: {len(amplicons)} amplicons, "
                f"{sum(len(a.primers) for a in amplicons)} primers"
            )
            return 0

        # Convert
        output_files = converter.convert(
            input_file=args.input,
            output_dir=args.output_dir,
            input_format=args.input_format,
            output_formats=args.output_formats,
            prefix=args.prefix,
            reference_file=args.reference,
            force=args.force,
        )

        # Report success
        logger.info("🎉 Conversion completed successfully!")
        for format_name, output_file in output_files.items():
            logger.info(f"  {format_name}: {output_file}")

        return 0

    except PrePrimerError as e:
        logger.error(f"❌ {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.debug("Full traceback:", exc_info=True)
        return 1


def cmd_list(args: argparse.Namespace) -> int:
    """Handle list command."""
    if args.parsers or args.all:
        print("📥 Available input formats:")
        for format_name in parser_registry.list_formats():
            extensions = parser_registry.list_extensions(format_name)
            print(f"  {format_name}: {', '.join(extensions)}")
        print()

    if args.writers or args.all:
        print("📤 Available output formats:")
        for format_name in writer_registry.list_formats():
            writer = writer_registry.get_writer(format_name)
            print(f"  {format_name}: {writer.file_extension}")
        print()

    if not (args.parsers or args.writers or args.all):
        # Default: show both
        return cmd_list(argparse.Namespace(parsers=True, writers=True, all=False))

    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Handle info command."""
    file_path = args.file

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 1

    # Try to detect format
    detected_format = parser_registry.detect_format(file_path)

    print(f"📁 File: {file_path}")
    print(f"📏 Size: {file_path.stat().st_size:,} bytes")

    if detected_format:
        print(f"🔍 Detected format: {detected_format}")

        try:
            parser = parser_registry.get_parser(detected_format)
            amplicons = parser.parse(file_path, "test")

            total_primers = sum(len(a.primers) for a in amplicons)
            print(f"🧬 Amplicons: {len(amplicons)}")
            print(f"🔬 Primers: {total_primers}")

            # Show amplicon summary
            if amplicons:
                print("\n📊 Amplicon details:")
                for i, amplicon in enumerate(amplicons[:5]):  # Show first 5
                    fwd_count = len(amplicon.forward_primers)
                    rev_count = len(amplicon.reverse_primers)
                    print(f"  {amplicon.amplicon_id}: {fwd_count}F + {rev_count}R")

                if len(amplicons) > 5:
                    print(f"  ... and {len(amplicons) - 5} more amplicons")

        except Exception as e:
            print(f"⚠️  Could not parse file: {e}")
    else:
        print("❓ Format: Unknown/unsupported")
        available = parser_registry.list_formats()
        print(f"   Supported formats: {', '.join(available)}")

    return 0


def cmd_align(args: argparse.Namespace) -> int:
    """Handle align command."""
    try:
        # Validate input files exist
        if not args.sts_file.exists():
            logger.error(f"STS file not found: {args.sts_file}")
            return 1

        if not args.reference.exists():
            logger.error(f"Reference file not found: {args.reference}")
            return 1

        # Check if required tools are available
        if "primers" in args.output_formats:
            aligner = args.aligner
            provider = alignment_registry.get_provider(aligner)
            if not provider.is_available():
                logger.error(
                    f"{aligner} is not available on this system. "
                    f"Please install {aligner} and ensure it's in your PATH."
                )
                return 1

        if "me-pcr" in args.output_formats:
            mepcr_provider = alignment_registry.get_provider("me-pcr")
            if not mepcr_provider.is_available():
                logger.error(
                    "me-PCR is not available on this system. "
                    "Please install me-PCR and ensure it's in your PATH."
                )
                return 1

        if "merpcr" in args.output_formats:
            merpcr_provider = alignment_registry.get_provider("merpcr")
            if not merpcr_provider.is_available():
                logger.error(
                    "merPCR is not available on this system. "
                    "Please install merPCR (pip install merpcr) and ensure it's in your PATH."
                )
                return 1

        # Run alignment
        logger.info(f"Aligning primers from {args.sts_file.name}...")
        output_paths = align_primers(
            sts_file=args.sts_file,
            reference_file=args.reference,
            output_dir=args.output_dir,
            output_formats=args.output_formats,
            aligner=args.aligner,
            prefix=args.prefix,
            force=args.force,
        )

        # Report success
        logger.info("🎉 Alignment completed successfully!")
        for format_name, output_path in output_paths.items():
            logger.info(f"  {format_name}: {output_path}")

        return 0

    except PrePrimerError as e:
        logger.error(f"❌ {e}")
        return 1
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        logger.debug("Full traceback:", exc_info=True)
        return 1


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.log_level)

    # Load configuration
    try:
        if args.config:
            config = EnhancedConfig.from_file(args.config)
            logger.info(f"Loaded configuration from: {args.config}")
        else:
            config = EnhancedConfig()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1

    # Route to command handlers
    if args.command == "convert":
        return cmd_convert(args, config)
    elif args.command == "list":
        return cmd_list(args)
    elif args.command == "info":
        return cmd_info(args)
    elif args.command == "align":
        return cmd_align(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
