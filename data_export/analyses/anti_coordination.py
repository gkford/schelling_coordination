"""
Anti-Coordination Analysis

Rate at which pairs that converged in control diverged under coordination.
Lower is better - indicates models don't break existing convergence.
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
    return "anti_coordination_results.json"


def get_description() -> str:
    return "Rate at which control-converged pairs diverged under coordination (anti-coordination)"


def process_model_dataset(model_config: str, dataset: str) -> dict | None:
    """Process a single model x dataset combination for anti-coordination results."""
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
        swap_to_coordinate = summary["metrics"]["swap_to_coordinate"]

        # Get date from coordination eval
        date_tested = get_eval_date(coordination_config_name, "coordination_sita", dataset)

        # Anti-coordination metrics (pairs that converged in control but diverged in coordination)
        anti_n = swap_to_coordinate["base"]  # Pairs that converged in control
        anti_coordination_pct = swap_to_coordinate["percentage"]
        anti_coordination_count = swap_to_coordinate["count"]

        return {
            "model_id": model_info["model_id"],
            "model_name": model_info["model_name"],
            "model_family": model_info["model_family"],
            "is_reasoning": model_info["is_reasoning"],
            "control_eval_config": control_config_name,
            "coordination_eval_config": coordination_config_name,
            "dataset": DATASET_MAPPING[dataset],
            "coordination_pct": anti_coordination_pct,  # % that diverged (anti-coordinated)
            "coordination_n": anti_n,
            "coordination_ci": wilson_ci_half_width(anti_coordination_count, anti_n),
            "control_pct": 100.0,  # By definition - we filtered to pairs that converged
            "control_n": anti_n,
            "control_ci": 0.0,
            "invalid_responses": control_config["invalid"],
            "date_tested": date_tested
        }

    except Exception as e:
        print(f"  Error processing {model_config}/{dataset}: {e}")
        return None


def run() -> dict:
    """Run the anti-coordination analysis."""
    print("Running Anti-Coordination analysis...")

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
            "metric": "% of control-converged pairs that diverged under coordination (lower is better)",
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
