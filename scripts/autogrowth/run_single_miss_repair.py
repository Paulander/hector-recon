#!/usr/bin/env python3
"""Run TG27b single Mate_In_2 miss repair checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import SingleMissRepairConfig, run_single_miss_repair


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg27b_single_miss_repair.json"),
    )
    parser.add_argument(
        "--progress-output",
        type=str,
        default="reports/autogrowth/krk_autogrowth_tg27b_single_miss_repair_progress.json",
    )
    parser.add_argument("--mate1-train-count", type=int, default=32)
    parser.add_argument("--mate1-heldout-count", type=int, default=16)
    parser.add_argument("--mate2-train-count", type=int, default=16)
    parser.add_argument("--mate2-heldout-count", type=int, default=8)
    parser.add_argument("--repaired-high-recall-threshold", type=float, default=0.018)
    parser.add_argument("--replay-count", type=int, default=10)
    parser.add_argument("--full-replay-count", type=int, default=10)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg27b_single_miss_repair_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg27b_single_miss_repair.json")
        else args.output
    )
    cfg = SingleMissRepairConfig(
        mate1_train_count=4 if args.smoke else args.mate1_train_count,
        mate1_heldout_count=2 if args.smoke else args.mate1_heldout_count,
        mate2_train_count=1 if args.smoke else args.mate2_train_count,
        mate2_heldout_count=1 if args.smoke else args.mate2_heldout_count,
        max_shared_atom_candidates_per_choice=2 if args.smoke else 3,
        equivalence_count=1 if args.smoke else 4,
        max_samples=3 if args.smoke else 24,
        repaired_high_recall_threshold=args.repaired_high_recall_threshold,
        replay_count=2 if args.smoke else args.replay_count,
        full_replay_count=0 if args.smoke else args.full_replay_count,
        run_ablations=not args.smoke,
        run_scheduler_equivalence=not args.smoke,
        progress_output=args.progress_output,
    )
    result = run_single_miss_repair(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "original_tg27a_conversion_rate",
        "repaired_conversion_rate",
        "repaired_first_move_success_rate",
        "repaired_same_graph_second_move_count",
        "mate1_heldout_accuracy",
        "mate1_null_count",
        "failed_fen",
        "failure_bucket",
        "false_negative_count_before",
        "false_negative_count_after",
        "false_positive_count_before",
        "false_positive_count_after",
        "deep_reply_checks_before",
        "deep_reply_checks_after",
        "scheduler_equivalence_mismatch_count",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
