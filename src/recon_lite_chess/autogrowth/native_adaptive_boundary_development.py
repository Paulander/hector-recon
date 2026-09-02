"""Viewed, development-only runner for the adaptive-boundary integration shot.

The intrinsic V2 runner owns curriculum construction and execution. This
module binds a bounded work profile to the strict local-action, empty-boundary
mechanism and fails closed if a caller re-enables a retired host control.
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
    R0_ACTION_SELECTION_LOCAL_RECON,
    R0DevelopmentCeilingReached,
    R1DevelopmentCeilingReached,
    R1_ACTION_SELECTION_LOCAL_RECON,
    R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
    _Pools,
)
from .native_prospective_evidence_authority_v2 import (
    NativeProspectiveAuthorityV2,
    StructuralMode,
)
from .native_single_graph_curriculum import NativeReConKRKGraph
from recon_lite_hector.learning import IntrinsicCreditEngine


# v3 binds the empty local shell and fail-closed adaptive mechanism contract in
# addition to the explicit scientific-gate summary in ``attempt.json``. In
# particular, process completion and an R1 gate pass are different outcomes.
SCHEMA_VERSION = "native_adaptive_boundary_development.v3"
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

FOLLOW_THROUGH_PROFILE = "follow-through"
PROFILES = ("canary", FOLLOW_THROUGH_PROFILE, "gate")

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
    FOLLOW_THROUGH_PROFILE: {
        "r1_pool_mode": "random",
        "r1_train_count": 8,
        "r1_validation_count": 4,
        "r1_regression_count": 4,
        # Continue only through the fixed epoch-8 boundary.  This is the
        # bounded follow-through window after the epoch-4 canary.
        "r1_epochs": 8,
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
    normalized = str(profile).strip().lower().replace("_", "-")
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
    r0_training = r0.get("training")
    r0_training = r0_training if isinstance(r0_training, Mapping) else {}
    contract = result_payload.get("scientific_contract")
    contract = contract if isinstance(contract, Mapping) else {}
    initial_authority = result_payload.get("r0_child_authority")
    initial_authority = (
        initial_authority if isinstance(initial_authority, Mapping) else {}
    )
    initial_authority_state = initial_authority.get("initial_state")
    initial_authority_state = (
        initial_authority_state
        if isinstance(initial_authority_state, Mapping)
        else {}
    )
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

    curriculum_gate_passed = bool(
        r0_pass is True and r1_executed is True and r1_pass is True
    )
    primary = (
        r1_arms.get("full_intrinsic", {})
        if isinstance(r1_arms, Mapping)
        else {}
    )
    primary = primary if isinstance(primary, Mapping) else {}
    training = primary.get("training")
    training = training if isinstance(training, Mapping) else {}
    validation = primary.get("validation")
    validation = validation if isinstance(validation, Mapping) else {}
    retention = primary.get("r0_validation_retention")
    retention = retention if isinstance(retention, Mapping) else {}
    frozen_retention = primary.get("r0_frozen_native_policy_retention")
    frozen_retention = (
        frozen_retention if isinstance(frozen_retention, Mapping) else retention
    )
    shell_coverage = primary.get("r0_v2_shell_coverage")
    shell_coverage = (
        shell_coverage if isinstance(shell_coverage, Mapping) else None
    )
    authority = primary.get("v2_child_authority")
    authority = authority if isinstance(authority, Mapping) else {}
    lineages = authority.get("adaptive_positive_lineages")
    lineages = lineages if isinstance(lineages, Mapping) else {}
    recent_actions = training.get("local_action_recent_events")
    recent_actions = (
        recent_actions
        if isinstance(recent_actions, list)
        else []
    )
    # A position being revisited is not evidence that the learned policy was
    # revisited: native-local exploration can emit a fresh pattern each time.
    # Require the exact local pattern identity to recur before reporting a
    # score/action change.  A positive exposure count can corroborate that
    # recurrence, but cannot replace the prior same-identity check.
    prior_action_by_pattern: dict[str, Mapping[str, Any]] = {}
    revisited_score_or_action_change = False
    for event in recent_actions:
        if not isinstance(event, Mapping):
            continue
        pattern_id = event.get("pattern_id")
        if not isinstance(pattern_id, str) or not pattern_id:
            continue
        prior = prior_action_by_pattern.get(pattern_id)
        same_pattern_id = bool(
            prior is not None and prior.get("pattern_id") == pattern_id
        )
        # ``prediction`` is the bounded graph-owned value that actually enters
        # local competition and TD.  ``raw_value`` is only the generalized
        # pre-choice audit score and may now be absent for an already learned
        # exact option because re-auditing it cannot affect behavior.
        prior_policy_value = (
            prior.get("prediction", prior.get("raw_value"))
            if prior
            else None
        )
        policy_value = event.get("prediction", event.get("raw_value"))
        if same_pattern_id and (
            prior.get("move_uci") != event.get("move_uci")
            or prior_policy_value != policy_value
        ):
            revisited_score_or_action_change = True
        prior_action_by_pattern[pattern_id] = event
    ecology = training.get("boundary_ecology")
    ecology = ecology if isinstance(ecology, Mapping) else {}
    structural_events = authority.get("structural_events")
    structural_events = (
        structural_events if isinstance(structural_events, list) else []
    )
    retirement_and_reuse_same_safe_point = any(
        isinstance(event, Mapping)
        and bool(event.get("retired_cell_ids"))
        and bool(event.get("child_ids"))
        for event in structural_events
    )
    mechanism_checks = {
        "r0_native_local_action_policy": bool(
            r0_training.get("r0_action_selection_mode")
            == R0_ACTION_SELECTION_LOCAL_RECON
            and int(r0_training.get("native_local_action_count", 0) or 0) > 0
            and int(r0_training.get("scheduled_action_count", -1) or 0) == 0
        ),
        "empty_event_driven_positive_shell": bool(
            initial_authority.get("boundary_initialization")
            == "empty_event_driven_positive_shell"
            and initial_authority.get("no_scheduled_frontiers") is True
            and initial_authority_state
            and all(
                int(value or 0) == 0
                for value in initial_authority_state.values()
            )
        ),
        "validation_outcome_mastery_report_only": bool(
            contract.get(
                "validation_outcome_mastery_is_report_only_for_stage_transitions"
            )
            is True
        ),
        "native_local_action_policy": (
            training.get("r1_action_selection_mode")
            == R1_ACTION_SELECTION_LOCAL_RECON
        ),
        "exact_emission_credit_identity": bool(
            recent_actions
            and all(
                isinstance(event, Mapping)
                and event.get("triplet_id")
                == event.get("credited_triplet_id")
                for event in recent_actions
            )
        ),
        "candidate_cap_unbound": not bool(
            training.get("local_candidate_cap_bound", True)
        ),
        "revisited_local_score_or_action_changed": (
            revisited_score_or_action_change
        ),
        "positive_promoted_lineage": bool(
            int(lineages.get("lineage_count", 0) or 0) > 0
        ),
        "postbirth_certification": bool(
            int(lineages.get("certified_node_count", 0) or 0) > 0
            and int(
                lineages.get("postbirth_certification_receipt_count", 0)
                or 0
            ) > 0
        ),
        "zero_certification_leakage": bool(
            lineages.get("all_certification_disjoint") is True
            and lineages.get("all_certification_postbirth") is True
            and int(lineages.get("certification_leak_count", -1) or 0) == 0
        ),
        "available_all_reply_envelope": bool(
            int(training.get("all_reply_envelope_available_count", 0) or 0)
            > 0
        ),
        "nonzero_handoff": bool(
            int(training.get("child_handoff_count", 0) or 0) > 0
        ),
        "nonzero_successor_value": bool(
            float(training.get("successor_value_sum", 0.0) or 0.0) > 0.0
        ),
        "actual_mate_in_two_conversion": bool(
            int(validation.get("conversion_count", 0) or 0) > 0
        ),
        "r0_validation_retained": bool(
            # Keep the compatibility check name, but use the explicitly
            # frozen native-policy metric when present.  In adaptive V2 the
            # old retention field is shell admission coverage and may fall
            # as the shell evolves without indicating graph forgetting.
            float(frozen_retention.get("accuracy", 0.0) or 0.0) == 1.0
        ),
        "authority_roundtrip_and_history_exact": bool(
            authority.get("serialization_roundtrip_exact") is True
            and authority.get("full_history_boundary_exact") is True
        ),
        "bounded_ecology_turnover": bool(
            int(ecology.get("tombstone_count", 0) or 0) > 0
            and int(ecology.get("active_candidate_count", 0) or 0)
            <= int(ecology.get("active_candidate_cap", -1) or -1)
        ),
        "authority_retirement_and_slot_reuse": (
            retirement_and_reuse_same_safe_point
        ),
        "actual_snapshot_resume_exercised": bool(
            training.get("resumed_from_snapshot") is True
        ),
    }
    mechanism_gate_passed = bool(
        curriculum_gate_passed and all(mechanism_checks.values())
    )
    return {
        "r0_pass": r0_pass,
        "r1_executed": r1_executed,
        "r1_pass": r1_pass,
        "work_completed": True,
        "curriculum_gate_passed": curriculum_gate_passed,
        "mechanism_checks": mechanism_checks,
        "per_run_mechanism_gate_passed": mechanism_gate_passed,
        # Every artifact from this module is explicitly development-only, and
        # the real go decision also requires replication across independent
        # seeds.  A single local process must never call itself scientific.
        "scientific_gate_passed": False,
        "multi_seed_scientific_adjudication_required": True,
        "r0_validation_retention_metric": retention.get("metric_name"),
        "r0_validation_retention_semantics": retention.get("metric_semantics"),
        "r0_frozen_native_policy_retention": frozen_retention,
        "r0_v2_shell_coverage": shell_coverage,
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
    if gates.get("per_run_mechanism_gate_passed") is not True:
        return "COMPLETED_R1_MECHANISM_GATE_FAILED"
    return "PER_RUN_MECHANISM_GATE_PASSED_DEVELOPMENT_ONLY"


def _unknown_gate_fields(*, work_completed: bool) -> dict[str, Any]:
    """Return the explicit, conservative fields for interrupted/failed work."""

    return {
        "r0_pass": None,
        "r1_executed": None,
        "r1_pass": None,
        "work_completed": bool(work_completed),
        "curriculum_gate_passed": False,
        "mechanism_checks": {},
        "per_run_mechanism_gate_passed": False,
        "scientific_gate_passed": False,
        "multi_seed_scientific_adjudication_required": True,
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
        "r1_action_selection_mode": config.r1_action_selection_mode,
        "r1_action_order": config.r1_action_order,
        "r1_action_order_field_used": False,
        "legacy_hash_or_round_robin_first_move_picker_used": False,
        "r0_replay_move_provider_used": bool(
            config.r0_replay_per_r1_epoch > 0
        ),
        "adaptive_config_is_fail_closed": True,
        "prototype_gate_used_for_adaptive_runtime_routing": False,
        "r0_action_selection_mode": config.r0_action_selection_mode,
        "r0_native_local_action_selection": bool(
            config.r0_action_selection_mode
            == R0_ACTION_SELECTION_LOCAL_RECON
        ),
        # The harness still decides when the fixed R0 interaction phase ends
        # and when R1 examples begin.  At that content-blind safe point it may
        # stop if the graph has no self-authorized local provider, but it does
        # not turn an aggregate train/validation score into maturity, value,
        # action priority, or graph structure.
        "stage_gates_are_harness_stop_go_only": True,
        "stage_gates_are_harness_controlled": True,
        "r0_stage_entry_controller": "local_direct_outcome_provider_readiness",
        "training_outcome_controls_maturity_consolidation_freeze_and_stage_entry": (
            False
        ),
        "aggregate_training_score_controls_learning_or_stage_entry": False,
        "exact_local_real_returns_control_exact_provider_authority": True,
        "content_blind_safe_point_commits_local_provider_states": True,
        "global_r0_competence_state_used": False,
        "graph_wide_maturation_used": False,
        "whole_curriculum_endogenous_claimed": False,
        "validation_controls_maturity_consolidation_freeze_and_stage_entry": (
            config.validation_controls_stage_transitions
        ),
        "validation_selected_stage_mutations": (
            [
                "maturity",
                "value_consolidation",
                "parameter_freeze",
                "curriculum_stage_entry",
            ]
            if config.validation_controls_stage_transitions
            else []
        ),
        "validation_outcome_mastery_is_report_only_for_stage_transitions": not bool(
            config.validation_controls_stage_transitions
        ),
        "validation_is_report_only_for_stage_transitions": True,
        "validation_runtime_integrity_safety_veto_may_block_stage_entry": bool(
            not config.validation_controls_stage_transitions
            and config.r0_boundary_ecology_enabled
        ),
        "validation_does_not_select_runtime_actions": True,
        "resource_ceilings": {
            "wall_seconds_safe_epoch_boundary": (
                config.development_wall_ceiling_seconds
            ),
            "peak_rss_mib_safe_epoch_boundary": (
                config.development_peak_rss_ceiling_mib
            ),
        },
        "no_protected_outcomes_or_learner_oracle_or_tuning": True,
        "no_bootstrap_control_semantics": (
            "same_authority_and_ecology_without_successor_value_handoff"
        ),
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


def build_empty_event_driven_v2_r0_authority(
    graph: NativeReConKRKGraph,
    credit: IntrinsicCreditEngine,
    pools: _Pools,
    config: NativeIntrinsicCurriculumConfig,
) -> tuple[NativeProspectiveAuthorityV2, Mapping[str, Any]]:
    """Build an evidence-empty shell whose later growth is event-driven."""

    authority, audit = _intrinsic.build_empty_event_driven_v2_r0_authority(
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
    """Return a bounded work plan with frozen learner settings."""

    normalized = _normalize_profile(profile)
    base = _intrinsic.development_config(
        output_dir=Path(output_dir),
        max_wall_seconds=float(max_wall_seconds),
        max_peak_rss_mib=float(max_peak_rss_mib),
    )
    return replace(
        base,
        seed=int(seed),
        r0_action_selection_mode=R0_ACTION_SELECTION_LOCAL_RECON,
        r1_reply_policy=R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
        r1_action_selection_mode=R1_ACTION_SELECTION_LOCAL_RECON,
        r0_boundary_ecology_enabled=True,
        validation_controls_stage_transitions=False,
        development_fen_fullmove_base=DEVELOPMENT_FEN_FULLMOVE_BASE,
        **_PROFILE_WORK[normalized],
    )


def _validate_adaptive_mechanism_config(
    config: NativeIntrinsicCurriculumConfig,
) -> None:
    """Fail closed if a caller re-enables a retired host control."""

    required = {
        "r0_action_selection_mode": R0_ACTION_SELECTION_LOCAL_RECON,
        "r1_action_selection_mode": R1_ACTION_SELECTION_LOCAL_RECON,
        "r1_reply_policy": R1_REPLY_POLICY_PROSPECTIVE_COUNTEREXAMPLE,
        "r0_availability_mode": _intrinsic.V2_PROSPECTIVE_AVAILABILITY,
        "r0_boundary_ecology_enabled": True,
        "validation_controls_stage_transitions": False,
        "r0_replay_per_r1_epoch": 0,
        "run_r1": True,
        "freeze_r0_parameters_for_r1": True,
        # In strict mode this is not a training preference: it guarantees that
        # read-only evaluation queries the same authority-owned competence
        # shell used by training instead of silently reporting a legacy graph
        # route with the child authority disconnected.
        "mature_child_priority": True,
        "run_redundant_child_ablation": False,
        "r1_mechanistic_factorial": False,
        "r1_composite_proposal_epochs": (),
        "r1_composite_consolidation_epochs": (),
    }
    mismatches = {
        field: {"required": expected, "observed": getattr(config, field)}
        for field, expected in required.items()
        if getattr(config, field) != expected
    }
    if mismatches:
        raise ValueError(
            "adaptive mechanism config re-enabled a retired host control: "
            + json.dumps(mismatches, sort_keys=True)
        )


def run_development(
    config: NativeIntrinsicCurriculumConfig | None = None,
) -> NativeIntrinsicCurriculumResult:
    cfg = config or development_config()
    _validate_adaptive_mechanism_config(cfg)
    result = run_native_intrinsic_curriculum(
        config=cfg,
        r0_child_authority_factory=build_empty_event_driven_v2_r0_authority,
    )
    result.payload.update(_artifact_flags())
    result.payload["development_protocol"] = _development_protocol(cfg)
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default="canary",
        type=_normalize_profile,
    )
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
    except R0DevelopmentCeilingReached as exc:
        _atomic_write_json(
            attempt_path,
            {
                "schema_version": SCHEMA_VERSION,
                **_artifact_flags(),
                "status": "R0_CEILING_REACHED_AT_COMPLETE_EPOCH_NON_RESUMABLE",
                **_unknown_gate_fields(work_completed=False),
                "profile": args.profile,
                "epoch": exc.epoch,
                "reason": exc.reason,
                "resumable": False,
                "wall_seconds": perf_counter() - started,
                "source_identity": _development_source_identity(),
                "config": asdict(cfg),
            },
        )
        print(json.dumps({"status": "R0_CEILING_REACHED", "attempt": str(attempt_path)}))
        return 2
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
