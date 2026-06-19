#!/usr/bin/env python3
"""Run TG27a native foundation scale plus frozen replay checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    NativeFoundationScaleReplayConfig,
    run_native_foundation_scale_replay,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports/autogrowth/krk_autogrowth_tg27a_native_foundation_scale_replay.json"),
    )
    parser.add_argument(
        "--progress-output",
        type=str,
        default="reports/autogrowth/krk_autogrowth_tg27a_native_foundation_scale_replay_progress.json",
    )
    parser.add_argument("--mate1-train-count", type=int, default=32)
    parser.add_argument("--mate1-heldout-count", type=int, default=16)
    parser.add_argument("--mate2-train-count", type=int, default=16)
    parser.add_argument("--mate2-heldout-count", type=int, default=8)
    parser.add_argument("--replay-count", type=int, default=10)
    parser.add_argument("--full-replay-count", type=int, default=0)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg27a_native_foundation_scale_replay_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg27a_native_foundation_scale_replay.json")
        else args.output
    )
    cfg = NativeFoundationScaleReplayConfig(
        mate1_train_count=4 if args.smoke else args.mate1_train_count,
        mate1_heldout_count=2 if args.smoke else args.mate1_heldout_count,
        mate2_train_count=1 if args.smoke else args.mate2_train_count,
        mate2_heldout_count=1 if args.smoke else args.mate2_heldout_count,
        max_shared_atom_candidates_per_choice=2 if args.smoke else 3,
        equivalence_count=1 if args.smoke else 4,
        max_samples=3 if args.smoke else 24,
        replay_count=2 if args.smoke else args.replay_count,
        full_replay_count=0 if args.smoke else args.full_replay_count,
        run_ablations=not args.smoke,
        run_scheduler_equivalence=not args.smoke,
        progress_output=args.progress_output,
    )
    result = run_native_foundation_scale_replay(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "mate1_heldout_accuracy",
        "mate1_null_count",
        "mate2_conversion_rate",
        "mate2_first_move_success_rate",
        "mate2_same_graph_second_move_count",
        "continuation_mate1_accuracy",
        "continuation_mate1_null_count",
        "frozen_m3_used",
        "any_weight_updates_during_eval",
        "m4_promotions_during_eval",
        "replay_stability_pass",
        "replay_uses_cached_frozen_records",
        "scheduler_equivalence_mismatch_count",
        "failure_mode",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
