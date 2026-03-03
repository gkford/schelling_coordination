"""
Raw Convergence Analysis

Raw convergence rates across all pairs (no filtering for bias).
Shows what % of pairs converged in control vs coordination conditions.
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
    return "raw_convergence.json"


def get_description() -> str:
    return "Raw convergence rates across all pairs (no filtering for bias)"


def process_model_dataset(model_config: str, dataset: str) -> dict | None:
    """Process a single model x dataset combination for full results."""
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

        control_config = summary["control_config"]
        intervention_config = summary["intervention_config"]

        # Get date from coordination eval
        date_tested = get_eval_date(coordination_config_name, "coordination_sita", dataset)

        # Calculate metrics
        full_control_n = control_config["valid_total"]
        full_coordination_n = intervention_config["valid_total"]
        full_control_pct = round((control_config["converged"] / full_control_n * 100) if full_control_n > 0 else 0, 1)
        full_coordination_pct = round((intervention_config["converged"] / full_coordination_n * 100) if full_coordination_n > 0 else 0, 1)

        return {
            "model_id": model_info["model_id"],
            "model_name": model_info["model_name"],
            "model_family": model_info["model_family"],
            "is_reasoning": model_info["is_reasoning"],
            "control_eval_config": control_config_name,
            "coordination_eval_config": coordination_config_name,
            "dataset": DATASET_MAPPING[dataset],
            "coordination_pct": full_coordination_pct,
            "coordination_n": full_coordination_n,
            "coordination_ci": wilson_ci_half_width(intervention_config["converged"], full_coordination_n),
            "control_pct": full_control_pct,
            "control_n": full_control_n,
            "control_ci": wilson_ci_half_width(control_config["converged"], full_control_n),
            "invalid_responses": control_config["invalid"],
            "date_tested": date_tested
        }

    except Exception as e:
        print(f"  Error processing {model_config}/{dataset}: {e}")
        return None


def run() -> dict:
    """Run the raw convergence analysis."""
    print("Running Raw Convergence analysis...")

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
            print(f"    Added {len(model_results)} results")
        else:
            print(f"    Skipped - incomplete data ({len(model_results)}/{len(DATASETS)} datasets)")

    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": get_description(),
            "metric": "Raw convergence rate (% of pairs converged)",
            "note": "For thinking models, control uses non-thinking config, coordination uses thinking config",
            "models_included": len(results) // len(DATASETS) if results else 0,
            "datasets_per_model": len(DATASETS),
        },
        "results": results
    }

    # Write output
    output_path = OUTPUT_DIR / get_output_filename()
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"  Wrote {output_path} ({len(results)} rows)")

    return output
