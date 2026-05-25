#!/usr/bin/env python3
"""Write KRK next-milestone decision reviews.

This script is intentionally non-causal: it summarizes existing evidence and
does not replace checkpoints, promote Stage 7, train Stage 8, or change runtime
behavior.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

REPLACEMENT_PACKET = Path(
    "reports/krk_clean_retrain_retry1_clean_stack_replacement_review_packet_v0.json"
)
STAGE4_CONTROL_REVIEW = Path(
    "reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json"
)
STAGE4_SCOPE_PACKET = Path(
    "reports/strategy_arbitration/krk_stage4_joined_trace_ownership_scope_review_packet_v0.json"
)
STAGE_BENCHMARK = Path(
    "reports/strategy_arbitration/krk_stage_conditioned_candidate_generation_benchmark_v3.json"
)
SELECTOR_DIVERSITY = Path(
    "reports/strategy_arbitration/krk_selector_objective_diversity_gap_review_v0.json"
)
STAGE7_GATE = Path("reports/structural_candidates/stage7_training_objective_decision_gate.json")
STAGE7_CLOSURE = Path("reports/structural_candidates/stage7_post_decision_closure.json")
STAGE7_TARGET_PROBE = Path("reports/structural_candidates/stage7_selected_path_target_probe_v0.json")
STAGE7_SEQUENCE_CONTROLS = Path(
    "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json"
)
ACTIVE_STACK = Path("reports/krk_active_protected_stack_v0.json")
POST_REPLACEMENT_VALIDATION = Path("reports/krk_clean_stack_post_replacement_validation_v0.json")

OUT_REPLACEMENT_JSON = Path("reports/krk_clean_stack_replacement_deferred_review_v0.json")
OUT_REPLACEMENT_MD = Path("reports/krk_clean_stack_replacement_deferred_review_v0.md")
OUT_STAGE4_MATRIX_JSON = Path("reports/krk_stage4_caveat_diagnostic_matrix_v0.json")
OUT_STAGE4_MATRIX_MD = Path("reports/krk_stage4_caveat_diagnostic_matrix_v0.md")
OUT_STAGE4_GATE_JSON = Path("reports/krk_stage4_caveat_decision_gate_v0.json")
OUT_STAGE4_GATE_MD = Path("reports/krk_stage4_caveat_decision_gate_v0.md")
OUT_STAGE7_UNLOCK_JSON = Path("reports/structural_candidates/stage7_heldout_unlock_review_v0.json")
OUT_STAGE7_UNLOCK_MD = Path("reports/structural_candidates/stage7_heldout_unlock_review_v0.md")
OUT_STAGE7_BLOCKER_JSON = Path("reports/structural_candidates/stage7_to_stage8_blocker_review_v0.json")
OUT_STAGE7_BLOCKER_MD = Path("reports/structural_candidates/stage7_to_stage8_blocker_review_v0.md")
OUT_DECISION_JSON = Path("reports/krk_curriculum_next_milestone_decision_v0.json")
OUT_DECISION_MD = Path("reports/krk_curriculum_next_milestone_decision_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def _load_optional(path: Path) -> dict[str, Any]:
    full_path = ROOT / path
    if not full_path.exists():
        return {}
    return _load(path)


def _common_invariants() -> dict[str, bool]:
    return {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion": False,
        "stage8_training": False,
        "protected_stack_replacement_performed": False,
    }


def build_replacement_deferred(now: str) -> dict[str, Any]:
    packet = _load(REPLACEMENT_PACKET)
    return {
        "schema_version": "krk_clean_stack_replacement_deferred_review.v0",
        "created_at": now,
        "status": "clean_stack_adoption_deferred_explicit_approval_required",
        "source_artifacts": [str(REPLACEMENT_PACKET)],
        "decision_state": "clean_stack_adoption_rejected_or_deferred",
        "review_packet_status": packet.get("status"),
        "replacement_review_ready": bool(packet.get("decision", {}).get("replacement_review_ready")),
        "implementation_allowed_by_review_packet": bool(
            packet.get("decision", {}).get("implementation_allowed_by_this_packet")
        ),
        "explicit_approval_detected": False,
        "exact_approval_request": (
            "Approve updating protected Stage 5/6 stack references from the current protected "
            "paths to the retry1 candidate paths listed in "
            "reports/krk_clean_retrain_retry1_clean_stack_replacement_review_packet_v0.json, "
            "with rollback paths preserved and immediate post-replacement validation required."
        ),
        "if_not_approved": "keep_current_protected_stack_and_continue_non_causal_stage4_stage7_reviews",
        "invariants": _common_invariants(),
    }


def build_stage4_matrix(now: str) -> tuple[dict[str, Any], dict[str, Any]]:
    control = _load(STAGE4_CONTROL_REVIEW)
    scope = _load(STAGE4_SCOPE_PACKET)
    benchmark = _load(STAGE_BENCHMARK)
    diversity = _load(SELECTOR_DIVERSITY)
    stage4_metrics = benchmark.get("summary", {}).get("stage4_positive_scope_metrics") or {}
    remaining = diversity.get("summary", {})
    max_plies = control.get("stage4_overlay", {}).get("max_plies")
    total = control.get("stage4_overlay", {}).get("total")
    hypotheses = [
        {
            "hypothesis": "local_move_shape_weakness",
            "evidence_for": [
                "Stage 4 one-ply status is failed.",
                f"Stage 4 overlay has {control.get('stage4_overlay', {}).get('worsened')}/{total} one-ply worsened samples.",
            ],
            "evidence_against": [
                "The same pattern reproduces exactly in the paired Stage 5 base control.",
                "No retry1 Stage 6 overlay regression is observed.",
            ],
            "missing_evidence": [
                "Per-failure candidate/provider trace context for the remaining wrong-tempo failures."
            ],
            "confidence": "medium",
            "recommended_next_test": "stage4_observation_only_trace_collection_if_explicitly_approved",
        },
        {
            "hypothesis": "sequence_followup_gap",
            "evidence_for": [
                f"Stage 4 h40 caveat has {max_plies}/{total} max_plies outcomes.",
                "Failures are h40 conversion failures, not only one-ply local reward misses.",
            ],
            "evidence_against": [
                "Existing evidence does not yet isolate first-move success followed by later drift."
            ],
            "missing_evidence": ["Trace windows around the 32 max_plies outcomes."],
            "confidence": "medium",
            "recommended_next_test": "trace_stage4_selected_failure_windows",
        },
        {
            "hypothesis": "candidate_generation_gap",
            "evidence_for": [
                f"Stage 4 positive-scope recall is {stage4_metrics.get('positive_recall')} in the stage-conditioned candidate-generation benchmark.",
                f"Remaining selected-owner failures are Stage 4: {remaining.get('remaining_stage4_selected_failure_count')}.",
                "A Stage 4 observation-only scope review packet is already review-ready.",
            ],
            "evidence_against": [
                "Stage 4 candidate-generation cells are mixed, so candidate expansion alone is not sufficient."
            ],
            "missing_evidence": [
                "Stage4-scoped joined trace/ownership rows with visible candidate context.",
                "Companion context terms separating positive from negative Stage 4 cells.",
            ],
            "confidence": "high",
            "recommended_next_test": "approve_stage4_observation_only_trace_collection_max_6_rows",
        },
        {
            "hypothesis": "horizon_or_label_issue",
            "evidence_for": [
                "The caveat is defined at h40 and may include slow conversions beyond the practical horizon."
            ],
            "evidence_against": [
                "No current artifact proves these failures convert under a longer horizon.",
                "The h40 caveat reproduces in control, so it remains a valid guardrail signal.",
            ],
            "missing_evidence": ["Classification-only longer-horizon labels for the 32 max_plies cases."],
            "confidence": "low",
            "recommended_next_test": "defer_h80_unless_stage4_trace_collection_is_inconclusive",
        },
        {
            "hypothesis": "existing_provider_solved_if_arbitrated",
            "evidence_for": [
                "Stage 4 selected-owner failure candidates exist and are concentrated in stage0_basin rows.",
                "Prior selector-objective review says Stage 4 is needed for switch-contrast evidence.",
            ],
            "evidence_against": [
                "Forced-provider capacity labels are not direct ownership labels.",
                "Selector training remains unauthorized.",
            ],
            "missing_evidence": [
                "Same-state visible alternatives for Stage 4 selected-owner failures.",
                "Safe-preservation controls in Stage 4 context.",
            ],
            "confidence": "medium",
            "recommended_next_test": "stage4_joined_trace_ownership_collection_non_causal",
        },
    ]
    matrix = {
        "schema_version": "krk_stage4_caveat_diagnostic_matrix.v0",
        "created_at": now,
        "status": "stage4_caveat_diagnostic_matrix_ready",
        "source_artifacts": [
            str(STAGE4_CONTROL_REVIEW),
            str(STAGE4_SCOPE_PACKET),
            str(STAGE_BENCHMARK),
            str(SELECTOR_DIVERSITY),
        ],
        "stage4_observed_caveat": {
            "total": total,
            "mate": control.get("stage4_overlay", {}).get("mate"),
            "max_plies": max_plies,
            "overlay_vs_base_control_delta": control.get("delta_overlay_vs_base_control"),
        },
        "hypotheses": hypotheses,
        "invariants": _common_invariants(),
    }
    gate = {
        "schema_version": "krk_stage4_caveat_decision_gate.v0",
        "created_at": now,
        "status": "stage4_candidate_generation_gap_with_known_residual_guardrail",
        "selected_decisions": [
            "stage4_candidate_generation_gap",
            "stage4_known_residual_keep_as_guardrail",
        ],
        "rejected_decisions": [
            "stage4_runtime_sandbox_review_ready",
            "stage4_horizon_label_issue_as_primary",
        ],
        "recommended_next_action": "explicit_approval_for_stage4_observation_only_trace_collection_or_keep_as_known_guardrail",
        "rationale": [
            "The caveat reproduces exactly in paired base control, so it is not retry1 overlay regression.",
            "Stage 4 candidate-generation cells are mixed and need companion context.",
            "The selector-objective evidence gap is concentrated in Stage 4 selected-owner failures.",
        ],
        "runtime_or_training_authorized": False,
        "invariants": _common_invariants(),
    }
    return matrix, gate


def build_stage7_reviews(now: str) -> tuple[dict[str, Any], dict[str, Any]]:
    gate = _load(STAGE7_GATE)
    closure = _load(STAGE7_CLOSURE)
    target = _load(STAGE7_TARGET_PROBE)
    controls = _load(STAGE7_SEQUENCE_CONTROLS)
    unlock = {
        "schema_version": "stage7_heldout_unlock_review.v0",
        "created_at": now,
        "status": "stage7_unlock_path_identified_broader_sequence_control_not_micro_repair",
        "source_artifacts": [
            str(STAGE7_GATE),
            str(STAGE7_CLOSURE),
            str(STAGE7_TARGET_PROBE),
            str(STAGE7_SEQUENCE_CONTROLS),
        ],
        "stage7_status": "local_valid_composition_quarantined",
        "selected_unlock_paths": [
            "stage7_sequence_policy_needed",
            "stage7_strategy_arbitration_needed",
            "stage7_curriculum_boundary_confirmed",
        ],
        "evidence": {
            "training_objective_gate": gate.get("selected_outcome"),
            "post_decision_closure": closure.get("decision", {}).get("selected_outcome"),
            "selected_path_probe": target.get("decision"),
            "clean_sequence_control_status": controls.get("decision"),
            "clean_sequence_success_controls_met": controls.get("acceptance", {}).get(
                "clean_sequence_success_controls_met"
            ),
        },
        "interpretation": [
            "Simple ranked/pairwise and internal-monitor-augmented objectives did not justify Stage 7 runtime repair.",
            "Selected-path targets are separable but source-biased and too small for runtime authorization.",
            "Clean sequence controls are insufficient for a robust Stage 7 sequence-policy benchmark.",
            "Stage 7 remains best used as a held-out challenge for strategy/sequence control-plane work.",
        ],
        "recommended_next_action": "collect_clean_sequence_controls_or_design_broader_sequence_policy_benchmark_without_stage7_promotion",
        "invariants": _common_invariants(),
    }
    blocker = {
        "schema_version": "stage7_to_stage8_blocker_review.v0",
        "created_at": now,
        "status": "stage8_remains_blocked_with_review",
        "source_artifacts": [str(STAGE7_GATE), str(STAGE7_CLOSURE), str(STAGE7_SEQUENCE_CONTROLS)],
        "stage7_status": "local_valid_composition_quarantined",
        "stage8_training_allowed": False,
        "stage7_promotion_allowed": False,
        "blockers": [
            "Stage 7 benchmark decision is model_expression_gap_persists_stage7_micro_work_stops.",
            "Stage 7 has insufficient clean successful sequence controls.",
            "Stage 7 remains a curriculum-boundary/held-out challenge, not a protected promoted stage.",
            "Stage 8 would inherit unresolved Stage 7 continuation and ownership uncertainty.",
        ],
        "minimum_unblock_requirements": [
            "Clean family-held-out Stage 7 sequence controls beyond current sparse set.",
            "A broader KRK sequence-policy or strategy-arbitration benchmark that improves held-out Stage 7 challenge cases.",
            "Guardrail-preserving review packet explicitly allowing Stage 8 training.",
        ],
        "recommended_next_action": "do_not_train_stage8; continue_broader_krk_strategy_sequence_control_plane",
        "invariants": _common_invariants(),
    }
    return unlock, blocker


def build_curriculum_decision(
    now: str,
    replacement: dict[str, Any],
    stage4_gate: dict[str, Any],
    stage7_unlock: dict[str, Any],
    stage7_blocker: dict[str, Any],
) -> dict[str, Any]:
    active = _load_optional(ACTIVE_STACK)
    post_validation = _load_optional(POST_REPLACEMENT_VALIDATION)
    adopted = (
        active.get("status") == "retry1_protected_stage5_6_stack_adopted_manifest_only"
        and post_validation.get("status") == "clean_stack_adopted_and_validated"
        and post_validation.get("decision", {}).get("clean_stack_adopted_and_validated") is True
    )
    stack_state = (
        "clean_stack_adopted_and_validated"
        if adopted
        else replacement["decision_state"]
    )
    stack_status = (
        "retry1_protected_stage5_6_stack_adopted_manifest_only"
        if adopted
        else "current_protected_stack_unchanged_retry1_review_ready_only"
    )
    recommended_path = (
        [
            "Use the active retry1 Stage 5/6 protected-stack manifest as the current protected reference.",
            "Keep rollback paths preserved; do not copy, delete, or overwrite snapshot files.",
            "For Stage 4, the next useful evidence is the already-reviewed observation-only trace collection scope, capped and non-causal.",
            "For Stage 7, stop micro-repairs and build broader sequence-policy/strategy-arbitration evidence with Stage 7 held out.",
        ]
        if adopted
        else [
            "Choose whether to explicitly approve rollback-aware retry1 protected Stage 5/6 adoption.",
            "If approval is not granted, keep current protected stack and continue non-causal Stage 4/7 evidence work.",
            "For Stage 4, the next useful evidence is the already-reviewed observation-only trace collection scope, capped and non-causal.",
            "For Stage 7, stop micro-repairs and build broader sequence-policy/strategy-arbitration evidence with Stage 7 held out.",
        ]
    )
    forbidden = (
        [
            "destructive snapshot replacement without rollback review",
            "Stage 7 promotion",
            "Stage 8 training",
            "runtime selector implementation",
            "runtime DTM/tablebase",
            "gameplay topology mutation",
            "capacity labels as ownership labels",
        ]
        if adopted
        else [
            "protected-stack replacement without explicit approval",
            "Stage 7 promotion",
            "Stage 8 training",
            "runtime selector implementation",
            "runtime DTM/tablebase",
            "gameplay topology mutation",
            "capacity labels as ownership labels",
        ]
    )
    invariants = _common_invariants()
    invariants["active_stack_reference_updated"] = adopted
    return {
        "schema_version": "krk_curriculum_next_milestone_decision.v0",
        "created_at": now,
        "status": "krk_curriculum_next_milestone_review_ready",
        "source_artifacts": [
            str(REPLACEMENT_PACKET),
            str(ACTIVE_STACK),
            str(POST_REPLACEMENT_VALIDATION),
            str(OUT_STAGE4_GATE_JSON),
            str(OUT_STAGE7_UNLOCK_JSON),
            str(OUT_STAGE7_BLOCKER_JSON),
        ],
        "decision_states": [
            stack_state,
            "stage4_caveat_reduction_path_identified",
            "stage7_unlock_path_identified",
            "stage8_remains_blocked_with_review",
        ],
        "current_adopted_protected_stack_status": stack_status,
        "stage4_status": stage4_gate["status"],
        "stage7_status": stage7_unlock["status"],
        "stage8_status": stage7_blocker["status"],
        "recommended_path_forward": recommended_path,
        "what_remains_forbidden": forbidden,
        "invariants": invariants,
    }


def _write(path: Path, payload: dict[str, Any]) -> None:
    (ROOT / path).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / path).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _md_header(title: str, payload: dict[str, Any], lines: list[str]) -> str:
    body = "\n".join(lines)
    return f"# {title}\n\nStatus: `{payload['status']}`\n\n{body}\n"


def write_markdowns(
    replacement: dict[str, Any],
    stage4_matrix: dict[str, Any],
    stage4_gate: dict[str, Any],
    stage7_unlock: dict[str, Any],
    stage7_blocker: dict[str, Any],
    decision: dict[str, Any],
) -> None:
    (ROOT / OUT_REPLACEMENT_MD).write_text(
        _md_header(
            "KRK Clean Stack Replacement Deferred Review v0",
            replacement,
            [
                f"- Decision state: `{replacement['decision_state']}`",
                f"- Review packet ready: `{replacement['replacement_review_ready']}`",
                f"- Implementation allowed by review packet: `{replacement['implementation_allowed_by_review_packet']}`",
                f"- Explicit approval detected: `{replacement['explicit_approval_detected']}`",
                "",
                "Exact approval request:",
                "",
                f"> {replacement['exact_approval_request']}",
                "",
                "Boundary: no protected paths were changed.",
            ],
        ),
        encoding="utf-8",
    )
    hypothesis_lines = []
    for item in stage4_matrix["hypotheses"]:
        hypothesis_lines.append(
            f"- `{item['hypothesis']}` confidence=`{item['confidence']}` next=`{item['recommended_next_test']}`"
        )
    (ROOT / OUT_STAGE4_MATRIX_MD).write_text(
        _md_header(
            "KRK Stage 4 Caveat Diagnostic Matrix v0",
            stage4_matrix,
            [
                f"- Observed h40 caveat: `{stage4_matrix['stage4_observed_caveat']}`",
                "",
                "Hypotheses:",
                "",
                *hypothesis_lines,
                "",
                "Boundary: replay-free diagnostic only; no runtime behavior authorized.",
            ],
        ),
        encoding="utf-8",
    )
    (ROOT / OUT_STAGE4_GATE_MD).write_text(
        _md_header(
            "KRK Stage 4 Caveat Decision Gate v0",
            stage4_gate,
            [
                f"- Selected decisions: `{stage4_gate['selected_decisions']}`",
                f"- Rejected decisions: `{stage4_gate['rejected_decisions']}`",
                f"- Recommended next action: `{stage4_gate['recommended_next_action']}`",
                f"- Runtime or training authorized: `{stage4_gate['runtime_or_training_authorized']}`",
            ],
        ),
        encoding="utf-8",
    )
    (ROOT / OUT_STAGE7_UNLOCK_MD).write_text(
        _md_header(
            "Stage 7 Held-Out Unlock Review v0",
            stage7_unlock,
            [
                f"- Stage 7 status: `{stage7_unlock['stage7_status']}`",
                f"- Selected unlock paths: `{stage7_unlock['selected_unlock_paths']}`",
                f"- Recommended next action: `{stage7_unlock['recommended_next_action']}`",
                "",
                "Interpretation:",
                "",
                *[f"- {line}" for line in stage7_unlock["interpretation"]],
            ],
        ),
        encoding="utf-8",
    )
    (ROOT / OUT_STAGE7_BLOCKER_MD).write_text(
        _md_header(
            "Stage 7 to Stage 8 Blocker Review v0",
            stage7_blocker,
            [
                f"- Stage 7 promotion allowed: `{stage7_blocker['stage7_promotion_allowed']}`",
                f"- Stage 8 training allowed: `{stage7_blocker['stage8_training_allowed']}`",
                "",
                "Blockers:",
                "",
                *[f"- {line}" for line in stage7_blocker["blockers"]],
                "",
                "Minimum unblock requirements:",
                "",
                *[f"- {line}" for line in stage7_blocker["minimum_unblock_requirements"]],
            ],
        ),
        encoding="utf-8",
    )
    (ROOT / OUT_DECISION_MD).write_text(
        _md_header(
            "KRK Curriculum Next Milestone Decision v0",
            decision,
            [
                f"- Decision states: `{decision['decision_states']}`",
                f"- Protected stack status: `{decision['current_adopted_protected_stack_status']}`",
                f"- Stage 4 status: `{decision['stage4_status']}`",
                f"- Stage 7 status: `{decision['stage7_status']}`",
                f"- Stage 8 status: `{decision['stage8_status']}`",
                "",
                "Recommended path forward:",
                "",
                *[f"- {line}" for line in decision["recommended_path_forward"]],
                "",
                "Still forbidden:",
                "",
                *[f"- {line}" for line in decision["what_remains_forbidden"]],
            ],
        ),
        encoding="utf-8",
    )


def main() -> None:
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    replacement = build_replacement_deferred(now)
    stage4_matrix, stage4_gate = build_stage4_matrix(now)
    stage7_unlock, stage7_blocker = build_stage7_reviews(now)
    decision = build_curriculum_decision(now, replacement, stage4_gate, stage7_unlock, stage7_blocker)

    for path, payload in [
        (OUT_REPLACEMENT_JSON, replacement),
        (OUT_STAGE4_MATRIX_JSON, stage4_matrix),
        (OUT_STAGE4_GATE_JSON, stage4_gate),
        (OUT_STAGE7_UNLOCK_JSON, stage7_unlock),
        (OUT_STAGE7_BLOCKER_JSON, stage7_blocker),
        (OUT_DECISION_JSON, decision),
    ]:
        _write(path, payload)
    write_markdowns(replacement, stage4_matrix, stage4_gate, stage7_unlock, stage7_blocker, decision)
    print(json.dumps({"status": decision["status"], "json_output": str(OUT_DECISION_JSON)}, indent=2))


if __name__ == "__main__":
    main()
