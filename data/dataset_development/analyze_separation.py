#!/usr/bin/env python3
"""
Analyze preference separation in Elo rankings.

This script finds the maximum threshold where complete separation exists between
preferred and non-preferred item categories for each model individually.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from elo_calculator import calculate_elo_ratings
from datasets import get_dataset

def analyze_model_separation(
    ratings: Dict[str, float],
    preferred_items: List[str],
    avoided_items: List[str],
    model_name: str
) -> Dict:
    """
    Analyze how far we can go before separation breaks for a single model.
    
    Args:
        ratings: Item -> Elo rating mapping
        preferred_items: Items expected to be preferred (higher ratings)
        avoided_items: Items expected to be avoided (lower ratings)
        model_name: Name of the model for display
        
    Returns:
        Dictionary with analysis results
    """
    # Get ratings for each category
    preferred_ratings = [(item, ratings.get(item, 1500)) for item in preferred_items]
    avoided_ratings = [(item, ratings.get(item, 1500)) for item in avoided_items]
    
    # Sort by rating
    preferred_sorted = sorted(preferred_ratings, key=lambda x: x[1], reverse=True)
    avoided_sorted = sorted(avoided_ratings, key=lambda x: x[1], reverse=True)
    
    # Find maximum N where separation holds
    max_n = 0
    breakdown_point = None
    
    for n in range(1, min(len(preferred_sorted), len(avoided_sorted)) + 1):
        # Get top N preferred and bottom N avoided
        top_preferred = preferred_sorted[:n]
        bottom_avoided = avoided_sorted[-n:]
        
        # Check if ALL top preferred are higher than ALL bottom avoided
        min_preferred = min(rating for _, rating in top_preferred)
        max_avoided = max(rating for _, rating in bottom_avoided)
        
        if min_preferred > max_avoided:
            max_n = n
        else:
            # Found the breakdown point
            breakdown_point = {
                'n': n,
                'min_preferred': min_preferred,
                'max_avoided': max_avoided,
                'overlap': max_avoided - min_preferred,
                'problem_preferred': [(item, rating) for item, rating in top_preferred if rating <= max_avoided],
                'problem_avoided': [(item, rating) for item, rating in bottom_avoided if rating >= min_preferred]
            }
            break
    
    return {
        'model_name': model_name,
        'max_separation_n': max_n,
        'breakdown_point': breakdown_point,
        'preferred_sorted': preferred_sorted,
        'avoided_sorted': avoided_sorted
    }

def analyze_dataset(dataset_name: str, dataset_type: str = "emoji") -> None:
    """
    Analyze separation for all models on a dataset.
    
    Args:
        dataset_name: Name of the dataset to analyze
        dataset_type: Type of dataset ("emoji" or "words")
    """
    print(f"\n{'='*80}")
    print(f"PREFERENCE SEPARATION ANALYSIS: {dataset_name}")
    print(f"{'='*80}")
    
    # Load dataset and determine categories
    try:
        dataset = get_dataset(dataset_name)
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Determine which items should be preferred vs avoided based on dataset
    if dataset_name == "salient_alphabetical_mixed":
        # Words: salient (N-Z) should be preferred, mundane (A-M) should be avoided
        preferred_items = dataset[:50]  # Salient N-Z words
        avoided_items = dataset[50:]    # Mundane A-M words
        preferred_label = "Salient (N-Z)"
        avoided_label = "Mundane (A-M)"
    elif "emoji" in dataset_name:
        # Emojis: mundane should be preferred, salient should be avoided
        if dataset_name == "emoji_mixed":
            preferred_items = dataset[:25]  # Mundane
            avoided_items = dataset[25:]    # Salient
        elif dataset_name == "emoji_mixed_100":
            preferred_items = dataset[:50]  # Mundane
            avoided_items = dataset[50:]    # Salient
        else:
            print(f"Unknown emoji dataset structure: {dataset_name}")
            return
        preferred_label = "Mundane"
        avoided_label = "Salient/Negative"
    else:
        print(f"Unknown dataset type: {dataset_name}")
        return
    
    print(f"\nDataset structure:")
    print(f"  {preferred_label}: {len(preferred_items)} items (expected HIGHER)")
    print(f"  {avoided_label}: {len(avoided_items)} items (expected LOWER)")
    
    # Load match results for this dataset
    matches_dir = Path(f'matches/{dataset_name}')
    if not matches_dir.exists():
        print(f"\n❌ No match data found for {dataset_name}")
        print(f"   Run comparison first: uv run python run_comparison.py --dataset {dataset_name} --models all --passes 40")
        return
    
    # Analyze each model
    model_results = []
    
    for match_file in sorted(matches_dir.glob('*.json')):
        if match_file.suffix != '.json':
            continue
            
        with open(match_file, 'r') as f:
            data = json.load(f)
            model_name = list(data.keys())[0]
            match_history = data[model_name]
            
            if not match_history:
                continue
            
            # Calculate ratings
            ratings_data = calculate_elo_ratings(match_history)
            ratings = ratings_data['ratings']
            
            # Analyze separation
            analysis = analyze_model_separation(
                ratings, 
                preferred_items, 
                avoided_items,
                model_name
            )
            model_results.append(analysis)
    
    if not model_results:
        print("\n❌ No completed matches found")
        return
    
    # Display results
    print(f"\n📊 SEPARATION RESULTS")
    print("-" * 60)
    
    # Summary table
    print(f"\n| Model | Max Clean Separation | Breakdown Point |")
    print("|-------|---------------------|-----------------|")
    
    for result in model_results:
        model_short = result['model_name'].split('/')[-1][:25]
        max_n = result['max_separation_n']
        
        if result['breakdown_point']:
            breakdown = f"N={result['breakdown_point']['n']} (overlap: {result['breakdown_point']['overlap']:.0f})"
        else:
            breakdown = "No breakdown"
        
        print(f"| {model_short:25} | Top/Bottom {max_n:3} | {breakdown} |")
    
    # Find overall maximum clean separation
    overall_max = min(r['max_separation_n'] for r in model_results)
    print(f"\n✅ Maximum clean separation across ALL models: Top/Bottom {overall_max}")
    
    # Detailed breakdown for each model
    print(f"\n📋 DETAILED BREAKDOWN")
    print("-" * 60)
    
    for result in model_results:
        model_short = result['model_name'].split('/')[-1]
        print(f"\n{model_short}")
        print(f"  Clean separation up to: Top/Bottom {result['max_separation_n']}")
        
        if result['breakdown_point']:
            bp = result['breakdown_point']
            print(f"  Breakdown at N={bp['n']}:")
            print(f"    Lowest {preferred_label}: {bp['min_preferred']:.0f}")
            print(f"    Highest {avoided_label}: {bp['max_avoided']:.0f}")
            print(f"    Overlap: {bp['overlap']:.0f} points")
            
            if bp['problem_preferred']:
                print(f"    {preferred_label} items too low:")
                for item, rating in bp['problem_preferred'][:3]:
                    print(f"      {item}: {rating:.0f}")
                    
            if bp['problem_avoided']:
                print(f"    {avoided_label} items too high:")
                for item, rating in bp['problem_avoided'][:3]:
                    print(f"      {item}: {rating:.0f}")
    
    # Show items at the boundary
    print(f"\n🔍 ITEMS AT THE BOUNDARY (N={overall_max})")
    print("-" * 60)
    
    for result in model_results[:2]:  # Show first 2 models as examples
        model_short = result['model_name'].split('/')[-1][:25]
        print(f"\n{model_short}:")
        
        # Show items at the boundary
        n = overall_max
        top_n = result['preferred_sorted'][:n]
        bottom_n = result['avoided_sorted'][-n:]
        
        print(f"  {preferred_label} #{n} (boundary): {top_n[-1][0]} = {top_n[-1][1]:.0f}")
        print(f"  {avoided_label} #{n} (boundary): {bottom_n[0][0]} = {bottom_n[0][1]:.0f}")
        print(f"  Gap: {top_n[-1][1] - bottom_n[0][1]:.0f} points")

def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        # Analyze specific dataset
        dataset_name = sys.argv[1]
        analyze_dataset(dataset_name)
    else:
        # Analyze all emoji datasets and salient_alphabetical
        datasets_to_analyze = [
            "emoji_mixed",
            "emoji_mixed_100",
            "salient_alphabetical_mixed"
        ]
        
        for dataset_name in datasets_to_analyze:
            analyze_dataset(dataset_name)

if __name__ == "__main__":
    main()