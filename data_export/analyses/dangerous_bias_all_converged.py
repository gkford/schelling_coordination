"""
Dangerous Bias - All Converged Pairs Analysis

Analysis of all pairs that converged in each condition (control and coordination).
Shows what % of converged pairs chose mundane vs dangerous options.

Only uses the mundane_vs_dangerous_elo dataset.
"""

import json
from datetime import datetime

from ..shared.config import MODEL_MAPPING, OUTPUT_DIR
from ..shared.utils import (
    wilson_ci_half_width,
    get_eval_date,
    load_eval_results,
    categorize_and_summarize,
)


DATASET = "mundane_vs_dangerous_elo"
DATASET_EXPORT_NAME = "mundane_dangerous"


def get_output_filename() -> str:
    return "dangerous_bias_all_converged.json"


def get_description() -> str:
    return "Option preference for all converged pairs in control and coordination conditions (mundane_dangerous dataset only)"


def process_model(model_config: str) -> dict | None:
    """Process a single model for ALL CONVERGED pairs analysis."""
    try:
        model_info = MODEL_MAPPING.get(model_config, {})
        control_config_name = model_info.get("control_config", model_config)
        coordination_config_name = model_info.get("coordination_config", model_config)

        control_results, coordination_results = load_eval_results(
            control_config_name, coordination_config_name, DATASET
        )

        if control_results is None or coordination_results is None:
            return None

        # Get pair_results dict from each condition
        control_pair_results = control_results.get('pair_results', {})
        coord_pair_results = coordination_results.get('pair_results', {})

        # Get invalid responses from categorized summary
        categorized, summary = categorize_and_summarize(control_results, coordination_results)
        invalid_responses = summary["control_config"]["invalid"]

        # Count converged and differed pairs in control condition
        # In mundane_vs_dangerous: A = mundane (safe), B = dangerous
        control_converged_on_A = 0  # Converged on mundane
        control_converged_on_B = 0  # Converged on dangerous
        control_differed_both_first = 0  # AB→A, BA→B (both picked first-listed)
        control_differed_both_second = 0  # AB→B, BA→A (both picked second-listed)

        for pair_id, pair_data in control_pair_results.items():
            if pair_data.get('converged'):
                converged_on = pair_data.get('converged_on_option')
                if converged_on == 'A':
                    control_converged_on_A += 1
                elif converged_on == 'B':
                    control_converged_on_B += 1
            else:
                # Differed - categorize by position bias
                ab_choice = pair_data.get('AB_choice')
                ba_choice = pair_data.get('BA_choice')
                if ab_choice == 'A' and ba_choice == 'B':
                    control_differed_both_first += 1
                elif ab_choice == 'B' and ba_choice == 'A':
                    control_differed_both_second += 1

        control_total_converged = control_converged_on_A + control_converged_on_B
        control_total_differed = control_differed_both_first + control_differed_both_second

        # Count converged and differed pairs in coordination condition
        coord_converged_on_A = 0  # Converged on mundane
        coord_converged_on_B = 0  # Converged on dangerous
        coord_differed_both_first = 0
        coord_differed_both_second = 0

        for pair_id, pair_data in coord_pair_results.items():
            if pair_data.get('converged'):
                converged_on = pair_data.get('converged_on_option')
                if converged_on == 'A':
                    coord_converged_on_A += 1
                elif converged_on == 'B':
                    coord_converged_on_B += 1
            else:
                ab_choice = pair_data.get('AB_choice')
                ba_choice = pair_data.get('BA_choice')
                if ab_choice == 'A' and ba_choice == 'B':
                    coord_differed_both_first += 1
                elif ab_choice == 'B' and ba_choice == 'A':
                    coord_differed_both_second += 1

        coord_total_converged = coord_converged_on_A + coord_converged_on_B
        coord_total_differed = coord_differed_both_first + coord_differed_both_second

        # Calculate percentages for converged pairs
        control_mundane_pct = round((control_converged_on_A / control_total_converged * 100), 1) if control_total_converged > 0 else 0
        control_dangerous_pct = round((control_converged_on_B / control_total_converged * 100), 1) if control_total_converged > 0 else 0

        coord_mundane_pct = round((coord_converged_on_A / coord_total_converged * 100), 1) if coord_total_converged > 0 else 0
        coord_dangerous_pct = round((coord_converged_on_B / coord_total_converged * 100), 1) if coord_total_converged > 0 else 0

        # Calculate percentages for differed pairs (position bias)
        control_differed_first_pct = round((control_differed_both_first / control_total_differed * 100), 1) if control_total_differed > 0 else 0
        control_differed_second_pct = round((control_differed_both_second / control_total_differed * 100), 1) if control_total_differed > 0 else 0

        coord_differed_first_pct = round((coord_differed_both_first / coord_total_differed * 100), 1) if coord_total_differed > 0 else 0
        coord_differed_second_pct = round((coord_differed_both_second / coord_total_differed * 100), 1) if coord_total_differed > 0 else 0

        # Get date from coordination eval
        date_tested = get_eval_date(coordination_config_name, "coordination_sita", DATASET)

        total_pairs = control_total_converged + control_total_differed

        return {
            "model_id": model_info["model_id"],
            "model_name": model_info["model_name"],
            "model_family": model_info["model_family"],
            "is_reasoning": model_info["is_reasoning"],
            "control_eval_config": control_config_name,
            "coordination_eval_config": coordination_config_name,
            "dataset": DATASET_EXPORT_NAME,
            "total_pairs": total_pairs,

            # Control condition - converged pairs
            "control_converged_n": control_total_converged,
            "control_converged_on_mundane": control_converged_on_A,
            "control_converged_on_dangerous": control_converged_on_B,
            "control_mundane_pct": control_mundane_pct,
            "control_dangerous_pct": control_dangerous_pct,
            "control_mundane_ci": wilson_ci_half_width(control_converged_on_A, control_total_converged),

            # Control condition - differed pairs (position bias)
            "control_differed_n": control_total_differed,
            "control_differed_both_first": control_differed_both_first,
            "control_differed_both_second": control_differed_both_second,
            "control_differed_first_pct": control_differed_first_pct,
            "control_differed_second_pct": control_differed_second_pct,

            # Coordination condition - converged pairs
            "coordination_converged_n": coord_total_converged,
            "coordination_converged_on_mundane": coord_converged_on_A,
            "coordination_converged_on_dangerous": coord_converged_on_B,
            "coordination_mundane_pct": coord_mundane_pct,
            "coordination_dangerous_pct": coord_dangerous_pct,
            "coordination_mundane_ci": wilson_ci_half_width(coord_converged_on_A, coord_total_converged),

            # Coordination condition - differed pairs (position bias)
            "coordination_differed_n": coord_total_differed,
            "coordination_differed_both_first": coord_differed_both_first,
            "coordination_differed_both_second": coord_differed_both_second,
            "coordination_differed_first_pct": coord_differed_first_pct,
            "coordination_differed_second_pct": coord_differed_second_pct,

            "invalid_responses": invalid_responses,
            "date_tested": date_tested
        }

    except Exception as e:
        print(f"  Error processing {model_config}: {e}")
        import traceback
        traceback.print_exc()
        return None


def run() -> dict:
    """Run the all converged pairs dangerous bias analysis."""
    print("Running Dangerous Bias (All Converged) analysis...")
    print(f"  Dataset: {DATASET}")

    results = []

    for model_config, model_info in MODEL_MAPPING.items():
        print(f"  Processing {model_info['model_name']}...")

        result = process_model(model_config)

        if result:
            results.append(result)
            print(f"    Control: {result['control_converged_n']} converged ({result['control_mundane_pct']}% mundane)")
            print(f"    Coordination: {result['coordination_converged_n']} converged ({result['coordination_mundane_pct']}% mundane)")
        else:
            print(f"    Skipped - data not available")

    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": get_description(),
            "dataset": DATASET_EXPORT_NAME,
            "option_A": "Mundane (safe/neutral emoji)",
            "option_B": "Dangerous (negative/dangerous emoji)",
            "methodology": "For each condition (control and coordination), categorizes all pairs into: converged on mundane, converged on dangerous, differed with both picking first-listed, differed with both picking second-listed.",
            "differed_explanation": {
                "both_first": "AB ordering picked A (first-listed), BA ordering picked B (first-listed) - indicates position bias toward first option",
                "both_second": "AB ordering picked B (second-listed), BA ordering picked A (second-listed) - indicates position bias toward second option"
            },
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
