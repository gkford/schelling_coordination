#!/usr/bin/env python3
"""
Justification Collector

Runs models on eval items and collects their stated justifications (strategy names,
heuristic names, predicted choices). This data can then be used for adherence analysis
to check whether models actually followed their stated strategies.

Uses 'inspect eval' CLI command to ensure task file and args are preserved for eval-retry.

Results are saved to: results/{model}/{condition}/{dataset}/justification/{variation}.eval

Usage:
    python run_justification_collector.py --model opus_4_5_november_25 --prompt coordination_sita --batch
    python run_justification_collector.py --model deepseek_v3_1_august_25 --prompt coordination_sita
    python run_justification_collector.py --model deepseek_v3_1_august_25 --prompt control_sita --test-run
    python run_justification_collector.py --model deepseek_v3_1_august_25 --prompt coordination_sita --variation heuristic
"""

import sys
import json
import argparse
import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))

from eval_configs import EVAL_CONFIGS


def run_adherence_test(
    model_name: str,
    prompt_template: str,
    dataset_file: str = "../data/salient_vs_alphabetical_elo.json",
    item_ids: list[int] = None,
    max_connections: int = 10,
    variation_name: str = "strategy",
    batch: bool = False,
):
    """
    Run adherence test using 'inspect eval' CLI command.

    This ensures task file and args are preserved for eval-retry.

    Args:
        model_name: Model identifier (e.g., "deepseek_v3_1_august_25")
        prompt_template: Prompt template name (e.g., "control_sita", "coordination_sita")
        dataset_file: Path to dataset file
        item_ids: List of item IDs to test (None = all)
        max_connections: Max concurrent connections (ignored when batch=True)
        variation_name: Name of the variation (e.g., "strategy", "heuristic")
        batch: Enable batch processing (50% cost reduction for supported providers)
    """
    print(f"\n{'='*80}")
    print(f"Justification Collector - {variation_name.title()}")
    print(f"{'='*80}")
    print(f"Model: {model_name}")
    print(f"Prompt: {prompt_template}")
    print(f"Variation: {variation_name}")
    print(f"Item IDs: {item_ids if item_ids else 'all'}")
    print(f"Dataset: {dataset_file}")
    if batch:
        print(f"Batch mode: ENABLED (50% cost reduction)")
    print(f"{'='*80}\n")

    # Get model config
    if model_name not in EVAL_CONFIGS:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(EVAL_CONFIGS.keys())}")

    model_config = EVAL_CONFIGS[model_name]

    # Get prompt modifiers
    prompt_modifiers = model_config.get('prompt_modifiers', None)

    # Build task arguments
    task_args = [
        "-T", f"pairs_file={dataset_file}",
        "-T", f"prompt_template={prompt_template}",
        "-T", f"variation_name={variation_name}",
    ]

    # Add item_ids if specified
    if item_ids:
        item_ids_json = json.dumps(item_ids)
        task_args.extend(["-T", f"item_ids={item_ids_json}"])

    # Add prompt_modifiers if present
    if prompt_modifiers:
        prompt_modifiers_json = json.dumps(prompt_modifiers)
        task_args.extend(["-T", f"prompt_modifiers={prompt_modifiers_json}"])

    # Extract dataset name from file path
    dataset_name = Path(dataset_file).stem  # e.g., "salient_vs_alphabetical_elo"

    # Set up log directory structure: results/{model_name}/{prompt_template}/{dataset_name}/justification/
    results_base = Path(__file__).parent.parent / "results"  # Go up to project root /results
    log_dir = results_base / model_name / prompt_template / dataset_name / "justification"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Build command
    cmd = [
        "uv", "run", "inspect", "eval",
        "strategy_investigation/strategy_extraction_task.py@strategy_extraction",
        *task_args,
        "--model", model_config['model'],
        "--log-dir", str(log_dir),
    ]

    # Add temperature settings if not default/unsupported
    temperature = model_config.get('temperature')
    top_p = model_config.get('top_p')
    max_tokens = model_config.get('max_tokens')

    if temperature not in [None, "default", "unsupported"]:
        cmd.extend(["--temperature", str(temperature)])
    if top_p not in [None, "default", "unsupported"]:
        cmd.extend(["--top-p", str(top_p)])
    if max_tokens not in [None, "default", "unsupported"]:
        cmd.extend(["--max-tokens", str(max_tokens)])

    # Add batch flag or max connections (mutually exclusive)
    if batch:
        cmd.append("--batch")
    elif max_connections:
        cmd.extend(["--max-connections", str(max_connections)])

    # Handle model-specific config
    model_specific_config_name = model_config.get('model_specific_config')
    if model_specific_config_name:
        from model_specific_configs import get_model_specific_config
        specific_config = get_model_specific_config(model_specific_config_name)
        eval_kwargs = specific_config.get('eval_kwargs', {})

        # Model args (provider settings)
        if 'model_args' in eval_kwargs:
            for key, value in eval_kwargs['model_args'].items():
                cmd.extend(["-M", f"{key}={value}"])

    # Print command
    print("Executing command:")
    print(" ".join(cmd))
    print(f"\nLogs will be saved to: {log_dir}/\n")

    # Run command
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"\n{'='*80}")
        print(f"EVALUATION COMPLETE")
        print(f"{'='*80}")
        print(f"\nLogs saved to: {log_dir}/")
        print("\nTo retry failed samples, use:")
        print(f"  inspect eval-retry {log_dir}/<eval-file>.eval")
        return result
    except subprocess.CalledProcessError as e:
        print(f"\n{'='*80}")
        print(f"EVALUATION FAILED")
        print(f"{'='*80}")
        print(f"Exit code: {e.returncode}")
        print(f"\nTo retry failed samples, use:")
        print(f"  inspect eval-retry {log_dir}/<eval-file>.eval")
        return None


def main():
    parser = argparse.ArgumentParser(description="Collect model justifications (strategy/heuristic names and predictions)")
    parser.add_argument(
        "--model",
        required=True,
        help="Model name (e.g., deepseek_v3_1_august_25)"
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Prompt template (e.g., 'control_sita', 'coordination_sita')"
    )
    parser.add_argument(
        "--item-ids",
        help="Comma-separated list of item IDs (e.g., '0,1,2,3')"
    )
    parser.add_argument(
        "--test-run",
        action="store_true",
        help="Run test with first 10 items"
    )
    parser.add_argument(
        "--dataset",
        default="../data/salient_vs_alphabetical_elo.json",
        help="Path to dataset file (relative to script location)"
    )
    parser.add_argument(
        "--max-connections",
        type=int,
        default=10,
        help="Max concurrent connections"
    )
    parser.add_argument(
        "--variation",
        default="strategy",
        help="Variation name (e.g., 'strategy', 'heuristic')"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Enable batch processing (50%% cost reduction, async processing)"
    )

    args = parser.parse_args()

    # Parse item IDs
    item_ids = None
    if args.test_run:
        item_ids = list(range(10))  # First 10 items
    elif args.item_ids:
        item_ids = [int(x.strip()) for x in args.item_ids.split(",")]

    # Run test
    run_adherence_test(
        model_name=args.model,
        prompt_template=args.prompt,
        dataset_file=args.dataset,
        item_ids=item_ids,
        max_connections=args.max_connections,
        variation_name=args.variation,
        batch=args.batch,
    )


if __name__ == "__main__":
    main()
