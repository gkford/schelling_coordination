"""
Model-specific configurations for the pairs evaluation system.

These configurations define parameters specific to particular models
that will be passed to the eval() function.

Flex Processing:
- Flex processing provides lower costs for slower response times
- Currently supported for o3, o4-mini, and gpt-5 models
- O4 and GPT-5 configs automatically use flex processing with service_tier="flex"
- Client timeout is set to 1200 seconds (20 minutes) for flex requests

OpenRouter Quantization:
- OpenRouter supports explicit quantization control via provider preferences
- fp8 quantization is recommended for DeepSeek models (fp8 native)
- Setting allow_fallbacks=true enables fallback within the specified provider list
- Provider preferences are passed via extra_body parameter to litellm
"""

MODEL_SPECIFIC_CONFIGS = {
    "openai_high_flex": {
        "eval_kwargs": {
            "reasoning_summary": "detailed",
            "reasoning_effort": "high",
            "model_args": {
                "service_tier": "flex",
                "client_timeout": 1200  # 20 minutes for flex
            }
        }
    },

    "openai_minimal_flex": {
        "eval_kwargs": {
            "reasoning_summary": "detailed",
            "reasoning_effort": "minimal",
            "model_args": {
                "service_tier": "flex",
                "client_timeout": 1200  # 20 minutes for flex
            }
        }
    },
    # Legacy config used for some earlier o4 version of the eval
    "openai_high_effort": {
        "eval_kwargs": {
            "reasoning_summary": "detailed",
            "reasoning_effort": "high"
        }
    },

    # OpenRouter quantization control for fp8 models (e.g., DeepSeek)
    # Provider order: Tries fp8-compatible providers in sequence until one succeeds
    # All listed providers support native fp8 quantization
    "openrouter_fp8": {
        "eval_kwargs": {
            "model_args": {
                "provider": {
                    "order": ["Novita", "GMICloud", "SiliconFlow", "Atlas-Cloud"],
                    "quantizations": ["fp8"],
                    "allow_fallbacks": True,
                    "data_collection": "deny"
                }
            }
        }
    },

    # OpenRouter fp8 with reasoning enabled for DeepSeek V3.2-Exp
    # Combines fp8 quantization with visible reasoning traces
    # Uses reasoning_effort parameter supported by Inspect AI's OpenRouter provider
    #
    # Provider order: Tries fp8-compatible providers in sequence until one succeeds
    # All listed providers support native fp8 quantization
    #
    # IMPORTANT: DO NOT REMOVE THE PROVIDER ORDER AND QUANTIZATION RESTRICTIONS!
    # These providers are specifically chosen for fp8 support and must be maintained.
    "openrouter_fp8_reasoning": {
        "eval_kwargs": {
            "reasoning_effort": "high",  # Enable reasoning with high effort
            "model_args": {
                "provider": {
                    "order": ["Novita", "GMICloud", "SiliconFlow", "Atlas-Cloud"],
                    "quantizations": ["fp8"],
                    "allow_fallbacks": True,
                    "data_collection": "deny"
                }
            }
        }
    },

    # Simple reasoning config without provider restrictions
    # Let OpenRouter choose the best available provider
    "openrouter_reasoning_simple": {
        "eval_kwargs": {
            "reasoning_effort": "high",  # Enable reasoning with high effort
            "model_args": {
                "provider": {
                    "data_collection": "deny"
                }
            }
        }
    },

    # Anthropic extended thinking for Claude Opus 4.5
    # Uses reasoning_tokens which maps to Claude's budget_tokens
    # The budget is a ceiling - Claude uses only what it needs
    # 16K provides generous room without hitting networking issues (>32K)
    "anthropic_extended_thinking": {
        "eval_kwargs": {
            "reasoning_tokens": 16000  # Maps to thinking.budget_tokens
        }
    }
}


def get_model_specific_config(config_name: str) -> dict:
    """
    Get model-specific configuration by name.
    
    Args:
        config_name: Name of the model-specific configuration
        
    Returns:
        Configuration dictionary
        
    Raises:
        ValueError: If config not found
    """
    if config_name not in MODEL_SPECIFIC_CONFIGS:
        available = ", ".join(MODEL_SPECIFIC_CONFIGS.keys())
        raise ValueError(f"Unknown model-specific config: {config_name}. Available configs: {available}")
    
    return MODEL_SPECIFIC_CONFIGS[config_name].copy()