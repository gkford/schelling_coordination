"""
Alphabetisation Bias - Pairs That Differed in Control

Analysis of pairs that DIFFERED in control condition, showing their outcomes
in the coordination condition. This is the bias-controlled subset.

For each pair that differed in control:
- Did it converge on salient in coordination?
- Did it converge on alphabetical in coordination?
- Did it still differ (both picking 1st)?
- Did it still differ (both picking 2nd)?

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


DATASET = "salient_vs_alphabetical_elo"
DATASET_EXPORT_NAME = "salient_alphabetical"


def get_output_filename() -> str:
    return "alphabetisation_bias_differed_in_control.json"


def get_description() -> str:
    return "Coordination outcomes for pairs that differed in control condition (salient_alphabetical dataset only)"


def process_model(model_config: str) -> dict | None:
    """Process a single model for DIFFERED IN CONTROL pairs analysis."""
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

        # Find pairs that differed in control and count coordination outcomes
        # Also track pairs with invalid coordination responses
        coord_converged_on_A = 0  # Converged on salient
        coord_converged_on_B = 0  # Converged on alphabetical
        coord_differed_both_first = 0  # AB→A, BA→B (both picked first-listed)
        coord_differed_both_second = 0  # AB→B, BA→A (both picked second-listed)
        invalid_in_calculation = 0  # Differed in control but invalid coordination

        n_differed_in_control_total = 0  # Total pairs that differed in control (including invalid coord)

        for pair_id, ctrl_pair in control_pair_results.items():
            if not ctrl_pair.get('converged'):
                # This pair differed in control
                n_differed_in_control_total += 1

                coord_pair = coord_pair_results.get(pair_id, {})
                coord_ab = coord_pair.get('AB_choice')
                coord_ba = coord_pair.get('BA_choice')

                # Check if coordination responses are valid
                if coord_ab not in ['A', 'B'] or coord_ba not in ['A', 'B']:
                    invalid_in_calculation += 1
                    continue

                if coord_pair.get('converged'):
                    converged_on = coord_pair.get('converged_on_option')
                    if converged_on == 'A':
                        coord_converged_on_A += 1
                    elif converged_on == 'B':
                        coord_converged_on_B += 1
                else:
                    # Differed - categorize by position bias
                    if coord_ab == 'A' and coord_ba == 'B':
                        coord_differed_both_first += 1
                    elif coord_ab == 'B' and coord_ba == 'A':
                        coord_differed_both_second += 1

        # n_differed_in_control is the valid pairs (used as denominator)
        n_differed_in_control = n_differed_in_control_total - invalid_in_calculation

        if n_differed_in_control == 0:
            return None

        coord_total_converged = coord_converged_on_A + coord_converged_on_B
        coord_total_differed = coord_differed_both_first + coord_differed_both_second

        # Calculate percentages (out of all differed-in-control pairs)
        coord_converged_salient_pct = round((coord_converged_on_A / n_differed_in_control * 100), 1)
        coord_converged_alpha_pct = round((coord_converged_on_B / n_differed_in_control * 100), 1)
        coord_differed_first_pct = round((coord_differed_both_first / n_differed_in_control * 100), 1)
        coord_differed_second_pct = round((coord_differed_both_second / n_differed_in_control * 100), 1)

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

            # Total pairs that differed in control (our denominator)
            "n_differed_in_control": n_differed_in_control,

            # Coordination outcomes for those pairs
            "coord_converged_on_salient": coord_converged_on_A,
            "coord_converged_on_salient_pct": coord_converged_salient_pct,
            "coord_converged_on_alphabetical": coord_converged_on_B,
            "coord_converged_on_alphabetical_pct": coord_converged_alpha_pct,
            "coord_differed_both_first": coord_differed_both_first,
            "coord_differed_both_first_pct": coord_differed_first_pct,
            "coord_differed_both_second": coord_differed_both_second,
            "coord_differed_both_second_pct": coord_differed_second_pct,

            # Summary stats
            "coord_total_converged": coord_total_converged,
            "coord_total_converged_pct": round((coord_total_converged / n_differed_in_control * 100), 1),
            "coord_total_differed": coord_total_differed,
            "coord_total_differed_pct": round((coord_total_differed / n_differed_in_control * 100), 1),

            # CI for converged rate
            "coord_converged_ci": wilson_ci_half_width(coord_total_converged, n_differed_in_control),

            "invalid_responses": invalid_in_calculation,
            "date_tested": date_tested
        }

    except Exception as e:
        print(f"  Error processing {model_config}: {e}")
        import traceback
        traceback.print_exc()
        return None


def run() -> dict:
    """Run the differed-in-control alphabetisation bias analysis."""
    print("Running Alphabetisation Bias (Differed in Control) analysis...")
    print(f"  Dataset: {DATASET}")

    results = []

    for model_config, model_info in MODEL_MAPPING.items():
        print(f"  Processing {model_info['model_name']}...")

        result = process_model(model_config)

        if result:
            results.append(result)
            print(f"    {result['n_differed_in_control']} pairs differed in control")
            print(f"    Coord: {result['coord_converged_on_salient']} salient, {result['coord_converged_on_alphabetical']} alpha, {result['coord_differed_both_first']} 1st, {result['coord_differed_both_second']} 2nd")
        else:
            print(f"    Skipped - data not available")

    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": get_description(),
            "dataset": DATASET_EXPORT_NAME,
            "option_A": "Salient (semantically meaningful item)",
            "option_B": "Alphabetical (first alphabetically, not semantically salient)",
            "methodology": "For pairs that DIFFERED in control, shows their coordination outcomes: converged on salient, converged on alphabetical, differed (both 1st), differed (both 2nd).",
            "filtering": "Only includes pairs where AB and BA made different choices in control condition",
            "percentages": "All percentages are out of n_differed_in_control (the pairs that differed in control)",
            "differed_explanation": {
                "both_first": "AB ordering picked A (first-listed), BA ordering picked B (first-listed) - indicates position bias toward first option",
                "both_second": "AB ordering picked B (second-listed), BA ordering picked A (second-listed) - indicates position bias toward second option"
            },
            "note": "For thinking models, control uses non-thinking config, coordination uses thinking config",
            "invalid_responses_note": "Count of pairs that differed in control but had invalid coordination responses (excluded from calculation)",
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
