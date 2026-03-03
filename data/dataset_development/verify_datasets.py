#!/usr/bin/env python3
import json
from pathlib import Path

def get_codepoint_tuple(item):
    """Get tuple of codepoints for all characters for proper comparison."""
    return tuple(ord(c) for c in item)

def verify_dataset(filepath):
    """Verify that all pairs in a dataset are properly ordered and unique."""
    print(f"\n{'='*60}")
    print(f"Verifying: {filepath}")
    print(f"{'='*60}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    dataset_id = data.get('dataset_id', 'Unknown')
    pairs = data['pairs']
    selected_items = data.get('selected_items', [])
    
    print(f"Dataset ID: {dataset_id}")
    print(f"Number of items: {len(selected_items)}")
    print(f"Number of pairs: {len(pairs)}")
    print(f"Expected pairs for {len(selected_items)} items: {len(selected_items) * (len(selected_items) - 1) // 2}")
    
    # Check for uniqueness
    pair_set = set()
    duplicates = []
    
    # Check ordering and collect issues
    ordering_issues = []
    
    for i, pair in enumerate(pairs):
        option_a = pair['option_A']
        option_b = pair['option_B']
        pair_tuple = (option_a, option_b)
        
        # Check uniqueness
        if pair_tuple in pair_set:
            duplicates.append((i, pair_tuple))
        pair_set.add(pair_tuple)
        
        # Check codepoint ordering (full string comparison)
        codepoint_tuple_a = get_codepoint_tuple(option_a)
        codepoint_tuple_b = get_codepoint_tuple(option_b)
        
        if codepoint_tuple_a >= codepoint_tuple_b:
            ordering_issues.append({
                'pair_id': pair['pair_id'],
                'index': i,
                'option_A': option_a,
                'option_B': option_b,
                'codepoint_A': codepoint_tuple_a,
                'codepoint_B': codepoint_tuple_b
            })
    
    # Report results
    print(f"\n✓ Uniqueness Check:")
    if duplicates:
        print(f"  ✗ Found {len(duplicates)} duplicate pairs:")
        for idx, pair in duplicates[:5]:  # Show first 5
            print(f"    - Index {idx}: {pair}")
    else:
        print(f"  ✓ All {len(pairs)} pairs are unique")
    
    print(f"\n✓ Codepoint Ordering Check:")
    if ordering_issues:
        print(f"  ✗ Found {len(ordering_issues)} ordering issues:")
        for issue in ordering_issues[:5]:  # Show first 5
            print(f"    - Pair {issue['pair_id']} (index {issue['index']}): ")
            print(f"      '{issue['option_A']}' {issue['codepoint_A']} >= '{issue['option_B']}' {issue['codepoint_B']}")
    else:
        print(f"  ✓ All pairs correctly ordered (option_A codepoint < option_B codepoint)")
    
    # Show sample of items with their codepoints
    if selected_items:
        print(f"\n✓ Sample of selected items with codepoints:")
        for item in selected_items[:10]:
            codepoints = get_codepoint_tuple(item)
            if len(item) == 1:
                print(f"  - '{item}': U+{codepoints[0]:04X} ({codepoints[0]})")
            else:
                hex_codes = ' '.join(f"U+{cp:04X}" for cp in codepoints)
                print(f"  - '{item}': {hex_codes}")
    
    # Overall verdict
    print(f"\n{'='*60}")
    if not duplicates and not ordering_issues:
        print(f"✅ DATASET VALID: All checks passed!")
    else:
        print(f"❌ DATASET INVALID: Found {len(duplicates)} duplicates and {len(ordering_issues)} ordering issues")
    print(f"{'='*60}")
    
    return len(duplicates) == 0 and len(ordering_issues) == 0

def main():
    """Verify both generated datasets."""
    datasets = [
        "data/random_emoji.json",
        "data/random_mix.json"
    ]
    
    all_valid = True
    for dataset_path in datasets:
        if Path(dataset_path).exists():
            valid = verify_dataset(dataset_path)
            all_valid = all_valid and valid
        else:
            print(f"\n⚠️  Dataset not found: {dataset_path}")
            all_valid = False
    
    print(f"\n{'='*60}")
    if all_valid:
        print("✅ ALL DATASETS VALID")
    else:
        print("❌ VALIDATION ISSUES FOUND")
    print(f"{'='*60}\n")
    
    return all_valid

if __name__ == "__main__":
    main()