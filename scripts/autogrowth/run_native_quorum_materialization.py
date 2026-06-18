#!/usr/bin/env python3
"""Run TG26u native quorum materialization checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth import (
    NativeQuorumMaterializationConfig,
    run_native_quorum_materialization,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/autogrowth/krk_autogrowth_tg26u_native_quorum_materialization.json"))
    parser.add_argument("--train-count", type=int, default=12)
    parser.add_argument("--heldout-count", type=int, default=6)
    parser.add_argument("--max-ticks", type=int, default=30)
    parser.add_argument("--max-samples", type=int, default=24)
    parser.add_argument("--max-candidates-per-move", type=int, default=1)
    parser.add_argument("--max-shared-atom-candidates-per-choice", type=int, default=3)
    parser.add_argument("--shared-atom-min-overlap", type=int, default=6)
    parser.add_argument("--soft-quorum-min-positive-atoms", type=int, default=3)
    parser.add_argument("--materialized-quorum-min-positive-atoms", type=int, default=3)
    parser.add_argument("--materialized-quorum-min-evidence", type=float, default=-10000.0)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()

    output = (
        Path("reports/autogrowth/krk_autogrowth_tg26u_native_quorum_materialization_smoke.json")
        if args.smoke and args.output == Path("reports/autogrowth/krk_autogrowth_tg26u_native_quorum_materialization.json")
        else args.output
    )
    cfg = NativeQuorumMaterializationConfig(
        train_count=4 if args.smoke else args.train_count,
        heldout_count=2 if args.smoke else args.heldout_count,
        max_ticks=args.max_ticks,
        max_samples=args.max_samples,
        max_candidates_per_move=args.max_candidates_per_move,
        max_shared_atom_candidates_per_choice=2 if args.smoke else args.max_shared_atom_candidates_per_choice,
        shared_atom_min_overlap=args.shared_atom_min_overlap,
        soft_quorum_min_positive_atoms=args.soft_quorum_min_positive_atoms,
        materialized_quorum_min_positive_atoms=args.materialized_quorum_min_positive_atoms,
        materialized_quorum_min_evidence=args.materialized_quorum_min_evidence,
        equivalence_count=1 if args.smoke else 4,
    )
    result = run_native_quorum_materialization(config=cfg)
    path = result.write_json(output)
    decision = result.to_dict()["decision"]
    print(f"wrote {path}")
    for key in (
        "baseline_prototype_accuracy",
        "soft_quorum_accuracy",
        "materialized_quorum_accuracy",
        "materialized_quorum_nulls",
        "materialized_quorum_confirmed_inside_formal_engine_count",
        "top_atom_ablation_accuracy",
        "action_atom_ablation_accuracy",
        "actuator_ablation_accuracy",
        "scheduler_equivalence_mismatch_count",
        "checkpoint_pass",
    ):
        print(key, decision[key])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

