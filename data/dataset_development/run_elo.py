#!/usr/bin/env python3
"""
CLI script for running Elo rating tests on language models.

Usage:
    python run_elo.py <model_name> --dataset <dataset_name> [options]

Examples:
    python run_elo.py gpt-4 --dataset emojis                    # Interactive mode
    python run_elo.py gpt-4 --dataset common_words --passes 5   # Run 5 passes
    python run_elo.py claude-3-opus --dataset emojis --passes 1 # Run 1 pass (default)
    python run_elo.py gpt-4 --dataset emojis --show-ratings     # Just show current ratings

Options:
    --dataset NAME  Dataset to use (REQUIRED)
    --passes N      Run N passes (skips interactive prompt)
    --show-ratings  Display current Elo ratings and exit
    --verbose       Show detailed progress during runs
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from datasets import get_dataset
from match_manager import (
    load_model_history, 
    save_model_history,
    get_existing_pairs,
    generate_pass_pairings,
    run_matches_parallel,
    count_passes
)
from elo_calculator import (
    calculate_elo_ratings,
    analyze_preference_structure,
    generate_elo_report
)

def progress_bar(current, total, width=50):
    """
    Generate a simple progress bar string.
    """
    percent = current / total
    filled = int(width * percent)
    bar = '█' * filled + '░' * (width - filled)
    return f"[{bar}] {current}/{total}"

def interactive_prompt(model_name, existing_passes):
    """
    Shows interactive prompt if --passes not specified.
    
    Args:
        model_name: Name of the model
        existing_passes: Number of passes already run
        
    Returns:
        int: Number of passes to run
    """
    if existing_passes > 0:
        print(f"Model '{model_name}' has {existing_passes:.0f} passes already run.")
        prompt = "How many additional passes would you like to run? [1]: "
    else:
        print(f"No existing history for model '{model_name}'.")
        prompt = "How many passes would you like to run? [1]: "
    
    while True:
        response = input(prompt).strip()
        if not response:
            return 1  # Default
        
        try:
            num_passes = int(response)
            if num_passes < 0:
                print("Please enter a positive number.")
                continue
            return num_passes
        except ValueError:
            print("Please enter a valid number.")

def run_passes(model_name, dataset_name, num_passes, verbose=False, use_defaults=False, temperature=None, top_p=None, top_k=None):
    """
    Runs specified number of passes for a model on a specific dataset.
    
    Args:
        model_name: Name of the model
        dataset_name: Name of the dataset
        num_passes: Number of passes to run
        verbose: Whether to show detailed progress
    """
    if num_passes == 0:
        print("No passes to run.")
        return
    
    # Load items from dataset
    items = get_dataset(dataset_name)
    print(f"Loaded {len(items)} items from dataset '{dataset_name}'.")
    
    # Load existing history for this dataset
    match_history = load_model_history(model_name, dataset_name)
    initial_passes = count_passes(match_history, len(items))
    
    print(f"\nRunning {num_passes} pass{'es' if num_passes != 1 else ''} on model '{model_name}'...")
    
    for pass_num in range(1, num_passes + 1):
        current_pass = initial_passes + pass_num
        print(f"\nPass {pass_num}/{num_passes} (overall pass #{int(current_pass)}):")
        
        # Get existing pairs
        existing_pairs = get_existing_pairs(match_history)
        
        # Generate new pairings
        pairings, unpaired = generate_pass_pairings(items, existing_pairs)
        
        if not pairings:
            print("  No new unique pairings could be generated!")
            if unpaired:
                print(f"  {len(unpaired)} items could not be paired.")
            break
        
        print(f"  Generated {len(pairings)} new pairings")
        if unpaired:
            print(f"  {len(unpaired)} items could not be paired")
        
        # Progress callback
        def show_progress(completed, total):
            if verbose or completed == total:
                print(f"\r  Running matches: {progress_bar(completed, total)}", end='')
                if completed == total:
                    print()  # New line at completion
        
        # Run matches
        results = run_matches_parallel(pairings, model_name, progress_callback=show_progress, 
                                     use_defaults=use_defaults, temperature=temperature, top_p=top_p, top_k=top_k)
        
        # Add results to history
        match_history.extend(results)
        
        # Save after each pass
        save_model_history(model_name, dataset_name, match_history)
        
        # Show pass statistics
        pass_stats = {"converged": 0, "draw": 0, "invalid": 0}
        for result in results:
            pass_stats[result["status"]] = pass_stats.get(result["status"], 0) + 1
        
        print(f"  Pass complete: {pass_stats['converged']} converged, "
              f"{pass_stats['draw']} draws, {pass_stats['invalid']} invalid")
    
    print(f"\nAll passes complete. Total matches in history: {len(match_history)}")

def display_ratings(model_name, dataset_name):
    """
    Loads match history and displays current Elo ratings for a dataset.
    
    Args:
        model_name: Name of the model
        dataset_name: Name of the dataset
    """
    # Load history for this dataset
    match_history = load_model_history(model_name, dataset_name)
    
    if not match_history:
        print(f"No match history found for model '{model_name}' on dataset '{dataset_name}'.")
        return
    
    # Load items to get total count
    items = get_dataset(dataset_name)
    passes = count_passes(match_history, len(items))
    
    # Calculate ratings
    ratings_data = calculate_elo_ratings(match_history)
    
    # Analyze structure
    analysis = analyze_preference_structure(match_history, ratings_data["ratings"])
    
    # Generate and display report
    print(f"\nElo Ratings for {model_name} ({passes:.1f} passes, {len(match_history)} matches)")
    print(generate_elo_report(ratings_data, analysis))

def main():
    """
    Main CLI entry point.
    """
    parser = argparse.ArgumentParser(
        description="Run Elo rating tests on language models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument("model", help="Model name (e.g., gpt-4, claude-3-opus)")
    parser.add_argument("--dataset", required=True,
                       help="Dataset to use (e.g., emojis, common_words)")
    parser.add_argument("--passes", type=int, help="Number of passes to run")
    parser.add_argument("--show-ratings", action="store_true", 
                       help="Display current ratings and exit")
    parser.add_argument("--verbose", action="store_true",
                       help="Show detailed progress")
    parser.add_argument("--default-params", action="store_true",
                       help="Use model's default temperature and top_p instead of 0")
    parser.add_argument("--temperature", type=float,
                       help="Set temperature (when set, top_p uses model default)")
    parser.add_argument("--top-p", type=float, dest="top_p",
                       help="Set top_p (when set alone, temperature uses model default)")
    parser.add_argument("--top-k", type=int, dest="top_k",
                       help="Set top_k (when set, temperature and top_p use model defaults)")
    
    args = parser.parse_args()
    
    # Validate dataset
    try:
        items = get_dataset(args.dataset)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    
    # Just show ratings if requested
    if args.show_ratings:
        display_ratings(args.model, args.dataset)
        return
    
    # Determine number of passes
    if args.passes is not None:
        num_passes = args.passes
    else:
        # Interactive mode
        match_history = load_model_history(args.model, args.dataset)
        existing_passes = count_passes(match_history, len(items))
        num_passes = interactive_prompt(args.model, existing_passes)
    
    # Run passes
    if num_passes > 0:
        run_passes(args.model, args.dataset, num_passes, args.verbose, args.default_params, args.temperature, args.top_p, args.top_k)
        
        # Show final ratings
        print("\n" + "="*60)
        display_ratings(args.model, args.dataset)

if __name__ == "__main__":
    main()