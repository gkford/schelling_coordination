"""
Ad-hoc analysis for the introspect/reason ablation pilot.

Pilot conditions:
    - introspect_sita: coordination_sita + "Introspect deeply to reveal..."
    - reason_sita:     coordination_sita + "Reason deeply to determine..."

Reads .eval files directly (does NOT use load_eval_results which is
hardcoded to control_sita vs coordination_sita) and reports per-run:
    - salient % (option_A) vs alphabetical % (option_B) at the sample level
    - convergence rate and converged-on-salient vs converged-on-alphabetical
    - mean / max reasoning_tokens (for GPT-5.4 sanity check)
    - a few sample responses for eyeballing

For the salient_vs_alphabetical_elo{_pilot20} dataset:
    option_A = salient word, option_B = alphabetical word.

Run:
    uv run python -m data_export.analyses.introspect_reason_pilot
"""

import csv
import sys
from datetime import datetime
from pathlib import Path

from ..shared.config import OUTPUT_DIR, PROJECT_ROOT

sys.path.insert(0, str(PROJECT_ROOT))
from utils.eval_results import get_eval_results_by_features


DATASET = "salient_vs_alphabetical_elo_pilot20"

MODELS = [
    ("gpt_4_1_mini_april_25",       "GPT-4.1 Mini"),
    ("gpt_4_1_nano_april_25",       "GPT-4.1 Nano"),
    ("gpt_5_4_nano_none_march_26",  "GPT-5.4 Nano (effort=none)"),
    ("gpt_5_4_mini_none_march_26",  "GPT-5.4 Mini (effort=none)"),
    ("gpt_5_4_none_march_26",       "GPT-5.4 (effort=none)"),
]

PROMPTS = ["introspect_sita", "reason_sita"]


def analyse_run(config_name: str, prompt: str) -> dict | None:
    res = get_eval_results_by_features(config_name, prompt, DATASET)
    if res is None or "error" in res:
        print(f"  [skip] {config_name} / {prompt}: {res.get('error') if res else 'no results'}")
        return None

    pair_results = res["pair_results"]

    n_pairs = len(pair_results)
    n_samples = 0
    n_salient = 0          # chose option_A
    n_alphabetical = 0     # chose option_B
    n_invalid = 0

    n_converged = 0
    n_converged_on_salient = 0
    n_converged_on_alphabetical = 0

    reasoning_tokens_list: list[int] = []

    sample_responses: list[tuple[str, str, str, str]] = []  # (pair_id, order, choice, response)

    for pair_id, p in pair_results.items():
        for order_key, choice_key, resp_key, rt_key in [
            ("AB", "AB_choice", "AB_response", "AB_reasoning_tokens"),
            ("BA", "BA_choice", "BA_response", "BA_reasoning_tokens"),
        ]:
            choice = p[choice_key]
            if choice is None:
                continue
            n_samples += 1
            if choice == "A":
                n_salient += 1
            elif choice == "B":
                n_alphabetical += 1
            else:
                n_invalid += 1

            rt = p[rt_key]
            if rt is not None:
                reasoning_tokens_list.append(rt)

            if len(sample_responses) < 3:
                sample_responses.append((pair_id, order_key, choice, p[resp_key] or ""))

        if p["converged"]:
            n_converged += 1
            if p["converged_on_option"] == "A":
                n_converged_on_salient += 1
            elif p["converged_on_option"] == "B":
                n_converged_on_alphabetical += 1

    def pct(num: int, denom: int) -> float:
        return round(100.0 * num / denom, 1) if denom > 0 else 0.0

    mean_rt = round(sum(reasoning_tokens_list) / len(reasoning_tokens_list), 1) if reasoning_tokens_list else None
    max_rt = max(reasoning_tokens_list) if reasoning_tokens_list else None

    return {
        "config": config_name,
        "prompt": prompt,
        "model": res["metadata"]["model"],
        "n_pairs": n_pairs,
        "n_samples": n_samples,
        "n_salient": n_salient,
        "n_alphabetical": n_alphabetical,
        "n_invalid": n_invalid,
        "pct_salient": pct(n_salient, n_samples),
        "pct_alphabetical": pct(n_alphabetical, n_samples),
        "pct_invalid": pct(n_invalid, n_samples),
        "n_converged": n_converged,
        "pct_converged": pct(n_converged, n_pairs),
        "pct_converged_on_salient": pct(n_converged_on_salient, n_pairs),
        "pct_converged_on_alphabetical": pct(n_converged_on_alphabetical, n_pairs),
        "mean_reasoning_tokens": mean_rt,
        "max_reasoning_tokens": max_rt,
        "sample_responses": sample_responses,
    }


def main() -> None:
    rows: list[dict] = []

    for config_name, label in MODELS:
        for prompt in PROMPTS:
            print(f"\n=== {label} / {prompt} ===")
            result = analyse_run(config_name, prompt)
            if result is None:
                continue
            rows.append(result)
            print(
                f"  n_pairs={result['n_pairs']} n_samples={result['n_samples']}\n"
                f"  salient%={result['pct_salient']}  alphabetical%={result['pct_alphabetical']}  invalid%={result['pct_invalid']}\n"
                f"  converged%={result['pct_converged']}  on_salient%={result['pct_converged_on_salient']}  on_alphabetical%={result['pct_converged_on_alphabetical']}\n"
                f"  reasoning_tokens: mean={result['mean_reasoning_tokens']} max={result['max_reasoning_tokens']}"
            )
            print("  sample responses:")
            for pair_id, order, choice, resp in result["sample_responses"]:
                resp_snippet = (resp[:120] + "...") if len(resp) > 120 else resp
                print(f"    pair {pair_id} {order} choice={choice}  resp={resp_snippet!r}")

    # CSV
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d")
    csv_path = OUTPUT_DIR / f"introspect_reason_pilot_{stamp}.csv"
    fieldnames = [
        "config", "prompt", "model", "n_pairs", "n_samples",
        "n_salient", "n_alphabetical", "n_invalid",
        "pct_salient", "pct_alphabetical", "pct_invalid",
        "n_converged", "pct_converged",
        "pct_converged_on_salient", "pct_converged_on_alphabetical",
        "mean_reasoning_tokens", "max_reasoning_tokens",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r[k] for k in fieldnames})
    print(f"\nWrote {csv_path}")


if __name__ == "__main__":
    main()
