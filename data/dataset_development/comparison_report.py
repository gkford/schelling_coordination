"""
Generate comprehensive markdown reports for multi-model Elo comparisons.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import json

def format_item_with_rating(item: str, rating: float) -> str:
    """Format an item with its rating for display."""
    return f"{item} ({rating:.0f})"

def get_top_bottom_items(
    ratings: Dict[str, float], 
    n: int = 10
) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    """
    Get top N and bottom N items from ratings.
    
    Args:
        ratings: Dictionary of item -> rating
        n: Number of items to get from top and bottom
        
    Returns:
        tuple: (top_n_items, bottom_n_items) as lists of (item, rating) tuples
    """
    sorted_items = sorted(ratings.items(), key=lambda x: x[1], reverse=True)
    top_n = sorted_items[:n]
    bottom_n = sorted_items[-n:] if len(sorted_items) > n else []
    return top_n, bottom_n

def generate_model_section(model_result: Dict) -> str:
    """
    Generate markdown section for a single model's results.
    
    Args:
        model_result: Results dictionary for one model
        
    Returns:
        str: Markdown formatted section
    """
    lines = []
    model_name = model_result["model_name"]
    ratings_data = model_result["ratings_data"]
    ratings = ratings_data["ratings"]
    
    # Header
    lines.append(f"### {model_name}")
    lines.append(f"**Passes:** {model_result['num_passes']:.1f} | ")
    lines.append(f"**Total Matches:** {model_result['total_matches']} | ")
    lines.append(f"**Valid:** {ratings_data['valid_matches']} | ")
    lines.append(f"**Invalid:** {ratings_data['invalid_matches']}")
    lines.append("")
    
    # Get top and bottom items
    top_items, bottom_items = get_top_bottom_items(ratings)
    
    # Top 10
    lines.append("#### Top 10 Items")
    for i, (item, rating) in enumerate(top_items, 1):
        delta = rating - 1500  # Delta from base rating
        delta_str = f"+{delta:.0f}" if delta >= 0 else f"{delta:.0f}"
        lines.append(f"{i}. **{item}** - Rating: {rating:.0f} ({delta_str})")
    lines.append("")
    
    # Bottom 10
    if bottom_items:
        lines.append("#### Bottom 10 Items")
        for i, (item, rating) in enumerate(reversed(bottom_items), 1):
            delta = rating - 1500
            delta_str = f"+{delta:.0f}" if delta >= 0 else f"{delta:.0f}"
            lines.append(f"{i}. **{item}** - Rating: {rating:.0f} ({delta_str})")
        lines.append("")
    
    return "\n".join(lines)

def generate_weighted_average_section(
    weighted_elos: Dict[str, float]
) -> str:
    """
    Generate section showing weighted average rankings.
    
    Args:
        weighted_elos: Dictionary of item -> average Elo
        
    Returns:
        str: Markdown formatted section
    """
    lines = []
    lines.append("## 📊 Weighted Average Rankings (All Models)")
    lines.append("")
    
    # Get top and bottom
    top_items, bottom_items = get_top_bottom_items(weighted_elos)
    
    # Top 10
    lines.append("### 🏆 Top 10 Overall")
    lines.append("| Rank | Item | Average Rating | Δ from Base |")
    lines.append("|------|------|----------------|-------------|")
    for i, (item, rating) in enumerate(top_items, 1):
        delta = rating - 1500
        delta_str = f"+{delta:.0f}" if delta >= 0 else f"{delta:.0f}"
        lines.append(f"| {i} | **{item}** | {rating:.0f} | {delta_str} |")
    lines.append("")
    
    # Bottom 10
    if bottom_items:
        lines.append("### 📉 Bottom 10 Overall")
        lines.append("| Rank | Item | Average Rating | Δ from Base |")
        lines.append("|------|------|----------------|-------------|")
        for i, (item, rating) in enumerate(reversed(bottom_items), 1):
            delta = rating - 1500
            delta_str = f"+{delta:.0f}" if delta >= 0 else f"{delta:.0f}"
            rank = len(weighted_elos) - len(bottom_items) + i
            lines.append(f"| {rank} | **{item}** | {rating:.0f} | {delta_str} |")
    lines.append("")
    
    return "\n".join(lines)

def generate_consensus_analysis_section(
    consensus_analysis: Dict,
    weighted_elos: Dict[str, float]
) -> str:
    """
    Generate section analyzing cross-model consensus and disagreement.
    
    Args:
        consensus_analysis: Analysis results from find_consensus_and_outliers
        weighted_elos: Weighted average Elos for rating display
        
    Returns:
        str: Markdown formatted section
    """
    lines = []
    lines.append("## 🤝 Cross-Model Analysis")
    lines.append("")
    
    # High agreement items
    if consensus_analysis["consensus_items"]:
        lines.append("### High Agreement Items")
        lines.append("Items that all models ranked similarly (low variance):")
        lines.append("")
        for item in consensus_analysis["consensus_items"][:10]:
            rating = weighted_elos.get(item, 0)
            variance = consensus_analysis["item_variance"].get(item, 0)
            lines.append(f"- **{item}** (Avg: {rating:.0f}, Variance: {variance:.1f})")
        lines.append("")
    
    # High disagreement items
    if consensus_analysis["controversial_items"]:
        lines.append("### High Disagreement Items")
        lines.append("Items with the most varied rankings across models (high variance):")
        lines.append("")
        for item in consensus_analysis["controversial_items"][:10]:
            rating = weighted_elos.get(item, 0)
            variance = consensus_analysis["item_variance"].get(item, 0)
            lines.append(f"- **{item}** (Avg: {rating:.0f}, Variance: {variance:.1f})")
        lines.append("")
    
    # Model-specific outliers
    if consensus_analysis["outliers"]:
        lines.append("### Model-Specific Outliers")
        lines.append("Items that specific models rated very differently from the average:")
        lines.append("")
        for model_name, outliers in consensus_analysis["outliers"].items():
            if outliers:
                lines.append(f"**{model_name}:**")
                for outlier in outliers[:5]:  # Show top 5 outliers per model
                    item = outlier["item"]
                    rating = outlier["rating"]
                    deviation = outlier["deviation"]
                    dev_str = f"+{deviation:.0f}" if deviation >= 0 else f"{deviation:.0f}"
                    lines.append(f"- {item}: {rating:.0f} ({dev_str} from average)")
                lines.append("")
    
    return "\n".join(lines)

def generate_comparison_report(
    results: Dict,
    output_path: str = None
) -> str:
    """
    Generate complete comparison report in markdown format.
    
    Args:
        results: Complete results from run_multi_model_comparison
        output_path: Optional path to save the report
        
    Returns:
        str: Complete markdown report
    """
    lines = []
    
    # Header
    lines.append("# 🎯 Multi-Model Elo Comparison Report")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Summary
    lines.append("## 📋 Summary")
    lines.append(f"- **Models Compared:** {len(results['models'])}")
    model_list = ", ".join([f"`{m}`" for m in results['models']])
    lines.append(f"  - {model_list}")
    lines.append(f"- **Dataset Size:** {results['dataset_size']} items")
    lines.append(f"- **Passes per Model:** {results['passes_per_model']}")
    total_matches = sum(r['total_matches'] for r in results['model_results'])
    lines.append(f"- **Total Matches Run:** {total_matches}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Weighted average section
    report = "\n".join(lines)
    report += generate_weighted_average_section(results['weighted_average_elos'])
    report += "---\n\n"
    
    # Cross-model analysis
    report += generate_consensus_analysis_section(
        results['consensus_analysis'],
        results['weighted_average_elos']
    )
    report += "---\n\n"
    
    # Individual model sections
    report += "## 📈 Individual Model Results\n\n"
    for model_result in results['model_results']:
        report += generate_model_section(model_result)
        report += "---\n\n"
    
    # Statistical summary
    report += "## 📊 Statistical Summary\n\n"
    
    # Rating distribution
    all_ratings = []
    for model_result in results['model_results']:
        all_ratings.extend(model_result['ratings_data']['ratings'].values())
    
    if all_ratings:
        min_rating = min(all_ratings)
        max_rating = max(all_ratings)
        avg_rating = sum(all_ratings) / len(all_ratings)
        
        report += "### Rating Distribution\n"
        report += f"- **Minimum Rating:** {min_rating:.0f}\n"
        report += f"- **Maximum Rating:** {max_rating:.0f}\n"
        report += f"- **Average Rating:** {avg_rating:.0f}\n"
        report += f"- **Rating Range:** {max_rating - min_rating:.0f}\n\n"
    
    # Match statistics
    report += "### Match Statistics by Model\n"
    report += "| Model | Total | Valid | Converged | Draws | Invalid |\n"
    report += "|-------|-------|-------|-----------|-------|----------|\n"
    
    for model_result in results['model_results']:
        model_name = model_result['model_name']
        rd = model_result['ratings_data']
        total = rd['total_matches']
        valid = rd['valid_matches']
        converged = rd['converged_matches']
        draws = rd['draw_matches']
        invalid = rd['invalid_matches']
        
        report += f"| {model_name} | {total} | {valid} | {converged} | {draws} | {invalid} |\n"
    
    report += "\n---\n\n"
    
    # Footer
    report += "## 📝 Notes\n\n"
    report += "- **Base Rating:** 1500 (Elo starting point)\n"
    report += "- **Rating Interpretation:**\n"
    report += "  - Ratings > 1500: Preferred more often than average\n"
    report += "  - Ratings < 1500: Preferred less often than average\n"
    report += "  - Rating difference of ~400 points = 10:1 win probability\n"
    report += "- **Variance:** Lower variance indicates higher agreement between models\n"
    report += "- **Outliers:** Items where a model's rating deviates >100 points from average\n"
    
    # Save if path provided
    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"Report saved to: {output_file}")
    
    return report

def load_and_generate_report(results_file: str, output_path: str = None) -> str:
    """
    Load results from JSON and generate report.
    
    Args:
        results_file: Path to raw_results.json file
        output_path: Optional path to save the report
        
    Returns:
        str: Generated markdown report
    """
    with open(results_file, 'r', encoding='utf-8') as f:
        saved_data = json.load(f)
    
    # Reconstruct results format expected by generate_comparison_report
    results = {
        "timestamp": saved_data["timestamp"],
        "output_name": saved_data["output_name"],
        "dataset_size": saved_data["dataset_size"],
        "models": saved_data["models"],
        "passes_per_model": saved_data["passes_per_model"],
        "weighted_average_elos": saved_data["weighted_average_elos"],
        "consensus_analysis": saved_data["consensus_analysis"],
        "model_results": []
    }
    
    # Reconstruct model results
    for summary in saved_data["model_summaries"]:
        model_result = {
            "model_name": summary["model_name"],
            "total_matches": summary["total_matches"],
            "num_passes": summary["num_passes"],
            "ratings_data": {
                "ratings": summary["ratings"],
                "total_matches": summary["total_matches"],
                "valid_matches": summary.get("valid_matches", summary["total_matches"]),
                "invalid_matches": summary.get("invalid_matches", 0),
                "converged_matches": summary.get("converged_matches", 0),
                "draw_matches": summary.get("draw_matches", 0)
            }
        }
        results["model_results"].append(model_result)
    
    return generate_comparison_report(results, output_path)

if __name__ == "__main__":
    # Test report generation with sample data
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "output_name": "test",
        "dataset_size": 6,
        "models": ["test-model-1", "test-model-2"],
        "passes_per_model": 2,
        "model_results": [
            {
                "model_name": "test-model-1",
                "total_matches": 30,
                "num_passes": 2.0,
                "ratings_data": {
                    "ratings": {
                        "🔥": 1600,
                        "💧": 1550,
                        "🌍": 1500,
                        "💨": 1450,
                        "⚡": 1400,
                        "🌟": 1500
                    },
                    "total_matches": 30,
                    "valid_matches": 28,
                    "invalid_matches": 2,
                    "converged_matches": 20,
                    "draw_matches": 8
                }
            },
            {
                "model_name": "test-model-2",
                "total_matches": 30,
                "num_passes": 2.0,
                "ratings_data": {
                    "ratings": {
                        "🔥": 1580,
                        "💧": 1520,
                        "🌍": 1510,
                        "💨": 1490,
                        "⚡": 1420,
                        "🌟": 1480
                    },
                    "total_matches": 30,
                    "valid_matches": 29,
                    "invalid_matches": 1,
                    "converged_matches": 22,
                    "draw_matches": 7
                }
            }
        ],
        "weighted_average_elos": {
            "🔥": 1590,
            "💧": 1535,
            "🌍": 1505,
            "🌟": 1490,
            "💨": 1470,
            "⚡": 1410
        },
        "consensus_analysis": {
            "consensus_items": ["🌍", "🌟"],
            "controversial_items": ["🔥", "💨"],
            "outliers": {
                "test-model-1": [
                    {"item": "💨", "rating": 1450, "deviation": -20}
                ]
            },
            "item_variance": {
                "🔥": 100,
                "💧": 225,
                "🌍": 25,
                "💨": 400,
                "⚡": 100,
                "🌟": 100
            }
        }
    }
    
    report = generate_comparison_report(test_results)
    print(report[:2000])  # Print first 2000 chars
    print("\n... [truncated] ...")