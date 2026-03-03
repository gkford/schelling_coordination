#!/usr/bin/env python3
import json
import random
from pathlib import Path
import sys
sys.path.append('.')
from verify_datasets import verify_dataset
from common_emojis import COMMON_EMOJIS

def get_english_words():
    """Get a list of common English words."""
    # Using a curated list of common words
    words = [
        "time", "person", "year", "way", "day", "thing", "man", "world", "life", "hand",
        "part", "child", "eye", "woman", "place", "work", "week", "case", "point", "group",
        "problem", "fact", "number", "system", "program", "question", "student", "book", "house", "country",
        "company", "month", "lot", "right", "study", "family", "government", "night", "home", "water",
        "room", "mother", "area", "money", "story", "month", "business", "program", "moment", "air"
    ]
    return words

def get_math_logic_symbols():
    """Get mathematical and logical symbols."""
    symbols = [
        "∀", "∃", "∈", "∉", "⊂", "⊃", "⊆", "⊇", "∪", "∩",
        "∅", "∧", "∨", "¬", "→", "↔", "⇒", "⇔", "≡", "≠",
        "≤", "≥", "≈", "∝", "∞", "∑", "∏", "∫", "∂", "∇",
        "±", "×", "÷", "√", "∛", "⊕", "⊗", "⊥", "∥", "∠"
    ]
    return symbols

def get_kanji():
    """Get common kanji characters."""
    kanji = [
        "日", "月", "火", "水", "木", "金", "土", "人", "本", "中",
        "大", "小", "上", "下", "左", "右", "前", "後", "内", "外",
        "東", "西", "南", "北", "春", "夏", "秋", "冬", "朝", "昼",
        "夜", "時", "分", "今", "先", "来", "行", "見", "聞", "話",
        "読", "書", "食", "飲", "買", "売", "作", "使", "始", "終",
        "会", "社", "学", "校", "国", "家", "市", "町", "村", "山"
    ]
    return kanji

def get_emojis():
    """Get common emojis from standard emoji keyboards."""
    return COMMON_EMOJIS

def get_codepoint_key(item):
    """Get a tuple of codepoints for all characters for proper ordering."""
    return tuple(ord(c) for c in item)

def generate_random_mix_dataset(seed=0):
    """Generate dataset with mixed items (words, symbols, kanji, emojis)."""
    random.seed(seed)
    
    # Get all item pools
    words = get_english_words()
    symbols = get_math_logic_symbols()
    kanji = get_kanji()
    emojis = get_emojis()
    
    # Select approximately 1/4 of 29 from each category
    # 29 / 4 ≈ 7.25, so we'll do 7, 7, 7, 8
    selected_items = []
    selected_items.extend(random.sample(words, 7))
    selected_items.extend(random.sample(symbols, 7))
    selected_items.extend(random.sample(kanji, 7))
    selected_items.extend(random.sample(emojis, 8))
    
    # Sort by full codepoint sequence for consistent ordering
    selected_items.sort(key=get_codepoint_key)
    
    # Generate all pairs where option_A has HIGHER codepoint than option_B
    # Compare full strings character by character
    pairs = []
    pair_id = 1
    
    for i in range(len(selected_items)):
        for j in range(i + 1, len(selected_items)):
            # Items are already sorted, so swap to make option_A > option_B
            pairs.append({
                "pair_id": f"{pair_id:03d}",
                "option_A": selected_items[j],  # Higher codepoint (alphabetically later)
                "option_B": selected_items[i]   # Lower codepoint (alphabetically earlier)
            })
            pair_id += 1
    
    # Create dataset
    dataset = {
        "dataset_id": "random_mixed_types",
        "description": f"29 randomly selected items (7 English words, 7 mathematical/logical symbols, 7 kanji, 8 emojis) paired where option_A has higher codepoint than option_B. Generated with seed={seed}.",
        "seed": seed,
        "methodology": "Items randomly selected from four categories: English words, mathematical/logical symbols, kanji characters, and emojis. Paired in all possible combinations with consistent ordering.",
        "composition": {
            "english_words": 7,
            "math_logic_symbols": 7,
            "kanji": 7,
            "emojis": 8
        },
        "selected_items": selected_items,
        "pairs": pairs
    }
    
    return dataset

def main():
    # Generate dataset with seed 0
    dataset = generate_random_mix_dataset(seed=0)
    
    # Save to data folder
    output_path = Path("data/random_mixed_types.json")
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"Generated {len(dataset['pairs'])} pairs from {len(dataset['selected_items'])} items")
    print(f"Saved to {output_path}")
    print(f"Selected items: {', '.join(dataset['selected_items'])}")
    
    # Verify the dataset
    print("\nVerifying dataset...")
    verify_dataset(output_path)

if __name__ == "__main__":
    main()