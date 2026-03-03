#!/bin/bash
# Example: Run evaluations in batch mode (50% cost reduction for supported providers)
#
# This script demonstrates how to run a full set of evaluations across
# multiple model configs, prompt templates, and datasets.
#
# Modify the CONFIGS, PROMPTS, and DATASETS arrays for your needs.
# Evals that already have results in results/ will be skipped.
#
# Usage:
#   chmod +x run_example_batch.sh
#   ./run_example_batch.sh

set -uo pipefail

# Check if eval already has results
has_results() {
    local config="$1"
    local prompt="$2"
    local dataset="$3"
    local results_dir="results/${config}/${prompt}/${dataset}"

    if [ -d "$results_dir" ] && [ -n "$(find "$results_dir" -name "*.eval" -type f 2>/dev/null | head -1)" ]; then
        return 0  # Has results
    fi
    return 1  # No results
}

# Run eval if no results exist
run_if_missing() {
    local config="$1"
    local prompt="$2"
    local dataset="$3"
    local pairs_file="data/${dataset}.json"

    echo ""
    echo "=== ${config}: ${prompt} ${dataset} ==="

    if has_results "$config" "$prompt" "$dataset"; then
        echo "  SKIPPED - results already exist"
        return 0
    fi

    echo "  Running eval..."
    python run_eval.py --config "$config" --prompt "$prompt" --pairs "$pairs_file" --batch

    if [ $? -eq 0 ]; then
        echo "  Submitted successfully"
    else
        echo "  Failed"
        return 1
    fi
}

# ============================================================
# CONFIGURE YOUR EVAL RUN HERE
# ============================================================

# Which model configs to run (see eval_configs.py for all options)
CONFIGS=(
    "gpt_4_1_april_25"
    # "opus_4_5_november_25"
    # "sonnet_4_6_february_26"
)

# Which prompt templates to use
PROMPTS=(
    "control_sita"          # Control condition (no coordination instruction)
    "coordination_sita"     # Coordination condition (with coordination instruction)
)

# Which datasets to evaluate on
DATASETS=(
    "salient_vs_alphabetical_elo"
    "mundane_vs_dangerous_elo"
    "random_emoji"
    "random_mixed_types"
)

# ============================================================

echo "========================================"
echo "Batch Evaluation Run"
echo "========================================"
echo "Models: ${CONFIGS[*]}"
echo "Datasets: ${#DATASETS[@]}"
echo "Prompts: ${#PROMPTS[@]}"
echo "Total evals: $(( ${#CONFIGS[@]} * ${#DATASETS[@]} * ${#PROMPTS[@]} ))"
echo "========================================"

for config in "${CONFIGS[@]}"; do
    echo ""
    echo "----------------------------------------"
    echo "Model: ${config}"
    echo "----------------------------------------"

    for prompt in "${PROMPTS[@]}"; do
        for dataset in "${DATASETS[@]}"; do
            run_if_missing "$config" "$prompt" "$dataset"
        done
    done
done

echo ""
echo "========================================"
echo "All evals submitted!"
echo "Check batch status with: uv run inspect batch list"
echo "========================================"
