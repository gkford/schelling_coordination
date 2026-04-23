"""
Evaluation configurations for the pairs evaluation system.

Each configuration must include all required fields:
- model: The full model path (e.g., "groq/llama-3.3-70b-versatile")
- post_hoc_explanation: Whether to request post-hoc explanation (bool)
- reasoning_model: Whether this is a reasoning model (bool)
- model_specific_config: Name of model-specific config or None
- temperature: Temperature setting (float, "default", or "unsupported")
- top_p: Top-p setting (float, "default", or "unsupported")
- max_tokens: Maximum completion tokens (int, "default", or "unsupported")

Optional fields:
- prompt_modifiers: List of prompt modifiers to apply (e.g., ["must_begin_strict"])
  - "must_begin_strict": Adds strict constraint requiring response to begin with exact option
  - Note: "must_begin_strict" is incompatible with post_hoc_explanation

Note: Use "unsupported" for parameters that the model doesn't accept (e.g., gpt-5 models don't support temperature/top_p)
"""

EVAL_CONFIGS = {
    "llama_groq_70b_3-3": {
        "model": "groq/llama-3.3-70b-versatile",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },
    "o4_mini_high_april_25": {
        "model": "openai/o4-mini-2025-04-16",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_high_flex",
        "temperature": "default",
        "top_p": "default",
        "max_tokens": "default"
    },
    
    "gpt_oss_120b": {
        "model": "groq/openai/gpt-oss-120b",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_high_effort",
        "temperature": "default",
        "top_p": "default",
        "max_tokens": "default"
    },

    "gpt_5_nano_min_august_25": {
        "model" : "openai/gpt-5-nano-2025-08-07",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_minimal_flex",
        "temperature": "unsupported",
        "top_p": "unsupported",
        "max_tokens": "default" 
    },
    
    "gpt_5_nano_high_august_25": {
        "model" : "openai/gpt-5-nano-2025-08-07",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_high_flex",
        "temperature": "unsupported",
        "top_p": "unsupported",
        "max_tokens": "default" 
    },

      "gpt_5_mini_min_august_25": {
        "model" : "openai/gpt-5-mini-2025-08-07",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_minimal_flex",
        "temperature": "unsupported",
        "top_p": "unsupported",
        "max_tokens": "default" 
    },
    
    "gpt_5_mini_high_august_25": {
        "model" : "openai/gpt-5-mini-2025-08-07",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_high_flex",
        "temperature": "unsupported",
        "top_p": "unsupported",
        "max_tokens": "default"
    },

    "gpt_5_4_nano_none_march_26": {
        "model": "openai/gpt-5.4-nano-2026-03-17",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_none_flex",
        "temperature": "unsupported",
        "top_p": "unsupported",
        "max_tokens": "default"
    },

    "gpt_5_4_mini_none_march_26": {
        "model": "openai/gpt-5.4-mini-2026-03-17",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_none_flex",
        "temperature": "unsupported",
        "top_p": "unsupported",
        "max_tokens": "default"
    },

    "gpt_5_4_none_march_26": {
        "model": "openai/gpt-5.4-2026-03-05",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_none_flex",
        "temperature": "unsupported",
        "top_p": "unsupported",
        "max_tokens": "default"
    },

    "qwen_3_sept_25": {
        "model": "openrouter/qwen/qwen3-235b-a22b-07-25",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },
    
    "deepseek_v3_march_25": {
        "model": "openrouter/deepseek/deepseek-chat-v3-0324",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },
    
    "sonnet_4_may_25": {
        "model": "anthropic/claude-sonnet-4-20250514",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },
    
    "opus_4_may_25": {
        "model": "anthropic/claude-opus-4-20250514",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },
  
    "opus_4_1_august_25": {
        "model": "anthropic/claude-opus-4-1-20250805",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": "default",
        "top_p": "default",
        "max_tokens": "default",
        "prompt_modifiers": ["must_begin_strict"]
    },

    "haiku_3_5_october_24": {
        "model": "anthropic/claude-3-5-haiku-20241022",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": "default",
        "max_tokens": "default"
    },

    "haiku_4_5_october_25": {
        "model": "anthropic/claude-haiku-4-5-20251001",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": "default",  # Claude 4 models don't allow both temp and top_p
        "max_tokens": "default",
        "prompt_modifiers": ["must_begin_strict"]
    },

    # Haiku 4.5 with question repeat for testing
    "haiku_4_5_repeat_5": {
        "model": "anthropic/claude-haiku-4-5-20251001",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": "default",
        "max_tokens": "default",
        "prompt_modifiers": ["must_begin_strict", "question_repeat_5"]
    },

    # Haiku 4.5 with extended thinking enabled (for cheaper testing)
    "haiku_4_5_thinking_october_25": {
        "model": "anthropic/claude-haiku-4-5-20251001",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "anthropic_extended_thinking",
        "temperature": "default",  # Required for extended thinking
        "top_p": "default",
        "max_tokens": 20000,  # Must be > reasoning_tokens (16000)
        "prompt_modifiers": ["must_begin_strict"]
    },

    "sonnet_4_5_september_25": {
        "model": "anthropic/claude-sonnet-4-5-20250929",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": "default",  # Claude 4 models don't allow both temp and top_p
        "max_tokens": "default",
        "prompt_modifiers": ["must_begin_strict"]
    },

    "opus_4_5_november_25": {
        "model": "anthropic/claude-opus-4-5-20251101",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": "default",  # Claude 4 models don't allow both temp and top_p
        "max_tokens": "default",
        "prompt_modifiers": ["must_begin_strict"]
    },

    # Opus 4.5 with question repeat for testing compute scaling
    "opus_4_5_repeat_5": {
        "model": "anthropic/claude-opus-4-5-20251101",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": "default",
        "max_tokens": "default",
        "prompt_modifiers": ["must_begin_strict", "question_repeat_5"]
    },

    # Opus 4.5 with extended thinking enabled
    # Temperature must be default (not compatible with thinking)
    # max_tokens must be > reasoning_tokens (16000), so we set 20000
    "opus_4_5_thinking_november_25": {
        "model": "anthropic/claude-opus-4-5-20251101",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "anthropic_extended_thinking",
        "temperature": "default",  # Required for extended thinking
        "top_p": "default",
        "max_tokens": 20000,  # Must be > reasoning_tokens (16000)
        "prompt_modifiers": ["must_begin_strict"]
    },

    "gpt_4_1_april_25": {
        "model": "openai/gpt-4.1-2025-04-14",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },

    # GPT 4.1 with question repeat for testing compute scaling
    "gpt_4_1_repeat_5": {
        "model": "openai/gpt-4.1-2025-04-14",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default",
        "prompt_modifiers": ["question_repeat_5"]
    },
    
    "gpt_4_1_nano_april_25": {
        "model": "openai/gpt-4.1-nano-2025-04-14",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },

    # GPT 4.1 Nano with question repeat for testing compute scaling
    "gpt_4_1_nano_repeat_5": {
        "model": "openai/gpt-4.1-nano-2025-04-14",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default",
        "prompt_modifiers": ["question_repeat_5"]
    },
    
    "gpt_4_1_mini_april_25": {
        "model": "openai/gpt-4.1-mini-2025-04-14",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },
    
    "kimi_k2_july_25": {
        "model": "openrouter/moonshotai/kimi-k2",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },

    "kimi_k2_july_25_PH": {
        "model": "openrouter/moonshotai/kimi-k2",
        "post_hoc_explanation": True,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },

    "kimi_k2_groq_september_25": {
        "model": "groq/moonshotai/kimi-k2-instruct-0905",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": 0.0,
        "max_tokens": "default"
    },
    
    "deepseek_r1_distill_70b": {
        "model": "groq/deepseek-r1-distill-llama-70b",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": None,
        "temperature": "default",
        "top_p": "default",
        "max_tokens": 20480
    },
    
    "deepseek_r1_0528": {
        "model": "openrouter/deepseek/deepseek-r1-0528",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": None,
        "temperature": "default",
        "top_p": "default",
        "max_tokens": 20480
    },

    "deepseek_v3_1_august_25": {
        "model": "openrouter/deepseek/deepseek-chat-v3.1",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": "openrouter_fp8",
        "temperature": 0.0,
        "top_p": "default",
        "max_tokens": "default"
    },

    "deepseek_v3_2_exp_october_25": {
        "model": "openrouter/deepseek/deepseek-v3.2-exp",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": "openrouter_fp8",
        "temperature": 0.0,
        "top_p": "default",
        "max_tokens": "default"
    },

    "deepseek_v3_2_exp_reasoning_october_25": {
        "model": "openrouter/deepseek/deepseek-v3.2-exp",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openrouter_fp8_reasoning",
        "temperature": "default",
        "top_p": "default",
        "max_tokens": "default"
    },
    
    "gpt_oss_20b_high": {
        "model": "groq/openai/gpt-oss-20b",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_high_effort",
        "temperature": "default",
        "top_p": "default",
        "max_tokens": "default"
    },
    
    "gpt_5_minimal_august_25": {
        "model": "openai/gpt-5-2025-08-07",
        "post_hoc_explanation": False,
        "reasoning_model": True,
        "model_specific_config": "openai_minimal_flex",
        "temperature": "unsupported",
        "top_p": "unsupported",
        "max_tokens": "default"
    },

    "sonnet_4_6_february_26": {
        "model": "anthropic/claude-sonnet-4-6",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": "default",
        "max_tokens": "default",
        "prompt_modifiers": ["must_begin_strict"]
    },

    "opus_4_6_february_26": {
        "model": "anthropic/claude-opus-4-6",
        "post_hoc_explanation": False,
        "reasoning_model": False,
        "model_specific_config": None,
        "temperature": 0.0,
        "top_p": "default",
        "max_tokens": "default",
        "prompt_modifiers": ["must_begin_strict"]
    },

}


def get_eval_config(config_name: str) -> dict:
    """
    Get evaluation configuration by name.

    Args:
        config_name: Name of the configuration

    Returns:
        Configuration dictionary

    Raises:
        ValueError: If config not found or missing required fields
    """
    if config_name not in EVAL_CONFIGS:
        available = ", ".join(EVAL_CONFIGS.keys())
        raise ValueError(f"Unknown config: {config_name}. Available configs: {available}")

    config = EVAL_CONFIGS[config_name].copy()

    # Validate required fields
    required_fields = ["model", "post_hoc_explanation", "reasoning_model", "model_specific_config", "temperature", "top_p", "max_tokens"]
    missing_fields = [field for field in required_fields if field not in config]

    if missing_fields:
        raise ValueError(f"Config '{config_name}' missing required fields: {missing_fields}")

    # Validate prompt_modifiers if present
    if "prompt_modifiers" in config:
        modifiers = config["prompt_modifiers"]
        if not isinstance(modifiers, list):
            raise ValueError(f"Config '{config_name}': prompt_modifiers must be a list, got {type(modifiers)}")

        allowed_modifiers = ["must_begin_strict"]
        for modifier in modifiers:
            # Check for question_repeat_N pattern
            if modifier.startswith("question_repeat_"):
                try:
                    repeat_count = int(modifier.split("_")[-1])
                    if repeat_count < 1:
                        raise ValueError(f"Config '{config_name}': question_repeat count must be >= 1, got {repeat_count}")
                except ValueError as e:
                    if "invalid literal" in str(e):
                        raise ValueError(
                            f"Config '{config_name}': invalid question_repeat modifier '{modifier}'. "
                            f"Expected format: question_repeat_N where N is a positive integer."
                        )
                    raise
            elif modifier not in allowed_modifiers:
                raise ValueError(
                    f"Config '{config_name}': unknown prompt modifier '{modifier}'. "
                    f"Allowed modifiers: {', '.join(allowed_modifiers)}, question_repeat_N"
                )

    return config