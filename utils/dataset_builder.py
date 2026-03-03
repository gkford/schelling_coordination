"""
Convert pairs JSON to Inspect AI samples.
"""
from typing import List, Dict, Optional
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageSystem, ChatMessageUser
import sys
import os

# Add parent directory to path to import prompts
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from prompts import get_prompts

def build_sample(
    pair: Dict[str, str],
    prompt_template: str,
    dataset_id: str = "unknown",
    prompt_modifiers: List[str] = None
) -> List[Sample]:
    """
    Build Inspect AI samples for a single pair.

    Creates two samples: AB order and BA order.

    Args:
        pair: Dictionary with pair_id, option_A, option_B
        prompt_template: Name of prompt template to use
        dataset_id: Dataset identifier
        prompt_modifiers: Optional list of prompt modifiers to apply

    Returns:
        List of two Sample objects (AB and BA order)
    """
    # Get prompts for the template
    prompts = get_prompts(prompt_template, modifiers=prompt_modifiers)
    
    # Build messages for AB order
    ab_messages = []
    
    # System message (may be empty)
    if prompts['system_message']:
        ab_messages.append(ChatMessageSystem(content=prompts['system_message']))
    
    # User message with AB order
    user_content = prompts['user_template'].format(
        option1=pair['option_A'],
        option2=pair['option_B']
    )
    ab_messages.append(ChatMessageUser(content=user_content))
    
    # Build messages for BA order
    ba_messages = []
    
    # System message (same as AB)
    if prompts['system_message']:
        ba_messages.append(ChatMessageSystem(content=prompts['system_message']))
    
    # User message with BA order
    user_content = prompts['user_template'].format(
        option1=pair['option_B'],
        option2=pair['option_A']
    )
    ba_messages.append(ChatMessageUser(content=user_content))
    
    # Create samples with custom IDs
    samples = []
    
    # AB sample with custom ID
    ab_id = f"{dataset_id}_{pair['pair_id']}_AB"
    samples.append(Sample(
        id=ab_id,
        input=ab_messages,
        metadata={
            "pair_id": pair['pair_id'],
            "order": "AB",
            "option_A": pair['option_A'],
            "option_B": pair['option_B']
        }
    ))
    
    # BA sample with custom ID
    ba_id = f"{dataset_id}_{pair['pair_id']}_BA"
    samples.append(Sample(
        id=ba_id,
        input=ba_messages,
        metadata={
            "pair_id": pair['pair_id'],
            "order": "BA",
            "option_A": pair['option_A'],
            "option_B": pair['option_B']
        }
    ))
    
    return samples


def build_dataset(
    pairs: List[Dict[str, str]],
    prompt_template: str,
    dataset_id: str = "unknown",
    prompt_modifiers: List[str] = None
) -> List[Sample]:
    """
    Build complete dataset from pairs.

    Args:
        pairs: List of pair dictionaries
        prompt_template: Name of prompt template to use
        dataset_id: Dataset identifier
        prompt_modifiers: Optional list of prompt modifiers to apply

    Returns:
        List of Sample objects (2 per pair)
    """
    all_samples = []

    for pair in pairs:
        samples = build_sample(pair, prompt_template, dataset_id, prompt_modifiers)
        all_samples.extend(samples)

    return all_samples