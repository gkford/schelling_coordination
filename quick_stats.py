#!/usr/bin/env python3
"""
Quick Stats — single-model summary from whatever eval data exists.

Usage:
    # Both prompts auto-detected
    uv run python quick_stats.py --config haiku_4_5_october_25 --dataset salient_vs_alphabetical_elo

    # Single prompt condition
    uv run python quick_stats.py --config haiku_4_5_october_25 --dataset salient_vs_alphabetical_elo --prompt control_sita

    # Thinking model (control from non-thinking config)
    uv run python quick_stats.py --config haiku_4_5_thinking_october_25 --dataset salient_vs_alphabetical_elo \\
        --control-config haiku_4_5_october_25
"""

import argparse
import json
import math
import sys
from pathlib import Path

# Add project root for imports
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.eval_results import get_eval_results_by_features
from utils.comparison import categorize_pair_results, generate_comparison_summary


PROMPTS = ["control_sita", "coordination_sita"]


def wilson_ci_half_width(successes: int, n: int) -> float:
    """95% CI half-width using Wilson score interval, as percentage points."""
    if n == 0:
        return 0.0
    z = 1.96
    p = successes / n
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    margin = z * math.sqrt((p * (1 - p) / n + z**2 / (4 * n**2))) / denominator
    return round(margin * 100, 2)


def pct(num, denom):
    """Format a percentage, returning the string and raw value."""
    if denom == 0:
        return "N/A", None
    val = num / denom * 100
    return f"{val:.1f}%", round(val, 1)


def compute_single_condition_stats(results):
    """Compute per-condition stats from eval results dict."""
    pair_results = results["pair_results"]
    sample_stats = results["sample_stats"]

    total_pairs = len(pair_results)
    converged_pairs = sum(1 for p in pair_results.values() if p["converged"])
    invalid_pairs = sum(1 for p in pair_results.values() if p["pattern"] == "invalid")
    valid_pairs = total_pairs - invalid_pairs

    total_samples = sample_stats["total_samples"]
    valid_samples = sample_stats["valid_samples"]
    invalid_samples = sample_stats["invalid_samples"]
    option_a_samples = sample_stats["option_A_samples"]

    # Position bias: count samples that chose the first-presented option
    # In AB order: choosing A = choosing first. In BA order: choosing B = choosing first.
    ab = sample_stats["samples_by_order"]["AB"]
    ba = sample_stats["samples_by_order"]["BA"]
    first_chosen = ab["option_A"] + ba["option_B"]

    ci = wilson_ci_half_width(converged_pairs, valid_pairs)

    return {
        "convergence_rate": round(converged_pairs / valid_pairs * 100, 1) if valid_pairs else None,
        "converged_pairs": converged_pairs,
        "valid_pairs": valid_pairs,
        "total_pairs": total_pairs,
        "convergence_ci": ci,
        "option_a_pct": round(option_a_samples / valid_samples * 100, 1) if valid_samples else None,
        "option_a_samples": option_a_samples,
        "valid_samples": valid_samples,
        "position_first_pct": round(first_chosen / valid_samples * 100, 1) if valid_samples else None,
        "first_chosen": first_chosen,
        "invalid_rate": round(invalid_samples / total_samples * 100, 1) if total_samples else None,
        "invalid_samples": invalid_samples,
        "total_samples": total_samples,
    }


def print_single_condition(prompt, stats):
    """Print formatted stats for one condition."""
    conv_str, _ = pct(stats["converged_pairs"], stats["valid_pairs"])
    print(f"\n── {prompt} {'─' * max(1, 48 - len(prompt) - 4)}")
    print(f"  Convergence:    {conv_str:8s} ({stats['converged_pairs']}/{stats['valid_pairs']} pairs)  95% CI: ±{stats['convergence_ci']}%")

    opt_a_str, _ = pct(stats["option_a_samples"], stats["valid_samples"])
    print(f"  Option A pref:  {opt_a_str:8s} ({stats['option_a_samples']}/{stats['valid_samples']} samples)")

    pos_str, _ = pct(stats["first_chosen"], stats["valid_samples"])
    print(f"  Position bias:  {pos_str:8s} chose first-presented option")

    inv_str, _ = pct(stats["invalid_samples"], stats["total_samples"])
    print(f"  Invalid:        {inv_str:8s} ({stats['invalid_samples']}/{stats['total_samples']} samples)")


def print_comparison(control_results, coord_results, control_stats, coord_stats):
    """Print comparison stats using categorize_pair_results."""
    categorized = categorize_pair_results(control_results, coord_results)
    summary = generate_comparison_summary(categorized)

    ctrl_conv = control_stats["convergence_rate"]
    coord_conv = coord_stats["convergence_rate"]
    lift = coord_conv - ctrl_conv if ctrl_conv is not None and coord_conv is not None else None

    stc = summary["metrics"]["swap_to_converge"]

    print(f"\n── Comparison {'─' * 36}")
    if lift is not None:
        print(f"  Coordination lift:    {lift:+.1f}pp  ({ctrl_conv:.1f}% → {coord_conv:.1f}%)")
    print(f"  Swap to converge:    {stc['percentage']:5.1f}%    ({stc['count']}/{stc['base']} pairs that differed in control)")

    return summary


def build_output_json(config, dataset, condition_data, comparison_summary):
    """Build the JSON output dict."""
    output = {
        "config": config,
        "dataset": dataset,
        "conditions": {},
    }
    for prompt, (results, stats) in condition_data.items():
        output["conditions"][prompt] = {
            "model": results["metadata"]["model"],
            **stats,
        }
    if comparison_summary:
        output["comparison"] = comparison_summary
    return output


def main():
    parser = argparse.ArgumentParser(
        description="Quick stats from a single eval run",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    uv run python quick_stats.py --config haiku_4_5_october_25 --dataset salient_vs_alphabetical_elo
    uv run python quick_stats.py --config haiku_4_5_october_25 --dataset salient_vs_alphabetical_elo --prompt control_sita

    # Thinking model: control from non-thinking config
    uv run python quick_stats.py --config haiku_4_5_thinking_october_25 --dataset salient_vs_alphabetical_elo \\
        --control-config haiku_4_5_october_25
""",
    )
    parser.add_argument("--config", required=True, help="Model config folder name")
    parser.add_argument("--dataset", required=True, help="Dataset name")
    parser.add_argument("--prompt", choices=PROMPTS, default=None,
                        help="Prompt condition (default: auto-detect both)")
    parser.add_argument("--control-config", default=None,
                        help="Separate config for control_sita (for thinking models)")
    args = parser.parse_args()

    control_config = args.control_config or args.config
    prompts_to_check = [args.prompt] if args.prompt else PROMPTS

    # Header
    print(f"\n{'═' * 55}")
    print(f"Quick Stats: {args.config} / {args.dataset}")
    if args.control_config:
        print(f"  (control from: {args.control_config})")
    print(f"{'═' * 55}")

    # Load results for each prompt condition
    condition_data = {}  # prompt -> (results, stats)
    for prompt in prompts_to_check:
        # For control_sita, use control_config; for coordination_sita, use main config
        config_for_prompt = control_config if prompt == "control_sita" else args.config
        results = get_eval_results_by_features(config_for_prompt, prompt, args.dataset)
        if results is None or "error" in results:
            if args.prompt:
                # User explicitly asked for this prompt — report the error
                err = results["error"] if results and "error" in results else "not found"
                print(f"\n  {prompt}: {err}")
            continue
        stats = compute_single_condition_stats(results)
        condition_data[prompt] = (results, stats)

    if not condition_data:
        print("\n  No eval data found.")
        sys.exit(1)

    # Print per-condition stats
    for prompt in PROMPTS:
        if prompt in condition_data:
            _, stats = condition_data[prompt]
            label = prompt
            if prompt == "control_sita" and args.control_config:
                label = f"{prompt} (from {args.control_config})"
            print_single_condition(label, stats)

    # Comparison (if both conditions exist)
    comparison_summary = None
    if "control_sita" in condition_data and "coordination_sita" in condition_data:
        ctrl_results, ctrl_stats = condition_data["control_sita"]
        coord_results, coord_stats = condition_data["coordination_sita"]
        comparison_summary = print_comparison(ctrl_results, coord_results, ctrl_stats, coord_stats)

    # Write JSON
    output_dir = PROJECT_ROOT / "data_export" / "outputs" / "quick_stats"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{args.config}_{args.dataset}.json"

    output = build_output_json(args.config, args.dataset, condition_data, comparison_summary)
    if args.control_config:
        output["control_config"] = args.control_config
    output_file.write_text(json.dumps(output, indent=2) + "\n")
    print(f"\nJSON written to: {output_file.relative_to(PROJECT_ROOT)}")
    print()


if __name__ == "__main__":
    main()
