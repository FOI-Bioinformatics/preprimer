#!/usr/bin/env python3
"""
Error Handling Example

Demonstrates comprehensive error handling for robust primer scheme processing,
including graceful degradation, detailed error reporting, and recovery strategies.
"""

from pathlib import Path
from typing import Optional, Tuple

from preprimer.core.converter import Converter
from preprimer.core.exceptions import (
    CorruptedDataError,
    InsufficientDataError,
    InvalidFormatError,
    ParserError,
    PrePrimerError,
    SecurityError,
)


def convert_with_detailed_error_handling(
    input_file: str, output_dir: str, output_formats: list
) -> Tuple[Optional[list], Optional[dict]]:
    """
    Convert primer scheme with comprehensive error handling.

    Args:
        input_file: Path to input file
        output_dir: Output directory
        output_formats: List of output formats

    Returns:
        Tuple of (amplicons, error_info)
          - amplicons: List of amplicons if successful, None if failed
          - error_info: Dictionary with error details if failed, None if successful
    """
    try:
        converter = Converter()
        amplicons = converter.convert(
            input_file=input_file,
            output_dir=output_dir,
            output_formats=output_formats,
            prefix="scheme",
        )
        return amplicons, None

    except SecurityError as e:
        # Security violations (path traversal, file size limits, etc.)
        return None, {
            "category": "Security",
            "type": "SecurityError",
            "message": str(e),
            "user_message": getattr(e, "user_message", None),
            "suggestions": getattr(e, "suggestions", []),
            "severity": "HIGH",
            "recoverable": False,
        }

    except InvalidFormatError as e:
        # File format validation errors
        return None, {
            "category": "Format",
            "type": "InvalidFormatError",
            "message": str(e),
            "user_message": getattr(e, "user_message", None),
            "expected_format": getattr(e, "expected_format", None),
            "file_path": getattr(e, "file_path", None),
            "suggestions": getattr(e, "suggestions", []),
            "severity": "MEDIUM",
            "recoverable": True,
        }

    except CorruptedDataError as e:
        # Data integrity issues
        return None, {
            "category": "Data",
            "type": "CorruptedDataError",
            "message": str(e),
            "user_message": getattr(e, "user_message", None),
            "file_path": getattr(e, "file_path", None),
            "details": getattr(e, "details", None),
            "suggestions": getattr(e, "suggestions", []),
            "severity": "HIGH",
            "recoverable": False,
        }

    except InsufficientDataError as e:
        # Not enough valid data
        return None, {
            "category": "Data",
            "type": "InsufficientDataError",
            "message": str(e),
            "user_message": getattr(e, "user_message", None),
            "suggestions": getattr(e, "suggestions", []),
            "severity": "MEDIUM",
            "recoverable": True,
        }

    except ParserError as e:
        # General parsing errors
        return None, {
            "category": "Parsing",
            "type": "ParserError",
            "message": str(e),
            "user_message": getattr(e, "user_message", None),
            "file_path": getattr(e, "file_path", None),
            "suggestions": getattr(e, "suggestions", []),
            "severity": "MEDIUM",
            "recoverable": True,
        }

    except PrePrimerError as e:
        # Other PrePrimer-specific errors
        return None, {
            "category": "PrePrimer",
            "type": type(e).__name__,
            "message": str(e),
            "user_message": getattr(e, "user_message", None),
            "suggestions": getattr(e, "suggestions", []),
            "severity": "MEDIUM",
            "recoverable": True,
        }

    except FileNotFoundError as e:
        # File not found
        return None, {
            "category": "System",
            "type": "FileNotFoundError",
            "message": str(e),
            "suggestions": [
                "Check the file path is correct",
                "Verify the file exists",
                "Check file permissions",
            ],
            "severity": "MEDIUM",
            "recoverable": True,
        }

    except PermissionError as e:
        # Permission denied
        return None, {
            "category": "System",
            "type": "PermissionError",
            "message": str(e),
            "suggestions": [
                "Check file permissions",
                "Run with appropriate privileges",
                "Verify directory access rights",
            ],
            "severity": "MEDIUM",
            "recoverable": True,
        }

    except Exception as e:
        # Unexpected errors
        return None, {
            "category": "Unexpected",
            "type": type(e).__name__,
            "message": str(e),
            "suggestions": [
                "Check input file format",
                "Verify system requirements",
                "Report as bug if issue persists",
            ],
            "severity": "HIGH",
            "recoverable": False,
        }


def print_error_report(error_info: dict):
    """
    Print detailed error report.

    Args:
        error_info: Error information dictionary
    """
    print()
    print("=" * 70)
    print("ERROR REPORT")
    print("=" * 70)
    print()

    # Severity indicator
    severity_symbols = {"LOW": "ℹ", "MEDIUM": "⚠", "HIGH": "✗"}
    symbol = severity_symbols.get(error_info.get("severity", "MEDIUM"), "⚠")

    print(f"{symbol} Severity: {error_info.get('severity', 'UNKNOWN')}")
    print(f"  Category: {error_info.get('category', 'Unknown')}")
    print(f"  Type: {error_info.get('type', 'Unknown')}")
    print()

    # Main error message
    print("Error Message:")
    print(f"  {error_info.get('message', 'No message available')}")
    print()

    # User-friendly message
    if error_info.get("user_message"):
        print("Details:")
        print(f"  {error_info['user_message']}")
        print()

    # Additional context
    if error_info.get("expected_format"):
        print(f"Expected format: {error_info['expected_format']}")

    if error_info.get("file_path"):
        print(f"File: {error_info['file_path']}")

    if error_info.get("details"):
        print(f"Details: {error_info['details']}")

    # Suggestions
    if error_info.get("suggestions"):
        print()
        print("Suggested actions:")
        for suggestion in error_info["suggestions"]:
            print(f"  • {suggestion}")

    # Recoverability
    print()
    if error_info.get("recoverable"):
        print("✓ This error may be recoverable by correcting the input.")
    else:
        print("✗ This error requires intervention and cannot be automatically recovered.")

    print()
    print("=" * 70)


def main():
    """Demonstrate error handling with various scenarios."""

    print("=" * 70)
    print("PrePrimer Error Handling Example")
    print("=" * 70)
    print()

    # Test scenarios
    test_scenarios = [
        {
            "name": "Non-existent file",
            "input_file": "nonexistent_file.tsv",
            "output_dir": "output/test1",
            "formats": ["artic"],
        },
        {
            "name": "Invalid format file",
            "input_file": "path/to/invalid_format.txt",
            "output_dir": "output/test2",
            "formats": ["artic"],
        },
        {
            "name": "Valid conversion (will succeed if file exists)",
            "input_file": "tests/test_data/datasets/small/primers.tsv",
            "output_dir": "output/test3",
            "formats": ["artic", "fasta"],
        },
    ]

    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\nScenario {i}: {scenario['name']}")
        print("-" * 70)
        print(f"Input:  {scenario['input_file']}")
        print(f"Output: {scenario['output_dir']}")
        print(f"Formats: {', '.join(scenario['formats'])}")

        # Attempt conversion
        amplicons, error = convert_with_detailed_error_handling(
            input_file=scenario["input_file"],
            output_dir=scenario["output_dir"],
            output_formats=scenario["formats"],
        )

        if amplicons:
            # Success
            print()
            print(f"✓ SUCCESS: Converted {len(amplicons)} amplicons")

            # Show first few amplicons
            for amplicon in amplicons[:3]:
                print(f"  • {amplicon.amplicon_id}: {amplicon.length} bp")

            if len(amplicons) > 3:
                print(f"  ... and {len(amplicons) - 3} more")

        else:
            # Error
            print_error_report(error)

    # Summary
    print()
    print("=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("This example demonstrates:")
    print("  • Comprehensive error handling for all error types")
    print("  • Detailed error reporting with actionable suggestions")
    print("  • Graceful degradation and recovery strategies")
    print("  • User-friendly error messages")
    print()
    print("Best practices:")
    print("  • Always catch specific exceptions before generic ones")
    print("  • Provide actionable error messages and suggestions")
    print("  • Log errors for debugging and monitoring")
    print("  • Implement retry logic for recoverable errors")
    print("  • Validate inputs before processing")


if __name__ == "__main__":
    main()
