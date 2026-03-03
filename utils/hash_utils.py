"""
Utilities for calculating dataset hashes.
"""
import hashlib
import json
from typing import List, Dict


def calculate_pairs_hash(pairs: List[Dict[str, str]]) -> str:
    """
    Calculate SHA-256 hash of pairs content.
    
    Only includes pair_id, option_A, and option_B fields.
    Excludes any metadata like dataset_id or description.
    
    Args:
        pairs: List of pair dictionaries
        
    Returns:
        SHA-256 hash as hexadecimal string
    """
    # Sort pairs by pair_id for consistency
    sorted_pairs = sorted(pairs, key=lambda p: p['pair_id'])
    
    # Extract only the fields we care about
    pairs_for_hash = []
    for pair in sorted_pairs:
        pairs_for_hash.append({
            'pair_id': pair['pair_id'],
            'option_A': pair['option_A'],
            'option_B': pair['option_B']
        })
    
    # Convert to JSON string with sorted keys for consistency
    pairs_json = json.dumps(pairs_for_hash, sort_keys=True, ensure_ascii=False)
    
    # Calculate SHA-256 hash
    hash_obj = hashlib.sha256(pairs_json.encode('utf-8'))
    return hash_obj.hexdigest()


def load_dataset_and_hash(dataset_path: str) -> tuple[dict, str]:
    """
    Load a dataset file and calculate its hash.
    
    Args:
        dataset_path: Path to the JSON dataset file
        
    Returns:
        Tuple of (dataset_dict, pairs_hash)
    """
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    pairs_hash = calculate_pairs_hash(dataset['pairs'])
    return dataset, pairs_hash