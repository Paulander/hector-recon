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
    parser.add_argument("--r0-epochs", type=int, default=defaults.r0_epochs)
    parser.add_argument("--r1-epochs", type=int, default=defaults.r1_epochs)
    parser.add_argument("--r0-replay-per-r1-epoch", type=int, default=defaults.r0_replay_per_r1_epoch)
    parser.add_argument(
        "--availability",
        choices=("prototype_gate", "virtual_frame_verified"),
        default=defaults.r0_availability_mode,
    )
    parser.add_argument("--no-r1", action="store_true")
    parser.add_argument("--no-freeze-r0", action="store_true")
    parser.add_argument("--no-child-priority", action="store_true")
    parser.add_argument("--include-redundant-child-ablation", action="store_true")
    args = parser.parse_args()

    config = NativeIntrinsicCurriculumConfig(
        output_path=str(args.output),
        progress_path=str(args.progress),
        seed=args.seed,
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
        r0_replay_per_r1_epoch=args.r0_replay_per_r1_epoch,
        run_r1=not args.no_r1,
        freeze_r0_parameters_for_r1=not args.no_freeze_r0,
        mature_child_priority=not args.no_child_priority,
        run_redundant_child_ablation=args.include_redundant_child_ablation,
        r0_availability_mode=args.availability,
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
