#!/usr/bin/env python3
"""
Advanced mutation testing script for preprimer.

This script provides comprehensive mutation testing with detailed reporting,
selective targeting, and quality metrics calculation.
"""

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class MutationTestRunner:
    """Advanced mutation testing runner with comprehensive reporting."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.mutmut_cache = project_root / ".mutmut-cache"
        self.results_dir = project_root / "mutation_results"
        self.results_dir.mkdir(exist_ok=True)

    def run_baseline_tests(self) -> bool:
        """Run baseline tests to ensure they pass before mutation testing."""
        print("Running baseline tests...")

        cmd = ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
        result = subprocess.run(
            cmd, cwd=self.project_root, capture_output=True, text=True
        )

        if result.returncode == 0:
            print("✓ Baseline tests passed")
            return True
        else:
            print("✗ Baseline tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False

    def run_mutation_testing(
        self,
        target_modules: Optional[List[str]] = None,
        max_mutations: Optional[int] = None,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """
        Run mutation testing with specified parameters.

        Args:
            target_modules: Specific modules to target for mutation
            max_mutations: Maximum number of mutations to test
            timeout: Timeout for each test run in seconds

        Returns:
            Dictionary containing mutation testing results
        """
        print("Starting mutation testing...")

        # Build mutmut command
        cmd = ["mutmut", "run"]

        if target_modules:
            for module in target_modules:
                cmd.extend(["--paths-to-mutate", module])
        else:
            cmd.extend(["--paths-to-mutate", "preprimer/"])

        # Exclude test files and other non-core files
        exclude_patterns = [
            "tests/",
            "*test*.py",
            "*__init__.py",
            "examples/",
            "docs/",
            "setup.py",
        ]

        for pattern in exclude_patterns:
            cmd.extend(["--exclude", pattern])

        # Set timeout
        cmd.extend(["--timeout", str(timeout)])

        # Use cache for faster re-runs
        cmd.append("--use-cache")

        # Show progress
        cmd.append("--show-times")

        if max_mutations:
            cmd.extend(["--max-mutations", str(max_mutations)])

        print(f"Running command: {' '.join(cmd)}")

        start_time = time.time()
        result = subprocess.run(
            cmd, cwd=self.project_root, capture_output=True, text=True
        )
        end_time = time.time()

        # Parse results
        return self._parse_mutation_results(result, end_time - start_time)

    def _parse_mutation_results(
        self, result: subprocess.CompletedProcess, duration: float
    ) -> Dict[str, Any]:
        """Parse mutation testing results from mutmut output."""
        results = {
            "duration": duration,
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "total_mutations": 0,
            "killed_mutations": 0,
            "survived_mutations": 0,
            "skipped_mutations": 0,
            "timeout_mutations": 0,
            "error_mutations": 0,
            "mutation_score": 0.0,
            "surviving_mutants": [],
        }

        # Parse stdout for mutation statistics
        output = result.stdout + result.stderr

        # Extract total mutations
        total_match = re.search(r"(\d+) mutations", output)
        if total_match:
            results["total_mutations"] = int(total_match.group(1))

        # Extract killed mutations
        killed_match = re.search(r"(\d+) killed", output)
        if killed_match:
            results["killed_mutations"] = int(killed_match.group(1))

        # Extract survived mutations
        survived_match = re.search(r"(\d+) survived", output)
        if survived_match:
            results["survived_mutations"] = int(survived_match.group(1))

        # Extract skipped mutations
        skipped_match = re.search(r"(\d+) skipped", output)
        if skipped_match:
            results["skipped_mutations"] = int(skipped_match.group(1))

        # Calculate mutation score
        if results["total_mutations"] > 0:
            effective_total = results["total_mutations"] - results["skipped_mutations"]
            if effective_total > 0:
                results["mutation_score"] = (
                    results["killed_mutations"] / effective_total
                ) * 100

        return results

    def get_surviving_mutants(self) -> List[Dict[str, Any]]:
        """Get detailed information about surviving mutants."""
        cmd = ["mutmut", "results"]
        result = subprocess.run(
            cmd, cwd=self.project_root, capture_output=True, text=True
        )

        surviving_mutants = []
        if result.returncode == 0:
            # Parse mutmut results output
            lines = result.stdout.split("\n")
            for line in lines:
                if "survived" in line.lower():
                    # Extract mutant information
                    mutant_info = self._parse_mutant_line(line)
                    if mutant_info:
                        surviving_mutants.append(mutant_info)

        return surviving_mutants

    def _parse_mutant_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single mutant result line."""
        # This would need to be adapted based on actual mutmut output format
        # For now, return basic parsing
        parts = line.strip().split()
        if len(parts) >= 3:
            return {
                "id": parts[0] if parts[0].isdigit() else None,
                "status": "survived" if "survived" in line.lower() else "unknown",
                "location": line,
            }
        return None

    def generate_detailed_report(self, results: Dict[str, Any]) -> str:
        """Generate a detailed mutation testing report."""
        surviving_mutants = self.get_surviving_mutants()
        results["surviving_mutants"] = surviving_mutants

        report = f"""
Mutation Testing Report
=======================

Test Execution Summary:
- Duration: {results['duration']:.2f} seconds
- Return Code: {results['return_code']}

Mutation Statistics:
- Total Mutations: {results['total_mutations']}
- Killed Mutations: {results['killed_mutations']}
- Survived Mutations: {results['survived_mutations']}
- Skipped Mutations: {results['skipped_mutations']}
- Timeout Mutations: {results['timeout_mutations']}
- Error Mutations: {results['error_mutations']}

Quality Metrics:
- Mutation Score: {results['mutation_score']:.2f}%
- Test Effectiveness: {'High' if results['mutation_score'] >= 80 else 'Medium' if results['mutation_score'] >= 60 else 'Low'}

Surviving Mutants ({len(surviving_mutants)}):
"""

        for i, mutant in enumerate(surviving_mutants[:10]):  # Show first 10
            report += f"\n{i+1}. {mutant.get('location', 'Unknown location')}"

        if len(surviving_mutants) > 10:
            report += f"\n... and {len(surviving_mutants) - 10} more"

        report += f"""

Recommendations:
"""

        if results["mutation_score"] < 60:
            report += "- CRITICAL: Mutation score is below 60%. Consider adding more comprehensive tests.\n"
        elif results["mutation_score"] < 80:
            report += "- WARNING: Mutation score is below 80%. Consider improving test coverage.\n"
        else:
            report += (
                "- GOOD: Mutation score is above 80%. Test suite appears robust.\n"
            )

        if results["survived_mutations"] > 0:
            report += f"- Investigate {results['survived_mutations']} surviving mutants to improve test coverage.\n"

        if results["timeout_mutations"] > 0:
            report += f"- {results['timeout_mutations']} mutations timed out. Consider optimizing test performance.\n"

        return report

    def save_results(self, results: Dict[str, Any], report: str) -> None:
        """Save mutation testing results and report."""
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        # Save JSON results
        json_file = self.results_dir / f"mutation_results_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(results, f, indent=2, default=str)

        # Save text report
        report_file = self.results_dir / f"mutation_report_{timestamp}.txt"
        with open(report_file, "w") as f:
            f.write(report)

        # Save latest results (for CI/CD)
        latest_json = self.results_dir / "latest_results.json"
        with open(latest_json, "w") as f:
            json.dump(results, f, indent=2, default=str)

        latest_report = self.results_dir / "latest_report.txt"
        with open(latest_report, "w") as f:
            f.write(report)

        print(f"Results saved to: {json_file}")
        print(f"Report saved to: {report_file}")

    def run_targeted_mutation_testing(self, target_files: List[str]) -> Dict[str, Any]:
        """Run mutation testing on specific files."""
        print(f"Running targeted mutation testing on: {', '.join(target_files)}")

        all_results = {}

        for target_file in target_files:
            print(f"\nTesting mutations in: {target_file}")

            # Run mutation testing for this specific file
            cmd = [
                "mutmut",
                "run",
                "--paths-to-mutate",
                target_file,
                "--use-cache",
                "--show-times",
            ]

            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )
            file_results = self._parse_mutation_results(result, 0)

            all_results[target_file] = file_results

            print(f"  Mutations: {file_results['total_mutations']}")
            print(f"  Killed: {file_results['killed_mutations']}")
            print(f"  Survived: {file_results['survived_mutations']}")
            print(f"  Score: {file_results['mutation_score']:.1f}%")

        return all_results

    def analyze_test_quality(self) -> Dict[str, Any]:
        """Analyze overall test quality based on mutation testing results."""
        latest_results_file = self.results_dir / "latest_results.json"

        if not latest_results_file.exists():
            print("No mutation testing results found. Run mutation tests first.")
            return {}

        with open(latest_results_file, "r") as f:
            results = json.load(f)

        analysis = {
            "overall_quality": "Unknown",
            "mutation_score": results.get("mutation_score", 0),
            "test_effectiveness": "Unknown",
            "recommendations": [],
        }

        score = results.get("mutation_score", 0)

        if score >= 90:
            analysis["overall_quality"] = "Excellent"
            analysis["test_effectiveness"] = "Very High"
        elif score >= 80:
            analysis["overall_quality"] = "Good"
            analysis["test_effectiveness"] = "High"
        elif score >= 70:
            analysis["overall_quality"] = "Fair"
            analysis["test_effectiveness"] = "Medium"
        elif score >= 60:
            analysis["overall_quality"] = "Poor"
            analysis["test_effectiveness"] = "Low"
        else:
            analysis["overall_quality"] = "Very Poor"
            analysis["test_effectiveness"] = "Very Low"

        # Generate recommendations
        if score < 70:
            analysis["recommendations"].append("Add more edge case tests")
            analysis["recommendations"].append("Increase assertion coverage")
            analysis["recommendations"].append("Test error conditions more thoroughly")

        if results.get("survived_mutations", 0) > 5:
            analysis["recommendations"].append("Investigate surviving mutants")

        if results.get("timeout_mutations", 0) > 0:
            analysis["recommendations"].append("Optimize test performance")

        return analysis


def main():
    """Main entry point for mutation testing script."""
    parser = argparse.ArgumentParser(description="Run mutation testing for preprimer")

    parser.add_argument(
        "--baseline", action="store_true", help="Run baseline tests only"
    )

    parser.add_argument(
        "--target-modules",
        nargs="+",
        help="Specific modules to target for mutation testing",
    )

    parser.add_argument(
        "--target-files",
        nargs="+",
        help="Specific files to target for mutation testing",
    )

    parser.add_argument(
        "--max-mutations", type=int, help="Maximum number of mutations to test"
    )

    parser.add_argument(
        "--timeout", type=int, default=300, help="Timeout for each test run in seconds"
    )

    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze test quality from previous results",
    )

    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Generate report from existing results without running new tests",
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    runner = MutationTestRunner(project_root)

    if args.analyze:
        analysis = runner.analyze_test_quality()
        print(json.dumps(analysis, indent=2))
        return 0

    if args.report_only:
        latest_results_file = runner.results_dir / "latest_results.json"
        if latest_results_file.exists():
            with open(latest_results_file, "r") as f:
                results = json.load(f)
            report = runner.generate_detailed_report(results)
            print(report)
        else:
            print("No previous results found.")
        return 0

    if args.baseline:
        if not runner.run_baseline_tests():
            return 1
        return 0

    # Run baseline tests first
    if not runner.run_baseline_tests():
        print("Baseline tests failed. Fix tests before running mutation testing.")
        return 1

    # Run mutation testing
    if args.target_files:
        results = runner.run_targeted_mutation_testing(args.target_files)
        print("\nTargeted Mutation Testing Results:")
        for file_path, file_results in results.items():
            print(f"\n{file_path}:")
            print(f"  Mutation Score: {file_results['mutation_score']:.1f}%")
    else:
        results = runner.run_mutation_testing(
            target_modules=args.target_modules,
            max_mutations=args.max_mutations,
            timeout=args.timeout,
        )

        # Generate and display report
        report = runner.generate_detailed_report(results)
        print("\n" + report)

        # Save results
        runner.save_results(results, report)

        # Return appropriate exit code
        if results["mutation_score"] < 60:
            print("\nWARNING: Low mutation score indicates poor test quality.")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
