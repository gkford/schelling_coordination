"""
Utilities for handling configuration-based output directories.
"""
import os


def ensure_config_output_dir(config_name: str, base_dir: str = "results") -> str:
    """
    Create and return the output directory for a config.
    
    Args:
        config_name: Name of the configuration
        base_dir: Base directory for results (default: "results")
        
    Returns:
        Full path to the created config output directory
    """
    output_dir = os.path.join(base_dir, config_name)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir