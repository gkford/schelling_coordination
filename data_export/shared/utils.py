"""
Shared utilities for data export.
"""

import math
import sys
from datetime import datetime
from pathlib import Path

from .config import PROJECT_ROOT

# Import comparison and eval result utilities
sys.path.insert(0, str(PROJECT_ROOT))
from utils.comparison import categorize_pair_results, generate_comparison_summary
from utils.eval_results import get_eval_results_by_features


def wilson_ci_half_width(successes: int, n: int) -> float:
    """
    Calculate 95% CI half-width using Wilson score interval.
    More accurate than normal approximation for proportions near 0 or 1.

    Args:
        successes: Number of successes
        n: Total number of trials

    Returns:
        Half-width of the 95% CI as percentage points
    """
    if n == 0:
        return 0.0

    z = 1.96  # 95% confidence
    p = successes / n

    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    margin = z * math.sqrt((p * (1 - p) / n + z**2 / (4 * n**2))) / denominator

    # Return half-width as percentage points
    return round(margin * 100, 2)


def get_eval_date(model_config: str, prompt: str, dataset: str) -> str:
    """
    Get the date when the eval was run from the eval file.

    Args:
        model_config: Model configuration name (folder name)
        prompt: Prompt identifier (e.g., 'control_sita', 'coordination_sita')
        dataset: Dataset name

    Returns:
        Date string in YYYY-MM-DD format, or empty string if not found
    """
    results_dir = PROJECT_ROOT / "results" / model_config / prompt / dataset
    if not results_dir.exists():
        return ""

    eval_files = list(results_dir.glob("*.eval"))
    if not eval_files:
        return ""

    # Get most recent eval file
    latest = max(eval_files, key=lambda p: p.stat().st_mtime)

    # Parse date from filename (format: 2025-01-03T04-39-06+00-00_...)
    filename = latest.stem
    try:
        date_part = filename.split("_")[0]
        # Convert to ISO format
        dt = datetime.fromisoformat(date_part.replace("T", " ").replace("-", ":", 2).replace("-", ":"))
        return dt.strftime("%Y-%m-%d")
    except:
        return ""


def load_eval_results(control_config: str, coordination_config: str, dataset: str) -> tuple:
    """
    Load eval results for a control/coordination pair.

    Args:
        control_config: Config name for control condition
        coordination_config: Config name for coordination condition
        dataset: Dataset name

    Returns:
        Tuple of (control_results, coordination_results) dicts, or (None, None) if not found
    """
    control_results = get_eval_results_by_features(control_config, "control_sita", dataset)
    coordination_results = get_eval_results_by_features(coordination_config, "coordination_sita", dataset)

    if not control_results or not coordination_results:
        return None, None

    return control_results, coordination_results


def categorize_and_summarize(control_results, coordination_results) -> tuple:
    """
    Categorize pairs and generate comparison summary.

    Args:
        control_results: Results from control condition
        coordination_results: Results from coordination condition

    Returns:
        Tuple of (categorized, summary) dicts
    """
    categorized = categorize_pair_results(control_results, coordination_results)
    summary = generate_comparison_summary(categorized)
    return categorized, summary
