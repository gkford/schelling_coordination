#!/usr/bin/env python3
"""
Run Post-Hoc Explanation Analysis

Rescores existing post-hoc evaluation logs to categorize the explanations.
Uses inspect eval-retry to add the post_hoc_explanation_scorer to existing logs.
"""

import sys
import subprocess
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from eval_configs import get_eval_config


def find_coordination_eval(config_name: str, dataset_name: str) -> Path | None:
    """
    Find the coordination_sita eval file for a given config and dataset.

    Args:
        config_name: Eval config name (e.g., "kimi_k2_july_25_PH")
        dataset_name: Dataset name (e.g., "salient_vs_alphabetical_elo")

    Returns:
        Path to eval file, or None if not found
    """
    results_dir = Path(__file__).parent.parent / "results"
    eval_dir = results_dir / config_name / "coordination_sita" / dataset_name

    if not eval_dir.exists():
        return None

    # Find most recent .eval file
    eval_files = sorted(eval_dir.glob("*.eval"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not eval_files:
        return None

    return eval_files[0]


def run_post_hoc_analysis(
    config_name: str,
    dataset_name: str,
    output_dir: str = None,
    max_samples: int = None
):
    """
    Run post-hoc explanation analysis by rescoring an existing eval.

    Args:
        config_name: Eval config name
        dataset_name: Dataset name
        output_dir: Optional output directory (defaults to post_hoc_analysis/)
        max_samples: Optional limit on number of samples
    """
    # Validate config exists
    try:
        config = get_eval_config(config_name)
    except ValueError as e:
        print(f"Error: {e}")
        return False

    # Check if this is a post-hoc config
    if not config.get('post_hoc_explanation', False):
        print(f"Error: Config '{config_name}' does not have post_hoc_explanation enabled")
        print("Only post-hoc evaluation configs can be analyzed for explanations")
        return False

    # Find the coordination eval file
    eval_file = find_coordination_eval(config_name, dataset_name)

    if not eval_file:
        print(f"Error: Could not find coordination_sita eval for {config_name} / {dataset_name}")
        print(f"Expected location: results/{config_name}/coordination_sita/{dataset_name}/")
        return False

    print(f"Found eval file: {eval_file}")

    # Determine output directory
    if output_dir is None:
        output_dir = eval_file.parent / "post_hoc_analysis"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output directory: {output_dir}")

    # Build command using inspect score
    output_file = output_dir / f"{eval_file.stem}_post_hoc_analysis.eval"

    cmd = [
        "inspect", "score",
        str(eval_file),
        "--scorer", "strategy_investigation/post_hoc_explanation_scorer.py@post_hoc_explanation_scorer",
        "--output-file", str(output_file),
        "--action", "append"
    ]

    print(f"\nRunning command:")
    print(" ".join(cmd))
    print()

    # Run the command
    try:
        result = subprocess.run(cmd, check=True)
        print(f"\n✅ Post-hoc analysis complete!")
        print(f"Results saved to: {output_dir}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error running analysis: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Run post-hoc explanation analysis")
    parser.add_argument(
        "--config",
        required=True,
        help="Eval config name (e.g., kimi_k2_july_25_PH)"
    )
    parser.add_argument(
        "--dataset",
        default="salient_vs_alphabetical_elo",
        help="Dataset name (default: salient_vs_alphabetical_elo)"
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory (default: results/{config}/coordination_sita/{dataset}/post_hoc_analysis/)"
    )
    args = parser.parse_args()

    success = run_post_hoc_analysis(
        config_name=args.config,
        dataset_name=args.dataset,
        output_dir=args.output_dir,
        max_samples=None
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
