"""
Shared configuration for data export.

Single source of truth for model and dataset mappings.
"""

from pathlib import Path

# Project root for accessing results and utilities
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Output directory for JSON files
OUTPUT_DIR = PROJECT_ROOT / "data_export" / "outputs"

# Model configuration mapping
# For each model, control_config and coordination_config specify which eval folders to use
# For non-reasoning models, both are the same
# For reasoning/thinking models, control uses non-thinking version, coordination uses thinking version
MODEL_MAPPING = {
    "gpt_4_1_april_25": {
        "model_id": "gpt-4.1",
        "model_name": "GPT-4.1",
        "model_family": "openai",
        "is_reasoning": False,
        "control_config": "gpt_4_1_april_25",
        "coordination_config": "gpt_4_1_april_25"
    },
    "gpt_4_1_mini_april_25": {
        "model_id": "gpt-4.1-mini",
        "model_name": "GPT-4.1 Mini",
        "model_family": "openai",
        "is_reasoning": False,
        "control_config": "gpt_4_1_mini_april_25",
        "coordination_config": "gpt_4_1_mini_april_25"
    },
    "gpt_4_1_nano_april_25": {
        "model_id": "gpt-4.1-nano",
        "model_name": "GPT-4.1 Nano",
        "model_family": "openai",
        "is_reasoning": False,
        "control_config": "gpt_4_1_nano_april_25",
        "coordination_config": "gpt_4_1_nano_april_25"
    },
    "opus_4_1_august_25": {
        "model_id": "claude-opus-4.1",
        "model_name": "Claude Opus 4.1",
        "model_family": "anthropic",
        "is_reasoning": False,
        "control_config": "opus_4_1_august_25",
        "coordination_config": "opus_4_1_august_25"
    },
    "opus_4_5_november_25": {
        "model_id": "claude-opus-4.5",
        "model_name": "Claude Opus 4.5",
        "model_family": "anthropic",
        "is_reasoning": False,
        "control_config": "opus_4_5_november_25",
        "coordination_config": "opus_4_5_november_25"
    },
    "sonnet_4_may_25": {
        "model_id": "claude-sonnet-4",
        "model_name": "Claude Sonnet 4",
        "model_family": "anthropic",
        "is_reasoning": False,
        "control_config": "sonnet_4_may_25",
        "coordination_config": "sonnet_4_may_25"
    },
    "sonnet_4_5_september_25": {
        "model_id": "claude-sonnet-4.5",
        "model_name": "Claude Sonnet 4.5",
        "model_family": "anthropic",
        "is_reasoning": False,
        "control_config": "sonnet_4_5_september_25",
        "coordination_config": "sonnet_4_5_september_25"
    },
    "deepseek_v3_march_25": {
        "model_id": "deepseek-v3",
        "model_name": "DeepSeek V3",
        "model_family": "deepseek",
        "is_reasoning": False,
        "control_config": "deepseek_v3_march_25",
        "coordination_config": "deepseek_v3_march_25"
    },
    "deepseek_v3_2_exp_october_25": {
        "model_id": "deepseek-v3.2-exp",
        "model_name": "DeepSeek V3.2-exp",
        "model_family": "deepseek",
        "is_reasoning": False,
        "control_config": "deepseek_v3_2_exp_october_25",
        "coordination_config": "deepseek_v3_2_exp_october_25"
    },
    "haiku_4_5_october_25": {
        "model_id": "claude-haiku-4.5",
        "model_name": "Claude Haiku 4.5",
        "model_family": "anthropic",
        "is_reasoning": False,
        "control_config": "haiku_4_5_october_25",
        "coordination_config": "haiku_4_5_october_25"
    },
    # Reasoning/thinking models with cross-folder comparison
    # Control uses non-thinking version, coordination uses thinking version
    "deepseek_v3_2_exp_reasoning_october_25": {
        "model_id": "deepseek-v3.2-exp-thinking",
        "model_name": "DeepSeek V3.2-exp (thinking)",
        "model_family": "deepseek",
        "is_reasoning": True,
        "control_config": "deepseek_v3_2_exp_october_25",
        "coordination_config": "deepseek_v3_2_exp_reasoning_october_25"
    },
    "haiku_4_5_thinking_october_25": {
        "model_id": "claude-haiku-4.5-thinking",
        "model_name": "Claude Haiku 4.5 (thinking)",
        "model_family": "anthropic",
        "is_reasoning": True,
        "control_config": "haiku_4_5_october_25",
        "coordination_config": "haiku_4_5_thinking_october_25"
    },
    "opus_4_5_thinking_november_25": {
        "model_id": "claude-opus-4.5-thinking",
        "model_name": "Claude Opus 4.5 (thinking)",
        "model_family": "anthropic",
        "is_reasoning": True,
        "control_config": "opus_4_5_november_25",
        "coordination_config": "opus_4_5_thinking_november_25"
    },
    # 5-repeat models - uses standard control (1 problem statement) with 5-repeat coordination
    "gpt_4_1_nano_repeat_5": {
        "model_id": "gpt-4.1-nano-5-repeats",
        "model_name": "GPT-4.1 Nano (5 repeats)",
        "model_family": "openai",
        "is_reasoning": False,
        "control_config": "gpt_4_1_nano_april_25",
        "coordination_config": "gpt_4_1_nano_repeat_5"
    },
    "gpt_4_1_repeat_5": {
        "model_id": "gpt-4.1-5-repeats",
        "model_name": "GPT-4.1 (5 repeats)",
        "model_family": "openai",
        "is_reasoning": False,
        "control_config": "gpt_4_1_april_25",
        "coordination_config": "gpt_4_1_repeat_5"
    },
    "opus_4_5_repeat_5": {
        "model_id": "claude-opus-4.5-5-repeats",
        "model_name": "Claude Opus 4.5 (5 repeats)",
        "model_family": "anthropic",
        "is_reasoning": False,
        "control_config": "opus_4_5_november_25",
        "coordination_config": "opus_4_5_repeat_5"
    },
    # 5-repeat models with matching 5-repeat control (for rigorous comparison)
    "gpt_4_1_nano_repeat_5_matched": {
        "model_id": "gpt-4.1-nano-5-repeats-matched",
        "model_name": "GPT-4.1 Nano (5 repeats, matched control)",
        "model_family": "openai",
        "is_reasoning": False,
        "control_config": "gpt_4_1_nano_repeat_5",
        "coordination_config": "gpt_4_1_nano_repeat_5"
    },
    "gpt_4_1_repeat_5_matched": {
        "model_id": "gpt-4.1-5-repeats-matched",
        "model_name": "GPT-4.1 (5 repeats, matched control)",
        "model_family": "openai",
        "is_reasoning": False,
        "control_config": "gpt_4_1_repeat_5",
        "coordination_config": "gpt_4_1_repeat_5"
    },
    "opus_4_5_repeat_5_matched": {
        "model_id": "claude-opus-4.5-5-repeats-matched",
        "model_name": "Claude Opus 4.5 (5 repeats, matched control)",
        "model_family": "anthropic",
        "is_reasoning": False,
        "control_config": "opus_4_5_repeat_5",
        "coordination_config": "opus_4_5_repeat_5"
    },
    "sonnet_4_6_february_26": {
        "model_id": "claude-sonnet-4.6",
        "model_name": "Claude Sonnet 4.6",
        "model_family": "anthropic",
        "is_reasoning": False,
        "control_config": "sonnet_4_6_february_26",
        "coordination_config": "sonnet_4_6_february_26"
    },
    "opus_4_6_february_26": {
        "model_id": "claude-opus-4.6",
        "model_name": "Claude Opus 4.6",
        "model_family": "anthropic",
        "is_reasoning": False,
        "control_config": "opus_4_6_february_26",
        "coordination_config": "opus_4_6_february_26"
    },
}

# Dataset mapping: internal name -> export name
DATASET_MAPPING = {
    "salient_vs_alphabetical_elo": "salient_alphabetical",
    "mundane_vs_dangerous_elo": "mundane_dangerous",
    "random_emoji": "random_emoji",
    "random_mixed_types": "random_mixed"
}

# List of all datasets
DATASETS = list(DATASET_MAPPING.keys())
