"""
Eval results reader.

Loads and processes .eval files from the results directory,
extracting pair-level convergence data.
"""

from pathlib import Path
from inspect_ai.log import read_eval_log


def get_eval_results_by_features(config_name, prompt_identifier, dataset_name):
    """Get eval results by specifying config, prompt, and dataset names.

    Args:
        config_name: Name of the eval config (e.g., "gpt_4_1_mini_april_25")
        prompt_identifier: Name of the prompt (e.g., "control_sita")
        dataset_name: Name of the dataset (e.g., "mundane_vs_dangerous_elo")

    Returns:
        Dict with eval results if successful, or None if file not found
        May also return dict with 'error' key if there's an exception
    """
    # Build path
    results_path = Path(__file__).parent.parent / "results"
    eval_path = results_path / config_name / prompt_identifier / dataset_name

    # Check if path exists
    if not eval_path.exists():
        return {'error': f"Path not found: {eval_path}"}

    # Find eval file
    eval_files = list(eval_path.glob("*.eval"))

    if len(eval_files) == 0:
        return {'error': f"No .eval file found in: {eval_path}"}
    elif len(eval_files) > 1:
        return {'error': f"Multiple eval files found in {eval_path}"}

    # Read and return results
    try:
        eval_log = read_eval_log(str(eval_files[0]))

        # Get metadata from run level
        run_metadata = eval_log.eval.metadata if hasattr(eval_log.eval, 'metadata') and eval_log.eval.metadata else {}

        # Extract model parameters from eval config
        temperature = None
        top_p = None

        # Check if model_generate_config exists and has the parameters
        if hasattr(eval_log.eval, 'model_generate_config') and eval_log.eval.model_generate_config:
            temperature = eval_log.eval.model_generate_config.temperature
            top_p = eval_log.eval.model_generate_config.top_p

        metadata = {
            'model': eval_log.eval.model,
            'temperature': temperature,
            'top_p': top_p,
            'dataset_id': run_metadata.get('dataset_id', 'unknown'),
            'dataset_hash': run_metadata.get('dataset_hash', ''),
            'total_pairs': run_metadata.get('total_pairs', len(eval_log.samples) // 2),
            'eval_path': str(eval_files[0]),
            'prompt_identifier': run_metadata.get('prompt_identifier', 'unknown')
        }

        # Process samples to extract pair results
        pair_results = {}

        # Initialize sample-level statistics
        sample_stats = {
            'total_samples': 0,
            'valid_samples': 0,
            'invalid_samples': 0,
            'option_A_samples': 0,
            'option_B_samples': 0,
            'samples_by_order': {
                'AB': {'total': 0, 'valid': 0, 'invalid': 0, 'option_A': 0, 'option_B': 0},
                'BA': {'total': 0, 'valid': 0, 'invalid': 0, 'option_A': 0, 'option_B': 0}
            }
        }

        for sample in eval_log.samples:
            if not sample.scores:
                continue

            pair_id = sample.metadata.get('pair_id')
            order = sample.metadata.get('order')  # AB or BA

            if pair_id not in pair_results:
                pair_results[pair_id] = {
                    'pair_id': pair_id,
                    'option_A': sample.metadata.get('option_A'),
                    'option_B': sample.metadata.get('option_B'),
                    'AB_response': None,
                    'BA_response': None,
                    'AB_choice': None,
                    'BA_choice': None,
                    'AB_reasoning_tokens': None,
                    'BA_reasoning_tokens': None,
                    'converged': False,
                    'converged_on': None,
                    'converged_on_option': None,
                    'pattern': None
                }

            # Get the response and choice from the validation_scorer
            validation_score = sample.scores.get('validation_scorer')
            if not validation_score:
                continue

            response = validation_score.answer
            choice = validation_score.metadata.get('choice', 'invalid')
            reasoning_tokens = validation_score.metadata.get('reasoning_tokens', None)

            # Update sample-level statistics
            sample_stats['total_samples'] += 1

            if order in sample_stats['samples_by_order']:
                sample_stats['samples_by_order'][order]['total'] += 1

            if choice == 'A':
                sample_stats['valid_samples'] += 1
                sample_stats['option_A_samples'] += 1
                if order in sample_stats['samples_by_order']:
                    sample_stats['samples_by_order'][order]['valid'] += 1
                    sample_stats['samples_by_order'][order]['option_A'] += 1
            elif choice == 'B':
                sample_stats['valid_samples'] += 1
                sample_stats['option_B_samples'] += 1
                if order in sample_stats['samples_by_order']:
                    sample_stats['samples_by_order'][order]['valid'] += 1
                    sample_stats['samples_by_order'][order]['option_B'] += 1
            else:
                sample_stats['invalid_samples'] += 1
                if order in sample_stats['samples_by_order']:
                    sample_stats['samples_by_order'][order]['invalid'] += 1

            if order == 'AB':
                pair_results[pair_id]['AB_response'] = response
                pair_results[pair_id]['AB_choice'] = choice
                pair_results[pair_id]['AB_reasoning_tokens'] = reasoning_tokens
            else:  # BA
                pair_results[pair_id]['BA_response'] = response
                pair_results[pair_id]['BA_choice'] = choice
                pair_results[pair_id]['BA_reasoning_tokens'] = reasoning_tokens

        # Determine convergence for each pair
        for pair_id, result in pair_results.items():
            ab_choice = result['AB_choice']
            ba_choice = result['BA_choice']

            # Check if both are valid choices
            if ab_choice in ['A', 'B'] and ba_choice in ['A', 'B']:
                # The choice letters (A/B) refer to which option was chosen, not position
                # A always means option_A, B always means option_B
                ab_actual = result['option_A'] if ab_choice == 'A' else result['option_B']
                ba_actual = result['option_A'] if ba_choice == 'A' else result['option_B']

                if ab_actual == ba_actual:
                    # They converged
                    result['converged'] = True
                    result['converged_on'] = ab_actual
                    # Add converged_on_option: A or B based on which option they converged on
                    result['converged_on_option'] = ab_choice if ab_choice == ba_choice else None
                else:
                    # They differed
                    result['converged'] = False
                    result['converged_on'] = None
                    result['converged_on_option'] = None
                    # Determine pattern based on positions chosen
                    # In AB order: first position is A, second is B
                    # In BA order: first position is B, second is A
                    ab_position = 'first' if ab_choice == 'A' else 'second'
                    ba_position = 'first' if ba_choice == 'B' else 'second'

                    if ab_position == 'first' and ba_position == 'first':
                        result['pattern'] = 'first_first'
                    elif ab_position == 'second' and ba_position == 'second':
                        result['pattern'] = 'second_second'
                    else:
                        result['pattern'] = 'mixed'  # Shouldn't happen in our setup
            else:
                # Invalid response(s)
                result['converged'] = False
                result['converged_on'] = None
                result['converged_on_option'] = None
                result['pattern'] = 'invalid'

        return {
            'metadata': metadata,
            'pair_results': pair_results,
            'sample_stats': sample_stats
        }
    except Exception as e:
        return {'error': f"Error reading eval file: {str(e)}"}
