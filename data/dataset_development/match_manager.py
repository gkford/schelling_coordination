"""
Match generation and processing functions.
"""

import json
import random
import asyncio
import os
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from llm_utils import make_single_llm_call, validate_choice
from elo_constants import STATUS_CONVERGED, STATUS_DRAW, STATUS_INVALID, BATCH_SIZE
from elo_calculator import calculate_elo_ratings, generate_markdown_report

def get_match_filepath(model_name, dataset_name):
    """
    Returns path to model's match history JSON for a specific dataset.
    
    Args:
        model_name: Name of the model
        dataset_name: Name of the dataset
        
    Returns:
        Path: Path object for the match file
    """
    # Sanitize names for filesystem
    safe_model = model_name.replace("/", "-").replace(":", "-")
    safe_dataset = dataset_name.replace("/", "-").replace(":", "-")
    return Path(__file__).parent / "matches" / safe_dataset / f"{safe_model}.json"

def load_model_history(model_name, dataset_name):
    """
    Loads match history for a specific model and dataset.
    Creates empty history if file doesn't exist.
    
    Args:
        model_name: Name of the model
        dataset_name: Name of the dataset
        
    Returns:
        list: Match history (empty list if new model/dataset)
    """
    filepath = get_match_filepath(model_name, dataset_name)
    
    if filepath.exists():
        with open(filepath, 'r') as f:
            data = json.load(f)
            return data.get(model_name, [])
    
    return []

def save_model_history(model_name, dataset_name, match_history):
    """
    Saves complete match history for a model and dataset.
    Creates dataset directory under matches/ if needed.
    Also generates a markdown report of current rankings.
    
    Args:
        model_name: Name of the model
        dataset_name: Name of the dataset
        match_history: List of match results
    """
    filepath = get_match_filepath(model_name, dataset_name)
    
    # Ensure directory exists (including dataset subdirectory)
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Save data with proper emoji encoding
    data = {model_name: match_history}
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # Generate and save markdown report
    if match_history:
        # Calculate current ratings
        ratings_data = calculate_elo_ratings(match_history)
        
        # Generate markdown report
        markdown_report = generate_markdown_report(match_history, ratings_data, model_name)
        
        # Save markdown file
        markdown_path = filepath.with_suffix('.md')
        with open(markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_report)

def get_existing_pairs(match_history):
    """
    Extracts set of already-run pairs from match history.
    
    Args:
        match_history: List of match results
        
    Returns:
        set: {("item1", "item2"), ...} Tuples are always sorted
    """
    existing_pairs = set()
    
    for match in match_history:
        pair = match.get("pair", [])
        if len(pair) == 2:
            # Ensure consistent ordering
            sorted_pair = tuple(sorted(pair))
            existing_pairs.add(sorted_pair)
    
    return existing_pairs

def generate_pass_pairings(items, existing_pairs):
    """
    Generates one new pairing for each item, ensuring uniqueness.
    
    Args:
        items: List of all items
        existing_pairs: Set of already-run pairs
        
    Returns:
        tuple: (pairings: list of tuples, unpaired_items: list)
    """
    pairings = []
    unpaired_items = []
    local_existing = existing_pairs.copy()  # Don't modify the original
    
    # Shuffle items to ensure variety across passes
    shuffled_items = items.copy()
    random.shuffle(shuffled_items)
    
    for item in shuffled_items:
        # Create candidate pool (all items except self)
        candidates = [x for x in items if x != item]
        random.shuffle(candidates)  # Randomize candidate order
        
        paired = False
        for candidate in candidates:
            # Create sorted pair
            sorted_pair = tuple(sorted([item, candidate]))
            
            # Check if this pair has been used
            if sorted_pair not in local_existing:
                pairings.append(sorted_pair)
                local_existing.add(sorted_pair)
                paired = True
                break
        
        if not paired:
            unpaired_items.append(item)
    
    return pairings, unpaired_items

def run_single_match(item1, item2, model, use_defaults=False, temperature=None, top_p=None, top_k=None):
    """
    Runs both orderings of a match and determines outcome.
    
    Args:
        item1: First item
        item2: Second item
        model: Model name
        
    Returns:
        dict: Match result with status, winner, responses, etc.
    """
    # Ensure consistent ordering for storage
    sorted_pair = sorted([item1, item2])
    
    try:
        # Run both orderings
        ab_response = make_single_llm_call(item1, item2, model, use_defaults, temperature, top_p, top_k)
        ba_response = make_single_llm_call(item2, item1, model, use_defaults, temperature, top_p, top_k)
        
        # Validate responses
        ab_valid, ab_choice = validate_choice(ab_response, item1, item2)
        ba_valid, ba_choice = validate_choice(ba_response, item1, item2)
        
        # Determine outcome
        if not ab_valid or not ba_valid:
            status = STATUS_INVALID
            winner = None
        elif ab_choice == ba_choice:
            status = STATUS_CONVERGED
            winner = ab_choice
        else:
            status = STATUS_DRAW
            winner = None
        
        return {
            "pair": sorted_pair,
            "status": status,
            "winner": winner,
            "ab_response": ab_response,
            "ba_response": ba_response,
            "ab_choice": ab_choice,
            "ba_choice": ba_choice,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # If LLM calls fail, mark as invalid
        return {
            "pair": sorted_pair,
            "status": STATUS_INVALID,
            "winner": None,
            "ab_response": None,
            "ba_response": None,
            "ab_choice": None,
            "ba_choice": None,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def run_matches_parallel(pairings, model, batch_size=BATCH_SIZE, progress_callback=None, use_defaults=False, temperature=None, top_p=None, top_k=None):
    """
    Runs matches in parallel batches.
    
    Args:
        pairings: List of (item1, item2) tuples to run
        model: Model name
        batch_size: Number of matches to run in parallel
        progress_callback: Optional function to call with progress updates
        
    Returns:
        list: Match results
    """
    results = []
    total_matches = len(pairings)
    completed = 0
    
    with ThreadPoolExecutor(max_workers=batch_size) as executor:
        # Submit all tasks
        future_to_pair = {}
        for pair in pairings:
            future = executor.submit(run_single_match, pair[0], pair[1], model, use_defaults, temperature, top_p, top_k)
            future_to_pair[future] = pair
        
        # Process completed tasks
        for future in as_completed(future_to_pair):
            pair = future_to_pair[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                # Handle unexpected errors
                results.append({
                    "pair": sorted(pair),
                    "status": STATUS_INVALID,
                    "winner": None,
                    "error": f"Unexpected error: {str(e)}",
                    "timestamp": datetime.now().isoformat()
                })
            
            completed += 1
            if progress_callback:
                progress_callback(completed, total_matches)
    
    return results

def count_passes(match_history, num_items):
    """
    Counts how many complete passes have been run.
    A pass means each item has been paired once.
    
    Args:
        match_history: List of match results
        num_items: Total number of items
        
    Returns:
        float: Number of passes (can be fractional if incomplete)
    """
    if num_items == 0:
        return 0.0
    
    # Count how many times each item appears
    item_counts = {}
    for match in match_history:
        pair = match.get("pair", [])
        for item in pair:
            item_counts[item] = item_counts.get(item, 0) + 1
    
    if not item_counts:
        return 0.0
    
    # The minimum count represents complete passes
    min_count = min(item_counts.values())
    return min_count

if __name__ == "__main__":
    # Test functions
    print("Testing match manager functions...")
    
    # Test pair generation
    items = ["A", "B", "C", "D", "E"]
    existing = {("A", "B"), ("C", "D")}
    
    print(f"\nItems: {items}")
    print(f"Existing pairs: {existing}")
    
    pairings, unpaired = generate_pass_pairings(items, existing)
    print(f"New pairings: {pairings}")
    print(f"Unpaired items: {unpaired}")
    
    # Test file operations
    test_model = "test-model"
    test_history = [
        {"pair": ["A", "B"], "status": "converged", "winner": "A"},
        {"pair": ["C", "D"], "status": "draw", "winner": None}
    ]
    
    print(f"\nTesting file operations for model: {test_model}")
    save_model_history(test_model, test_history)
    loaded = load_model_history(test_model)
    print(f"Saved and loaded successfully: {loaded == test_history}")
    
    # Clean up test file
    filepath = get_match_filepath(test_model)
    if filepath.exists():
        filepath.unlink()
        print("Test file cleaned up")