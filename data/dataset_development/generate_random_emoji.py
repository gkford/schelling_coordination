#!/usr/bin/env python3
import json
import random
from pathlib import Path
import sys
sys.path.append('.')
from verify_datasets import verify_dataset
from common_emojis import COMMON_EMOJIS

def get_all_emojis():
    """Get ALL emojis from the complete Unicode emoji ranges - no curation."""
    emojis = []
    
    # COMPLETE Unicode emoji ranges - this is exhaustive, not curated
    ranges = [
        # Basic Latin supplement symbols that are emojis
        (0x00A9, 0x00A9),    # ©
        (0x00AE, 0x00AE),    # ®
        (0x203C, 0x203C),    # ‼
        (0x2049, 0x2049),    # ⁉
        (0x2122, 0x2122),    # ™
        (0x2139, 0x2139),    # ℹ
        (0x2194, 0x2199),    # Arrows
        (0x21A9, 0x21AA),    # More arrows
        (0x231A, 0x231B),    # ⌚ ⌛
        (0x2328, 0x2328),    # ⌨
        (0x23CF, 0x23CF),    # ⏏
        (0x23E9, 0x23F3),    # Media symbols
        (0x23F8, 0x23FA),    # More media symbols
        (0x24C2, 0x24C2),    # Ⓜ
        (0x25AA, 0x25AB),    # ▪ ▫
        (0x25B6, 0x25B6),    # ▶
        (0x25C0, 0x25C0),    # ◀
        (0x25FB, 0x25FE),    # Squares
        (0x2600, 0x27FF),    # Miscellaneous Symbols, Dingbats (large range)
        (0x2900, 0x297F),    # Supplemental Arrows-B
        (0x2B00, 0x2BFF),    # Miscellaneous Symbols and Arrows
        (0x3030, 0x3030),    # 〰
        (0x303D, 0x303D),    # 〽
        (0x3297, 0x3297),    # ㊗
        (0x3299, 0x3299),    # ㊙
        
        # Main emoji blocks
        (0x1F000, 0x1F02F),  # Mahjong Tiles
        (0x1F030, 0x1F09F),  # Domino Tiles
        (0x1F0A0, 0x1F0FF),  # Playing Cards
        (0x1F100, 0x1F1FF),  # Enclosed Alphanumeric Supplement
        (0x1F200, 0x1F2FF),  # Enclosed Ideographic Supplement
        (0x1F300, 0x1F5FF),  # Miscellaneous Symbols and Pictographs
        (0x1F600, 0x1F64F),  # Emoticons
        (0x1F650, 0x1F67F),  # Ornamental Dingbats
        (0x1F680, 0x1F6FF),  # Transport and Map Symbols
        (0x1F700, 0x1F77F),  # Alchemical Symbols
        (0x1F780, 0x1F7FF),  # Geometric Shapes Extended
        (0x1F800, 0x1F8FF),  # Supplemental Arrows-C
        (0x1F900, 0x1F9FF),  # Supplemental Symbols and Pictographs
        (0x1FA00, 0x1FA6F),  # Chess Symbols
        (0x1FA70, 0x1FAFF),  # Symbols and Pictographs Extended-A
        (0x1FB00, 0x1FBFF),  # Symbols for Legacy Computing
        
        # Emoji modifiers and components (these combine with other emojis)
        (0x1F1E6, 0x1F1FF),  # Regional indicator symbols
        (0x1F3FB, 0x1F3FF),  # Skin tone modifiers
        (0xE0020, 0xE007F),  # Tag characters
        
        # Additional emoji in other blocks
        (0x2000B, 0x2000B),  # 𠀋
        (0x20020, 0x20020),  # 𠀠
    ]
    
    for start, end in ranges:
        for codepoint in range(start, end + 1):
            try:
                char = chr(codepoint)
                # No curation - include everything that's a valid character
                if len(char) > 0:
                    emojis.append(char)
            except:
                continue
    
    # Remove duplicates while preserving order
    seen = set()
    unique_emojis = []
    for emoji in emojis:
        if emoji not in seen:
            seen.add(emoji)
            unique_emojis.append(emoji)
    
    return unique_emojis

def generate_random_emoji_dataset(seed=0):
    """Generate dataset with 29 random emojis paired in all combinations."""
    random.seed(seed)
    
    # Use common emojis and select 29 randomly
    selected_emojis = random.sample(COMMON_EMOJIS, 29)
    
    # Sort by codepoint
    selected_emojis.sort(key=lambda x: ord(x))
    
    # Generate all pairs where option_A has HIGHER codepoint than option_B
    pairs = []
    pair_id = 1
    
    for i in range(len(selected_emojis)):
        for j in range(i + 1, len(selected_emojis)):
            # Swap so option_A has higher codepoint than option_B
            pairs.append({
                "pair_id": f"{pair_id:03d}",
                "option_A": selected_emojis[j],  # Higher codepoint
                "option_B": selected_emojis[i]   # Lower codepoint
            })
            pair_id += 1
    
    # Create dataset
    dataset = {
        "dataset_id": "random_emoji",
        "description": f"29 randomly selected emojis paired in all combinations (406 pairs total). Generated with seed={seed}.",
        "seed": seed,
        "methodology": "29 emojis randomly selected from Unicode emoji ranges, then paired in all possible combinations with option_A having higher codepoint than option_B.",
        "selected_items": selected_emojis,
        "pairs": pairs
    }
    
    return dataset

def main():
    # Generate dataset with seed 0
    dataset = generate_random_emoji_dataset(seed=0)
    
    # Save to data folder
    output_path = Path("data/random_emoji.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"Generated {len(dataset['pairs'])} pairs from {len(dataset['selected_items'])} emojis")
    print(f"Saved to {output_path}")
    print(f"Selected emojis: {' '.join(dataset['selected_items'])}")
    
    # Verify the dataset
    print("\nVerifying dataset...")
    verify_dataset(output_path)

if __name__ == "__main__":
    main()