"""
Enhanced evaluation runner that supports eval-retry.

This version uses 'inspect eval' CLI instead of calling eval() directly,
which allows 'inspect eval-retry' to work properly.

Key differences from run_eval.py:
- Shells out to 'inspect eval' command
- Task file and args are preserved in eval logs
- Supports 'inspect eval-retry' for failed samples
- Maintains all config management and validation
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
current_dir = Path.cwd()
while True:
    env_path = current_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        break
    parent = current_dir.parent
    if parent == current_dir:
        break
    current_dir = parent

# Import our components
from utils.model_utils import ensure_config_output_dir
from eval_configs import get_eval_config
from model_specific_configs import get_model_specific_config


def check_prompt_modifier_compatibility(config_name: str, post_hoc_explanation: bool, prompt_modifiers: list) -> bool:
    """Check if prompt modifiers are compatible with other config settings."""
    if not prompt_modifiers:
        return True

    if post_hoc_explanation and "must_begin_strict" in prompt_modifiers:
        raise ValueError(
            f"\nConfig '{config_name}' has incompatible settings:\n"
            f"  post_hoc_explanation: True\n"
            f"  prompt_modifiers: {prompt_modifiers}\n\n"
            f"The 'must_begin_strict' modifier is incompatible with post_hoc_explanation\n"
            f"because the post-hoc solver cannot parse strict prompts for removal.\n"
            f"Please set post_hoc_explanation to False or remove the must_begin_strict modifier."
        )

    if post_hoc_explanation and prompt_modifiers:
        print(f"\n⚠️  WARNING: Untested combination in '{config_name}':")
        print(f"   post_hoc_explanation: True")
        print(f"   prompt_modifiers: {prompt_modifiers}")
        print("\nThis combination may cause errors in output extraction.")
        response = input("Continue anyway? (y/n): ")
        return response.lower() == 'y'

    return True


def check_temperature_settings(config_name: str, config: dict) -> bool:
    """Check if temperature/top_p settings match expected values for model type."""
    is_reasoning = config.get("reasoning_model", False)
    temperature = config.get("temperature")
    top_p = config.get("top_p")

    if temperature == "unsupported" or top_p == "unsupported":
        return True

    if is_reasoning:
        if temperature != "default" or top_p != "default":
            print(f"\n⚠️  WARNING: Reasoning model '{config_name}' has non-default temperature/top_p!")
            print(f"   Temperature: {temperature} (expected: 'default')")
            print(f"   Top-p: {top_p} (expected: 'default')")
            print("\nReasoning models typically use default temperature settings.")
            response = input("Continue anyway? (y/n): ")
            return response.lower() == 'y'
    else:
        is_deterministic = (
            temperature == 0.0 or
            top_p == 0.0 or
            (temperature == "default" and top_p == "default")
        )

        if not is_deterministic:
            print(f"\n⚠️  WARNING: Non-reasoning model '{config_name}' is not configured for determinism!")
            print(f"   Temperature: {temperature} (expected: 0.0 or 'default')")
            print(f"   Top-p: {top_p} (expected: 0.0 or 'default')")
            print("\nAt least one of temperature or top_p should be 0 for reproducibility.")
            response = input("Continue anyway? (y/n): ")
            return response.lower() == 'y'

    return True


def build_inspect_eval_command(
    pairs_path: str,
    prompt_template: str,
    config_name: str,
    config: dict,
    output_dir: str,
    max_connections: int = None,
    max_samples: int = None,
    metadata: dict = None,
    test: bool = False,
    batch: bool = False
) -> tuple[list[str], str, str]:
    """
    Build the 'inspect eval' command with all necessary arguments.

    Returns:
        (command_list, log_dir, model_config_file) tuple
        model_config_file will be None if not needed, or path to temp file
    """
    # Get config values
    model = config["model"]
    post_hoc_explanation = config["post_hoc_explanation"]
    prompt_modifiers = config.get("prompt_modifiers")
    temperature = config.get("temperature")
    top_p = config.get("top_p")
    max_tokens = config.get("max_tokens")
    model_specific_config_name = config.get("model_specific_config")

    # Build task arguments
    task_args = [
        "-T", f"pairs_file={pairs_path}",
        "-T", f"prompt_name={prompt_template}",
        "-T", f"post_hoc_explanation_enabled={post_hoc_explanation}",
        "-T", f"test={test}",
    ]

    # Add prompt_modifiers if present
    if prompt_modifiers:
        # Convert list to JSON string for passing as task arg
        prompt_modifiers_json = json.dumps(prompt_modifiers)
        task_args.extend(["-T", f"prompt_modifiers={prompt_modifiers_json}"])

    # Create output directory structure
    config_output_dir = ensure_config_output_dir(config_name, output_dir)
    prompt_output_dir = os.path.join(config_output_dir, prompt_template)

    # Load dataset to get dataset_id
    with open(pairs_path, 'r') as f:
        dataset = json.load(f)
    dataset_id = dataset.get('dataset_id', 'unknown')

    dataset_output_dir = os.path.join(prompt_output_dir, dataset_id)
    os.makedirs(dataset_output_dir, exist_ok=True)

    # Build command
    cmd = [
        "uv", "run", "inspect", "eval",
        "schelling_pairs_task.py@schelling_pairs",
        *task_args,
        "--model", model,
        "--log-dir", dataset_output_dir,
    ]

    # Add temperature settings if not default/unsupported
    if temperature not in ["default", "unsupported"]:
        cmd.extend(["--temperature", str(temperature)])
    if top_p not in ["default", "unsupported"]:
        cmd.extend(["--top-p", str(top_p)])
    if max_tokens not in ["default", "unsupported"]:
        cmd.extend(["--max-tokens", str(max_tokens)])

    # Handle model-specific config
    model_config_file = None
    if model_specific_config_name:
        model_config = get_model_specific_config(model_specific_config_name)
        eval_kwargs = model_config.get("eval_kwargs", {})

        # Handle top-level eval flags
        if "reasoning_effort" in eval_kwargs:
            cmd.extend(["--reasoning-effort", eval_kwargs["reasoning_effort"]])

        if "reasoning_summary" in eval_kwargs:
            cmd.extend(["--reasoning-summary", eval_kwargs["reasoning_summary"]])

        if "reasoning_tokens" in eval_kwargs:
            cmd.extend(["--reasoning-tokens", str(eval_kwargs["reasoning_tokens"])])

        # Handle model_args - write to temp config file if complex
        if "model_args" in eval_kwargs:
            model_args = eval_kwargs["model_args"]

            # Check if we have simple args or complex nested structures
            has_complex_args = any(isinstance(v, (dict, list)) for v in model_args.values())

            if has_complex_args:
                # Write to temporary JSON config file
                fd, model_config_file = tempfile.mkstemp(suffix='.json', prefix='inspect_model_config_')
                with os.fdopen(fd, 'w') as f:
                    json.dump(model_args, f, indent=2)
                cmd.extend(["--model-config", model_config_file])
            else:
                # Simple args can be passed via -M
                for key, value in model_args.items():
                    cmd.extend(["-M", f"{key}={value}"])

    # Add concurrency settings
    if max_connections is not None:
        cmd.extend(["--max-connections", str(max_connections)])
    if max_samples is not None:
        cmd.extend(["--max-samples", str(max_samples)])

    # Add batch processing flag
    if batch:
        cmd.append("--batch")

    # Add metadata
    if metadata:
        for key, value in metadata.items():
            cmd.extend(["--metadata", f"{key}={json.dumps(value)}"])

    return cmd, dataset_output_dir, model_config_file


def run_evaluation(
    pairs_path: str,
    prompt_template: str,
    config_name: str,
    output_dir: str = "results",
    metadata: dict = None,
    max_connections: int = None,
    max_samples: int = None,
    test: bool = False,
    batch: bool = False
):
    """
    Run evaluation using 'inspect eval' CLI command.

    This ensures task file and args are preserved for eval-retry.
    """
    # Load configuration
    config = get_eval_config(config_name)
    post_hoc_explanation = config["post_hoc_explanation"]
    prompt_modifiers = config.get("prompt_modifiers")

    # Check compatibility
    if not check_prompt_modifier_compatibility(config_name, post_hoc_explanation, prompt_modifiers):
        print("\nEvaluation aborted by user.")
        return None

    if not check_temperature_settings(config_name, config):
        print("\nEvaluation aborted by user.")
        return None

    # Print configuration
    print(f"\n{'='*60}")
    print("Running Evaluation")
    print(f"{'='*60}")
    print(f"Config: {config_name}")
    print(f"Model: {config['model']}")
    print(f"Pairs file: {pairs_path}")
    print(f"Prompt: {prompt_template}")
    print(f"Temperature: {config['temperature'] if config['temperature'] != 'unsupported' else 'unsupported (not passed)'}")
    print(f"Top-p: {config['top_p'] if config['top_p'] != 'unsupported' else 'unsupported (not passed)'}")
    print(f"Max tokens: {config['max_tokens']}")
    print(f"Post-hoc explanation: {post_hoc_explanation}")
    print(f"Reasoning model: {config['reasoning_model']}")
    print(f"Model-specific config: {config.get('model_specific_config')}")
    print(f"Prompt modifiers: {prompt_modifiers if prompt_modifiers else 'None'}")
    if max_connections:
        print(f"Max connections: {max_connections}")
    if max_samples:
        print(f"Max samples: {max_samples}")
    if batch:
        print(f"Batch mode: ENABLED (50% cost reduction)")
    print(f"{'='*60}\n")

    # Build metadata including config info
    run_metadata = {
        'prompt_identifier': prompt_template,
        'config_name': config_name,
        'prompt_modifiers': prompt_modifiers
    }
    if metadata:
        run_metadata.update(metadata)

    # Build command
    cmd, log_dir, model_config_file = build_inspect_eval_command(
        pairs_path=pairs_path,
        prompt_template=prompt_template,
        config_name=config_name,
        config=config,
        output_dir=output_dir,
        max_connections=max_connections,
        max_samples=max_samples,
        metadata=run_metadata,
        test=test,
        batch=batch
    )

    # Print command for debugging
    print("Executing command:")
    print(" ".join(cmd))
    if model_config_file:
        print(f"\nUsing temporary model config file: {model_config_file}")
        with open(model_config_file, 'r') as f:
            print("Config contents:")
            print(f.read())
    print()

    # Run command
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print(f"\n{'='*60}")
        print("EVALUATION COMPLETE")
        print(f"{'='*60}")
        print(f"\nLogs saved to: {log_dir}/")
        print("\nTo retry failed samples, use:")
        print(f"  inspect eval-retry {log_dir}/<eval-file>.eval")
        return result
    except subprocess.CalledProcessError as e:
        print(f"\n{'='*60}")
        print("EVALUATION FAILED")
        print(f"{'='*60}")
        print(f"Exit code: {e.returncode}")
        print(f"\nTo retry failed samples, use:")
        print(f"  inspect eval-retry {log_dir}/<eval-file>.eval")
        return None
    finally:
        # Clean up temp config file if it was created
        if model_config_file and os.path.exists(model_config_file):
            os.remove(model_config_file)


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced evaluation runner with retry support"
    )
    parser.add_argument("--pairs", required=True, help="Path to pairs JSON file")
    parser.add_argument("--prompt", required=True, help="Prompt template name")
    parser.add_argument("--config", required=True, help="Configuration name")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: 'results', or 'test_results' with --test)")
    parser.add_argument("--max-connections", type=int, help="Maximum concurrent connections")
    parser.add_argument("--max-samples", type=int, help="Maximum concurrent samples")
    parser.add_argument("--test", action="store_true", help="Run in test mode (outputs to test_results/ and marks eval as test)")
    parser.add_argument("--batch", action="store_true", help="Enable batch processing (50%% cost reduction, async processing)")

    args = parser.parse_args()

    # Determine output directory
    if args.output_dir is None:
        output_dir = "test_results" if args.test else "results"
    else:
        output_dir = args.output_dir

    result = run_evaluation(
        pairs_path=args.pairs,
        prompt_template=args.prompt,
        config_name=args.config,
        output_dir=output_dir,
        max_connections=args.max_connections,
        max_samples=args.max_samples,
        test=args.test,
        batch=args.batch
    )

    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
