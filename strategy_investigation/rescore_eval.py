#!/usr/bin/env python3
"""
Rescore an existing eval log with the updated scorer and save to a new file.
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

# Import the scorer to register it
from strategy_investigation.strategy_name_extractor_scorer import strategy_name_extractor

from inspect_ai.log import read_eval_log, write_eval_log

async def rescore_eval(eval_file: Path):
    print(f"Rescoring: {eval_file}")

    # Read the original eval log
    print("Reading eval log...")
    eval_log = read_eval_log(str(eval_file))

    # Rescore all samples
    print(f"Rescoring {len(eval_log.samples)} samples...")
    scorer = strategy_name_extractor()

    for i, sample in enumerate(eval_log.samples):
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(eval_log.samples)} samples...")

        # Create a minimal TaskState-like object with what the scorer needs
        from types import SimpleNamespace
        state = SimpleNamespace(
            output=sample.output,
            metadata=sample.metadata
        )

        # Score the sample
        score_result = await scorer(state, sample.target)

        # Update the sample's scores
        sample.scores['strategy_name_extractor'] = score_result

    # Recalculate metrics
    print("Recalculating metrics...")
    from inspect_ai.log._log import EvalMetric
    from inspect_ai.scorer import SampleScore
    from strategy_investigation.strategy_name_extractor_scorer import inferability_rate

    # Create SampleScore objects for metric calculation
    sample_scores = [
        SampleScore(
            score=sample.scores['strategy_name_extractor'],
            sample_id=sample.id
        )
        for sample in eval_log.samples
    ]

    # Compute inferability_rate metric
    metric_fn = inferability_rate()
    metric_value = metric_fn(sample_scores)

    computed_metrics = {
        'inferability_rate': EvalMetric(
            name='inferability_rate',
            value=metric_value,
            params={},
            metadata=None
        )
    }

    # Update eval_log.results with new metrics
    if eval_log.results and eval_log.results.scores:
        eval_log.results.scores[0].metrics = computed_metrics
        print(f"  inferability_rate: {metric_value:.4f}")

    # Create new filename with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    new_filename = f"{eval_file.stem}_rescored_{timestamp}.eval"
    new_file = eval_file.parent / new_filename

    # Write to new file
    print(f"Writing rescored eval to: {new_file}")
    write_eval_log(eval_log, str(new_file))

    print(f"\nRescoring complete!")
    print(f"New file: {new_file}")

    return new_file

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rescore_eval.py <eval_file>")
        sys.exit(1)

    eval_file = Path(sys.argv[1])
    asyncio.run(rescore_eval(eval_file))
