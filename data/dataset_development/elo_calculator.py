"""
Elo rating calculation and analysis functions.
"""

import math
from collections import defaultdict, Counter
from elo_constants import (
    BASE_RATING, 
    K_FACTOR, 
    RATING_SCALE,
    OUTCOME_WIN,
    OUTCOME_DRAW,
    OUTCOME_LOSS,
    STATUS_CONVERGED,
    STATUS_DRAW,
    STATUS_INVALID
)

def expected_score(rating_a, rating_b):
    """
    Calculate expected score for player A against player B.
    
    Args:
        rating_a: Elo rating of player A
        rating_b: Elo rating of player B
        
    Returns:
        float: Expected score (0 to 1)
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / RATING_SCALE))

def update_rating(old_rating, expected, actual, k_factor=K_FACTOR):
    """
    Update Elo rating based on match outcome.
    
    Args:
        old_rating: Current rating
        expected: Expected score (0 to 1)
        actual: Actual score (1 for win, 0.5 for draw, 0 for loss)
        k_factor: Maximum rating change
        
    Returns:
        float: New rating
    """
    return old_rating + k_factor * (actual - expected)

def calculate_elo_ratings(match_history):
    """
    Computes current Elo ratings from complete match history.
    
    Args:
        match_history: List of match results
        
    Returns:
        dict: Contains ratings and statistics
    """
    # Initialize ratings
    ratings = defaultdict(lambda: BASE_RATING)
    
    # Track statistics
    total_matches = 0
    valid_matches = 0
    invalid_matches = 0
    converged_matches = 0
    draw_matches = 0
    
    # Track all items that have participated
    all_items = set()
    
    # Process matches in chronological order
    for match in match_history:
        total_matches += 1
        
        pair = match.get("pair", [])
        if len(pair) != 2:
            invalid_matches += 1
            continue
            
        item1, item2 = pair
        all_items.add(item1)
        all_items.add(item2)
        
        status = match.get("status")
        
        if status == STATUS_INVALID:
            invalid_matches += 1
            continue
            
        valid_matches += 1
        
        # Get current ratings
        rating1 = ratings[item1]
        rating2 = ratings[item2]
        
        # Calculate expected scores
        expected1 = expected_score(rating1, rating2)
        expected2 = 1 - expected1
        
        # Determine actual scores
        if status == STATUS_CONVERGED:
            converged_matches += 1
            winner = match.get("winner")
            if winner == item1:
                actual1 = OUTCOME_WIN
                actual2 = OUTCOME_LOSS
            else:  # winner == item2
                actual1 = OUTCOME_LOSS
                actual2 = OUTCOME_WIN
        else:  # STATUS_DRAW
            draw_matches += 1
            actual1 = OUTCOME_DRAW
            actual2 = OUTCOME_DRAW
        
        # Update ratings
        ratings[item1] = update_rating(rating1, expected1, actual1)
        ratings[item2] = update_rating(rating2, expected2, actual2)
    
    # Convert defaultdict to regular dict with all items
    final_ratings = {}
    for item in all_items:
        final_ratings[item] = ratings[item]
    
    return {
        "ratings": final_ratings,
        "total_matches": total_matches,
        "valid_matches": valid_matches,
        "invalid_matches": invalid_matches,
        "converged_matches": converged_matches,
        "draw_matches": draw_matches
    }

def analyze_preference_structure(match_history, ratings):
    """
    Analyzes for cycles, transitivity violations, dominance chains.
    
    Args:
        match_history: List of match results
        ratings: Dict of item ratings
        
    Returns:
        dict: Analysis results
    """
    # Build win/loss graph
    wins = defaultdict(set)  # wins[A] contains items that A beat
    losses = defaultdict(set)  # losses[A] contains items that beat A
    
    for match in match_history:
        if match.get("status") != STATUS_CONVERGED:
            continue
            
        pair = match.get("pair", [])
        if len(pair) != 2:
            continue
            
        winner = match.get("winner")
        loser = pair[0] if pair[1] == winner else pair[1]
        
        wins[winner].add(loser)
        losses[loser].add(winner)
    
    # Find cycles (rock-paper-scissors patterns)
    cycles = []
    visited = set()
    
    def find_cycles_from(start, path=[]):
        if start in path:
            # Found a cycle
            cycle_start = path.index(start)
            cycle = path[cycle_start:]
            if len(cycle) >= 3:  # Only interested in cycles of 3+ items
                cycles.append(cycle)
            return
            
        if start in visited:
            return
            
        visited.add(start)
        path.append(start)
        
        for next_item in wins.get(start, set()):
            find_cycles_from(next_item, path.copy())
    
    for item in wins:
        find_cycles_from(item)
    
    # Check for strict ordering (no cycles)
    strict_ordering = len(cycles) == 0
    
    # Create dominance tiers based on rating ranges
    sorted_items = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    
    dominance_tiers = []
    if sorted_items:
        current_tier = [sorted_items[0]]
        tier_threshold = 50  # Items within 50 rating points are in same tier
        
        for i in range(1, len(sorted_items)):
            item, rating = sorted_items[i]
            prev_rating = sorted_items[i-1][1]
            
            if prev_rating - rating <= tier_threshold:
                current_tier.append((item, rating))
            else:
                dominance_tiers.append(current_tier)
                current_tier = [(item, rating)]
        
        dominance_tiers.append(current_tier)
    
    # Find transitivity violations
    transitivity_violations = []
    for a in wins:
        for b in wins[a]:
            for c in wins.get(b, set()):
                if c in wins and a in wins[c]:
                    # A beats B, B beats C, but C beats A
                    transitivity_violations.append((a, b, c))
    
    return {
        "cycles": cycles,
        "strict_ordering": strict_ordering,
        "dominance_tiers": dominance_tiers,
        "transitivity_violations": transitivity_violations,
        "num_participants": len(ratings)
    }

def generate_elo_report(ratings_data, analysis=None):
    """
    Creates formatted report of Elo ratings and match statistics.
    
    Args:
        ratings_data: Dict from calculate_elo_ratings
        analysis: Optional dict from analyze_preference_structure
        
    Returns:
        str: Formatted report
    """
    ratings = ratings_data["ratings"]
    
    # Sort by rating
    sorted_ratings = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    
    # Build report
    lines = []
    lines.append("=" * 60)
    lines.append("ELO RATINGS REPORT")
    lines.append("=" * 60)
    lines.append("")
    
    # Match statistics
    lines.append("Match Statistics:")
    lines.append(f"  Total matches: {ratings_data['total_matches']}")
    lines.append(f"  Valid matches: {ratings_data['valid_matches']} ({ratings_data['valid_matches']/max(1, ratings_data['total_matches'])*100:.1f}%)")
    if ratings_data['valid_matches'] > 0:
        lines.append(f"  - Converged: {ratings_data['converged_matches']} ({ratings_data['converged_matches']/ratings_data['valid_matches']*100:.1f}% of valid)")
        lines.append(f"  - Draws: {ratings_data['draw_matches']} ({ratings_data['draw_matches']/ratings_data['valid_matches']*100:.1f}% of valid)")
    lines.append(f"  Invalid matches: {ratings_data['invalid_matches']} ({ratings_data['invalid_matches']/max(1, ratings_data['total_matches'])*100:.1f}%)")
    lines.append("")
    
    # Ratings table
    lines.append("Elo Ratings:")
    lines.append("-" * 60)
    lines.append(f"{'Rank':<6} {'Item':<20} {'Rating':<10} {'Δ from base':<12}")
    lines.append("-" * 60)
    
    for rank, (item, rating) in enumerate(sorted_ratings, 1):
        delta = rating - BASE_RATING
        delta_str = f"+{delta:.0f}" if delta >= 0 else f"{delta:.0f}"
        lines.append(f"{rank:<6} {item:<20} {rating:<10.0f} {delta_str:<12}")
    
    # Analysis section if provided
    if analysis:
        lines.append("")
        lines.append("Preference Structure Analysis:")
        lines.append("-" * 60)
        
        if analysis["strict_ordering"]:
            lines.append("✓ Strict ordering detected (no cycles)")
        else:
            lines.append(f"✗ {len(analysis['cycles'])} preference cycles detected")
            if analysis['cycles']:
                for i, cycle in enumerate(analysis['cycles'][:5], 1):  # Show first 5
                    cycle_str = " → ".join(cycle) + f" → {cycle[0]}"
                    lines.append(f"  Cycle {i}: {cycle_str}")
                if len(analysis['cycles']) > 5:
                    lines.append(f"  ... and {len(analysis['cycles']) - 5} more cycles")
        
        if analysis['transitivity_violations']:
            lines.append(f"\n{len(analysis['transitivity_violations'])} transitivity violations found")
        
        if analysis['dominance_tiers']:
            lines.append("\nDominance Tiers:")
            for i, tier in enumerate(analysis['dominance_tiers'], 1):
                tier_items = [f"{item} ({rating:.0f})" for item, rating in tier]
                lines.append(f"  Tier {i}: {', '.join(tier_items)}")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)

def generate_markdown_report(match_history, ratings_data, model_name):
    """
    Generates a markdown report showing detailed win/loss record for each item.
    
    Args:
        match_history: List of match results
        ratings_data: Dict from calculate_elo_ratings
        model_name: Name of the model
        
    Returns:
        str: Markdown formatted report
    """
    from datetime import datetime
    from emoji_list import get_item_info
    
    ratings = ratings_data["ratings"]
    
    # Build win/loss/draw records for each item
    records = defaultdict(lambda: {
        "wins": [],
        "losses": [],
        "draws": [],
        "win_count": 0,
        "loss_count": 0,
        "draw_count": 0
    })
    
    # Process match history
    for match in match_history:
        if match.get("status") == STATUS_INVALID:
            continue
            
        pair = match.get("pair", [])
        if len(pair) != 2:
            continue
            
        item1, item2 = pair
        status = match.get("status")
        
        if status == STATUS_CONVERGED:
            winner = match.get("winner")
            loser = item2 if winner == item1 else item1
            
            records[winner]["wins"].append(loser)
            records[winner]["win_count"] += 1
            records[loser]["losses"].append(winner)
            records[loser]["loss_count"] += 1
            
        elif status == STATUS_DRAW:
            records[item1]["draws"].append(item2)
            records[item1]["draw_count"] += 1
            records[item2]["draws"].append(item1)
            records[item2]["draw_count"] += 1
    
    # Sort items by rating
    sorted_items = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    
    # Build markdown
    lines = []
    lines.append(f"# Elo Rankings for {model_name}")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f"**Total matches:** {ratings_data['total_matches']} | ")
    lines.append(f"**Valid:** {ratings_data['valid_matches']} | ")
    lines.append(f"**Invalid:** {ratings_data['invalid_matches']}")
    lines.append("")
    
    # Add item details
    for rank, (item, rating) in enumerate(sorted_items, 1):
        record = records[item]
        total_matches = record["win_count"] + record["loss_count"] + record["draw_count"]
        
        # Get item name if available
        item_info = get_item_info(item)
        item_name = f" ({item_info['name']})" if item_info and 'name' in item_info else ""
        
        lines.append(f"## {rank}. {item}{item_name} - Rating: {rating:.0f}")
        
        if total_matches > 0:
            lines.append(f"**Record:** {record['win_count']}-{record['loss_count']}-{record['draw_count']}")
            
            if record["wins"]:
                wins_sorted = sorted(set(record["wins"]), key=lambda x: ratings.get(x, BASE_RATING), reverse=True)
                lines.append(f"- **Wins against:** {', '.join(wins_sorted)}")
            
            if record["losses"]:
                losses_sorted = sorted(set(record["losses"]), key=lambda x: ratings.get(x, BASE_RATING), reverse=True)
                lines.append(f"- **Losses to:** {', '.join(losses_sorted)}")
            
            if record["draws"]:
                draws_sorted = sorted(set(record["draws"]), key=lambda x: ratings.get(x, BASE_RATING), reverse=True)
                lines.append(f"- **Draws with:** {', '.join(draws_sorted)}")
        else:
            lines.append("**No matches played**")
        
        lines.append("")
    
    return "\n".join(lines)

if __name__ == "__main__":
    # Test the functions
    print("Testing Elo calculator...")
    
    # Test expected score
    print("\nTesting expected_score:")
    test_cases = [
        (1500, 1500),  # Equal ratings
        (1600, 1400),  # 200 point difference
        (1800, 1200),  # 600 point difference
    ]
    
    for r1, r2 in test_cases:
        expected = expected_score(r1, r2)
        print(f"Rating {r1} vs {r2}: Expected score = {expected:.3f}")
    
    # Test rating update
    print("\nTesting update_rating:")
    rating = 1500
    print(f"Starting rating: {rating}")
    
    # Win against equal opponent
    new_rating = update_rating(rating, 0.5, 1.0)
    print(f"After win vs equal: {new_rating:.0f} (+{new_rating - rating:.0f})")
    
    # Loss against equal opponent
    new_rating = update_rating(rating, 0.5, 0.0)
    print(f"After loss vs equal: {new_rating:.0f} ({new_rating - rating:.0f})")
    
    # Draw against equal opponent
    new_rating = update_rating(rating, 0.5, 0.5)
    print(f"After draw vs equal: {new_rating:.0f} ({new_rating - rating:.0f})")
    
    # Test with sample match history
    print("\nTesting with sample matches:")
    sample_matches = [
        {"pair": ["A", "B"], "status": "converged", "winner": "A"},
        {"pair": ["B", "C"], "status": "converged", "winner": "B"},
        {"pair": ["C", "A"], "status": "converged", "winner": "C"},  # Creates a cycle
        {"pair": ["A", "D"], "status": "draw", "winner": None},
        {"pair": ["B", "D"], "status": "invalid", "winner": None},
    ]
    
    ratings_data = calculate_elo_ratings(sample_matches)
    analysis = analyze_preference_structure(sample_matches, ratings_data["ratings"])
    report = generate_elo_report(ratings_data, analysis)
    
    print(report)