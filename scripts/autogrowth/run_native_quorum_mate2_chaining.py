#!/usr/bin/env python3
"""Run TG26v native quorum Mate_In_2 chaining checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    NativeQuorumMate2ChainingConfig,
    run_native_quorum_mate2_chaining,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26v_native_quorum_mate2_chaining.json"))
    parser.add_argument("--mate1-train-count", type=int, default=12)
    parser.add_argument("--mate1-heldout-count", type=int, default=6)
    parser.add_argument("--mate2-train-count", type=int, default=6)
    parser.add_argument("--mate2-heldout-count", type=int, default=3)
    parser.add_argument("--max-ticks", type=int, default=30)
    parser.add_argument("--max-samples", type=int, default=16)
    parser.add_argument("--max-candidates-per-move", type=int, default=1)
    parser.add_argument("--max-shared-atom-candidates-per-choice", type=int, default=3)
    parser.add_argument("--shared-atom-min-overlap", type=int, default=6)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26v_native_quorum_mate2_chaining_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg26v_native_quorum_mate2_chaining.json")
        else args.output
    )
    cfg = NativeQuorumMate2ChainingConfig(
        mate1_train_count=4 if args.smoke else args.mate1_train_count,
        mate1_heldout_count=2 if args.smoke else args.mate1_heldout_count,
        mate2_train_count=1 if args.smoke else args.mate2_train_count,
        mate2_heldout_count=1 if args.smoke else args.mate2_heldout_count,
        max_ticks=args.max_ticks,
        max_samples=args.max_samples,
        max_candidates_per_move=args.max_candidates_per_move,
        max_shared_atom_candidates_per_choice=2 if args.smoke else args.max_shared_atom_candidates_per_choice,
        shared_atom_min_overlap=args.shared_atom_min_overlap,
        equivalence_count=1 if args.smoke else 4,
    )
    result = run_native_quorum_mate2_chaining(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "checkpoint_pass",
        "mate1_materialized_quorum_accuracy",
        "mate1_materialized_quorum_nulls",
        "mate2_first_move_success_rate",
        "mate2_conversion_rate",
        "same_graph_second_move_count",
        "materialized_mate2_quorum_confirmed_count",
        "soft_chain_diagnostic_accuracy",
        "scheduler_equivalence_mismatch_count",
        "mate2_first_move_ablation_conversion",
        "mate1_quorum_ablation_conversion",
        "actuator_ablation_conversion",
        "failure_mode",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

