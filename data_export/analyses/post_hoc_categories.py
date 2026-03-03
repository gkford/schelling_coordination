"""
Post-Hoc Explanation Categories Analysis

Aggregated category distribution for post-hoc explanation data.
Shows what reasoning models claim to have used AFTER making their choice.

Unlike pre-hoc justifications (strategy/heuristic asked BEFORE choice),
post-hoc explanations are collected AFTER the choice was made.
"""

import json
import asyncio
from pathlib import Path
from datetime import datetime
from collections import Counter
from inspect_ai.log import read_eval_log

from ..shared.config import MODEL_MAPPING, OUTPUT_DIR, PROJECT_ROOT

import sys
sys.path.append(str(PROJECT_ROOT / "strategy_investigation"))
from categorize_post_hoc_explanations import categorize_explanation_with_llm


DATASET = "salient_vs_alphabetical_elo"


def get_output_filename() -> str:
    return "post_hoc_categories.json"


def get_description() -> str:
    return "Aggregated category distribution for post-hoc explanation data"


def find_post_hoc_eval(config_name: str) -> Path | None:
    """Find post-hoc eval file for a given config."""
    results_path = PROJECT_ROOT / "results"
    post_hoc_dir = results_path / config_name / "coordination_sita" / DATASET / "post_hoc_continuation"

    if not post_hoc_dir.exists():
        return None

    eval_files = list(post_hoc_dir.glob("*.eval"))
    if not eval_files:
        return None

    # Return most recent
    return sorted(eval_files)[-1]


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

        pairs = {}
        for sample in eval_log.samples:
            pair_id = sample.metadata.get('pair_id')
            ordering = sample.metadata.get('ordering') or sample.metadata.get('order')

            choice = None
            if sample.scores and 'validation_scorer' in sample.scores:
                choice = sample.scores['validation_scorer'].metadata.get('choice')

            if pair_id not in pairs:
                pairs[pair_id] = {}
            pairs[pair_id][ordering] = choice

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


async def categorize_sample(sample) -> dict:
    """Categorize a single sample's post-hoc explanation."""
    if len(sample.messages) < 5:
        return {'category': 'Error', 'subcategory': 'missing_messages'}

    explanation = sample.messages[4].content
    choice = sample.messages[2].content
    option_A = sample.metadata.get('option_A', '')
    option_B = sample.metadata.get('option_B', '')
    ordering = sample.metadata.get('order', '')

    try:
        result = await categorize_explanation_with_llm(
            explanation=explanation,
            actual_choice=choice,
            option_A=option_A,
            option_B=option_B,
            ordering=ordering
        )
        return result
    except Exception as e:
        return {'category': 'Error', 'subcategory': str(e)[:50]}


async def process_model(model_config: str) -> dict | None:
    """Process a single model's post-hoc explanations."""
    model_info = MODEL_MAPPING.get(model_config, {})

    # Find post-hoc eval file
    eval_path = find_post_hoc_eval(model_config)
    if not eval_path:
        return None

    print(f"    Loading {eval_path.name}...")
    eval_log = read_eval_log(str(eval_path))

    # Load control results for differed pairs
    control_config = model_info.get("control_config", model_config)
    differed_pairs = load_control_results(control_config)

    # Categorize all samples
    print(f"    Categorizing {len(eval_log.samples)} samples...")
    tasks = [categorize_sample(s) for s in eval_log.samples]
    results = await asyncio.gather(*tasks)

    # Aggregate results
    all_categories = Counter()
    all_subcategories = Counter()
    differed_categories = Counter()
    differed_subcategories = Counter()

    for sample, result in zip(eval_log.samples, results):
        cat = result.get('category', 'Unknown')
        subcat = result.get('subcategory', 'unknown')

        # Clean up subcategory (remove braces if present)
        subcat = subcat.strip('{}')

        all_categories[cat] += 1
        all_subcategories[f"{cat}:{subcat}"] += 1

        pair_id = sample.metadata.get('pair_id')
        if pair_id in differed_pairs:
            differed_categories[cat] += 1
            differed_subcategories[f"{cat}:{subcat}"] += 1

    return {
        "model_id": model_info.get("model_id", model_config),
        "model_name": model_info.get("model_name", model_config),
        "model_family": model_info.get("model_family", "unknown"),
        "is_reasoning": model_info.get("is_reasoning", False),
        "all_pairs": {
            "total_samples": len(eval_log.samples),
            "category_counts": dict(all_categories),
            "subcategory_counts": dict(all_subcategories)
        },
        "differed_in_control": {
            "total_samples": sum(differed_categories.values()),
            "category_counts": dict(differed_categories),
            "subcategory_counts": dict(differed_subcategories)
        }
    }


def run() -> dict:
    """Run the post-hoc categories analysis."""
    print("Running Post-Hoc Categories analysis...")
    print(f"  Dataset: {DATASET}")

    results = []

    for model_config, model_info in MODEL_MAPPING.items():
        print(f"  Processing {model_info['model_name']}...")

        # Check if post-hoc data exists
        eval_path = find_post_hoc_eval(model_config)
        if not eval_path:
            print(f"    No post-hoc data found")
            continue

        # Run async processing
        result = asyncio.run(process_model(model_config))

        if result:
            results.append(result)
            print(f"    Found {result['all_pairs']['total_samples']} samples")

    # Get all unique categories
    all_categories = set()
    for result in results:
        all_categories.update(result["all_pairs"]["category_counts"].keys())

    output = {
        "metadata": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "description": get_description(),
            "dataset": DATASET,
            "explanation": "Post-hoc: Model asked 'Explain the primary reason you made that choice.' AFTER making choice",
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
