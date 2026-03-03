"""
Strategy Name Extractor Scorer with Auto-Categorization

Extracts the strategy name from the model's response in {strategy_name} format.
If the strategy is not in the categorization database, automatically categorizes it
using the dual categorization system (Kimi K2 + GPT OSS 120B + Sonnet 4.5 tiebreaker).
"""
from inspect_ai.scorer import Score, Scorer, Target, scorer, metric, Metric
from inspect_ai.solver import TaskState
from typing import List
from inspect_ai.scorer import SampleScore
import re
import csv
import sys
from pathlib import Path

# Add parent for imports
sys.path.append(str(Path(__file__).parent))

# Import the new dual categorization function
from categorize_strategies_csv import categorize_strategy, save_categorization_to_csv

# Import for environment setup
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

# CSV file path
CSV_FILE = Path(__file__).parent / "strategy_categorizations.csv"

# Load categorizations at module level
CATEGORIZATIONS = {}
def load_categorizations():
    """Load strategy categorizations from CSV."""
    csv_path = CSV_FILE
    categorizations = {}
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            strategy = row['strategy'].lower()
            categorizations[strategy] = {
                'category': row['category'],
                'subcategory': row['subcategory']
            }
    return categorizations

CATEGORIZATIONS = load_categorizations()
print(f"Loaded {len(CATEGORIZATIONS)} strategy categorizations")


def parse_strategy_response(response: str) -> str:
    """
    Parse the response to extract strategy name from {strategy_name} format.

    Args:
        response: The raw response from the model

    Returns:
        The strategy name (string) or the raw response if parsing failed
    """
    # Try to extract from {strategy_name} format
    match = re.search(r'\{([a-zA-Z_0-9-]+)\}', response)
    if match:
        return match.group(1).lower().strip()

    # If that fails, try to extract the first word-like token
    match = re.search(r'\b([a-zA-Z_0-9-]+)\b', response)
    if match:
        return match.group(1).lower().strip()

    # If all else fails, return cleaned response
    return response.strip().lower()


def is_strategy_inferable(category: str, subcategory: str, dataset_id: str = None) -> bool:
    """
    Determine if a strategy allows us to infer the implied choice.

    Rules:
    - Length: shorter/longer = YES, ambiguous = NO
    - Frequency: common/rare/ambiguous = YES
    - Lexicographic: ascending/descending/ambiguous = YES (assume ascending)
    - Positional: first/second/ambiguous = YES (assume first)
    - Salience: YES only for salient_vs_alphabetical and mundane_vs_dangerous datasets
    - Other_Semantic, Other_Non-semantic, Random, Failures = NO

    Args:
        category: Strategy category
        subcategory: Strategy subcategory
        dataset_id: Dataset identifier (required for Salience strategies)

    Returns:
        True if we can infer the implied choice, False otherwise
    """
    if category == "Length":
        return subcategory in ["shorter", "longer"]

    elif category == "Frequency":
        return subcategory in ["common", "rare", "ambiguous"]

    elif category == "Lexicographic":
        return subcategory in ["ascending", "descending", "ambiguous"]

    elif category == "Positional":
        return subcategory in ["first", "second", "ambiguous"]

    elif category == "Salience":
        # Salience is only inferable for specific datasets
        if not dataset_id:
            return False
        dataset_id_lower = dataset_id.lower()
        return ("salient_vs_alphabetical" in dataset_id_lower or
                "mundane_vs_dangerous" in dataset_id_lower)

    else:
        # Other_Semantic, Other_Non-semantic, Random, Failures = not inferable
        return False


def predict_answer(
    category: str,
    subcategory: str,
    option_A: str,
    option_B: str,
    ordering: str,
    dataset_id: str = None
) -> tuple[str | None, str | None]:
    """
    Predict the answer based on the strategy.

    Args:
        category: Strategy category
        subcategory: Strategy subcategory
        option_A: First option (fixed identifier)
        option_B: Second option (fixed identifier)
        ordering: Presentation order ("AB" or "BA")
        dataset_id: Dataset identifier (for context)

    Returns:
        Tuple of (predicted_answer_option, predicted_answer_text)
        - predicted_answer_option: "A" or "B" or None
        - predicted_answer_text: the actual word or None
    """
    # If not inferable, return None, None
    if not is_strategy_inferable(category, subcategory, dataset_id):
        return None, None

    # Positional strategies
    if category == "Positional":
        if subcategory in ["first", "ambiguous"]:  # ambiguous defaults to first
            # Choose first presented option
            if ordering == "AB":
                return "A", option_A
            else:  # BA
                return "B", option_B
        elif subcategory == "second":
            # Choose second presented option
            if ordering == "AB":
                return "B", option_B
            else:  # BA
                return "A", option_A

    # Lexicographic strategies
    elif category == "Lexicographic":
        if subcategory in ["ascending", "ambiguous"]:  # ambiguous defaults to ascending
            # Choose alphabetically first (a < z)
            if option_A.lower() < option_B.lower():
                return "A", option_A
            else:
                return "B", option_B
        elif subcategory == "descending":
            # Choose alphabetically last (z > a)
            if option_A.lower() > option_B.lower():
                return "A", option_A
            else:
                return "B", option_B

    # Length strategies
    elif category == "Length":
        if subcategory == "shorter":
            if len(option_A) < len(option_B):
                return "A", option_A
            else:
                return "B", option_B
        elif subcategory == "longer":
            if len(option_A) > len(option_B):
                return "A", option_A
            else:
                return "B", option_B

    # Frequency strategies
    elif category == "Frequency":
        try:
            from wordfreq import word_frequency

            # Get word frequencies (using English)
            freq_A = word_frequency(option_A.lower(), 'en', wordlist='best')
            freq_B = word_frequency(option_B.lower(), 'en', wordlist='best')

            if subcategory in ["common", "ambiguous"]:  # ambiguous defaults to common
                # Choose more frequent word
                if freq_A > freq_B:
                    return "A", option_A
                else:
                    return "B", option_B
            elif subcategory == "rare":
                # Choose less frequent word
                if freq_A < freq_B:
                    return "A", option_A
                else:
                    return "B", option_B
        except Exception:
            # If wordfreq fails, return None
            return None, None

    # Salience strategies - dataset dependent
    elif category == "Salience":
        if not dataset_id:
            return None, None

        dataset_id_lower = dataset_id.lower()

        # mundane_vs_dangerous: option_B is more salient (negative valence)
        if "mundane_vs_dangerous" in dataset_id_lower:
            if subcategory in ["negative", "ambiguous"]:  # ambiguous defaults to negative
                return "B", option_B  # Choose dangerous (negative salient)
            elif subcategory == "positive":
                return "A", option_A  # Choose mundane (less negative)

        # salient_vs_alphabetical: option_A is more salient (positive valence)
        elif "salient_vs_alphabetical" in dataset_id_lower:
            if subcategory in ["positive", "ambiguous"]:  # ambiguous defaults to positive
                return "A", option_A  # Choose salient (positive)
            elif subcategory == "negative":
                return "B", option_B  # Choose alphabetical (less positive)

        return None, None

    return None, None


@metric
def inferability_rate() -> Metric:
    """
    Calculate the proportion of strategies that are inferable (can determine implied choice).
    """
    def metric_fn(scores: List[SampleScore]) -> float:
        if not scores:
            return 0.0

        total = len(scores)
        inferable = sum(1 for s in scores
                       if s.score.metadata.get('inferable', False))

        return inferable / total if total > 0 else 0.0

    return metric_fn


@scorer(metrics=[inferability_rate()])
def strategy_name_extractor() -> Scorer:
    """
    Extract strategy name from direct response and categorize it.
    If not in database, auto-categorize with Kimi K2 and add to database.

    Returns:
        Scorer that extracts, categorizes, and validates the strategy name.
        Score value is 1 if strategy is inferable (can determine implied choice), 0 otherwise.
    """
    async def score(state: TaskState, target: Target) -> Score:
        # Get the model's response
        if state.output and state.output.completion:
            raw_response = state.output.completion.strip()
        else:
            return Score(
                value=0,  # Not inferable
                answer="NO_RESPONSE",
                explanation="No completion found in output",
                metadata={
                    "strategy_name": "NO_RESPONSE",
                    "raw_response": "",
                    "in_database": False,
                    "auto_categorized": False,
                    "category": "Failures",
                    "subcategory": "other",
                    "inferable": False,
                }
            )

        # Parse strategy name from response
        strategy_name = parse_strategy_response(raw_response)

        # Get options for context
        option_A = state.metadata.get("option_A", "")
        option_B = state.metadata.get("option_B", "")

        # Check if it's in our categorization database
        strategy_lower = strategy_name.lower()
        in_database = strategy_lower in CATEGORIZATIONS
        auto_categorized = False
        categorizer_source = ""
        disagreement_details = ""

        # If not in database, categorize it with dual categorization system
        if not in_database:
            print(f"Auto-categorizing unknown strategy: {strategy_name}")
            pair_words = (option_A, option_B) if option_A and option_B else None

            category, subcategory, categorizer_source, disagreement_details = categorize_strategy(
                strategy_name, pair_words
            )

            # Save to CSV with new fields and update in-memory cache
            save_categorization_to_csv(
                strategy_name, category, subcategory,
                categorizer_source, option_A, option_B, disagreement_details
            )

            # Update in-memory cache
            CATEGORIZATIONS[strategy_lower] = {
                'category': category,
                'subcategory': subcategory
            }

            auto_categorized = True
            print(f"  → {category}|{subcategory} (source: {categorizer_source})")
        else:
            # Get from existing database
            category = CATEGORIZATIONS[strategy_lower]['category']
            subcategory = CATEGORIZATIONS[strategy_lower]['subcategory']

        # Determine if strategy is inferable (can determine implied choice)
        dataset_id = state.metadata.get("dataset_id", "")
        ordering = state.metadata.get("ordering", "AB")
        inferable = is_strategy_inferable(category, subcategory, dataset_id)

        # Predict the answer based on the strategy
        predicted_answer_option, predicted_answer_text = predict_answer(
            category=category,
            subcategory=subcategory,
            option_A=option_A,
            option_B=option_B,
            ordering=ordering,
            dataset_id=dataset_id
        )

        # Score value: 1 for inferable strategies, 0 for non-inferable
        score_value = 1 if inferable else 0

        # Store everything in metadata for later analysis
        return Score(
            value=score_value,
            answer=strategy_name,
            explanation=raw_response,
            metadata={
                "strategy_name": strategy_name,
                "raw_response": raw_response,
                "in_database": in_database,
                "auto_categorized": auto_categorized,
                "category": category,
                "subcategory": subcategory,
                "categorizer_source": categorizer_source,
                "disagreement_details": disagreement_details,
                "inferable": inferable,
                "predicted_answer_option": predicted_answer_option,
                "predicted_answer_text": predicted_answer_text,
                "option_A": option_A,
                "option_B": option_B,
                "item_id": state.metadata.get("item_id"),
                "pair_id": state.metadata.get("pair_id"),
                "ordering": ordering,
            }
        )

    return score
