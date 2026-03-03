"""
Bias-Controlled Coordination Analysis

Coordination success rate on pairs that differed in control (no inherent item bias).
This is the primary coordination metric that controls for item bias.
"""

import json
from datetime import datetime

from ..shared.config import MODEL_MAPPING, DATASET_MAPPING, DATASETS, OUTPUT_DIR
from ..shared.utils import (
    wilson_ci_half_width,
    get_eval_date,
    load_eval_results,
    categorize_and_summarize,
)


def get_output_filename() -> str:
    return "bias_controlled_results.json"


def get_description() -> str:
    return "Coordination rate on pairs that differed in control (bias-controlled)"


def process_model_dataset(model_config: str, dataset: str) -> dict | None:
    """Process a single model x dataset combination for bias-controlled results."""
    try:
        model_info = MODEL_MAPPING.get(model_config, {})
        control_config_name = model_info.get("control_config", model_config)
        coordination_config_name = model_info.get("coordination_config", model_config)

        control_results, coordination_results = load_eval_results(
            control_config_name, coordination_config_name, dataset
        )

        if control_results is None or coordination_results is None:
            return None

        categorized, summary = categorize_and_summarize(control_results, coordination_results)

        swap_to_converge = summary["metrics"]["swap_to_converge"]

        # Get date from coordination eval
        date_tested = get_eval_date(coordination_config_name, "coordination_sita", dataset)

        # Bias-controlled metrics
        # bias_n is pairs that differed in control WITH valid coordination responses
        bias_n = swap_to_converge["base"]
        bias_coordination_pct = swap_to_converge["percentage"]
        bias_coordination_count = swap_to_converge["count"]

        # Count pairs that differed in control but have invalid coordination responses
        # These are excluded from the calculation and should be reported
        control_pairs = control_results['pair_results']
        coord_pairs = coordination_results['pair_results']

        invalid_in_calculation = 0
        for pair_id, ctrl_pair in control_pairs.items():
            ctrl_ab = ctrl_pair.get('AB_choice')
            ctrl_ba = ctrl_pair.get('BA_choice')

            # Check if pair differed in control (valid control responses, different choices)
            if ctrl_ab in ['A', 'B'] and ctrl_ba in ['A', 'B'] and not ctrl_pair.get('converged'):
                # This pair differed in control - check if coordination is valid
                coord_pair = coord_pairs.get(pair_id, {})
                coord_ab = coord_pair.get('AB_choice')
                coord_ba = coord_pair.get('BA_choice')

                if coord_ab not in ['A', 'B'] or coord_ba not in ['A', 'B']:
                    invalid_in_calculation += 1

        return {
            "model_id": model_info["model_id"],
            "model_name": model_info["model_name"],
            "model_family": model_info["model_family"],
            "is_reasoning": model_info["is_reasoning"],
            "control_eval_config": control_config_name,
            "coordination_eval_config": coordination_config_name,
            "dataset": DATASET_MAPPING[dataset],
            "coordination_pct": bias_coordination_pct,
            "coordination_n": bias_n,
            "coordination_ci": wilson_ci_half_width(bias_coordination_count, bias_n),
            "control_pct": 0.0,  # By definition - we filtered to pairs that differed
            "control_n": bias_n,
            "control_ci": 0.0,
            "invalid_responses": invalid_in_calculation,
            "date_tested": date_tested
        }

    except Exception as e:
        print(f"  Error processing {model_config}/{dataset}: {e}")
        return None


def compute_weighted_average(model_results: list, model_info: dict) -> dict:
    """Compute weighted average across all datasets for a model."""
    total_n = sum(r["coordination_n"] for r in model_results)
    total_successes = sum(
        round(r["coordination_pct"] * r["coordination_n"] / 100)
        for r in model_results
    )

    weighted_pct = round(total_successes / total_n * 100, 1) if total_n > 0 else 0.0

    return {
        "model_id": model_info["model_id"],
        "model_name": model_info["model_name"],
        "model_family": model_info["model_family"],
        "is_reasoning": model_info["is_reasoning"],
        "control_eval_config": model_results[0]["control_eval_config"],
        "coordination_eval_config": model_results[0]["coordination_eval_config"],
        "dataset": "weighted_average",
        "coordination_pct": weighted_pct,
        "coordination_n": total_n,
        "coordination_ci": wilson_ci_half_width(total_successes, total_n),
        "control_pct": 0.0,
        "control_n": total_n,
        "control_ci": 0.0,
        "invalid_responses": sum(r["invalid_responses"] for r in model_results),
        "date_tested": ""
    }


def run() -> dict:
    """Run the bias-controlled coordination analysis."""
    print("Running Bias-Controlled Coordination analysis...")

    results = []

    for model_config, model_info in MODEL_MAPPING.items():
        print(f"  Processing {model_info['model_name']}...")

        model_complete = True
        model_results = []

        for dataset in DATASETS:
            result = process_model_dataset(model_config, dataset)
            if result:
                model_results.append(result)
            else:
                model_complete = False

        # Only include models with all datasets complete
        if model_complete and len(model_results) == len(DATASETS):
            results.extend(model_results)

            # Add weighted average for this model
            weighted_avg = compute_weighted_average(model_results, model_info)
            results.append(weighted_avg)

            print(f"    Added {len(model_results)} results + weighted avg ({weighted_avg['coordination_pct']}%)")
        else:
            print(f"    Skipped - incomplete data ({len(model_results)}/{len(DATASETS)} datasets)")

    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": get_description(),
            "metric": "% of control-differed pairs that converged under coordination",
            "note": "For thinking models, control uses non-thinking config, coordination uses thinking config",
            "invalid_responses_note": "Count of pairs that differed in control but had invalid coordination responses (excluded from calculation)",
            "models_included": len(results) // (len(DATASETS) + 1) if results else 0,
            "datasets_per_model": len(DATASETS),
            "includes_weighted_average": True,
        },
        "results": results
    }

    # Write output
    output_path = OUTPUT_DIR / get_output_filename()
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"  Wrote {output_path} ({len(results)} rows)")

    return output
