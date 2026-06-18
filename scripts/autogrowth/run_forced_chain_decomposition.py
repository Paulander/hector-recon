#!/usr/bin/env python3
"""Run TG26z forced-chain decomposition checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ForcedChainDecompositionConfig,
    run_forced_chain_decomposition,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26z_forced_chain_decomposition.json"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg26z_forced_chain_decomposition_progress.json")
    parser.add_argument("--mate1-train-count", type=int, default=24)
    parser.add_argument("--mate1-heldout-count", type=int, default=12)
    parser.add_argument("--mate2-train-count", type=int, default=12)
    parser.add_argument("--mate2-heldout-count", type=int, default=6)
    parser.add_argument("--non-forced-sample-limit", type=int, default=4)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26z_forced_chain_decomposition_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg26z_forced_chain_decomposition.json")
        else args.output
    )
    cfg = ForcedChainDecompositionConfig(
        mate1_train_count=4 if args.smoke else args.mate1_train_count,
        mate1_heldout_count=2 if args.smoke else args.mate1_heldout_count,
        mate2_train_count=1 if args.smoke else args.mate2_train_count,
        mate2_heldout_count=1 if args.smoke else args.mate2_heldout_count,
        max_shared_atom_candidates_per_choice=2 if args.smoke else 3,
        non_forced_sample_limit=1 if args.smoke else args.non_forced_sample_limit,
        equivalence_count=1 if args.smoke else 4,
        max_samples=3 if args.smoke else 24,
        progress_output=args.progress_output,
    )
    result = run_forced_chain_decomposition(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "mate1_heldout_accuracy",
        "mate1_null_count",
        "continuation_mate1_accuracy",
        "continuation_mate1_null_count",
        "forced_first_chain_success_rate",
        "mate2_conversion_rate",
        "mate2_first_move_success_rate",
        "mate2_same_graph_second_move_count",
        "failure_bucket_counts",
        "scheduler_equivalence_mismatch_count",
        "failure_mode",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
