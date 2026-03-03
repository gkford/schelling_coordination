"""
Comparison utilities for categorizing and summarizing pair results
between control and coordination evaluations.
"""


def categorize_pair_results(eval1_results, eval2_results):
    """
    Categorize pairs based on convergence patterns between two evaluations.

    Args:
        eval1_results: Results from first evaluation
        eval2_results: Results from second evaluation

    Returns:
        Dict with keys:
            - 'both_converged': Pairs that converged in both evaluations
            - 'eval1_converged_eval2_differed': Pairs that converged in eval1 but differed in eval2
            - 'eval1_differed_eval2_converged': Pairs that differed in eval1 but converged in eval2
            - 'both_differed': Pairs that differed in both evaluations
            - 'invalid_pairs': Pairs with invalid responses in at least one evaluation
    """
    both_converged = []
    eval1_converged_eval2_differed = []
    eval1_differed_eval2_converged = []
    both_differed = []
    invalid_pairs = []

    # Get all pair IDs from eval1
    for pair_id, eval1_pair in eval1_results['pair_results'].items():
        # Skip if not in eval2
        if pair_id not in eval2_results['pair_results']:
            continue

        eval2_pair = eval2_results['pair_results'][pair_id]

        # Check if either evaluation has invalid pattern
        if eval1_pair['pattern'] == 'invalid' or eval2_pair['pattern'] == 'invalid':
            # This is an invalid pair for comparison purposes
            invalid_entry = {
                'pair_id': pair_id,
                'option_A': eval1_pair['option_A'],
                'option_B': eval1_pair['option_B'],
                'eval_1': {
                    'AB_response': eval1_pair['AB_response'],
                    'BA_response': eval1_pair['BA_response'],
                    'outcome': 'converged' if eval1_pair['converged'] else
                              ('invalid' if eval1_pair['pattern'] == 'invalid' else 'differed')
                },
                'eval_2': {
                    'AB_response': eval2_pair['AB_response'],
                    'BA_response': eval2_pair['BA_response'],
                    'outcome': 'converged' if eval2_pair['converged'] else
                              ('invalid' if eval2_pair['pattern'] == 'invalid' else 'differed')
                }
            }
            invalid_pairs.append(invalid_entry)
            continue

        # Build result entry for valid pairs
        result_entry = {
            'pair_id': pair_id,
            'option_A': eval1_pair['option_A'],
            'option_B': eval1_pair['option_B']
        }

        # Categorize based on convergence (only for valid pairs)
        if eval1_pair['converged'] and eval2_pair['converged']:
            # Both converged
            result_entry['eval_1_converged_on'] = eval1_pair['converged_on']
            result_entry['eval_2_converged_on'] = eval2_pair['converged_on']
            result_entry['eval_1_converged_on_option'] = eval1_pair.get('converged_on_option')
            result_entry['eval_2_converged_on_option'] = eval2_pair.get('converged_on_option')
            result_entry['converged_on_same'] = eval1_pair['converged_on'] == eval2_pair['converged_on']
            result_entry['eval_1'] = {
                'AB_response': eval1_pair['AB_response'],
                'BA_response': eval1_pair['BA_response'],
                'outcome': 'converged'
            }
            result_entry['eval_2'] = {
                'AB_response': eval2_pair['AB_response'],
                'BA_response': eval2_pair['BA_response'],
                'outcome': 'converged'
            }
            both_converged.append(result_entry)

        elif eval1_pair['converged'] and not eval2_pair['converged']:
            # Eval 1 converged, Eval 2 differed
            result_entry['eval_1_converged_on'] = eval1_pair['converged_on']
            result_entry['eval_1_converged_on_option'] = eval1_pair.get('converged_on_option')
            result_entry['eval_2_pattern'] = eval2_pair['pattern']
            result_entry['eval_1'] = {
                'AB_response': eval1_pair['AB_response'],
                'BA_response': eval1_pair['BA_response'],
                'outcome': 'converged'
            }
            result_entry['eval_2'] = {
                'AB_response': eval2_pair['AB_response'],
                'BA_response': eval2_pair['BA_response'],
                'outcome': 'differed'
            }
            eval1_converged_eval2_differed.append(result_entry)

        elif not eval1_pair['converged'] and eval2_pair['converged']:
            # Eval 1 differed, Eval 2 converged
            result_entry['eval_1_pattern'] = eval1_pair['pattern']
            result_entry['eval_2_converged_on'] = eval2_pair['converged_on']
            result_entry['eval_2_converged_on_option'] = eval2_pair.get('converged_on_option')
            result_entry['eval_1'] = {
                'AB_response': eval1_pair['AB_response'],
                'BA_response': eval1_pair['BA_response'],
                'outcome': 'differed'
            }
            result_entry['eval_2'] = {
                'AB_response': eval2_pair['AB_response'],
                'BA_response': eval2_pair['BA_response'],
                'outcome': 'converged'
            }
            eval1_differed_eval2_converged.append(result_entry)

        else:
            # Both differed
            result_entry['eval_1_pattern'] = eval1_pair['pattern']
            result_entry['eval_2_pattern'] = eval2_pair['pattern']
            result_entry['eval_1'] = {
                'AB_response': eval1_pair['AB_response'],
                'BA_response': eval1_pair['BA_response'],
                'outcome': 'differed'
            }
            result_entry['eval_2'] = {
                'AB_response': eval2_pair['AB_response'],
                'BA_response': eval2_pair['BA_response'],
                'outcome': 'differed'
            }
            both_differed.append(result_entry)

    # Extract metadata - model and dataset should be the same for both evals
    eval1_metadata = eval1_results.get('metadata', {})
    eval2_metadata = eval2_results.get('metadata', {})

    # Use eval1's model and dataset, but verify they match
    model = eval1_metadata.get('model', 'unknown')
    dataset = eval1_metadata.get('dataset_id', 'unknown')

    # Optionally warn if there's a mismatch (shouldn't happen in normal usage)
    if eval2_metadata.get('model') and eval2_metadata.get('model') != model:
        print(f"Warning: Model mismatch - eval1: {model}, eval2: {eval2_metadata.get('model')}")
    if eval2_metadata.get('dataset_id') and eval2_metadata.get('dataset_id') != dataset:
        print(f"Warning: Dataset mismatch - eval1: {dataset}, eval2: {eval2_metadata.get('dataset_id')}")

    return {
        'both_converged': both_converged,
        'eval1_converged_eval2_differed': eval1_converged_eval2_differed,
        'eval1_differed_eval2_converged': eval1_differed_eval2_converged,
        'both_differed': both_differed,
        'invalid_pairs': invalid_pairs,
        'eval1_prompt': eval1_metadata.get('prompt_identifier', 'unknown'),
        'eval2_prompt': eval2_metadata.get('prompt_identifier', 'unknown'),
        'model_name_from_inspect': model,
        'dataset': dataset
    }


def calculate_sample_level_stats(categorized_results):
    """
    Calculate sample-level statistics for each category of pairs.

    Args:
        categorized_results: Dict returned by categorize_pair_results

    Returns:
        Dict with sample-level counts for options (A/B) and positions (first/second)
    """
    stats = {
        'both_converged': {
            'eval1': {'samples_A': 0, 'samples_B': 0, 'samples_first': 0, 'samples_second': 0},
            'eval2': {'samples_A': 0, 'samples_B': 0, 'samples_first': 0, 'samples_second': 0}
        },
        'eval1_converged_eval2_differed': {
            'eval1': {'samples_A': 0, 'samples_B': 0, 'samples_first': 0, 'samples_second': 0},
            'eval2': {'samples_A': 0, 'samples_B': 0, 'samples_first': 0, 'samples_second': 0}
        },
        'eval1_differed_eval2_converged': {
            'eval1': {'samples_A': 0, 'samples_B': 0, 'samples_first': 0, 'samples_second': 0},
            'eval2': {'samples_A': 0, 'samples_B': 0, 'samples_first': 0, 'samples_second': 0}
        },
        'both_differed': {
            'eval1': {'samples_A': 0, 'samples_B': 0, 'samples_first': 0, 'samples_second': 0},
            'eval2': {'samples_A': 0, 'samples_B': 0, 'samples_first': 0, 'samples_second': 0}
        }
    }

    def tally_samples(pairs, category_key):
        """Helper to tally sample choices for a category of pairs."""
        for pair in pairs:
            option_A = pair['option_A']
            option_B = pair['option_B']

            # Eval1 samples
            ab_response = pair['eval_1']['AB_response']
            ba_response = pair['eval_1']['BA_response']

            # AB order: A is first, B is second
            if ab_response == option_A:
                stats[category_key]['eval1']['samples_A'] += 1
                stats[category_key]['eval1']['samples_first'] += 1
            elif ab_response == option_B:
                stats[category_key]['eval1']['samples_B'] += 1
                stats[category_key]['eval1']['samples_second'] += 1

            # BA order: B is first, A is second
            if ba_response == option_A:
                stats[category_key]['eval1']['samples_A'] += 1
                stats[category_key]['eval1']['samples_second'] += 1
            elif ba_response == option_B:
                stats[category_key]['eval1']['samples_B'] += 1
                stats[category_key]['eval1']['samples_first'] += 1

            # Eval2 samples
            ab_response = pair['eval_2']['AB_response']
            ba_response = pair['eval_2']['BA_response']

            # AB order: A is first, B is second
            if ab_response == option_A:
                stats[category_key]['eval2']['samples_A'] += 1
                stats[category_key]['eval2']['samples_first'] += 1
            elif ab_response == option_B:
                stats[category_key]['eval2']['samples_B'] += 1
                stats[category_key]['eval2']['samples_second'] += 1

            # BA order: B is first, A is second
            if ba_response == option_A:
                stats[category_key]['eval2']['samples_A'] += 1
                stats[category_key]['eval2']['samples_second'] += 1
            elif ba_response == option_B:
                stats[category_key]['eval2']['samples_B'] += 1
                stats[category_key]['eval2']['samples_first'] += 1

    # Tally samples for each category
    tally_samples(categorized_results['both_converged'], 'both_converged')
    tally_samples(categorized_results['eval1_converged_eval2_differed'], 'eval1_converged_eval2_differed')
    tally_samples(categorized_results['eval1_differed_eval2_converged'], 'eval1_differed_eval2_converged')
    tally_samples(categorized_results['both_differed'], 'both_differed')

    # Calculate aggregated stats for control-differed pairs
    control_differed_stats = {
        'eval1': {
            'samples_A': (stats['eval1_differed_eval2_converged']['eval1']['samples_A'] +
                         stats['both_differed']['eval1']['samples_A']),
            'samples_B': (stats['eval1_differed_eval2_converged']['eval1']['samples_B'] +
                         stats['both_differed']['eval1']['samples_B']),
            'samples_first': (stats['eval1_differed_eval2_converged']['eval1']['samples_first'] +
                             stats['both_differed']['eval1']['samples_first']),
            'samples_second': (stats['eval1_differed_eval2_converged']['eval1']['samples_second'] +
                              stats['both_differed']['eval1']['samples_second'])
        },
        'eval2': {
            'samples_A': (stats['eval1_differed_eval2_converged']['eval2']['samples_A'] +
                         stats['both_differed']['eval2']['samples_A']),
            'samples_B': (stats['eval1_differed_eval2_converged']['eval2']['samples_B'] +
                         stats['both_differed']['eval2']['samples_B']),
            'samples_first': (stats['eval1_differed_eval2_converged']['eval2']['samples_first'] +
                             stats['both_differed']['eval2']['samples_first']),
            'samples_second': (stats['eval1_differed_eval2_converged']['eval2']['samples_second'] +
                              stats['both_differed']['eval2']['samples_second'])
        }
    }

    # Calculate sample-level odds ratios for control-differed pairs
    sample_or_option = None
    sample_or_position = None

    # Option OR (A vs B)
    if (control_differed_stats['eval1']['samples_B'] > 0 and
        control_differed_stats['eval2']['samples_B'] > 0 and
        control_differed_stats['eval1']['samples_A'] > 0 and
        control_differed_stats['eval2']['samples_A'] > 0):

        eval1_odds = control_differed_stats['eval1']['samples_A'] / control_differed_stats['eval1']['samples_B']
        eval2_odds = control_differed_stats['eval2']['samples_A'] / control_differed_stats['eval2']['samples_B']
        sample_or_option = eval2_odds / eval1_odds

    # Position OR (first vs second)
    if (control_differed_stats['eval1']['samples_second'] > 0 and
        control_differed_stats['eval2']['samples_second'] > 0 and
        control_differed_stats['eval1']['samples_first'] > 0 and
        control_differed_stats['eval2']['samples_first'] > 0):

        eval1_odds = control_differed_stats['eval1']['samples_first'] / control_differed_stats['eval1']['samples_second']
        eval2_odds = control_differed_stats['eval2']['samples_first'] / control_differed_stats['eval2']['samples_second']
        sample_or_position = eval2_odds / eval1_odds

    return {
        'by_category': stats,
        'control_differed_aggregated': control_differed_stats,
        'sample_or_option': sample_or_option,
        'sample_or_position': sample_or_position
    }


def generate_comparison_summary(categorized_results):
    """
    Generate a JSON summary from categorized pair results.

    Args:
        categorized_results: Dict returned by categorize_pair_results

    Returns:
        Dict with summary statistics and performance metrics
    """
    # Extract counts
    both_converged_count = len(categorized_results['both_converged'])
    control_converged_intervention_differed = len(categorized_results['eval1_converged_eval2_differed'])
    control_differed_intervention_converged = len(categorized_results['eval1_differed_eval2_converged'])
    both_differed_count = len(categorized_results['both_differed'])
    invalid_count = len(categorized_results['invalid_pairs'])

    # Calculate totals
    valid_pairs = (both_converged_count + control_converged_intervention_differed +
                   control_differed_intervention_converged + both_differed_count)
    total_pairs = valid_pairs + invalid_count

    # Control config totals
    control_converged_total = both_converged_count + control_converged_intervention_differed
    control_differed_total = control_differed_intervention_converged + both_differed_count

    # Control convergence A/B counts
    control_converged_on_A = 0
    control_converged_on_B = 0

    # Count from both_converged
    for pair in categorized_results["both_converged"]:
        if pair.get('eval_1_converged_on_option') == 'A':
            control_converged_on_A += 1
        elif pair.get('eval_1_converged_on_option') == 'B':
            control_converged_on_B += 1

    # Count from eval1_converged_eval2_differed
    for pair in categorized_results["eval1_converged_eval2_differed"]:
        if pair.get('eval_1_converged_on_option') == 'A':
            control_converged_on_A += 1
        elif pair.get('eval_1_converged_on_option') == 'B':
            control_converged_on_B += 1

    # Calculate control percentages
    if control_converged_total > 0:
        control_pct_A_of_converged = round((control_converged_on_A / control_converged_total) * 100, 1)
        control_pct_B_of_converged = round((control_converged_on_B / control_converged_total) * 100, 1)
    else:
        control_pct_A_of_converged = 0.0
        control_pct_B_of_converged = 0.0

    # Intervention config totals
    intervention_converged_total = both_converged_count + control_differed_intervention_converged
    intervention_differed_total = control_converged_intervention_differed + both_differed_count

    # Intervention convergence A/B counts
    intervention_converged_on_A = 0
    intervention_converged_on_B = 0

    # Count from both_converged
    for pair in categorized_results["both_converged"]:
        if pair.get('eval_2_converged_on_option') == 'A':
            intervention_converged_on_A += 1
        elif pair.get('eval_2_converged_on_option') == 'B':
            intervention_converged_on_B += 1

    # Count from eval1_differed_eval2_converged
    for pair in categorized_results["eval1_differed_eval2_converged"]:
        if pair.get('eval_2_converged_on_option') == 'A':
            intervention_converged_on_A += 1
        elif pair.get('eval_2_converged_on_option') == 'B':
            intervention_converged_on_B += 1

    # Calculate intervention percentages
    if intervention_converged_total > 0:
        intervention_pct_A_of_converged = round((intervention_converged_on_A / intervention_converged_total) * 100, 1)
        intervention_pct_B_of_converged = round((intervention_converged_on_B / intervention_converged_total) * 100, 1)
    else:
        intervention_pct_A_of_converged = 0.0
        intervention_pct_B_of_converged = 0.0

    # Calculate breakdowns for swap_to_converge metric
    swap_to_converge_breakdown = {"A": 0, "B": 0}
    for pair in categorized_results["eval1_differed_eval2_converged"]:
        eval2_option = pair.get('eval_2_converged_on_option')
        if eval2_option == 'A':
            swap_to_converge_breakdown["A"] += 1
        elif eval2_option == 'B':
            swap_to_converge_breakdown["B"] += 1

    # Calculate percentages for swap_to_converge
    swap_to_converge_total = swap_to_converge_breakdown["A"] + swap_to_converge_breakdown["B"]
    if swap_to_converge_total > 0:
        pct_A_of_converged = round((swap_to_converge_breakdown["A"] / swap_to_converge_total) * 100, 1)
        pct_B_of_converged = round((swap_to_converge_breakdown["B"] / swap_to_converge_total) * 100, 1)
    else:
        pct_A_of_converged = 0.0
        pct_B_of_converged = 0.0

    # Calculate breakdowns for maintain_converge metric
    maintained_converge_breakdown = {
        "A_to_A": 0,
        "A_to_B": 0,
        "B_to_A": 0,
        "B_to_B": 0
    }
    for pair in categorized_results["both_converged"]:
        eval1_option = pair.get('eval_1_converged_on_option')
        eval2_option = pair.get('eval_2_converged_on_option')

        if eval1_option == 'A' and eval2_option == 'A':
            maintained_converge_breakdown["A_to_A"] += 1
        elif eval1_option == 'A' and eval2_option == 'B':
            maintained_converge_breakdown["A_to_B"] += 1
        elif eval1_option == 'B' and eval2_option == 'A':
            maintained_converge_breakdown["B_to_A"] += 1
        elif eval1_option == 'B' and eval2_option == 'B':
            maintained_converge_breakdown["B_to_B"] += 1

    # Calculate breakdowns for swap_to_coordinate metric
    swap_to_coordinate_breakdown = {"A": 0, "B": 0}
    for pair in categorized_results["eval1_converged_eval2_differed"]:
        eval1_option = pair.get('eval_1_converged_on_option')
        if eval1_option == 'A':
            swap_to_coordinate_breakdown["A"] += 1
        elif eval1_option == 'B':
            swap_to_coordinate_breakdown["B"] += 1

    # Calculate metrics
    # Swap to converge: Of pairs that differed in control, what % converged in intervention
    if control_differed_total > 0:
        swap_to_converge_pct = (control_differed_intervention_converged / control_differed_total) * 100
    else:
        swap_to_converge_pct = 0.0

    # Maintain converge: Of pairs that converged in control, what % stayed converged in intervention
    if control_converged_total > 0:
        maintain_converge_pct = (both_converged_count / control_converged_total) * 100
    else:
        maintain_converge_pct = 100.0  # If no pairs converged in control, we maintain 100%

    # Swap to coordinate: Of pairs that converged in control, what % differed in intervention (inverse of maintain)
    if control_converged_total > 0:
        swap_to_coordinate_pct = (control_converged_intervention_differed / control_converged_total) * 100
    else:
        swap_to_coordinate_pct = 0.0

    # Maintain differed: Of pairs that differed in control, what % remained differed in intervention
    if control_differed_total > 0:
        maintain_differed_pct = (both_differed_count / control_differed_total) * 100
    else:
        maintain_differed_pct = 100.0  # If no pairs differed in control, we maintain 100%

    # Calculate sample-level statistics
    sample_stats = calculate_sample_level_stats(categorized_results)

    return {
        "prompts": {
            "control": categorized_results.get('eval1_prompt', 'unknown'),
            "intervention": categorized_results.get('eval2_prompt', 'unknown')
        },
        "model_name_from_inspect": categorized_results.get('model_name_from_inspect', 'unknown'),
        "dataset": categorized_results.get('dataset', 'unknown'),
        "control_config": {
            "converged": control_converged_total,
            "differed": control_differed_total,
            "converged_on_A": control_converged_on_A,
            "converged_on_B": control_converged_on_B,
            "pct_A_of_converged": control_pct_A_of_converged,
            "pct_B_of_converged": control_pct_B_of_converged,
            "valid_total": valid_pairs,
            "invalid": invalid_count,
            "total": total_pairs
        },
        "intervention_config": {
            "converged": intervention_converged_total,
            "differed": intervention_differed_total,
            "converged_on_A": intervention_converged_on_A,
            "converged_on_B": intervention_converged_on_B,
            "pct_A_of_converged": intervention_pct_A_of_converged,
            "pct_B_of_converged": intervention_pct_B_of_converged,
            "valid_total": valid_pairs,
            "invalid": invalid_count,
            "total": total_pairs
        },
        "comparison": {
            "valid_pairs": valid_pairs,
            "invalid_pairs": invalid_count,
            "total_pairs": total_pairs,
            "breakdown": {
                "both_converged": both_converged_count,
                "control_config_converged_intervention_config_differed": control_converged_intervention_differed,
                "control_config_differed_intervention_config_converged": control_differed_intervention_converged,
                "both_differed": both_differed_count
            }
        },
        "metrics": {
            "swap_to_converge": {
                "count": control_differed_intervention_converged,
                "base": control_differed_total,
                "percentage": round(swap_to_converge_pct, 1),
                "converged_on_breakdown": swap_to_converge_breakdown,
                "pct_A_of_converged": pct_A_of_converged,
                "pct_B_of_converged": pct_B_of_converged,
                "description": "Of all the valid pairs that differed in Control Config, this is the percentage that converged in Intervention Config. This is the primary metric for measuring coordination."
            },
            "maintain_converge": {
                "count": both_converged_count,
                "base": control_converged_total,
                "percentage": round(maintain_converge_pct, 1),
                "maintained_converge_breakdown": maintained_converge_breakdown,
                "description": "Of all the valid pairs that converged in Control Config, this is the percentage that remained converged in Intervention Config"
            },
            "swap_to_coordinate": {
                "count": control_converged_intervention_differed,
                "base": control_converged_total,
                "percentage": round(swap_to_coordinate_pct, 1),
                "converged_on_breakdown": swap_to_coordinate_breakdown,
                "description": "Of all the valid pairs that converged in Control Config, this is the percentage that differed in Intervention Config"
            },
            "maintain_differed": {
                "count": both_differed_count,
                "base": control_differed_total,
                "percentage": round(maintain_differed_pct, 1),
                "description": "Of all the valid pairs that differed in Control Config, this is the percentage that remained differed in Intervention Config"
            }
        },
        "sample_analysis": {
            "control_differed_pairs": {
                "control_samples": sample_stats['control_differed_aggregated']['eval1'],
                "intervention_samples": sample_stats['control_differed_aggregated']['eval2'],
                "sample_or_option": sample_stats['sample_or_option'],
                "sample_or_position": sample_stats['sample_or_position'],
                "description": "Sample-level analysis for pairs that differed in control"
            },
            "by_category": sample_stats['by_category']
        }
    }
