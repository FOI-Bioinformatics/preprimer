"""
Report generator for PrePrimer validation results.

Generates HTML and Markdown reports from validation results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from .validator import ValidationResult


class ReportGenerator:
    """Generate validation reports in multiple formats."""

    @staticmethod
    def generate_markdown_report(
        results: Dict[str, ValidationResult],
        output_file: Path,
        title: str = "PrePrimer Validation Report",
    ):
        """
        Generate Markdown validation report.

        Args:
            results: Dictionary mapping test name to ValidationResult
            output_file: Output file path for report
            title: Report title
        """
        lines = []

        # Header
        lines.append(f"# {title}")
        lines.append("")
        lines.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # Summary statistics
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.valid)
        failed_tests = total_tests - passed_tests

        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total Tests**: {total_tests}")
        lines.append(f"- **Passed**: {passed_tests} ✅")
        lines.append(f"- **Failed**: {failed_tests} {'✅' if failed_tests == 0 else '❌'}")
        lines.append(f"- **Pass Rate**: {(passed_tests/total_tests*100):.1f}%")
        lines.append("")

        # Detailed results
        lines.append("## Test Results")
        lines.append("")

        for test_name, result in sorted(results.items()):
            status = "✅ PASS" if result.valid else "❌ FAIL"
            lines.append(f"### {test_name} - {status}")
            lines.append("")

            # Errors
            if result.errors:
                lines.append("**Errors:**")
                for error in result.errors:
                    lines.append(f"- ❌ {error}")
                lines.append("")

            # Warnings
            if result.warnings:
                lines.append("**Warnings:**")
                for warning in result.warnings:
                    lines.append(f"- ⚠️  {warning}")
                lines.append("")

            # Statistics
            if result.stats:
                lines.append("**Statistics:**")
                for key, value in sorted(result.stats.items()):
                    if isinstance(value, (list, dict)):
                        lines.append(f"- **{key}**: `{json.dumps(value, indent=2)}`")
                    else:
                        lines.append(f"- **{key}**: `{value}`")
                lines.append("")

        # Write report
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write("\n".join(lines))

    @staticmethod
    def generate_summary_json(
        results: Dict[str, ValidationResult],
        output_file: Path,
    ):
        """
        Generate JSON summary of validation results.

        Args:
            results: Dictionary mapping test name to ValidationResult
            output_file: Output file path for JSON
        """
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_tests": len(results),
            "passed_tests": sum(1 for r in results.values() if r.valid),
            "failed_tests": sum(1 for r in results.values() if not r.valid),
            "tests": {},
        }

        for test_name, result in results.items():
            summary["tests"][test_name] = {
                "valid": result.valid,
                "errors": result.errors,
                "warnings": result.warnings,
                "stats": result.stats,
            }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            json.dump(summary, f, indent=2)

    @staticmethod
    def print_summary(results: Dict[str, ValidationResult]):
        """Print a quick summary to console."""
        total = len(results)
        passed = sum(1 for r in results.values() if r.valid)

        print(f"\n{'='*60}")
        print(f"Validation Summary: {passed}/{total} tests passed")
        print(f"{'='*60}\n")

        for name, result in sorted(results.items()):
            status = "✅" if result.valid else "❌"
            print(f"{status} {name}")
            if result.errors:
                for error in result.errors[:2]:  # Show first 2 errors
                    print(f"   ERROR: {error}")

        print(f"\n{'='*60}\n")
