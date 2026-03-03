#!/usr/bin/env python3
"""
Data Export CLI

Run all or specific analyses to generate JSON export files.

Usage:
    # Run all analyses
    uv run python data_export/run_export.py

    # Run a specific analysis
    uv run python data_export/run_export.py --analysis bias_controlled
    uv run python data_export/run_export.py -a alphabetisation_all_converged

    # List available analyses
    uv run python data_export/run_export.py --list
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir.parent))

from data_export.analyses import ANALYSES, list_analyses, run_analysis


def main():
    parser = argparse.ArgumentParser(
        description="Generate data export JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run all analyses
    uv run python data_export/run_export.py

    # Run a specific analysis
    uv run python data_export/run_export.py --analysis bias_controlled

    # List available analyses
    uv run python data_export/run_export.py --list
        """
    )
    parser.add_argument(
        "-a", "--analysis",
        type=str,
        help="Name of specific analysis to run (e.g., 'bias_controlled', 'full_results')"
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="List all available analyses"
    )

    args = parser.parse_args()

    # List analyses
    if args.list:
        print("\nAvailable analyses:")
        print("-" * 70)
        for analysis in list_analyses():
            print(f"  {analysis['name']:<35} -> {analysis['output_file']}")
            print(f"    {analysis['description']}")
            print()
        return

    # Run specific analysis
    if args.analysis:
        if args.analysis not in ANALYSES:
            print(f"Error: Unknown analysis '{args.analysis}'")
            print(f"Available analyses: {', '.join(ANALYSES.keys())}")
            sys.exit(1)

        print("=" * 70)
        print(f"Running analysis: {args.analysis}")
        print("=" * 70)
        run_analysis(args.analysis)
        print("\nDone!")
        return

    # Run all analyses
    print("=" * 70)
    print("Running ALL analyses")
    print("=" * 70)

    for name in ANALYSES.keys():
        print()
        run_analysis(name)

    print()
    print("=" * 70)
    print("All analyses complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
