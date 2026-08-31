"""Viewed, development-only runner for the adaptive-boundary integration shot.

The intrinsic V2 runner owns curriculum construction and execution.  This
module only selects a bounded R1 work profile and wraps its same-run authority
factory so deferred structure is event-driven rather than scheduled.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
from time import perf_counter
import traceback
from typing import Any, Mapping, Sequence

from . import native_intrinsic_v2_development as _intrinsic
from .native_intrinsic_curriculum import (
    NativeIntrinsicCurriculumConfig,
    NativeIntrinsicCurriculumResult,
    R1DevelopmentCeilingReached,
    R1_ACTION_ORDER_STABLE_HASH_PERMUTATION,
    R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
    _Pools,
)
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    StructuralMode,
)
from .native_single_graph_curriculum import NativeReConKRKGraph
from recon_lite_hector.learning import IntrinsicCreditEngine


# v2 adds an explicit scientific-gate summary to ``attempt.json``.  In
# particular, process completion and an R1 gate pass are different outcomes.
SCHEMA_VERSION = "native_adaptive_boundary_development.v2"
DEVELOPMENT_LABEL = "DEVELOPMENT_VIEWED_NOT_SCIENTIFIC"
DEFAULT_SEED = _intrinsic.DEFAULT_SEED

# The intrinsic runner uses 900_000.  Keep this runner's viewed FEN identity
# stream disjoint even when both runners use the same seed and geometry.
DEVELOPMENT_FEN_FULLMOVE_BASE = 1_700_000
DEFAULT_MAX_WALL_SECONDS = 7_200.0
DEFAULT_MAX_PEAK_RSS_MIB = 8_192.0
DEFAULT_OUTPUT_DIR = Path(
    "reports/autogrowth/development/"
    "native_adaptive_boundary_seed_2026082801"
)

PROFILES = ("canary", "gate")

# Keep the wrapped runner seams visible for focused tests and future ecology
# wiring without copying its implementation into this module.
run_native_intrinsic_curriculum = _intrinsic.run_native_intrinsic_curriculum
_atomic_write_json = _intrinsic._atomic_write_json

# These are deliberately the only profile-varying fields.  All R0 counts,
# learner values, gates, replay, and freeze controls come from the wrapped
# runner's fixed development_config().
_PROFILE_WORK: dict[str, dict[str, int | str]] = {
    "canary": {
        "r1_pool_mode": "random",
        "r1_train_count": 8,
        "r1_validation_count": 4,
        "r1_regression_count": 4,
        # Mechanism seeds stop at the exact epoch-4 checkpoint.  A longer
        # profile is a separate go decision after positive-shell evidence.
        "r1_epochs": 4,
        "r1_validation_interval": 1,
        "r1_snapshot_interval": 1,
    },
    "gate": {
        "r1_pool_mode": "balanced_setup",
        "r1_train_count": 16,
        "r1_validation_count": 16,
        "r1_regression_count": 16,
        "r1_epochs": 48,
        "r1_validation_interval": 4,
        "r1_snapshot_interval": 4,
    },
}


def _normalize_profile(profile: str) -> str:
    normalized = str(profile).strip().lower()
    if normalized not in PROFILES:
        raise ValueError(
            f"profile must be one of {', '.join(PROFILES)}"
        )
    return normalized


def _profile_for_config(config: NativeIntrinsicCurriculumConfig) -> str:
    for profile, overrides in _PROFILE_WORK.items():
        if all(getattr(config, key) == value for key, value in overrides.items()):
            return profile
    return "caller_configured"


def _development_source_identity() -> dict[str, Any]:
    identity = dict(_intrinsic._development_source_identity())
    identity["wrapped_intrinsic_development_runner_sha256"] = identity.get(
        "development_runner_sha256"
    )
    identity["development_runner_module"] = __name__
    identity["development_runner_sha256"] = hashlib.sha256(
        Path(__file__).read_bytes()
    ).hexdigest()
    return identity


def _artifact_flags() -> dict[str, Any]:
    return {
        "label": DEVELOPMENT_LABEL,
        "scientific_use_permitted": False,
        "protected_outcomes_accessed": False,
        "no_protected_outcomes": True,
        # Exhaustive all-reply mate evaluation is a scientific-harness read
        # performed after policy decisions.  It never supplies moves, labels,
        # or values to the learner, so name that narrower guarantee directly
        # instead of ambiguously claiming that the harness uses no oracle-like
        # evaluator at all.
        "learner_oracle_used": False,
        "no_learner_oracle": True,
        "harness_exhaustive_evaluation_used": True,
        "harness_evaluation_influences_learning": False,
        "learner_parameter_tuning_performed": False,
        "no_learner_tuning": True,
    }


def _strict_bool(value: Any) -> bool | None:
    """Return only an actual boolean; malformed gate evidence is unknown."""

    return value if type(value) is bool else None


def _result_gate_fields(result_payload: Mapping[str, Any]) -> dict[str, Any]:
    """Extract gate evidence without treating work completion as success.

    The curriculum's ``decision`` block is authoritative when present.  The
    fallbacks keep small test doubles and older result readers useful, but are
    deliberately one-way: missing R1 evidence can never become a pass.
    """

    decision = result_payload.get("decision")
    decision = decision if isinstance(decision, Mapping) else {}
    r0 = result_payload.get("r0")
    r0 = r0 if isinstance(r0, Mapping) else {}
    r1_arms = result_payload.get("r1_arms")
    r1_executed_fallback = isinstance(r1_arms, Mapping) and bool(r1_arms)

    r0_pass = _strict_bool(decision.get("r0_pass"))
    if r0_pass is None:
        r0_pass = _strict_bool(r0.get("pass"))

    r1_executed = _strict_bool(decision.get("r1_executed"))
    if r1_executed is None:
        r1_executed = bool(r1_executed_fallback)

    # A missing r1_pass is an unproven gate, never a successful completion.
    r1_pass = _strict_bool(decision.get("r1_pass"))
    if r1_pass is None:
        r1_pass = False

    scientific_gate_passed = bool(
        r0_pass is True and r1_executed is True and r1_pass is True
    )
    return {
        "r0_pass": r0_pass,
        "r1_executed": r1_executed,
        "r1_pass": r1_pass,
        "work_completed": True,
        "scientific_gate_passed": scientific_gate_passed,
    }


def _completion_status(gates: Mapping[str, Any]) -> str:
    """Name the completed-work outcome without conflating it with a pass."""

    r0_pass = gates.get("r0_pass")
    if r0_pass is False:
        return "BLOCKED_AT_R0_MASTERY_GATE"
    if r0_pass is not True:
        return "COMPLETED_WITHOUT_CONFIRMED_R0_GATE"
    if gates.get("r1_executed") is not True:
        return "COMPLETED_R0_ONLY_NO_R1_GATE"
    if gates.get("r1_pass") is not True:
        return "COMPLETED_R1_GATE_FAILED"
    return "SCIENTIFIC_GATE_PASSED"


def _unknown_gate_fields(*, work_completed: bool) -> dict[str, Any]:
    """Return the explicit, conservative fields for interrupted/failed work."""

    return {
        "r0_pass": None,
        "r1_executed": None,
        "r1_pass": None,
        "work_completed": bool(work_completed),
        "scientific_gate_passed": False,
    }


def _development_protocol(
    config: NativeIntrinsicCurriculumConfig,
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        **_artifact_flags(),
        "profile": _profile_for_config(config),
        "seed": int(config.seed),
        "development_input_physical_identity_namespace": {
            "fullmove_base": DEVELOPMENT_FEN_FULLMOVE_BASE,
            "source_generators_emit_fullmove_number": 1,
            "purpose": "separate viewed adaptive-boundary development stream",
        },
        "frozen_r0_learner_settings": True,
        "r1_reply_policy": config.r1_reply_policy,
        "r1_action_order": config.r1_action_order,
        "resource_ceilings": {
            "wall_seconds_safe_epoch_boundary": (
                config.development_wall_ceiling_seconds
            ),
            "peak_rss_mib_safe_epoch_boundary": (
                config.development_peak_rss_ceiling_mib
            ),
        },
        "no_protected_outcomes_or_learner_oracle_or_tuning": True,
    }


def _correct_event_driven_audit(
    audit: Mapping[str, Any],
) -> dict[str, Any]:
    corrected = copy.deepcopy(dict(audit))
    corrected.update(_artifact_flags())
    corrected["development_runner_schema_version"] = SCHEMA_VERSION
    schedule = dict(corrected.get("structural_schedule") or {})
    schedule.update({
        "mode": StructuralMode.EVENT_DRIVEN.value,
        "structural_mode": StructuralMode.EVENT_DRIVEN.value,
        "absolute_event_frontiers": [],
        "scheduled_frontiers": [],
        "prospective_events_before_structure": None,
        "frontier_policy": "event_driven_at_quiescent_real_boundary",
        "no_scheduled_frontiers": True,
    })
    corrected["structural_schedule"] = schedule
    corrected["structural_mode"] = StructuralMode.EVENT_DRIVEN.value
    corrected["structural_epoch_schedule"] = []
    corrected["no_scheduled_frontiers"] = True
    corrected["serialization_roundtrip_exact"] = True
    corrected["full_history_boundary_exact"] = True
    return corrected


def build_same_run_v2_r0_authority(
    graph: NativeReConKRKGraph,
    credit: IntrinsicCreditEngine,
    pools: _Pools,
    config: NativeIntrinsicCurriculumConfig,
) -> tuple[NativeProspectiveAuthorityV2, Mapping[str, Any]]:
    """Wrap the intrinsic same-run factory with event-driven structure."""

    authority, audit = _intrinsic.build_same_run_v2_r0_authority(
        graph, credit, pools, config
    )
    if authority.structural_mode is not StructuralMode.EVENT_DRIVEN:
        raise RuntimeError(
            "adaptive authority was not constructed in event-driven mode"
        )
    if authority.structural_epoch_schedule:
        raise RuntimeError("adaptive authority retained a scheduled frontier")
    authority.verify_full_history_boundary(
        "native-adaptive-boundary-development"
    )
    payload = authority.dumps()
    restored = type(authority).loads(payload)
    if restored.continuation_manifest() != authority.continuation_manifest():
        raise RuntimeError(
            "adaptive-boundary event-driven authority failed exact roundtrip"
        )
    restored.verify_full_history_boundary(
        "native-adaptive-boundary-development-roundtrip"
    )
    return authority, _correct_event_driven_audit(audit)


def development_config(
    profile: str = "canary",
    *,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
    seed: int = DEFAULT_SEED,
    max_wall_seconds: float = DEFAULT_MAX_WALL_SECONDS,
    max_peak_rss_mib: float = DEFAULT_MAX_PEAK_RSS_MIB,
) -> NativeIntrinsicCurriculumConfig:
    """Return one of two bounded work plans with frozen learner settings."""

    normalized = _normalize_profile(profile)
    base = _intrinsic.development_config(
        output_dir=Path(output_dir),
        max_wall_seconds=float(max_wall_seconds),
        max_peak_rss_mib=float(max_peak_rss_mib),
    )
    return replace(
        base,
        seed=int(seed),
        r1_reply_policy=R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
        r1_action_order=R1_ACTION_ORDER_STABLE_HASH_PERMUTATION,
        r0_boundary_ecology_enabled=True,
        development_fen_fullmove_base=DEVELOPMENT_FEN_FULLMOVE_BASE,
        **_PROFILE_WORK[normalized],
    )


def run_development(
    config: NativeIntrinsicCurriculumConfig | None = None,
) -> NativeIntrinsicCurriculumResult:
    cfg = config or development_config()
    result = run_native_intrinsic_curriculum(
        config=cfg,
        r0_child_authority_factory=build_same_run_v2_r0_authority,
    )
    result.payload.update(_artifact_flags())
    result.payload["development_protocol"] = _development_protocol(cfg)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=PROFILES, default="canary")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--max-wall-seconds",
        type=float,
        default=DEFAULT_MAX_WALL_SECONDS,
    )
    parser.add_argument(
        "--max-peak-rss-mib",
        type=float,
        default=DEFAULT_MAX_PEAK_RSS_MIB,
    )
    args = parser.parse_args(argv)
    output_dir = Path(args.output_dir)
    cfg = development_config(
        profile=args.profile,
        output_dir=output_dir,
        seed=args.seed,
        max_wall_seconds=args.max_wall_seconds,
        max_peak_rss_mib=args.max_peak_rss_mib,
    )
    started = perf_counter()
    attempt_path = output_dir / "attempt.json"
    try:
        result = run_development(cfg)
        output = Path(cfg.output_path)
        result_payload = result.to_dict()
        _atomic_write_json(output, result_payload)
    except R1DevelopmentCeilingReached as exc:
        _atomic_write_json(
            attempt_path,
            {
                "schema_version": SCHEMA_VERSION,
                **_artifact_flags(),
                "status": "CEILING_REACHED_AT_EXACT_EPOCH_SNAPSHOT",
                **_unknown_gate_fields(work_completed=False),
                "profile": args.profile,
                "epoch": exc.epoch,
                "snapshot_path": str(exc.snapshot_path),
                "reason": exc.reason,
                "wall_seconds": perf_counter() - started,
                "source_identity": _development_source_identity(),
                "config": asdict(cfg),
            },
        )
        print(json.dumps({"status": "CEILING_REACHED", "attempt": str(attempt_path)}))
        return 2
    except Exception as exc:
        _atomic_write_json(
            attempt_path,
            {
                "schema_version": SCHEMA_VERSION,
                **_artifact_flags(),
                "status": "FAILED",
                **_unknown_gate_fields(work_completed=False),
                "profile": args.profile,
                "error": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "wall_seconds": perf_counter() - started,
                "source_identity": _development_source_identity(),
                "config": asdict(cfg),
            },
        )
        print(json.dumps({"status": "FAILED", "attempt": str(attempt_path)}))
        return 1
    gates = _result_gate_fields(result_payload)
    completion_status = _completion_status(gates)
    r0_gate_failed = gates["r0_pass"] is False
    _atomic_write_json(
        attempt_path,
        {
            "schema_version": SCHEMA_VERSION,
            **_artifact_flags(),
            "status": completion_status,
            **gates,
            "profile": args.profile,
            "result_path": str(output),
            "wall_seconds": perf_counter() - started,
            "source_identity": _development_source_identity(),
            "config": asdict(cfg),
        },
    )
    if r0_gate_failed:
        print(json.dumps({"status": "R0_GATE_BLOCKED", "result": str(output)}))
        return 3
    print(json.dumps({
        "status": completion_status,
        "scientific_gate_passed": gates["scientific_gate_passed"],
        "result": str(output),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
