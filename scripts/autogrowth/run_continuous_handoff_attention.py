#!/usr/bin/env python3
"""Run TG26y continuous handoff attention checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    ContinuousHandoffAttentionConfig,
    run_continuous_handoff_attention,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26y_continuous_handoff_attention.json"))
    parser.add_argument("--progress-output", type=str, default="reports/autogrowth/krk_autogrowth_tg26y_continuous_handoff_attention_progress.json")
    parser.add_argument("--mate1-train-count", type=int, default=24)
    parser.add_argument("--mate1-heldout-count", type=int, default=12)
    parser.add_argument("--mate2-train-count", type=int, default=12)
    parser.add_argument("--mate2-heldout-count", type=int, default=6)
    parser.add_argument("--top-k", type=int, default=4)
    parser.add_argument("--two-stage-top-k", type=int, default=6)
    parser.add_argument("--epsilon-tail-count", type=int, default=2)
    parser.add_argument("--no-compare-repetition-2", action="store_true")
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26y_continuous_handoff_attention_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg26y_continuous_handoff_attention.json")
        else args.output
    )
    cfg = ContinuousHandoffAttentionConfig(
        mate1_train_count=4 if args.smoke else args.mate1_train_count,
        mate1_heldout_count=2 if args.smoke else args.mate1_heldout_count,
        mate2_train_count=1 if args.smoke else args.mate2_train_count,
        mate2_heldout_count=1 if args.smoke else args.mate2_heldout_count,
        max_shared_atom_candidates_per_choice=2 if args.smoke else 3,
        top_k=2 if args.smoke else args.top_k,
        two_stage_top_k=3 if args.smoke else args.two_stage_top_k,
        epsilon_tail_count=1 if args.smoke else args.epsilon_tail_count,
        equivalence_count=1 if args.smoke else 4,
        compare_repetition_2=False if args.smoke else not args.no_compare_repetition_2,
        progress_output=args.progress_output,
    )
    result = run_continuous_handoff_attention(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "selected_attention_mode",
        "mate1_heldout_accuracy",
        "mate1_null_count",
        "mate2_conversion_rate",
        "mate2_first_move_success_rate",
        "mate2_same_graph_second_move_count",
        "internal_attention_false_positive_count",
        "internal_attention_false_negative_count",
        "deep_reply_checks_run",
        "scheduler_equivalence_mismatch_count",
        "failure_mode",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
