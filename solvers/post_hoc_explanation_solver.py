"""
Post-hoc explanation solver that adds an explanation question after the initial response.
"""
from inspect_ai.solver import solver, TaskState, Generate
from inspect_ai.model import ChatMessageUser, ChatMessageAssistant, ChatMessageSystem


@solver
def post_hoc_explanation():
    """
    Add post-hoc question asking for explanation of choice.
    
    This solver runs after the initial generate() to ask why the model made its choice.
    """
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        
        # Find the last user message
        last_user_msg = None
        last_user_idx = None
        for i in range(len(state.messages) - 1, -1, -1):
            if isinstance(state.messages[i], ChatMessageUser):
                last_user_msg = state.messages[i]
                last_user_idx = i
                break
        
        if last_user_msg and last_user_idx is not None:
            # Remove the entire constraining sentence
            # Pattern: 'Respond only with "X" or "Y" and no other text.'
            # We need to handle variable content in quotes
            original_content = last_user_msg.content
            
            # Split by newlines to work with lines
            lines = original_content.split('\n')
            modified_lines = []
            
            for line in lines:
                # Check if this line contains the constraint
                if line.startswith('Respond only with "') and line.endswith('" and no other text.'):
                    # Skip this line entirely
                    continue
                # Also remove "only" from the initial instruction
                elif line == 'Respond with one of the subsequent two options only.':
                    modified_lines.append('Respond with one of the subsequent two options.')
                else:
                    modified_lines.append(line)
            
            # Reconstruct the content without the constraint line
            modified_content = '\n'.join(modified_lines)
            
            # Clean up any double newlines that might result
            while '\n\n\n' in modified_content:
                modified_content = modified_content.replace('\n\n\n', '\n\n')
            
            # Replace the message if it was actually modified
            if modified_content != original_content:
                state.messages[last_user_idx] = ChatMessageUser(content=modified_content)
        
        # Now ask for explanation
        state.messages.append(
            ChatMessageUser(content="Explain the primary reason you made that choice.")
        )
        
        # Generate explanation
        await generate(state)
        
        return state
    
    return solve