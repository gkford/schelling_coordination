#!/usr/bin/env python3
"""
Verify that datasets have been correctly swapped so that:
- option_B always has lower codepoint than option_A
- all pairs are unique
"""

import json
from pathlib import Path

def get_codepoint_tuple(item):
    """Get a tuple of codepoints for all characters (for multi-char strings like words)."""
    return tuple(ord(c) for c in item)

def verify_swapped_dataset(dataset_path):
    """Verify a dataset has correct swapped ordering and uniqueness."""
    print(f"\n{'='*60}")
    print(f"Verifying: {dataset_path}")
    print(f"{'='*60}")
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    pairs = data['pairs']
    selected_items = data.get('selected_items', [])
    
    print(f"Dataset ID: {data.get('dataset_id', 'unknown')}")
    print(f"Number of items: {len(selected_items)}")
    print(f"Number of pairs: {len(pairs)}")
    print(f"Expected pairs for {len(selected_items)} items: {len(selected_items) * (len(selected_items) - 1) // 2}")
    
    # Check uniqueness
    pair_set = set()
    for pair in pairs:
        pair_tuple = (pair['option_A'], pair['option_B'])
        if pair_tuple in pair_set:
            print(f"✗ Duplicate pair found: {pair}")
            return False
        pair_set.add(pair_tuple)
    
    print(f"\n✓ Uniqueness Check:")
    print(f"  ✓ All {len(pairs)} pairs are unique")
    
    # Check ordering (option_B should have LOWER codepoint than option_A)
    incorrect_pairs = []
    for pair in pairs:
        option_a = pair['option_A']
        option_b = pair['option_B']
        
        # Get codepoint tuples for comparison
        codepoint_a = get_codepoint_tuple(option_a)
        codepoint_b = get_codepoint_tuple(option_b)
        
        # option_B should be less than option_A
        if codepoint_b >= codepoint_a:
            incorrect_pairs.append({
                'pair_id': pair['pair_id'],
                'option_A': option_a,
                'option_B': option_b,
                'codepoint_A': codepoint_a,
                'codepoint_B': codepoint_b
            })
    
    if incorrect_pairs:
        print(f"\n✗ Codepoint Ordering Check:")
        print(f"  ✗ {len(incorrect_pairs)} pairs have incorrect ordering (option_B >= option_A):")
        for p in incorrect_pairs[:5]:  # Show first 5
            print(f"    Pair {p['pair_id']}: A='{p['option_A']}' {p['codepoint_A'][:3]}..., B='{p['option_B']}' {p['codepoint_B'][:3]}...")
        if len(incorrect_pairs) > 5:
            print(f"    ... and {len(incorrect_pairs) - 5} more")
        return False
    else:
        print(f"\n✓ Codepoint Ordering Check:")
        print(f"  ✓ All pairs correctly ordered (option_B codepoint < option_A codepoint)")
    
    # Show sample of items with codepoints
    if selected_items:
        print(f"\n✓ Sample of selected items with codepoints:")
        for item in selected_items[:10]:
            if len(item) == 1:
                print(f"  - '{item}': U+{ord(item):04X} ({ord(item)})")
            else:
                # For multi-char strings, show first few codepoints
                codepoints = ' '.join([f"U+{ord(c):04X}" for c in item[:3]])
                if len(item) > 3:
                    codepoints += "..."
                print(f"  - '{item}': {codepoints}")
    
    print(f"\n{'='*60}")
    print(f"✅ DATASET VALID: All checks passed!")
    print(f"{'='*60}")
    return True

def main():
    # Verify both datasets
    datasets = [
        "data/random_emoji.json",
        "data/random_mixed_types.json"
    ]
    
    all_valid = True
    for dataset_path in datasets:
        if Path(dataset_path).exists():
            if not verify_swapped_dataset(dataset_path):
                all_valid = False
        else:
            print(f"\n❌ Dataset not found: {dataset_path}")
            all_valid = False
    
    if all_valid:
        print("\n✅ All datasets have correct swapped ordering!")
    else:
        print("\n❌ Some datasets have issues. Please check the errors above.")

if __name__ == "__main__":
    main()