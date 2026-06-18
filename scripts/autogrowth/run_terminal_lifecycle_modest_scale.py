#!/usr/bin/env python3
"""Run TG26x terminal-kind lifecycle modest scale checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    TerminalLifecycleModestScaleConfig,
    run_terminal_lifecycle_modest_scale,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26x_terminal_lifecycle_modest_scale.json"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg26x_terminal_lifecycle_modest_scale_progress.json")
    parser.add_argument("--mate1-train-count", type=int, default=24)
    parser.add_argument("--mate1-heldout-count", type=int, default=12)
    parser.add_argument("--mate2-train-count", type=int, default=12)
    parser.add_argument("--mate2-heldout-count", type=int, default=6)
    parser.add_argument("--max-ticks", type=int, default=30)
    parser.add_argument("--max-samples", type=int, default=24)
    parser.add_argument("--max-shared-atom-candidates-per-choice", type=int, default=3)
    parser.add_argument("--shared-atom-min-overlap", type=int, default=6)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26x_terminal_lifecycle_modest_scale_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg26x_terminal_lifecycle_modest_scale.json")
        else args.output
    )
    cfg = TerminalLifecycleModestScaleConfig(
        tiny_mate1_train_count=3 if args.smoke else 12,
        tiny_mate1_heldout_count=1 if args.smoke else 6,
        tiny_mate2_train_count=1 if args.smoke else 6,
        tiny_mate2_heldout_count=1 if args.smoke else 3,
        mate1_train_count=4 if args.smoke else args.mate1_train_count,
        mate1_heldout_count=2 if args.smoke else args.mate1_heldout_count,
        mate2_train_count=1 if args.smoke else args.mate2_train_count,
        mate2_heldout_count=1 if args.smoke else args.mate2_heldout_count,
        max_ticks=args.max_ticks,
        max_samples=args.max_samples,
        max_shared_atom_candidates_per_choice=2 if args.smoke else args.max_shared_atom_candidates_per_choice,
        shared_atom_min_overlap=args.shared_atom_min_overlap,
        equivalence_count=1 if args.smoke else 4,
        progress_output=args.progress_output,
    )
    result = run_terminal_lifecycle_modest_scale(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "tiny_tg26w_conversion_rate",
        "tiny_tg26w_false_positive_internal_gate_count",
        "mate1_heldout_accuracy",
        "mate1_null_count",
        "mate2_conversion_rate",
        "mate2_first_move_success_rate",
        "mate2_same_graph_second_move_count",
        "internal_gate_approved_candidate_count",
        "internal_gate_rejected_candidate_count",
        "internal_gate_false_positive_count",
        "internal_gate_false_negative_count",
        "deep_reply_checks_run",
        "scheduler_equivalence_mismatch_count",
        "failure_mode",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

