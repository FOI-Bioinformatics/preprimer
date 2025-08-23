"""
Legacy main entry point for preprimer.
Redirects to the new CLI interface.
"""

import sys
import warnings
from .cli import main as cli_main

def main():
    """Legacy main function - redirects to new CLI."""
    warnings.warn(
        "Using legacy main() function. Please use the new CLI interface.",
        DeprecationWarning,
        stacklevel=2
    )
    return cli_main()

if __name__ == "__main__":
    sys.exit(main())