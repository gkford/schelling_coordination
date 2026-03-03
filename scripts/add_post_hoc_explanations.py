"""
Add post-hoc explanations to existing eval files.

This script takes an existing coordination_sita eval file that doesn't have
post-hoc explanations and adds them by calling the same model to explain
its choices.

Usage:
    uv run python scripts/add_post_hoc_explanations.py --config deepseek_v3_march_25 --test 5
    uv run python scripts/add_post_hoc_explanations.py --config gpt_4_1_april_25 --test 5
    uv run python scripts/add_post_hoc_explanations.py --config deepseek_v3_march_25  # Full run
"""

import argparse
import asyncio
import copy
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
current_dir = Path(__file__).parent
while True:
    env_path = current_dir / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        break
    parent = current_dir.parent
    if parent == current_dir:
        break
    current_dir = parent

from inspect_ai.log import read_eval_log, write_eval_log, EvalLog
from inspect_ai.model import (
    get_model,
    ChatMessageUser,
    ChatMessageAssistant,
    GenerateConfig,
)

from eval_configs import get_eval_config


DATASET = "salient_vs_alphabetical_elo"
PROMPT_TYPE = "coordination_sita"
POST_HOC_QUESTION = "Explain the primary reason you made that choice."


def find_eval_file(config_name: str, dataset: str = DATASET) -> Path | None:
    """Find the eval file for a given config and dataset."""
    results_dir = Path("results") / config_name / PROMPT_TYPE / dataset
    if not results_dir.exists():
        return None

    eval_files = list(results_dir.glob("*.eval"))
    if not eval_files:
        return None

    # Return the most recent one (by filename timestamp)
    return sorted(eval_files)[-1]


def get_output_path(input_path: Path, config_name: str) -> Path:
    """Generate output path for the new eval file with post-hoc data."""
    # Create output in post_hoc_continuation subdirectory
    output_dir = input_path.parent / "post_hoc_continuation"
    output_dir.mkdir(exist_ok=True)

    # Generate new filename with timestamp
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S+00-00")
    output_name = f"{timestamp}_{config_name}_post_hoc.eval"

    return output_dir / output_name


async def add_post_hoc_to_sample(
    model,
    messages: list,
    config: GenerateConfig,
    sample_idx: int,
    total_samples: int,
) -> str | None:
    """Add post-hoc explanation to a single sample's messages.

    Returns the explanation text, or None if there was an error.
    """
    # Build the conversation: original messages + explanation request
    conversation = list(messages) + [
        ChatMessageUser(content=POST_HOC_QUESTION)
    ]

    try:
        response = await model.generate(conversation, config=config)

        # Extract the explanation from the response
        if response.choices and response.choices[0].message:
            explanation = response.choices[0].message.content
            print(f"  [{sample_idx + 1}/{total_samples}] Got explanation: {str(explanation)[:80]}...")
            return explanation
        else:
            print(f"  [{sample_idx + 1}/{total_samples}] No response content")
            return None

    except Exception as e:
        print(f"  [{sample_idx + 1}/{total_samples}] Error: {e}")
        return None


async def process_eval(
    input_path: Path,
    output_path: Path,
    config_name: str,
    test_limit: int | None = None,
    batch_size: int = 10,
) -> None:
    """Process an eval file and add post-hoc explanations."""
    print(f"\nLoading eval from: {input_path}")

    # Load original eval
    original_log = read_eval_log(str(input_path))

    # Get model config
    eval_config = get_eval_config(config_name)
    model_name = eval_config["model"]
    temperature = eval_config["temperature"]
    top_p = eval_config["top_p"]

    print(f"Model: {model_name}")
    print(f"Temperature: {temperature}, Top-p: {top_p}")

    # Build generate config
    gen_config_kwargs = {}
    if temperature not in ("default", "unsupported"):
        gen_config_kwargs["temperature"] = temperature
    if top_p not in ("default", "unsupported"):
        gen_config_kwargs["top_p"] = top_p

    gen_config = GenerateConfig(**gen_config_kwargs)

    # Get model instance
    model = get_model(model_name, config=gen_config)

    # Determine samples to process
    samples_to_process = original_log.samples
    if test_limit:
        samples_to_process = samples_to_process[:test_limit]
        print(f"Test mode: processing {test_limit} samples")
    else:
        print(f"Processing all {len(samples_to_process)} samples")

    # Process samples in batches
    total = len(samples_to_process)
    modified_samples = []

    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = samples_to_process[batch_start:batch_end]

        print(f"\nProcessing batch {batch_start + 1}-{batch_end} of {total}...")

        # Create async tasks for batch
        tasks = []
        for i, sample in enumerate(batch):
            sample_idx = batch_start + i
            tasks.append(
                add_post_hoc_to_sample(
                    model,
                    sample.messages,
                    gen_config,
                    sample_idx,
                    total,
                )
            )

        # Run batch concurrently
        explanations = await asyncio.gather(*tasks)

        # Update samples with explanations
        for i, (sample, explanation) in enumerate(zip(batch, explanations)):
            # Deep copy the sample to avoid modifying original
            new_sample = copy.deepcopy(sample)

            # Add explanation messages
            new_sample.messages.append(
                ChatMessageUser(content=POST_HOC_QUESTION)
            )

            if explanation:
                new_sample.messages.append(
                    ChatMessageAssistant(content=explanation)
                )
            else:
                # Add placeholder for failed requests
                new_sample.messages.append(
                    ChatMessageAssistant(content="[ERROR: Failed to get explanation]")
                )

            modified_samples.append(new_sample)

    # Create new eval log with modified samples
    # We need to copy the original log structure
    new_log = EvalLog(
        version=original_log.version,
        status=original_log.status,
        eval=original_log.eval,
        plan=original_log.plan,
        results=original_log.results,
        stats=original_log.stats,
        error=original_log.error,
        samples=modified_samples if not test_limit else modified_samples + list(original_log.samples[test_limit:]),
    )

    # Write new eval file
    print(f"\nWriting output to: {output_path}")
    write_eval_log(new_log, output_path)

    # Summary
    success_count = sum(1 for s in modified_samples if len(s.messages) == 5 and "[ERROR" not in str(s.messages[-1].content))
    print(f"\nDone! Successfully added explanations to {success_count}/{len(modified_samples)} samples")


def main():
    parser = argparse.ArgumentParser(
        description="Add post-hoc explanations to existing eval files"
    )
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Eval config name (e.g., deepseek_v3_march_25, gpt_4_1_april_25)",
    )
    parser.add_argument(
        "--test",
        type=int,
        default=None,
        help="Test mode: only process this many samples",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of samples to process concurrently (default: 10)",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=DATASET,
        help=f"Dataset to process (default: {DATASET})",
    )

    args = parser.parse_args()

    # Find input eval file
    input_path = find_eval_file(args.config, args.dataset)
    if not input_path:
        print(f"Error: No eval file found for {args.config} / {args.dataset}")
        sys.exit(1)

    # Generate output path
    output_path = get_output_path(input_path, args.config)

    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")

    # Run async processing
    asyncio.run(
        process_eval(
            input_path,
            output_path,
            args.config,
            test_limit=args.test,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
