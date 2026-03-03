"""
Multi-model Elo comparison system.
Orchestrates running Elo tournaments across multiple models and datasets.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from collections import defaultdict

from match_manager import (
    load_model_history,
    save_model_history,
    get_existing_pairs,
    generate_pass_pairings,
    run_matches_parallel,
    count_passes
)
from elo_calculator import calculate_elo_ratings, analyze_preference_structure
from datasets import get_dataset

# Model name mappings for litellm
MODEL_MAPPINGS = {
    "haiku-3.5": "anthropic/claude-3-5-haiku-20241022",
    "gpt-4.1-mini": "openai/gpt-4.1-mini-2025-04-14",
    "kimi-k2": "openrouter/moonshotai/kimi-k2",
    "deepseek-v3": "openrouter/deepseek/deepseek-chat-v3-0324",
    # Allow full names too
    "anthropic/claude-3-5-haiku-20241022": "anthropic/claude-3-5-haiku-20241022",
    "openai/gpt-4.1-mini-2025-04-14": "openai/gpt-4.1-mini-2025-04-14",
    "moonshot/kimi-k2-1207": "openrouter/moonshotai/kimi-k2",
    "deepseek/deepseek-v3-march-2025": "openrouter/deepseek/deepseek-chat-v3-0324"
}

def get_model_name(model_key: str) -> str:
    """
    Get the full model name from a shorthand key.
    
    Args:
        model_key: Short name or full model name
        
    Returns:
        str: Full model name for litellm
    """
    return MODEL_MAPPINGS.get(model_key, model_key)

def run_model_passes(
    model_name: str, 
    items: List[str], 
    num_passes: int,
    dataset_name: str,
    verbose: bool = False
) -> Dict:
    """
    Run multiple passes for a single model.
    
    Args:
        model_name: Name of the model to run
        items: List of items to compare
        num_passes: Number of passes to run
        dataset_name: Name of the dataset being used
        verbose: Whether to show detailed progress
        
    Returns:
        dict: Contains match_history and ratings_data
    """
    print(f"\n{'='*60}")
    print(f"Running {model_name} on {dataset_name}")
    print(f"{'='*60}")
    
    # Load existing history for this dataset
    match_history = load_model_history(model_name, dataset_name)
    initial_matches = len(match_history)
    initial_passes = count_passes(match_history, len(items))
    
    print(f"Starting from {initial_passes:.1f} existing passes ({initial_matches} matches)")
    
    # Run passes
    for pass_num in range(1, num_passes + 1):
        current_pass = initial_passes + pass_num
        print(f"\nPass {pass_num}/{num_passes} (overall #{int(current_pass)}):")
        
        # Get existing pairs
        existing_pairs = get_existing_pairs(match_history)
        
        # Generate new pairings
        pairings, unpaired = generate_pass_pairings(items, existing_pairs)
        
        if not pairings:
            print("  No new unique pairings could be generated!")
            break
        
        print(f"  Generated {len(pairings)} new pairings")
        if unpaired:
            print(f"  {len(unpaired)} items could not be paired")
        
        # Progress callback
        def show_progress(completed, total):
            if verbose or completed == total:
                bar_width = 40
                percent = completed / total
                filled = int(bar_width * percent)
                bar = '█' * filled + '░' * (bar_width - filled)
                print(f"\r  Progress: [{bar}] {completed}/{total}", end='')
                if completed == total:
                    print()  # New line at completion
        
        # Run matches
        results = run_matches_parallel(
            pairings, 
            model_name, 
            progress_callback=show_progress
        )
        
        # Add results to history
        match_history.extend(results)
        
        # Save after each pass
        save_model_history(model_name, dataset_name, match_history)
        
        # Show pass statistics
        pass_stats = {"converged": 0, "draw": 0, "invalid": 0}
        for result in results:
            pass_stats[result["status"]] = pass_stats.get(result["status"], 0) + 1
        
        print(f"  Results: {pass_stats['converged']} converged, "
              f"{pass_stats['draw']} draws, {pass_stats['invalid']} invalid")
    
    # Calculate final ratings
    ratings_data = calculate_elo_ratings(match_history)
    
    print(f"\nCompleted {num_passes} passes for {model_name}")
    print(f"Total matches: {len(match_history)} (+{len(match_history) - initial_matches} new)")
    
    return {
        "model_name": model_name,
        "match_history": match_history,
        "ratings_data": ratings_data,
        "num_passes": initial_passes + num_passes,
        "total_matches": len(match_history)
    }

def calculate_weighted_average_elos(
    model_results: List[Dict]
) -> Dict[str, float]:
    """
    Calculate weighted average Elo scores across all models.
    
    Args:
        model_results: List of results from run_model_passes
        
    Returns:
        dict: Item -> weighted average Elo score
    """
    # Collect all items and their ratings
    item_ratings = defaultdict(list)
    
    for result in model_results:
        ratings = result["ratings_data"]["ratings"]
        for item, rating in ratings.items():
            item_ratings[item].append(rating)
    
    # Calculate averages
    weighted_elos = {}
    for item, ratings in item_ratings.items():
        weighted_elos[item] = sum(ratings) / len(ratings)
    
    return weighted_elos

def find_consensus_and_outliers(
    model_results: List[Dict],
    threshold: float = 100.0
) -> Dict:
    """
    Find items with high agreement and high disagreement across models.
    
    Args:
        model_results: List of results from run_model_passes
        threshold: Rating difference threshold for outliers
        
    Returns:
        dict: Contains consensus items and outliers
    """
    # Collect ratings by item
    item_ratings = defaultdict(dict)
    
    for result in model_results:
        model_name = result["model_name"]
        ratings = result["ratings_data"]["ratings"]
        for item, rating in ratings.items():
            item_ratings[item][model_name] = rating
    
    # Calculate variance for each item
    item_variance = {}
    for item, model_ratings in item_ratings.items():
        ratings = list(model_ratings.values())
        if len(ratings) > 1:
            mean = sum(ratings) / len(ratings)
            variance = sum((r - mean) ** 2 for r in ratings) / len(ratings)
            item_variance[item] = variance
    
    # Sort by variance
    sorted_by_variance = sorted(item_variance.items(), key=lambda x: x[1])
    
    # Get consensus (low variance) and controversial (high variance)
    num_items = min(10, len(sorted_by_variance) // 2)
    consensus_items = [item for item, _ in sorted_by_variance[:num_items]]
    controversial_items = [item for item, _ in sorted_by_variance[-num_items:]]
    
    # Find model-specific outliers
    outliers = defaultdict(list)
    for item, model_ratings in item_ratings.items():
        ratings = list(model_ratings.values())
        if len(ratings) > 1:
            mean = sum(ratings) / len(ratings)
            for model_name, rating in model_ratings.items():
                if abs(rating - mean) > threshold:
                    outliers[model_name].append({
                        "item": item,
                        "rating": rating,
                        "deviation": rating - mean
                    })
    
    return {
        "consensus_items": consensus_items,
        "controversial_items": controversial_items,
        "outliers": outliers,
        "item_variance": item_variance
    }

def run_multi_model_comparison(
    dataset: List[str],
    models: List[str],
    dataset_name: str,
    passes_per_model: int = 3,
    output_name: str = "comparison",
    verbose: bool = False
) -> Dict:
    """
    Run Elo comparison across multiple models.
    
    Args:
        dataset: List of items to compare
        models: List of model names (can be shorthand)
        dataset_name: Name of the dataset being used
        passes_per_model: Number of passes to run per model
        output_name: Name for output files
        verbose: Whether to show detailed progress
        
    Returns:
        dict: Complete results including all model data and analysis
    """
    print(f"\n{'='*70}")
    print(f"Multi-Model Elo Comparison")
    print(f"{'='*70}")
    print(f"Dataset: {dataset_name} ({len(dataset)} items)")
    print(f"Models: {', '.join(models)}")
    print(f"Passes per model: {passes_per_model}")
    
    # Run each model
    model_results = []
    for model_key in models:
        model_name = get_model_name(model_key)
        result = run_model_passes(
            model_name,
            dataset,
            passes_per_model,
            dataset_name,
            verbose=verbose
        )
        model_results.append(result)
    
    # Calculate aggregate metrics
    weighted_elos = calculate_weighted_average_elos(model_results)
    consensus_analysis = find_consensus_and_outliers(model_results)
    
    # Prepare complete results
    comparison_results = {
        "timestamp": datetime.now().isoformat(),
        "output_name": output_name,
        "dataset_size": len(dataset),
        "models": [r["model_name"] for r in model_results],
        "passes_per_model": passes_per_model,
        "model_results": model_results,
        "weighted_average_elos": weighted_elos,
        "consensus_analysis": consensus_analysis
    }
    
    # Save raw results
    output_dir = Path(__file__).parent / "comparisons" / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{output_name}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_file = output_dir / "raw_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        # Create serializable version (exclude match_history for space)
        save_data = {
            "timestamp": comparison_results["timestamp"],
            "output_name": comparison_results["output_name"],
            "dataset_size": comparison_results["dataset_size"],
            "models": comparison_results["models"],
            "passes_per_model": comparison_results["passes_per_model"],
            "weighted_average_elos": comparison_results["weighted_average_elos"],
            "consensus_analysis": {
                "consensus_items": consensus_analysis["consensus_items"],
                "controversial_items": consensus_analysis["controversial_items"],
                "outliers": {k: v for k, v in consensus_analysis["outliers"].items()}
            },
            "model_summaries": [
                {
                    "model_name": r["model_name"],
                    "total_matches": r["total_matches"],
                    "num_passes": r["num_passes"],
                    "ratings": r["ratings_data"]["ratings"]
                }
                for r in model_results
            ]
        }
        json.dump(save_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*70}")
    print(f"Comparison complete!")
    print(f"Results saved to: {output_dir}")
    
    return comparison_results

if __name__ == "__main__":
    # Test with a small dataset
    test_items = ["🔥", "💧", "🌍", "💨", "⚡", "🌟"]
    test_models = ["gpt-4.1-mini"]  # Quick test with one model
    
    results = run_multi_model_comparison(
        dataset=test_items,
        models=test_models,
        passes_per_model=1,
        output_name="test_run",
        verbose=True
    )
    
    print("\nWeighted average Elos:")
    sorted_items = sorted(
        results["weighted_average_elos"].items(),
        key=lambda x: x[1],
        reverse=True
    )
    for item, elo in sorted_items:
        print(f"  {item}: {elo:.0f}")