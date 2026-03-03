"""
Schelling coordination task for pairs evaluation.

This module defines a pure Inspect AI task that evaluates whether two instances
of an LLM can coordinate on selecting the same option from a pair when presented
in different orders (AB vs BA).

Supports multiple option types: words, emojis, symbols, or mixed.

Can be run either:
1. Via the Inspect CLI: inspect eval schelling_pairs_task.py
2. Programmatically via run_eval.py
"""
from inspect_ai import task, Task
from inspect_ai.solver import generate, chain
from utils.hash_utils import load_dataset_and_hash
from utils.dataset_builder import build_dataset
from scorers.validation_scorer import validation_scorer
from solvers.post_hoc_explanation_solver import post_hoc_explanation


def create_schelling_pairs_task(
    pairs_file: str = "data/test_10_pairs.json",
    prompt_name: str = "control_sita",
    post_hoc_explanation_enabled: bool = False,
    prompt_modifiers: list = None,
    test: bool = False
) -> tuple[Task, str, str]:
    """
    Create Schelling coordination evaluation task for option pairs.

    This task evaluates whether two instances of an LLM can coordinate
    on selecting the same option from a pair when presented in different orders.

    Supports pairs of words, emojis, symbols, or mixed types.

    Args:
        pairs_file: Path to JSON file containing option pairs
        prompt_name: Name of the prompt template to use
        post_hoc_explanation_enabled: Whether to ask for explanation after choice
        prompt_modifiers: Optional list of prompt modifiers to apply
        test: Whether this is a test run (stored in metadata)

    Returns:
        Tuple of (Task, dataset_id, dataset_hash) where Task is configured with dataset, solver, and scorer
    """
    # Load and validate dataset
    dataset, pairs_hash = load_dataset_and_hash(pairs_file)
    dataset_id = dataset.get('dataset_id', 'unknown')
    pairs = dataset['pairs']

    # Build samples (2 per pair - AB and BA orderings)
    samples = build_dataset(
        pairs=pairs,
        prompt_template=prompt_name,
        dataset_id=dataset_id,
        prompt_modifiers=prompt_modifiers
    )
    
    # Build solver chain based on configuration
    if post_hoc_explanation_enabled:
        solver = chain(generate(), post_hoc_explanation())
    else:
        solver = generate()
    
    # Use standard validation scorer
    scorer = validation_scorer()

    # Build task metadata
    metadata = {
        "dataset_id": dataset_id,
        "pairs_hash": pairs_hash,
        "test_run": test
    }

    # Create and return task with dataset_id and hash
    task = Task(
        dataset=samples,
        solver=solver,
        scorer=scorer,
        metadata=metadata
    )

    return task, dataset_id, pairs_hash


@task
def schelling_pairs(
    pairs_file: str = "data/test_10_pairs.json",
    prompt_name: str = "control_sita",
    post_hoc_explanation_enabled: bool = False,
    prompt_modifiers: list = None,
    test: bool = False
) -> Task:
    """
    Task-decorated version for CLI use.

    This version only returns the Task object for use with inspect eval CLI.
    """
    task, _, _ = create_schelling_pairs_task(
        pairs_file, prompt_name, post_hoc_explanation_enabled, prompt_modifiers, test
    )
    return task