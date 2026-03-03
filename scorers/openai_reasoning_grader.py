"""
OpenAI reasoning grader - extracts and analyzes reasoning traces from OpenAI models.
"""
from inspect_ai.scorer import Score, Scorer, Target, scorer
from inspect_ai.solver import TaskState
from typing import Optional


@scorer
def openai_reasoning_grader() -> Scorer:
    """
    Extract reasoning trace from OpenAI models and score based on content.
    
    Currently scores 1 if the reasoning trace contains "alphabetical", 0 otherwise.
    """
    async def score(state: TaskState, target: Target) -> Score:
        # Initialize metadata dictionary
        metadata = {}
        
        # Try to extract reasoning trace from state
        reasoning_text = extract_reasoning_trace(state)
        
        if reasoning_text:
            # Store the reasoning trace in metadata
            metadata['reasoning_trace'] = reasoning_text
            metadata['reasoning_trace_length'] = len(reasoning_text)
            
            # Score based on whether "alphabetical" appears in the reasoning
            # Case-insensitive search
            if "alphabetical" in reasoning_text.lower():
                score_value = 1
                metadata['contains_alphabetical'] = True
            else:
                score_value = 0
                metadata['contains_alphabetical'] = False
        else:
            # No reasoning trace found
            score_value = 0
            metadata['reasoning_trace'] = None
            metadata['reasoning_trace_length'] = 0
            metadata['contains_alphabetical'] = False
            metadata['error'] = 'No reasoning trace found'
        
        return Score(
            value=score_value,
            answer=reasoning_text if reasoning_text else "",
            metadata=metadata
        )
    
    return score


def extract_reasoning_trace(state: TaskState) -> Optional[str]:
    """
    Extract reasoning trace from the state object.
    
    Looks for reasoning in state.choices[0].message.reasoning
    
    Args:
        state: The TaskState object containing model response
        
    Returns:
        The reasoning trace text if found, None otherwise
    """
    try:
        # Check if state has choices attribute
        if hasattr(state, 'choices') and state.choices:
            # Get the first choice
            first_choice = state.choices[0]
            
            # Check if the choice has a message with reasoning
            if hasattr(first_choice, 'message'):
                message = first_choice.message
                
                # Check for reasoning attribute
                if hasattr(message, 'reasoning'):
                    reasoning = message.reasoning
                    if reasoning:
                        return str(reasoning)
        
        # Alternative: Check if there's a completion with reasoning
        if hasattr(state, 'completion') and state.completion:
            completion = state.completion
            
            # Check if completion has choices
            if hasattr(completion, 'choices') and completion.choices:
                first_choice = completion.choices[0]
                
                # Check for message.reasoning
                if hasattr(first_choice, 'message'):
                    message = first_choice.message
                    if hasattr(message, 'reasoning'):
                        reasoning = message.reasoning
                        if reasoning:
                            return str(reasoning)
        
        # Also check state.output for any reasoning-related content
        if hasattr(state, 'output') and state.output:
            output = state.output
            
            # If output has choices structure
            if hasattr(output, 'choices') and output.choices:
                first_choice = output.choices[0]
                if hasattr(first_choice, 'message'):
                    message = first_choice.message
                    if hasattr(message, 'reasoning'):
                        reasoning = message.reasoning
                        if reasoning:
                            return str(reasoning)
        
        # Final fallback: Check messages in state for any with reasoning
        if hasattr(state, 'messages') and state.messages:
            for message in state.messages:
                if hasattr(message, 'reasoning') and message.reasoning:
                    return str(message.reasoning)
        
    except (AttributeError, IndexError, TypeError) as e:
        # Log the error for debugging but don't crash
        # Just return None to indicate no reasoning trace found
        pass
    
    return None