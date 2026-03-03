"""
Alphabetisation Bias - Bias-Controlled Analysis

Sample-level analysis for bias-controlled pairs (pairs that differed in control).
Shows what % of samples chose salient vs alphabetical options.

Only uses the salient_vs_alphabetical_elo dataset.
"""

import json
from datetime import datetime

from ..shared.config import MODEL_MAPPING, OUTPUT_DIR
from ..shared.utils import (
    wilson_ci_half_width,
    get_eval_date,
    load_eval_results,
)

# Import categorize_pair_results directly since we need it here
import sys
from ..shared.config import PROJECT_ROOT
sys.path.insert(0, str(PROJECT_ROOT))
from utils.comparison import categorize_pair_results


DATASET = "salient_vs_alphabetical_elo"
DATASET_EXPORT_NAME = "salient_alphabetical"


def get_output_filename() -> str:
    return "alphabetisation_bias_samples.json"


def get_description() -> str:
    return "Sample-level alphabetisation preference for bias-controlled pairs (salient_alphabetical dataset only)"


def process_model(model_config: str) -> dict | None:
    """Process a single model for sample-level alphabetisation bias on bias-controlled pairs."""
    try:
        model_info = MODEL_MAPPING.get(model_config, {})
        control_config_name = model_info.get("control_config", model_config)
        coordination_config_name = model_info.get("coordination_config", model_config)

        control_results, coordination_results = load_eval_results(
            control_config_name, coordination_config_name, DATASET
        )

        if control_results is None or coordination_results is None:
            return None

        # Categorize pairs
        categorized = categorize_pair_results(control_results, coordination_results)

        # Get pairs that differed in control (our bias-controlled subset)
        differed_converged = categorized['eval1_differed_eval2_converged']
        both_differed = categorized['both_differed']

        # Count pairs that differed in control
        n_pairs_differed = len(differed_converged) + len(both_differed)

        # Get invalid responses from categorized summary
        from utils.comparison import generate_comparison_summary
        summary = generate_comparison_summary(categorized)
        invalid_responses = summary["control_config"]["invalid"]

        if n_pairs_differed == 0:
            return None

        # Count coordination outcomes for pairs that differed in control
        n_converged_on_A = 0  # Converged on salient
        n_converged_on_B = 0  # Converged on alphabetical
        n_still_differed = len(both_differed)  # Still differed

        for pair in differed_converged:
            converged_on = pair.get('eval_2_converged_on_option')
            if converged_on == 'A':
                n_converged_on_A += 1
            elif converged_on == 'B':
                n_converged_on_B += 1

        # Calculate sample-level counts
        # Each pair has 2 samples (AB order and BA order)
        total_samples = n_pairs_differed * 2

        # Control: By definition 50/50 since all pairs differed
        control_salient_samples = n_pairs_differed  # One salient per pair
        control_alphabetical_samples = n_pairs_differed  # One alphabetical per pair

        # Coordination: Based on convergence outcomes
        # - Converged on A: both samples chose salient (2 per pair)
        # - Converged on B: both samples chose alphabetical (2 per pair)
        # - Still differed: one of each (1 salient + 1 alphabetical per pair)
        coord_salient_samples = (n_converged_on_A * 2) + n_still_differed
        coord_alphabetical_samples = (n_converged_on_B * 2) + n_still_differed

        # Calculate percentages
        control_salient_pct = 50.0  # Always 50% by definition
        control_alphabetical_pct = 50.0  # Always 50% by definition

        coord_salient_pct = round((coord_salient_samples / total_samples) * 100, 1)
        coord_alphabetical_pct = round((coord_alphabetical_samples / total_samples) * 100, 1)

        # Get date from coordination eval
        date_tested = get_eval_date(coordination_config_name, "coordination_sita", DATASET)

        return {
            "model_id": model_info["model_id"],
            "model_name": model_info["model_name"],
            "model_family": model_info["model_family"],
            "is_reasoning": model_info["is_reasoning"],
            "control_eval_config": control_config_name,
            "coordination_eval_config": coordination_config_name,
            "dataset": DATASET_EXPORT_NAME,

            # Pair counts (for reference)
            "pairs_differed_in_control": n_pairs_differed,
            "pairs_converged_on_salient": n_converged_on_A,
            "pairs_converged_on_alphabetical": n_converged_on_B,
            "pairs_still_differed": n_still_differed,

            # Sample counts
            "total_samples": total_samples,

            # Control (always 50/50 by definition)
            "control_salient_samples": control_salient_samples,
            "control_alphabetical_samples": control_alphabetical_samples,
            "control_salient_pct": control_salient_pct,
            "control_alphabetical_pct": control_alphabetical_pct,

            # Coordination
            "coordination_salient_samples": coord_salient_samples,
            "coordination_alphabetical_samples": coord_alphabetical_samples,
            "coordination_salient_pct": coord_salient_pct,
            "coordination_alphabetical_pct": coord_alphabetical_pct,
            "coordination_salient_ci": wilson_ci_half_width(coord_salient_samples, total_samples),
            "coordination_alphabetical_ci": wilson_ci_half_width(coord_alphabetical_samples, total_samples),

            "invalid_responses": invalid_responses,
            "date_tested": date_tested
        }

    except Exception as e:
        print(f"  Error processing {model_config}: {e}")
        import traceback
        traceback.print_exc()
        return None


def run() -> dict:
    """Run the alphabetisation bias-controlled analysis."""
    print("Running Alphabetisation Bias (Bias-Controlled) analysis...")
    print(f"  Dataset: {DATASET}")

    results = []

    for model_config, model_info in MODEL_MAPPING.items():
        print(f"  Processing {model_info['model_name']}...")

        result = process_model(model_config)

        if result:
            results.append(result)
            print(f"    {result['coordination_salient_pct']}% salient, {result['coordination_alphabetical_pct']}% alphabetical")
        else:
            print(f"    Skipped - data not available")

    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": get_description(),
            "dataset": DATASET_EXPORT_NAME,
            "option_A": "Salient (semantically meaningful item)",
            "option_B": "Alphabetical (first alphabetically, not semantically salient)",
            "methodology": "Uses same pairs as bias-controlled coordination metric. Control is always 50/50 by definition. Coordination shows actual sample preference.",
            "note": "For thinking models, control uses non-thinking config, coordination uses thinking config",
            "models_included": len(results),
        },
        "results": results
    }

    # Write output
    output_path = OUTPUT_DIR / get_output_filename()
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"  Wrote {output_path} ({len(results)} rows)")

    return output
