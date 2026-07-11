#!/usr/bin/env python3
"""Freeze the high-resolution intrinsic KRK R1 experiment before execution."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    NativeIntrinsicCurriculumConfig,
    R1_RETIRED_DEVELOPMENT_FENS,
    _build_pools,
)


OUTPUT = Path(
    "reports/autogrowth/native_from_scratch/"
    "r1_highres_balanced_seed_20260718_preregistration.json"
)
RESULT = Path(
    "reports/autogrowth/native_from_scratch/"
    "r1_highres_balanced240_seed_20260718.json"
)
PROGRESS = Path(
    "reports/autogrowth/native_from_scratch/"
    "r1_highres_balanced240_seed_20260718_progress.json"
)


def main() -> int:
    config = NativeIntrinsicCurriculumConfig(
        output_path=str(RESULT),
        progress_path=str(PROGRESS),
        seed=20260718,
        r0_train_count=24,
        r0_validation_count=8,
        r0_regression_count=8,
        r0_gate_train_decoy_count=8,
        r0_gate_validation_decoy_count=8,
        r0_gate_regression_decoy_count=8,
        r1_train_count=48,
        r1_validation_count=16,
        r1_regression_count=16,
        r1_pool_mode="balanced_setup",
        r0_epochs=48,
        r1_epochs=240,
        r0_replay_per_r1_epoch=0,
        r0_validation_interval=8,
        max_samples=16,
        r0_availability_mode="virtual_frame_verified",
    )
    pools = _build_pools(config)
    artifact = {
        "schema_version": "krk_native_intrinsic_r1_preregistration.v0",
        "status": "frozen_before_execution",
        "frozen_on": "2026-07-11",
        "parent_commit": "37fcba7",
        "scientific_question": (
            "Can an empty learned-state ReCoN master Mate-in-2 by intrinsically "
            "handing control to its mature Mate-in-1 child when experience is "
            "balanced across the historically missed edge/corner orientations?"
        ),
        "hypotheses": {
            "H1": (
                "The full intrinsic-bootstrap arm reaches joint 100% conversion "
                "on the disjoint validation and regression pools and retains R0."
            ),
            "H0": (
                "The full arm remains below a gate or does not outperform the "
                "otherwise identical no-bootstrap control."
            ),
        },
        "fixed_config": asdict(config),
        "arms": {
            "full_intrinsic_bootstrap": (
                "Mature R0 child availability and learned intrinsic parent/edge "
                "credit are visible to R1 action selection."
            ),
            "no_bootstrap_control": (
                "Identical graph, pools, update budget, and outcome credit, with "
                "mature-child bootstrap unavailable."
            ),
        },
        "gates": {
            "r0_validation_accuracy": 1.0,
            "r0_regression_accuracy": 1.0,
            "r1_validation_conversion_rate": 1.0,
            "r1_regression_conversion_rate": 1.0,
            "r1_each_registered_stratum_conversion_rate": 1.0,
            "r0_retention_after_r1": 1.0,
            "causal_requirement": (
                "full intrinsic-bootstrap regression conversion is strictly "
                "greater than no-bootstrap regression conversion"
            ),
            "safety_requirement": "zero null or illegal selected moves",
        },
        "interpretation_policy": {
            "full_pass_control_fail": (
                "Outcome-grounded mature-child composition is causally useful "
                "for this bounded R1 curriculum."
            ),
            "both_pass": (
                "R1 is learnable here, but the hierarchical-bootstrap claim is "
                "not isolated by this experiment."
            ),
            "both_fail": (
                "Balanced experience is insufficient; inspect representation, "
                "competition, or autonomous composition without changing this run."
            ),
            "full_fail_control_pass": (
                "The bootstrap machinery is interfering and must not be rescued "
                "with a post-hoc narrative."
            ),
        },
        "purity_boundary": {
            "learned_state_at_start": "empty except the receptor root",
            "credit": "observed game outcome and internal mature-child value only",
            "exact_chess_predicates": (
                "used only before training for curriculum eligibility/stratification "
                "and after play for measurement; never supplied as learner features, "
                "action labels, shaping rewards, weights, or topology"
            ),
            "final_test": "not created or touched in this experiment",
        },
        "retired_development_fens": list(R1_RETIRED_DEVELOPMENT_FENS),
        "pool_manifest": pools.manifest(),
        "frozen_r1_pools": {
            "train": [
                {"fen": fen, "stratum": stratum}
                for fen, stratum in zip(
                    pools.r1_train, pools.r1_train_strata, strict=True
                )
            ],
            "validation": [
                {"fen": fen, "stratum": stratum}
                for fen, stratum in zip(
                    pools.r1_validation, pools.r1_validation_strata, strict=True
                )
            ],
            "regression": [
                {"fen": fen, "stratum": stratum}
                for fen, stratum in zip(
                    pools.r1_regression, pools.r1_regression_strata, strict=True
                )
            ],
        },
        "execution_command": (
            "uv run python scripts/autogrowth/run_native_intrinsic_curriculum.py "
            "--output reports/autogrowth/native_from_scratch/"
            "r1_highres_balanced240_seed_20260718.json "
            "--progress reports/autogrowth/native_from_scratch/"
            "r1_highres_balanced240_seed_20260718_progress.json "
            "--seed 20260718 --r0-train 24 --r0-validation 8 "
            "--r0-regression 8 --gate-train-decoys 8 "
            "--gate-validation-decoys 8 --gate-regression-decoys 8 "
            "--r1-train 48 --r1-validation 16 --r1-regression 16 "
            "--r1-pool-mode balanced_setup --r0-epochs 48 --r1-epochs 240 "
            "--r0-validation-interval 8 --r0-replay-per-r1-epoch 0 "
            "--max-samples 16 --availability virtual_frame_verified"
        ),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUTPUT}")
    print(artifact["pool_manifest"]["combined_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
