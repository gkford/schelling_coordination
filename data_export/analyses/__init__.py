"""
Analysis modules for data export.

Each analysis module provides:
- run() -> dict: Run the analysis and return results
- get_output_filename() -> str: Return the output filename
- get_description() -> str: Return a description
"""

from . import raw_convergence
from . import bias_controlled
from . import anti_coordination
from . import alphabetisation_bias_controlled
from . import alphabetisation_all_converged
from . import alphabetisation_bias_differed_in_control
from . import dangerous_bias_all_converged
from . import justification_categories
from . import post_hoc_categories

# Registry of all available analyses
ANALYSES = {
    "raw_convergence": raw_convergence,
    "bias_controlled": bias_controlled,
    "anti_coordination": anti_coordination,
    "alphabetisation_bias_controlled": alphabetisation_bias_controlled,
    "alphabetisation_all_converged": alphabetisation_all_converged,
    "alphabetisation_bias_differed_in_control": alphabetisation_bias_differed_in_control,
    "dangerous_bias_all_converged": dangerous_bias_all_converged,
    "justification_categories": justification_categories,
    "post_hoc_categories": post_hoc_categories,
}


def list_analyses() -> list[dict]:
    """List all available analyses with their descriptions."""
    return [
        {
            "name": name,
            "output_file": module.get_output_filename(),
            "description": module.get_description(),
        }
        for name, module in ANALYSES.items()
    ]


def run_analysis(name: str) -> dict:
    """Run a specific analysis by name."""
    if name not in ANALYSES:
        raise ValueError(f"Unknown analysis: {name}. Available: {list(ANALYSES.keys())}")
    return ANALYSES[name].run()


def run_all_analyses() -> dict[str, dict]:
    """Run all analyses and return results keyed by name."""
    return {name: module.run() for name, module in ANALYSES.items()}
