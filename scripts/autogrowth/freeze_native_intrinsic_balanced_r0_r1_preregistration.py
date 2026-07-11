#!/usr/bin/env python3
"""Freeze the balanced R0/R1 correction after the preregistered R0 gate failure."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from recon_lite_chess.autogrowth.native_intrinsic_curriculum import (
    NativeIntrinsicCurriculumConfig,
    _build_pools,
    _r1_orbit_key,
)

BASE = Path("reports/autogrowth/native_from_scratch")
RETIRED = BASE / "r0_failed_seed_20260718_retired_fens.json"
OUTPUT = BASE / "r0_r1_balanced_seed_20260719_preregistration.json"
RESULT = BASE / "r0_r1_balanced96_240_seed_20260719.json"
PROGRESS = BASE / "r0_r1_balanced96_240_seed_20260719_progress.json"


def _retired_r0_fens() -> tuple[str, ...]:
    prior = _build_pools(
        NativeIntrinsicCurriculumConfig(
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
        )
    )
    return prior.r0_train + prior.r0_validation + prior.r0_regression


def main() -> int:
    retired = _retired_r0_fens()
    config = NativeIntrinsicCurriculumConfig(
        output_path=str(RESULT),
        progress_path=str(PROGRESS),
        seed=20260719,
        r0_train_count=48,
        r0_validation_count=16,
        r0_regression_count=16,
        r0_gate_train_decoy_count=16,
        r0_gate_validation_decoy_count=16,
        r0_gate_regression_decoy_count=16,
        r1_train_count=48,
        r1_validation_count=16,
        r1_regression_count=16,
        r0_pool_mode="balanced_location",
        r0_excluded_fens=retired,
        r1_pool_mode="balanced_setup",
        r0_epochs=96,
        r1_epochs=240,
        r0_replay_per_r1_epoch=0,
        r0_validation_interval=8,
        max_samples=16,
        r0_availability_mode="virtual_frame_verified",
    )
    pools = _build_pools(config)
    retired_orbits = {_r1_orbit_key(fen) for fen in retired}
    generated_r0 = pools.r0_train + pools.r0_validation + pools.r0_regression
    overlap = retired_orbits.intersection(_r1_orbit_key(fen) for fen in generated_r0)
    if overlap:
        raise RuntimeError(f"balanced R0 pool reuses {len(overlap)} retired orbits")
    artifact = {
        "schema_version": "krk_native_intrinsic_balanced_r0_r1_preregistration.v0",
        "status": "frozen_before_correction_execution",
        "frozen_on": "2026-07-11",
        "parent_failed_preregistration": (
            "r1_highres_balanced_seed_20260718_preregistration.json"
        ),
        "parent_failed_result": "r1_highres_balanced240_seed_20260718.json",
        "failure_trigger": {
            "r0_validation_accuracy": 0.75,
            "r0_regression_accuracy": 1.0,
            "r1_executed": False,
            "interpretation": (
                "R1 was not tested. The random R0 pool repeated the historical "
                "corner/orientation coverage failure that R1 balancing had addressed."
            ),
        },
        "correction": (
            "Balance R0 across four edges and four corners, double R0 experience "
            "resolution to 48/16/16, exclude all observed R0 D4 orbits, retain "
            "the balanced R1 design and all purity constraints."
        ),
        "hypotheses": {
            "R0": (
                "The balanced, higher-resolution R0 curriculum reaches joint 100% "
                "validation/regression and freezes without later plastic drift."
            ),
            "R1": (
                "Conditional on R0 passing, the full intrinsic-bootstrap arm reaches "
                "joint 100% balanced R1 conversion and beats no-bootstrap."
            ),
        },
        "fixed_config": asdict(config),
        "gates": {
            "r0_validation_accuracy": 1.0,
            "r0_regression_accuracy": 1.0,
            "r1_validation_conversion_rate": 1.0,
            "r1_regression_conversion_rate": 1.0,
            "r0_retention_after_r1": 1.0,
            "causal_requirement": "full R1 regression > no-bootstrap R1 regression",
            "safety_requirement": "zero null, illegal, rook-loss, or stalemate selections",
        },
        "purity_boundary": {
            "learned_start": "empty except receptor root",
            "learner_credit": "observed outcome and internal mature-child value only",
            "solution_predicates": (
                "curriculum eligibility/stratification and measurement only; never "
                "learner features, action targets, shaping reward, weights, or topology"
            ),
        },
        "retired_r0_orbit_overlap_count": 0,
        "pool_manifest": pools.manifest(),
        "frozen_pools": {
            name: [
                {"fen": fen, "stratum": label}
                for fen, label in zip(fens, labels, strict=True)
            ]
            for name, fens, labels in (
                ("r0_train", pools.r0_train, pools.r0_train_strata),
                ("r0_validation", pools.r0_validation, pools.r0_validation_strata),
                ("r0_regression", pools.r0_regression, pools.r0_regression_strata),
                ("r1_train", pools.r1_train, pools.r1_train_strata),
                ("r1_validation", pools.r1_validation, pools.r1_validation_strata),
                ("r1_regression", pools.r1_regression, pools.r1_regression_strata),
            )
        },
        "execution_command": (
            "uv run python scripts/autogrowth/run_native_intrinsic_curriculum.py "
            "--output reports/autogrowth/native_from_scratch/"
            "r0_r1_balanced96_240_seed_20260719.json --progress reports/autogrowth/"
            "native_from_scratch/r0_r1_balanced96_240_seed_20260719_progress.json "
            "--seed 20260719 --r0-train 48 --r0-validation 16 --r0-regression 16 "
            "--gate-train-decoys 16 --gate-validation-decoys 16 "
            "--gate-regression-decoys 16 --r0-pool-mode balanced_location "
            "--r0-excluded-pool reports/autogrowth/native_from_scratch/"
            "r0_failed_seed_20260718_retired_fens.json --r1-train 48 "
            "--r1-validation 16 --r1-regression 16 --r1-pool-mode balanced_setup "
            "--r0-epochs 96 --r1-epochs 240 --r0-validation-interval 8 "
            "--r0-replay-per-r1-epoch 0 --max-samples 16 "
            "--availability virtual_frame_verified"
        ),
    }
    BASE.mkdir(parents=True, exist_ok=True)
    RETIRED.write_text(json.dumps(list(retired), indent=2) + "\n", encoding="utf-8")
    OUTPUT.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"wrote {RETIRED}")
    print(f"wrote {OUTPUT}")
    print(artifact["pool_manifest"]["combined_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
