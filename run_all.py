#!/usr/bin/env python3
"""
Run all 4 datasets × 2 conditions for a given model config.

Shows estimated token usage and cost, then prompts before proceeding.

Usage:
    uv run python run_all.py --config haiku_4_5_october_25
    uv run python run_all.py --config haiku_4_5_october_25 --batch
    uv run python run_all.py --config haiku_4_5_october_25 --skip-existing
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from eval_configs import get_eval_config

PROJECT_ROOT = Path(__file__).parent

DATASETS = [
    "salient_vs_alphabetical_elo",
    "mundane_vs_dangerous_elo",
    "random_emoji",
    "random_mixed_types",
]

PROMPTS = ["control_sita", "coordination_sita"]

# Pair counts per dataset
DATASET_PAIRS = {
    "salient_vs_alphabetical_elo": 400,
    "mundane_vs_dangerous_elo": 400,
    "random_emoji": 406,
    "random_mixed_types": 406,
}

# Token estimates per sample (conservative)
INPUT_TOKENS_PER_SAMPLE = 100
OUTPUT_TOKENS_PER_SAMPLE = 5


def has_results(config: str, prompt: str, dataset: str) -> bool:
    results_dir = PROJECT_ROOT / "results" / config / prompt / dataset
    if not results_dir.exists():
        return False
    return any(results_dir.glob("*.eval"))


def estimate_tokens(evals_to_run: list[tuple[str, str]]) -> tuple[int, int]:
    """Return (total_input_tokens, total_output_tokens) for the evals to run."""
    total_samples = 0
    for prompt, dataset in evals_to_run:
        pairs = DATASET_PAIRS[dataset]
        total_samples += pairs * 2  # AB + BA order
    return (
        total_samples * INPUT_TOKENS_PER_SAMPLE,
        total_samples * OUTPUT_TOKENS_PER_SAMPLE,
    )


def estimate_cost(input_tokens: int, output_tokens: int, input_price: float, output_price: float) -> float:
    """Cost in dollars given prices per million tokens."""
    return (input_tokens * input_price + output_tokens * output_price) / 1_000_000


def main():
    parser = argparse.ArgumentParser(
        description="Run all 4 datasets × 2 conditions for a model config",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--config", required=True, help="Model config name from eval_configs.py")
    parser.add_argument("--batch", action="store_true", help="Enable batch mode (50%% cost reduction)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip evals that already have results")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--max-connections", type=int, default=None, help="Max concurrent API connections")
    args = parser.parse_args()

    # Validate config exists
    try:
        config = get_eval_config(args.config)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Build list of evals to run
    evals_to_run = []
    evals_skipped = []
    for prompt in PROMPTS:
        for dataset in DATASETS:
            if args.skip_existing and has_results(args.config, prompt, dataset):
                evals_skipped.append((prompt, dataset))
            else:
                evals_to_run.append((prompt, dataset))

    if not evals_to_run:
        print(f"\nAll evals already have results for {args.config}. Nothing to do.")
        sys.exit(0)

    # Estimate tokens
    input_tokens, output_tokens = estimate_tokens(evals_to_run)

    # Print summary
    print(f"\n{'═' * 60}")
    print(f"Run All Evals: {args.config}")
    print(f"{'═' * 60}")
    print(f"  Model:       {config['model']}")
    print(f"  Evals:       {len(evals_to_run)} ({len(PROMPTS)} prompts × {len(DATASETS)} datasets)")
    if evals_skipped:
        print(f"  Skipped:     {len(evals_skipped)} (already have results)")
    if args.batch:
        print(f"  Batch mode:  ON (50% cost reduction)")
    print()

    print("── Token Estimates ─────────────────────────────────")
    print(f"  Input tokens:   ~{input_tokens:>10,}")
    print(f"  Output tokens:  ~{output_tokens:>10,}")
    print()

    print("── Cost Estimates (by provider pricing) ────────────")
    # Show a few representative price points
    price_examples = [
        ("Haiku 4.5",      0.80,  4.00),
        ("GPT-4.1 Mini",   0.40,  1.60),
        ("GPT-4.1 Nano",   0.10,  0.40),
        ("Sonnet 4.5",     3.00, 15.00),
        ("GPT-4.1",        2.00,  8.00),
        ("Opus 4.5",      15.00, 75.00),
    ]
    batch_mult = 0.5 if args.batch else 1.0
    for name, inp_price, out_price in price_examples:
        cost = estimate_cost(input_tokens, output_tokens, inp_price, out_price) * batch_mult
        print(f"  {name:20s}  ${cost:>6.2f}")
    print()

    print("── Evals to Run ────────────────────────────────────")
    for prompt, dataset in evals_to_run:
        pairs = DATASET_PAIRS[dataset]
        print(f"  {prompt:25s}  {dataset:35s}  ({pairs} pairs)")
    print()

    # Confirm
    if not args.yes:
        response = input("Proceed? [y/N] ")
        if response.lower() not in ("y", "yes"):
            print("Aborted.")
            sys.exit(0)

    # Run evals
    print(f"\n{'═' * 60}")
    failures = []
    for i, (prompt, dataset) in enumerate(evals_to_run, 1):
        pairs_file = f"data/{dataset}.json"
        print(f"\n[{i}/{len(evals_to_run)}] {args.config}: {prompt} / {dataset}")

        cmd = [
            "uv", "run", "python", "run_eval.py",
            "--config", args.config,
            "--prompt", prompt,
            "--pairs", pairs_file,
        ]
        if args.batch:
            cmd.append("--batch")
        if args.max_connections:
            cmd.extend(["--max-connections", str(args.max_connections)])

        result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        if result.returncode != 0:
            failures.append((prompt, dataset))
            print(f"  FAILED (exit code {result.returncode})")

    # Summary
    print(f"\n{'═' * 60}")
    succeeded = len(evals_to_run) - len(failures)
    print(f"Done: {succeeded}/{len(evals_to_run)} evals succeeded")
    if failures:
        print("\nFailed evals:")
        for prompt, dataset in failures:
            print(f"  {prompt} / {dataset}")
    print()


if __name__ == "__main__":
    main()
