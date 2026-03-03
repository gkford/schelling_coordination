"""
Justification Categories Analysis

Aggregated category distribution for pre-hoc justification data.
Shows what strategies/heuristics models claim to use.

Provides breakdowns for:
- All pairs (full dataset)
- Differed-in-control pairs only (where AB != BA in control condition)

For both "strategy" and "heuristic" variations.
"""

import json
from pathlib import Path
from datetime import datetime
from inspect_ai.log import read_eval_log

from ..shared.config import MODEL_MAPPING, OUTPUT_DIR, PROJECT_ROOT


DATASET = "salient_vs_alphabetical_elo"


def get_output_filename() -> str:
    return "justification_categories.json"


def get_description() -> str:
    return "Aggregated category distribution for pre-hoc justification data (strategy and heuristic variations)"


def load_justification_data(config_name: str, variation_name: str) -> dict | None:
    """Load justification eval data for a model and variation."""
    results_path = PROJECT_ROOT / "results"
    justification_dir = results_path / config_name / "coordination_sita" / DATASET / "justification"

    if not justification_dir.exists():
        return None

    # Find eval file matching the variation
    eval_files = list(justification_dir.glob(f"*justification-{variation_name}*.eval"))

    if len(eval_files) == 0:
        return None

    try:
        eval_log = read_eval_log(str(eval_files[0]))

        # Extract strategy metadata from samples
        strategy_data = {}
        for sample in eval_log.samples:
            if not sample.scores:
                continue

            strategy_score = sample.scores.get('strategy_name_extractor')
            if not strategy_score:
                continue

            pair_id = sample.metadata.get('pair_id')
            ordering = sample.metadata.get('ordering')
            sample_key = f"{pair_id}_{ordering}"

            strategy_data[sample_key] = {
                'pair_id': pair_id,
                'ordering': ordering,
                'category': strategy_score.metadata.get('category'),
                'subcategory': strategy_score.metadata.get('subcategory'),
                'inferable': strategy_score.metadata.get('inferable', False),
            }

        return strategy_data
    except Exception as e:
        print(f"    Error loading justification: {e}")
        return None


def load_control_results(config_name: str) -> set:
    """Load control_sita results and return set of pair_ids that differed."""
    results_path = PROJECT_ROOT / "results"
    control_dir = results_path / config_name / "control_sita" / DATASET

    if not control_dir.exists():
        return set()

    eval_files = list(control_dir.glob("*.eval"))
    if not eval_files:
        return set()

    try:
        eval_log = read_eval_log(str(eval_files[0]))

        # Group samples by pair_id
        pairs = {}
        for sample in eval_log.samples:
            pair_id = sample.metadata.get('pair_id')
            # Handle both 'order' and 'ordering' keys
            ordering = sample.metadata.get('ordering') or sample.metadata.get('order')

            # Get the choice from validation_scorer metadata
            choice = None
            if sample.scores and 'validation_scorer' in sample.scores:
                choice = sample.scores['validation_scorer'].metadata.get('choice')

            if pair_id not in pairs:
                pairs[pair_id] = {}
            pairs[pair_id][ordering] = choice

        # Find pairs that differed
        differed_pairs = set()
        for pair_id, orderings in pairs.items():
            ab_choice = orderings.get('AB')
            ba_choice = orderings.get('BA')
            if ab_choice and ba_choice and ab_choice != ba_choice:
                differed_pairs.add(pair_id)

        return differed_pairs
    except Exception as e:
        print(f"    Error loading control results: {e}")
        return set()


def aggregate_categories(strategy_data: dict, differed_pairs: set = None) -> dict:
    """Aggregate category counts from strategy data."""
    category_counts = {}
    total_samples = 0
    inferable_count = 0

    for sample_key, data in strategy_data.items():
        # Filter to differed pairs if specified
        if differed_pairs is not None:
            pair_id = data['pair_id']
            if pair_id not in differed_pairs:
                continue

        category = data.get('category', 'Unknown')
        category_counts[category] = category_counts.get(category, 0) + 1
        total_samples += 1

        if data.get('inferable'):
            inferable_count += 1

    return {
        'total_samples': total_samples,
        'inferable_samples': inferable_count,
        'category_counts': category_counts
    }


def process_model(model_config: str) -> dict | None:
    """Process a single model for both strategy and heuristic variations."""
    model_info = MODEL_MAPPING.get(model_config, {})

    # Use control_config for loading control results (handles thinking models)
    control_config_name = model_info.get("control_config", model_config)
    # Use coordination_config for loading justification data
    coordination_config_name = model_info.get("coordination_config", model_config)

    # Load control results to identify differed pairs
    differed_pairs = load_control_results(control_config_name)

    result = {
        "model_id": model_info.get("model_id", model_config),
        "model_name": model_info.get("model_name", model_config),
        "model_family": model_info.get("model_family", "unknown"),
        "is_reasoning": model_info.get("is_reasoning", False),
        "variations": {}
    }

    has_data = False

    for variation in ["strategy", "heuristic"]:
        # Load justification data
        strategy_data = load_justification_data(coordination_config_name, variation)

        if strategy_data is None:
            continue

        has_data = True

        # Aggregate for all pairs
        all_pairs_agg = aggregate_categories(strategy_data)

        # Aggregate for differed-in-control pairs only
        differed_agg = aggregate_categories(strategy_data, differed_pairs)

        result["variations"][variation] = {
            "all_pairs": all_pairs_agg,
            "differed_in_control": differed_agg
        }

    return result if has_data else None


def run() -> dict:
    """Run the justification categories analysis."""
    print("Running Justification Categories analysis...")
    print(f"  Dataset: {DATASET}")

    results = []

    for model_config, model_info in MODEL_MAPPING.items():
        print(f"  Processing {model_info['model_name']}...")

        result = process_model(model_config)

        if result and result.get("variations"):
            results.append(result)
            variations = list(result["variations"].keys())
            print(f"    Found variations: {variations}")
            for var in variations:
                all_n = result["variations"][var]["all_pairs"]["total_samples"]
                diff_n = result["variations"][var]["differed_in_control"]["total_samples"]
                print(f"      {var}: {all_n} all, {diff_n} differed")
        else:
            print(f"    No justification data found")

    # Get all unique categories across all models
    all_categories = set()
    for result in results:
        for var_data in result.get("variations", {}).values():
            all_categories.update(var_data["all_pairs"]["category_counts"].keys())

    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": get_description(),
            "dataset": DATASET,
            "variations_explained": {
                "strategy": "Model asked: 'What strategy would you use to answer this question?'",
                "heuristic": "Model asked: 'What heuristic would you use to answer this question?'"
            },
            "subsets_explained": {
                "all_pairs": "All 400 pairs × 2 orderings = up to 800 samples",
                "differed_in_control": "Only pairs where AB and BA made different choices in control condition"
            },
            "categories": sorted(list(all_categories)),
            "models_included": len(results),
        },
        "results": results
    }

    # Write output
    output_path = OUTPUT_DIR / get_output_filename()
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"  Wrote {output_path}")

    return output
