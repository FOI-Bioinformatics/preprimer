"""
Modern CLI interface for preprimer.
"""

import argparse
import importlib.metadata
import json
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

# Exit codes (stable contract for pipeline integration)
EXIT_OK = 0
EXIT_USER_ERROR = 1  # bad input, validation failure, etc.
EXIT_MISSING_TOOL = 2  # required external tool not available


def get_version() -> str:
    """Return the installed package version (single source of truth)."""
    try:
        return importlib.metadata.version("preprimer")
    except importlib.metadata.PackageNotFoundError:
        from . import __version__

        return __version__


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration.

    Diagnostics go to stderr so that stdout carries only results (and --json),
    keeping the tool pipeline-friendly.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )


def emit(message: str = "") -> None:
    """Write a user-facing result line to stdout (independent of log level)."""
    print(message, file=sys.stdout)


def report_error(exc: Exception) -> None:
    """Render an error to stderr, surfacing user message + suggestions."""
    if isinstance(exc, PrePrimerError):
        message = exc.get_user_message()
    else:
        message = str(exc)
    print(f"[ERROR] {message}", file=sys.stderr)


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

    parser.add_argument(
        "--version", action="version", version=f"PrePrimer {get_version()}"
    )
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

    convert_parser.add_argument(
        "--lenient",
        action="store_true",
        help="Downgrade validation failures to warnings and continue",
    )

    convert_parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Abort if primer coordinates are synthetic (estimated because the "
            "input format lacks positions)"
        ),
    )

    convert_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary to stdout",
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

    align_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary to stdout",
    )

    return parser


def cmd_convert(args: argparse.Namespace, config: EnhancedConfig) -> int:
    """Handle convert command."""
    as_json = getattr(args, "json", False)
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
                    report_error(PrePrimerError("Could not detect input format"))
                    return EXIT_USER_ERROR
                parser = parser_registry.get_parser(input_format)

            amplicons = parser.parse(args.input, args.prefix)
            converter._validate_amplicons(amplicons, lenient=args.lenient)
            primer_count = sum(len(a.primers) for a in amplicons)
            if as_json:
                emit(
                    json.dumps(
                        {
                            "status": "ok",
                            "validated": True,
                            "amplicons": len(amplicons),
                            "primers": primer_count,
                        }
                    )
                )
            else:
                emit(
                    f"[OK] Validation successful: {len(amplicons)} amplicons, "
                    f"{primer_count} primers"
                )
            return EXIT_OK

        # Convert
        output_files = converter.convert(
            input_file=args.input,
            output_dir=args.output_dir,
            input_format=args.input_format,
            output_formats=args.output_formats,
            prefix=args.prefix,
            reference_file=args.reference,
            lenient=args.lenient,
            strict=args.strict,
            force=args.force,
        )

        summary = converter.last_summary

        # Report success
        if as_json:
            emit(json.dumps({"status": "ok", **summary}))
        else:
            emit("Conversion completed successfully.")
            for format_name, output_file in output_files.items():
                emit(f"  {format_name}: {output_file}")
            for warning in summary.get("warnings", []):
                print(f"[WARN] {warning}", file=sys.stderr)

        return EXIT_OK

    except PrePrimerError as e:
        if as_json:
            emit(json.dumps({"status": "error", "message": e.get_user_message()}))
        else:
            report_error(e)
        return EXIT_USER_ERROR
    except Exception as e:
        if as_json:
            emit(json.dumps({"status": "error", "message": str(e)}))
        else:
            report_error(e)
        logger.debug("Full traceback:", exc_info=True)
        return EXIT_USER_ERROR


def cmd_list(args: argparse.Namespace) -> int:
    """Handle list command."""
    if args.parsers or args.all:
        emit("Available input formats:")
        for format_name in parser_registry.list_formats():
            extensions = parser_registry.list_extensions(format_name)
            emit(f"  {format_name}: {', '.join(extensions)}")
        emit()

    if args.writers or args.all:
        emit("Available output formats:")
        for format_name in writer_registry.list_formats():
            writer = writer_registry.get_writer(format_name)
            emit(f"  {format_name}: {writer.file_extension()}")
        emit()

    if not (args.parsers or args.writers or args.all):
        # Default: show both
        return cmd_list(argparse.Namespace(parsers=True, writers=True, all=False))

    return EXIT_OK


def cmd_info(args: argparse.Namespace) -> int:
    """Handle info command."""
    file_path = args.file

    if not file_path.exists():
        report_error(FileNotFoundError(f"File not found: {file_path}"))
        return EXIT_USER_ERROR

    # Try to detect format
    detected_format = parser_registry.detect_format(file_path)

    emit(f"File: {file_path}")
    emit(f"Size: {file_path.stat().st_size:,} bytes")

    if detected_format:
        emit(f"Detected format: {detected_format}")

        try:
            parser = parser_registry.get_parser(detected_format)
            amplicons = parser.parse(file_path, "test")

            total_primers = sum(len(a.primers) for a in amplicons)
            emit(f"Amplicons: {len(amplicons)}")
            emit(f"Primers: {total_primers}")

            # Show amplicon summary
            if amplicons:
                emit("\nAmplicon details:")
                for amplicon in amplicons[:5]:  # Show first 5
                    fwd_count = len(amplicon.forward_primers)
                    rev_count = len(amplicon.reverse_primers)
                    emit(f"  {amplicon.amplicon_id}: {fwd_count}F + {rev_count}R")

                if len(amplicons) > 5:
                    emit(f"  ... and {len(amplicons) - 5} more amplicons")

        except Exception as e:
            report_error(e)
            return EXIT_USER_ERROR
    else:
        emit("Format: Unknown/unsupported")
        available = parser_registry.list_formats()
        emit(f"   Supported formats: {', '.join(available)}")

    return EXIT_OK


def cmd_align(args: argparse.Namespace) -> int:
    """Handle align command."""
    as_json = getattr(args, "json", False)

    def missing_tool(message: str) -> int:
        if as_json:
            emit(json.dumps({"status": "error", "message": message}))
        else:
            print(f"[ERROR] {message}", file=sys.stderr)
        return EXIT_MISSING_TOOL

    try:
        # Validate input files exist
        if not args.sts_file.exists():
            report_error(FileNotFoundError(f"STS file not found: {args.sts_file}"))
            return EXIT_USER_ERROR

        if not args.reference.exists():
            report_error(
                FileNotFoundError(f"Reference file not found: {args.reference}")
            )
            return EXIT_USER_ERROR

        # Check if required tools are available
        if "primers" in args.output_formats:
            aligner = args.aligner
            provider = alignment_registry.get_provider(aligner)
            if not provider.is_available():
                return missing_tool(
                    f"{aligner} is not available on this system. "
                    f"Please install {aligner} and ensure it's in your PATH."
                )

        if "me-pcr" in args.output_formats:
            mepcr_provider = alignment_registry.get_provider("me-pcr")
            if not mepcr_provider.is_available():
                return missing_tool(
                    "me-PCR is not available on this system. "
                    "Please install me-PCR and ensure it's in your PATH."
                )

        if "merpcr" in args.output_formats:
            merpcr_provider = alignment_registry.get_provider("merpcr")
            if not merpcr_provider.is_available():
                return missing_tool(
                    "merPCR is not available on this system. "
                    "Please install merPCR (pip install merpcr) and ensure it's in "
                    "your PATH."
                )

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
        if as_json:
            emit(
                json.dumps(
                    {
                        "status": "ok",
                        "output_files": {
                            fmt: str(path) for fmt, path in output_paths.items()
                        },
                    }
                )
            )
        else:
            emit("Alignment completed successfully.")
            for format_name, output_path in output_paths.items():
                emit(f"  {format_name}: {output_path}")

        return EXIT_OK

    except PrePrimerError as e:
        if as_json:
            emit(json.dumps({"status": "error", "message": e.get_user_message()}))
        else:
            report_error(e)
        return EXIT_USER_ERROR
    except Exception as e:
        if as_json:
            emit(json.dumps({"status": "error", "message": str(e)}))
        else:
            report_error(e)
        logger.debug("Full traceback:", exc_info=True)
        return EXIT_USER_ERROR


def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()

    if len(sys.argv) == 1:
        parser.print_help()
        return EXIT_OK

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
        report_error(e)
        return EXIT_USER_ERROR

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
        return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
