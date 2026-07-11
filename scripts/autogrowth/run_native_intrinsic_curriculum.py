#!/usr/bin/env python3
"""Run the native empty-state intrinsic KRK R0/R1 curriculum."""

from __future__ import annotations

import argparse
from pathlib import Path

from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    NativeIntrinsicCurriculumConfig,
    run_native_intrinsic_curriculum,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    defaults = NativeIntrinsicCurriculumConfig()
    parser.add_argument("--output", type=Path, default=Path(defaults.output_path))
    parser.add_argument("--progress", type=Path, default=Path(defaults.progress_path))
    parser.add_argument("--seed", type=int, default=defaults.seed)
    parser.add_argument("--r0-train", type=int, default=defaults.r0_train_count)
    parser.add_argument("--r0-validation", type=int, default=defaults.r0_validation_count)
    parser.add_argument("--r0-regression", type=int, default=defaults.r0_regression_count)
    parser.add_argument("--r1-train", type=int, default=defaults.r1_train_count)
    parser.add_argument("--gate-train-decoys", type=int, default=defaults.r0_gate_train_decoy_count)
    parser.add_argument("--gate-validation-decoys", type=int, default=defaults.r0_gate_validation_decoy_count)
    parser.add_argument("--gate-regression-decoys", type=int, default=defaults.r0_gate_regression_decoy_count)
    parser.add_argument("--r1-validation", type=int, default=defaults.r1_validation_count)
    parser.add_argument("--r1-regression", type=int, default=defaults.r1_regression_count)
    parser.add_argument(
        "--r0-pool-mode",
        choices=("random", "balanced_location"),
        default=defaults.r0_pool_mode,
    )
    parser.add_argument("--r0-excluded-pool", type=Path)
    parser.add_argument(
        "--r1-pool-mode",
        choices=("random", "balanced_setup"),
        default=defaults.r1_pool_mode,
    )
    parser.add_argument(
        "--r0-validation-interval", type=int, default=defaults.r0_validation_interval
    )
    parser.add_argument(
        "--r1-validation-interval", type=int, default=defaults.r1_validation_interval
    )
    parser.add_argument(
        "--r1-snapshot-interval", type=int, default=defaults.r1_snapshot_interval
    )
    parser.add_argument(
        "--r1-snapshot-dir", type=Path, default=Path(defaults.r1_snapshot_dir)
    )
    parser.add_argument("--no-resume-r1", action="store_true")
    parser.add_argument("--no-checkpoint-history", action="store_true")
    parser.add_argument("--max-samples", type=int, default=defaults.max_samples)
    parser.add_argument("--r0-epochs", type=int, default=defaults.r0_epochs)
    parser.add_argument("--r1-epochs", type=int, default=defaults.r1_epochs)
    parser.add_argument("--r0-replay-per-r1-epoch", type=int, default=defaults.r0_replay_per_r1_epoch)
    parser.add_argument(
        "--availability",
        choices=(
            "prototype_gate",
            "virtual_frame_verified",
            "real_child_rollout",
        ),
        default=defaults.r0_availability_mode,
    )
    parser.add_argument(
        "--mechanistic-factorial",
        action="store_true",
        help="Run the availability/value decomposition with composition off.",
    )
    parser.add_argument(
        "--placebo-child-value", type=float, default=defaults.r1_placebo_child_value
    )
    parser.add_argument(
        "--shuffle-seed", type=int, default=defaults.r1_shuffle_seed
    )
    parser.add_argument(
        "--child-cache-validation",
        choices=("live_formal", "frozen_policy_token"),
        default=defaults.r0_child_cache_validation_mode,
    )
    parser.add_argument(
        "--composite-proposal-epoch",
        action="append",
        type=int,
        default=None,
        help="Opt-in R1 structural epoch; repeat for multiple epochs.",
    )
    parser.add_argument(
        "--composite-consolidation-epoch",
        action="append",
        type=int,
        default=None,
        help="Opt-in paired on/off consolidation epoch; repeat as needed.",
    )
    parser.add_argument(
        "--composite-max-candidates",
        type=int,
        default=defaults.r1_composite_max_candidates,
    )
    parser.add_argument(
        "--composite-max-atoms-per-triplet",
        type=int,
        default=defaults.r1_composite_max_atoms_per_triplet,
    )
    parser.add_argument(
        "--composite-min-support",
        type=int,
        default=defaults.r1_composite_min_support,
    )
    parser.add_argument("--no-r1", action="store_true")
    parser.add_argument("--no-freeze-r0", action="store_true")
    parser.add_argument("--no-child-priority", action="store_true")
    parser.add_argument("--include-redundant-child-ablation", action="store_true")
    args = parser.parse_args()
    r0_excluded_fens: tuple[str, ...] = ()
    if args.r0_excluded_pool is not None:
        import json

        values = json.loads(args.r0_excluded_pool.read_text(encoding="utf-8"))
        if not isinstance(values, list) or not all(isinstance(fen, str) for fen in values):
            raise ValueError("--r0-excluded-pool must contain a JSON list of FENs")
        r0_excluded_fens = tuple(values)

    config = NativeIntrinsicCurriculumConfig(
        output_path=str(args.output),
        progress_path=str(args.progress),
        seed=args.seed,
        r0_pool_mode=args.r0_pool_mode,
        r0_excluded_fens=r0_excluded_fens,
        r1_pool_mode=args.r1_pool_mode,
        r0_train_count=args.r0_train,
        r0_validation_count=args.r0_validation,
        r0_regression_count=args.r0_regression,
        r0_gate_train_decoy_count=args.gate_train_decoys,
        r0_gate_validation_decoy_count=args.gate_validation_decoys,
        r0_gate_regression_decoy_count=args.gate_regression_decoys,
        r1_train_count=args.r1_train,
        r1_validation_count=args.r1_validation,
        r1_regression_count=args.r1_regression,
        r0_epochs=args.r0_epochs,
        r1_epochs=args.r1_epochs,
        r0_validation_interval=args.r0_validation_interval,
        r1_validation_interval=args.r1_validation_interval,
        r1_snapshot_interval=args.r1_snapshot_interval,
        r1_snapshot_dir=str(args.r1_snapshot_dir),
        resume_r1_snapshots=not args.no_resume_r1,
        r1_keep_checkpoint_history=not args.no_checkpoint_history,
        r1_mechanistic_factorial=args.mechanistic_factorial,
        r1_placebo_child_value=args.placebo_child_value,
        r1_shuffle_seed=args.shuffle_seed,
        r0_replay_per_r1_epoch=args.r0_replay_per_r1_epoch,
        max_samples=args.max_samples,
        run_r1=not args.no_r1,
        freeze_r0_parameters_for_r1=not args.no_freeze_r0,
        mature_child_priority=not args.no_child_priority,
        run_redundant_child_ablation=args.include_redundant_child_ablation,
        r0_availability_mode=args.availability,
        r0_child_cache_validation_mode=args.child_cache_validation,
        r1_composite_proposal_epochs=tuple(args.composite_proposal_epoch or ()),
        r1_composite_consolidation_epochs=tuple(
            args.composite_consolidation_epoch or ()
        ),
        r1_composite_max_candidates=args.composite_max_candidates,
        r1_composite_max_atoms_per_triplet=args.composite_max_atoms_per_triplet,
        r1_composite_min_support=args.composite_min_support,
    )
    result = run_native_intrinsic_curriculum(config=config)
    path = result.write_json()
    decision = result.payload["decision"]
    print(f"wrote {path}")
    print(
        "r0_pass",
        decision["r0_pass"],
        "r1_pass",
        decision["r1_pass"],
        "causal",
        decision["r1_causal_positive_vs_no_bootstrap"],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
