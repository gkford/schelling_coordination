"""
LLM utility functions for making individual calls.
"""

import litellm
from elo_constants import (
    SYSTEM_PROMPT, 
    USER_PROMPT_TEMPLATE,
    TEMPERATURE,
    TOP_P,
    MAX_TOKENS,
    TIMEOUT,
    MAX_RETRIES
)

# Configure litellm
litellm.drop_params = True  # Drop unsupported parameters silently
litellm.set_verbose = False  # Disable verbose logging

# Enable debug mode for troubleshooting
# Uncomment the line below to see detailed debug output
# litellm._turn_on_debug()

def clean_response(response):
    """
    Strips quotes and whitespace from LLM response.
    Handles both single and double quotes.
    
    Args:
        response: Raw LLM response
        
    Returns:
        str: Cleaned response
    """
    if not response:
        return ""
    
    # Strip whitespace
    cleaned = response.strip()
    
    # Remove quotes if present
    if len(cleaned) >= 2:
        if (cleaned[0] == '"' and cleaned[-1] == '"') or \
           (cleaned[0] == "'" and cleaned[-1] == "'"):
            cleaned = cleaned[1:-1].strip()
    
    return cleaned

def make_single_llm_call(item1, item2, model, use_defaults=False, temperature=None, top_p=None, top_k=None):
    """
    Makes a single LLM call with two items in the specified order.
    
    Args:
        item1: First item to present
        item2: Second item to present
        model: Model name (e.g., "gpt-4", "claude-3-opus")
    
    Returns:
        str: The raw response from the model
        
    Raises:
        Exception: If the LLM call fails after retries
    """
    # Construct the user prompt
    user_prompt = USER_PROMPT_TEMPLATE.format(item1=item1, item2=item2)
    
    # Prepare messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
    
    # Make the LLM call with retries
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            # Build kwargs based on use_defaults
            kwargs = {
                "model": model,
                "messages": messages,
                "max_tokens": MAX_TOKENS,
                "timeout": TIMEOUT
            }
            
            # Handle sampling parameter settings
            if top_k is not None:
                # If top_k is set, only use top_k and let temp/top_p use model defaults
                kwargs["top_k"] = top_k
            elif temperature is not None or top_p is not None:
                # If either temp or top_p is explicitly set, use what's provided
                if temperature is not None:
                    kwargs["temperature"] = temperature
                if top_p is not None:
                    kwargs["top_p"] = top_p
            elif not use_defaults:
                # If not using defaults and no explicit values, use constants
                kwargs["temperature"] = TEMPERATURE
                kwargs["top_p"] = TOP_P
            
            response = litellm.completion(**kwargs)
            
            # Extract the response text
            if response and response.choices and len(response.choices) > 0:
                return response.choices[0].message.content
            else:
                raise ValueError("Empty response from model")
                
        except Exception as e:
            last_error = e
            # Print the actual error message for debugging
            if hasattr(e, 'response') and e.response:
                print(f"Error response: {e.response}")
                if hasattr(e.response, 'text'):
                    print(f"Error details: {e.response.text}")
            if attempt < MAX_RETRIES - 1:
                # Wait briefly before retry (could add exponential backoff here)
                import time
                time.sleep(1)
            continue
    
    # If we get here, all retries failed
    raise Exception(f"Failed to get response after {MAX_RETRIES} attempts. Last error: {last_error}")

def validate_choice(choice, item1, item2):
    """
    Validates if a choice matches one of the two items.
    
    Args:
        choice: Raw LLM response
        item1: First valid option
        item2: Second valid option
    
    Returns:
        tuple: (is_valid: bool, cleaned_choice: str or None)
    """
    cleaned = clean_response(choice)
    
    if cleaned == item1:
        return (True, item1)
    elif cleaned == item2:
        return (True, item2)
    else:
        return (False, None)

if __name__ == "__main__":
    # Test the functions
    print("Testing LLM utilities...")
    
    # Test response cleaning
    test_responses = [
        '"fire"',
        "'fire'",
        " fire ",
        "fire",
        '  "fire"  ',
        ""
    ]
    
    print("\nTesting clean_response:")
    for resp in test_responses:
        cleaned = clean_response(resp)
        print(f"'{resp}' -> '{cleaned}'")
    
    # Test validation
    print("\nTesting validate_choice:")
    test_cases = [
        ("fire", "fire", "water"),
        ('"fire"', "fire", "water"),
        ("water", "fire", "water"),
        ("earth", "fire", "water"),
        ("", "fire", "water")
    ]
    
    for choice, item1, item2 in test_cases:
        is_valid, cleaned = validate_choice(choice, item1, item2)
        print(f"Choice: '{choice}', Items: [{item1}, {item2}] -> Valid: {is_valid}, Cleaned: {cleaned}")