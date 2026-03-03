#!/usr/bin/env python3
"""
Test the dual categorization system with COT and conditional prompting.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from strategy_investigation.categorize_strategies_csv import (
    build_dynamic_prompt,
    parse_categorization_response,
    categorize_strategy,
    is_important_disagreement
)

def test_prompt_generation():
    """Test the conditional prompt generation."""
    print("="*80)
    print("TEST 1: Strategy contains pair word (choose_wonder)")
    print("="*80)

    strategy = "choose_wonder"
    pair_words = ("wonder", "dread")

    prompt = build_dynamic_prompt(strategy, pair_words)
    print(prompt)
    print()

    print("="*80)
    print("TEST 2: Strategy does NOT contain pair word (choose_longer)")
    print("="*80)

    strategy = "choose_longer"
    pair_words = ("peace", "war")

    prompt = build_dynamic_prompt(strategy, pair_words)
    print(prompt)
    print()

    print("="*80)
    print("TEST 3: Strategy contains word + strategy (choose_wonder_by_length)")
    print("="*80)

    strategy = "choose_wonder_by_length"
    pair_words = ("wonder", "dread")

    prompt = build_dynamic_prompt(strategy, pair_words)
    print(prompt)
    print()


def test_parser():
    """Test the response parser with various COT scenarios."""
    print("="*80)
    print("TEST 4: Parse responses (handles COT by taking LAST occurrence)")
    print("="*80)

    test_responses = [
        # Test 1: Simple response with curly braces
        (
            "After thinking about this, I believe this is a length-based strategy.\n{Category: Length, Subcategory: longer}",
            "Length", "longer"
        ),
        # Test 2: COT mentions category in reasoning, final answer at end
        (
            "Let me think... this could be Category: Salience but actually looking closer, it's just naming a word.\n{Category: Failures, Subcategory: specified_word}",
            "Failures", "specified_word"
        ),
        # Test 3: Multiple curly brace occurrences (should take LAST)
        (
            "Initially I thought {Category: Length, Subcategory: shorter} but reconsidering, this is actually {Category: Lexicographic, Subcategory: ascending}",
            "Lexicographic", "ascending"
        ),
        # Test 4: Old format without COT
        (
            "Category: Lexicographic\nSubcategory: ascending",
            "Lexicographic", "ascending"
        ),
        # Test 5: Old format WITH COT (mentions category in reasoning)
        (
            "This might be Category: Length or maybe Category: Frequency, but I think it's actually:\nCategory: Positional\nSubcategory: first",
            "Positional", "first"
        ),
        # Test 6: No COT, just curly braces
        (
            "{Category: Random, Subcategory: none}",
            "Random", "none"
        ),
    ]

    for i, (response, expected_cat, expected_subcat) in enumerate(test_responses, 1):
        category, subcategory = parse_categorization_response(response)
        match = category == expected_cat and subcategory == expected_subcat
        status = "✓" if match else "✗"

        print(f"\nTest {i}: {status}")
        print(f"  Input: {response[:100]}...")
        print(f"  Expected: Category={expected_cat}, Subcategory={expected_subcat}")
        print(f"  Parsed:   Category={category}, Subcategory={subcategory}")

        if not match:
            print(f"  ⚠️  MISMATCH!")


def test_disagreement_checker():
    """Test the disagreement importance checker."""
    print("="*80)
    print("TEST 5: Disagreement importance checker")
    print("="*80)

    test_cases = [
        # (cat1, subcat1, cat2, subcat2, expected_important, description)
        ("Length", "longer", "Length", "longer", False, "Complete agreement"),
        ("Length", "longer", "Frequency", "common", True, "Category disagreement"),
        ("Length", "longer", "Length", "shorter", True, "Important subcategory disagreement (Length)"),
        ("Salience", "positive", "Salience", "negative", True, "Important subcategory disagreement (Salience)"),
        ("Other_Semantic", "abstract", "Other_Semantic", "concrete", False, "Minor subcategory disagreement (Other_Semantic)"),
        ("Failures", "specified_word", "Failures", "meta-awareness", False, "Minor subcategory disagreement (Failures)"),
        ("Other_Non-semantic", "other", "Other_Non-semantic", "ambiguous", False, "Minor subcategory disagreement (Other_Non-semantic)"),
    ]

    for cat1, subcat1, cat2, subcat2, expected_important, description in test_cases:
        is_important, reason = is_important_disagreement(cat1, subcat1, cat2, subcat2)
        match = is_important == expected_important
        status = "✓" if match else "✗"

        print(f"\n{status} {description}")
        print(f"  Input: ({cat1}, {subcat1}) vs ({cat2}, {subcat2})")
        print(f"  Expected important: {expected_important}, Got: {is_important}")
        print(f"  Reason: {reason}")

        if not match:
            print(f"  ⚠️  MISMATCH!")

    print()


def test_live_categorization():
    """Test actual dual categorization with Sonnet 4.5 independent tiebreaker (requires API keys)."""
    print("="*80)
    print("TEST 6: Live dual categorization (Kimi K2 + GPT OSS 120B + Sonnet 4.5)")
    print("="*80)

    # Test case 1: Bare word selection
    print("\nCategorizing: choose_wonder (wonder vs dread)")
    category, subcategory, source, disagreement = categorize_strategy("choose_wonder", ("wonder", "dread"))
    print(f"Result: {category}, {subcategory} (source: {source})")
    if disagreement:
        print(f"Disagreement: {disagreement}")
    print(f"Expected: Failures, specified_word")
    print(f"Match: {'✓' if category == 'Failures' and subcategory == 'specified_word' else '✗'}")

    # Test case 2: Word + explicit strategy
    print("\nCategorizing: choose_wonder_by_length (wonder vs dread)")
    category, subcategory, source, disagreement = categorize_strategy("choose_wonder_by_length", ("wonder", "dread"))
    print(f"Result: {category}, {subcategory} (source: {source})")
    if disagreement:
        print(f"Disagreement: {disagreement}")
    print(f"Expected: Length, (longer or ambiguous)")
    print(f"Match: {'✓' if category == 'Length' else '✗'}")

    # Test case 3: No pair word in strategy
    print("\nCategorizing: choose_alphabetically_first (peace vs war)")
    category, subcategory, source, disagreement = categorize_strategy("choose_alphabetically_first", ("peace", "war"))
    print(f"Result: {category}, {subcategory} (source: {source})")
    if disagreement:
        print(f"Disagreement: {disagreement}")
    print(f"Expected: Lexicographic, ascending")
    print(f"Match: {'✓' if category == 'Lexicographic' and subcategory == 'ascending' else '✗'}")


if __name__ == "__main__":
    import sys

    # Run prompt generation tests
    test_prompt_generation()

    # Run parser tests
    test_parser()

    # Run disagreement checker tests
    test_disagreement_checker()

    # Ask user if they want to run live tests (requires API)
    print("="*80)
    if sys.stdin.isatty():
        # Interactive mode - ask user
        response = input("Run live dual categorization tests? (requires API keys) (y/n): ")
        if response.lower() == 'y':
            test_live_categorization()
        else:
            print("Skipping live tests.")
    else:
        # Non-interactive mode - skip live tests
        print("Non-interactive mode detected. Skipping live tests.")
