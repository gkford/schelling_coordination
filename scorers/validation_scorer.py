"""
Validation scorer for pairs evaluation - validates responses as A, B, or invalid.
"""
from inspect_ai.scorer import Score, Scorer, Target, scorer, metric, Metric, SampleScore
from inspect_ai.solver import TaskState
from inspect_ai.model import ChatMessageAssistant
from typing import List


@metric
def valid_pairs_proportion() -> Metric:
    """
    Calculate the proportion of pairs where BOTH samples have valid responses.
    
    This metric groups scores by pair_id and checks if both samples in each pair
    have valid responses (value=1). Returns the proportion of valid pairs.
    """
    def metric_fn(scores: List[SampleScore]) -> float:
        # Group scores by pair_id
        pairs = {}
        for sample_score in scores:
            # Get pair_id from the sample metadata
            metadata = sample_score.sample_metadata or {}
            pair_id = metadata.get('pair_id', None)
            
            if pair_id:
                if pair_id not in pairs:
                    pairs[pair_id] = []
                pairs[pair_id].append(sample_score)
        
        # Count pairs where both samples are valid
        valid_pairs = 0
        total_pairs = len(pairs)
        
        for pair_id, pair_scores in pairs.items():
            # Each pair should have exactly 2 samples
            if len(pair_scores) == 2:
                # Check if both samples have valid responses (value=1)
                if all(sample_score.score.value == 1 for sample_score in pair_scores):
                    valid_pairs += 1
        
        # Return proportion of valid pairs
        if total_pairs == 0:
            return 0.0
        
        return valid_pairs / total_pairs
    
    return metric_fn


@scorer(metrics=[valid_pairs_proportion()])
def validation_scorer() -> Scorer:
    """
    Validate model responses as A, B, or invalid with strict matching.
    """
    async def score(state: TaskState, target: Target) -> Score:
        # Look for the model's initial response
        # If follow-up solver was used, the first assistant message has the emoji choice
        # If not, it's in the output
        model_response = ""
        
        # Check message history first (for when follow-up solver is used)
        for msg in state.messages:
            if isinstance(msg, ChatMessageAssistant):
                # First assistant message contains the emoji choice
                # Handle both string and structured content formats
                if isinstance(msg.content, str):
                    model_response = msg.content.strip()
                elif isinstance(msg.content, list) and len(msg.content) > 0:
                    # Content is a list of parts (e.g., for reasoning models)
                    # Look for text content
                    for part in msg.content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            model_response = part.get("text", "").strip()
                            break
                        elif isinstance(part, str):
                            model_response = part.strip()
                            break
                        elif hasattr(part, 'text'):
                            # Handle ContentText objects (e.g., from Sonnet)
                            model_response = part.text.strip()
                            break
                break
        
        # If no assistant message found, use output (for when no follow-up is used)
        if not model_response and state.output and state.output.completion:
            model_response = state.output.completion.strip()
        
        if not model_response:
            return Score(value=0, answer="No response", metadata={"choice": "invalid"})
        
        # Get the options from metadata
        option_A = state.metadata.get("option_A", "")
        option_B = state.metadata.get("option_B", "")
        
        # Extract usage information including reasoning tokens
        usage_metadata = {}
        if state.output and hasattr(state.output, 'usage') and state.output.usage:
            usage = state.output.usage
            # Extract standard token counts
            if hasattr(usage, 'input_tokens'):
                usage_metadata['input_tokens'] = usage.input_tokens
            if hasattr(usage, 'output_tokens'):
                usage_metadata['output_tokens'] = usage.output_tokens
            if hasattr(usage, 'total_tokens'):
                usage_metadata['total_tokens'] = usage.total_tokens
            
            # Try to extract reasoning tokens (may not be available for all models)
            if hasattr(usage, 'reasoning_tokens'):
                try:
                    usage_metadata['reasoning_tokens'] = usage.reasoning_tokens
                except (AttributeError, TypeError):
                    # Model doesn't support reasoning tokens or error accessing them
                    pass
        
        # Strict matching - exact match only
        # Use numeric values: 1 for valid response (A or B), 0 for invalid
        # Store actual choice and usage in metadata
        if model_response == option_A:
            return Score(value=1, answer=model_response, metadata={"choice": "A", **usage_metadata})
        elif model_response == option_B:
            return Score(value=1, answer=model_response, metadata={"choice": "B", **usage_metadata})
        else:
            return Score(value=0, answer=model_response, metadata={"choice": "invalid", **usage_metadata})
    
    return score