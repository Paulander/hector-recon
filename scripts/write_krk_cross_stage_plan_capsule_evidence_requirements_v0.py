#!/usr/bin/env python3
"""Write cross-stage PlanCapsule evidence requirements for KRK.

This is design/readiness only. It does not add runtime PlanCapsule behavior,
does not collect labels, and does not make PlanCapsuleSpec causal.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN_CAPSULE_REVIEW = ROOT / "reports/strategy_arbitration/krk_plan_capsule_sequence_candidate_observation_review_v1.json"
SEQUENCE_POLICY_DESIGN = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json"
CONTROL_PLANE_GATE = ROOT / "reports/krk_current_control_plane_gate_v0.json"
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_cross_stage_plan_capsule_evidence_requirements_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_cross_stage_plan_capsule_evidence_requirements_v0.md"

SCHEMA_VERSION = "krk_cross_stage_plan_capsule_evidence_requirements.v0"


COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_candidate_generator_changes_implemented": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(
    *,
    plan_capsule_review: dict[str, Any] | None = None,
    sequence_policy_design: dict[str, Any] | None = None,
    control_plane_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan_capsule_review = plan_capsule_review or _load(PLAN_CAPSULE_REVIEW)
    sequence_policy_design = sequence_policy_design or _load(SEQUENCE_POLICY_DESIGN)
    control_plane_gate = control_plane_gate or _load(CONTROL_PLANE_GATE)

    plan_readiness = plan_capsule_review.get("readiness", {})
    seq_readiness = sequence_policy_design.get("readiness", {})
    stage7_only = bool(plan_readiness.get("stage7_only_evidence", True))
    protected_cross_stage = bool(plan_readiness.get("protected_cross_stage_evidence", False))
    clean_success_met = bool(seq_readiness.get("stage7_clean_success_controls_met", False))
    clean_failure_met = bool(seq_readiness.get("stage7_clean_failure_controls_met", False))

    evidence_ready = protected_cross_stage and clean_success_met and clean_failure_met
    status = (
        "cross_stage_plan_capsule_evidence_ready_for_non_causal_benchmark"
        if evidence_ready
        else "cross_stage_plan_capsule_evidence_requirements_defined_blocked"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_requirements_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_plan_capsule_sequence_candidate_observation_review_v1.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json",
            "reports/krk_current_control_plane_gate_v0.json",
        ],
        "current_readiness": {
            "plan_capsule_stage7_only_evidence": stage7_only,
            "protected_cross_stage_plan_capsule_evidence": protected_cross_stage,
            "plan_capsule_policy_succeeded": bool(plan_readiness.get("policy_succeeded")),
            "stage7_clean_success_controls_met": clean_success_met,
            "stage7_clean_failure_controls_met": clean_failure_met,
            "sequence_policy_benchmark_ready": bool(seq_readiness.get("benchmark_ready")),
            "control_plane_gate_status": control_plane_gate.get("decision", {}).get("status"),
        },
        "required_evidence_frames": [
            {
                "frame_id": "stage4.first_move_or_wrong_tempo_plan_window",
                "source_stage": "stage4",
                "purpose": "test whether short plan windows can distinguish wrong-tempo first-move contrast from drift",
                "required_fields": [
                    "plan_candidate_id",
                    "entry_terms_confirmed",
                    "first_move_candidate_terms",
                    "progress_terms_after_first_reply",
                    "abort_terms",
                    "handoff_target_if_any",
                    "h40_outcome_label",
                    "causal_status=non_causal",
                ],
                "minimum_examples": {"success": 4, "failure": 4},
            },
            {
                "frame_id": "stage5.fence_handoff_plan_window",
                "source_stage": "stage5",
                "purpose": "verify that plan-window evidence preserves validated fence/handoff behavior",
                "required_fields": [
                    "fence_contract_terms",
                    "handoff_packet_trace",
                    "plan_entry_or_abstain",
                    "safe_preservation_label",
                    "h40_outcome_label",
                    "causal_status=non_causal",
                ],
                "minimum_examples": {"success": 4, "failure": 2},
            },
            {
                "frame_id": "stage6.drive_to_edge_plan_window",
                "source_stage": "stage6",
                "purpose": "verify that plan-window evidence does not override protected drive-to-edge overlay behavior",
                "required_fields": [
                    "drive_progress_terms",
                    "owner_preservation_terms",
                    "candidate_handoff_terms",
                    "h40_outcome_label",
                    "causal_status=non_causal",
                ],
                "minimum_examples": {"success": 4, "failure": 2},
            },
            {
                "frame_id": "stage7.heldout_post_box_plan_window",
                "source_stage": "stage7",
                "purpose": "held-out challenge only; evaluate whether cross-stage plan evidence explains post-box failures",
                "required_fields": [
                    "post_box_entry_terms",
                    "progress_terms",
                    "exit_or_handoff_terms",
                    "stagnation_terms",
                    "h40_outcome_label",
                    "heldout_challenge=true",
                    "causal_status=non_causal",
                ],
                "minimum_examples": {"success": 5, "failure": 5},
            },
        ],
        "acceptance_before_sequence_policy_benchmark": {
            "protected_stage4_5_6_frame_count_min": 20,
            "stage7_heldout_success_min": 5,
            "stage7_heldout_failure_min": 5,
            "stage7_training_rows": 0,
            "selector_training_rows": 0,
            "runtime_authorization_rows": 0,
            "plan_capsule_spec_causal": False,
            "dtm_runtime_lookup": False,
            "topology_mutation": False,
        },
        "non_causal_collection_options": [
            {
                "option_id": "replay_free_protected_window_extraction",
                "description": "recover plan-window terms from existing protected Stage 4/5/6 traces if available",
                "requires_approval": False,
                "risk": "may lack explicit entry/progress/exit/abort fields",
            },
            {
                "option_id": "bounded_protected_trace_collection",
                "description": "collect trace-only protected Stage 4/5/6 plan-window metadata with no score/routing effect",
                "requires_approval": True,
                "risk": "new collection run; must prove default-off equivalence",
            },
            {
                "option_id": "approved_stage7_diverse_clean_label_run",
                "description": "run the existing Stage 7 diverse clean sampling manifest to fill held-out success controls",
                "requires_approval": True,
                "risk": "Stage7-only labels; still not promotion or Stage8 authorization",
            },
        ],
        "decision": {
            "status": status,
            "recommended_next_step": "attempt_replay_free_protected_window_extraction_before_new_runs",
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    readiness = payload["current_readiness"]
    lines = [
        "# KRK Cross-Stage PlanCapsule Evidence Requirements v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a non-causal requirements artifact. It does not implement PlanCapsule runtime behavior, collect labels, train a selector, promote Stage 7, or train Stage 8.",
        "",
        "## Current Readiness",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in readiness.items())
    lines.extend(["", "## Required Evidence Frames", ""])
    for frame in payload["required_evidence_frames"]:
        lines.extend([
            f"### {frame['frame_id']}",
            "",
            f"- source_stage: `{frame['source_stage']}`",
            f"- purpose: {frame['purpose']}",
            f"- minimum_examples: `{frame['minimum_examples']}`",
            "- required_fields:",
        ])
        lines.extend(f"  - `{field}`" for field in frame["required_fields"])
        lines.append("")
    lines.extend([
        "## Acceptance Before Sequence-Policy Benchmark",
        "",
    ])
    lines.extend(
        f"- {key}: `{value}`"
        for key, value in payload["acceptance_before_sequence_policy_benchmark"].items()
    )
    lines.extend(["", "## Non-Causal Collection Options", ""])
    for option in payload["non_causal_collection_options"]:
        lines.extend([
            f"- `{option['option_id']}`: {option['description']} requires_approval=`{option['requires_approval']}`",
        ])
    lines.extend([
        "",
        "## Decision",
        "",
        f"- recommended_next_step: `{decision['recommended_next_step']}`",
        "- runtime_changes_allowed: `false`",
        "- label_run_allowed: `false`",
        "- selector_training_allowed: `false`",
        "- Stage 7 promotion and Stage 8 training remain blocked.",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"]["status"],
        "recommended_next_step": payload["decision"]["recommended_next_step"],
    }, indent=2))


if __name__ == "__main__":
    main()
