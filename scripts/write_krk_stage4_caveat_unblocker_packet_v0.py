#!/usr/bin/env python3
"""Write a passive Stage 4 caveat unblocker packet.

This packet consolidates the known Stage 4 h40 caveat, the first-move contrast
runtime-review packet, and the current control-plane approval state. It does
not implement the sandbox or authorize runtime behavior.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTROL_GATE = ROOT / "reports/krk_current_control_plane_gate_v0.json"
RUNTIME_PACKET = ROOT / "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json"
APPROVAL_REQUEST = (
    ROOT / "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
)
CAVEAT_CONTROL = ROOT / "reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json"
SEQUENCE_REVIEW = ROOT / "reports/krk_stage4_caveat_sequence_review_v0.json"
STRATIFIED_VALIDATION = ROOT / "reports/krk_stage4_stratified_contrast_validation_v0.json"
SEQUENCE_CONTRAST = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json"
OUTPUT_JSON = ROOT / "reports/krk_stage4_caveat_unblocker_packet_v0.json"
OUTPUT_MD = ROOT / "reports/krk_stage4_caveat_unblocker_packet_v0.md"

SCHEMA_VERSION = "krk_stage4_caveat_unblocker_packet.v0"

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _find_stage4_option(control_gate: dict[str, Any]) -> dict[str, Any]:
    for option in control_gate.get("approval_options") or []:
        if option.get("option_id") == "approve_stage4_first_move_contrast_sandbox":
            return option
    return {}


def build_payload() -> dict[str, Any]:
    control_gate = _load(CONTROL_GATE)
    runtime_packet = _load(RUNTIME_PACKET)
    approval_request = _load(APPROVAL_REQUEST)
    caveat_control = _load(CAVEAT_CONTROL)
    sequence_review = _load(SEQUENCE_REVIEW)
    stratified_validation = _load(STRATIFIED_VALIDATION)
    sequence_contrast = _load(SEQUENCE_CONTRAST)

    stage4_option = _find_stage4_option(control_gate)
    runtime_decision = runtime_packet.get("decision") or {}
    approval_request_decision = approval_request.get("decision") or {}
    approval_request_blockers = approval_request.get("blockers") or []
    approval_request_ready_for_runtime_approval = (
        approval_request_decision.get("status")
        == "stage4_first_move_contrast_sandbox_approval_request_ready"
        and not approval_request_blockers
    )
    approval_scope = approval_request.get("required_scope_if_user_approves") or {}
    sequence_summary = sequence_review.get("summary") or {}
    stratified_summary = stratified_validation.get("summary") or {}
    contrast_summary = sequence_contrast.get("summary") or {}

    runtime_review_ready = (
        runtime_decision.get("runtime_review_ready") is True
        and runtime_decision.get("requires_explicit_approval_before_implementation") is True
        and runtime_decision.get("implementation_authorized_by_this_packet") is False
        and stage4_option.get("status")
        == "stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval"
    )

    blockers: list[str] = []
    if not runtime_review_ready:
        blockers.append("stage4_first_move_contrast_runtime_review_not_ready")
    if (
        approval_request_decision.get("status")
        != "stage4_first_move_contrast_sandbox_approval_request_ready"
    ):
        blockers.append("stage4_first_move_contrast_approval_request_not_ready")
    if approval_request_blockers:
        blockers.append("stage4_first_move_contrast_approval_request_has_blockers")
    if caveat_control.get("status") != "stage4_caveat_reproduces_in_base_control_no_overlay_regression":
        blockers.append("stage4_caveat_control_status_unexpected")
    if not stratified_summary.get("gap_variant_count"):
        blockers.append("stage4_stratified_gap_variants_missing")

    status = (
        "stage4_caveat_unblocker_ready_pending_explicit_runtime_approval"
        if not blockers
        else "stage4_caveat_unblocker_blocked_pending_review"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_stage4_unblocker_packet",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_current_control_plane_gate_v0.json",
            "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json",
            "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json",
            "reports/krk_clean_retrain_retry1_stage4_caveat_control_review_v0.json",
            "reports/krk_stage4_caveat_sequence_review_v0.json",
            "reports/krk_stage4_stratified_contrast_validation_v0.json",
            "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json",
        ],
        "current_stage4_status": {
            "control_plane_option_status": stage4_option.get("status"),
            "control_plane_option_artifact": stage4_option.get("artifact"),
            "control_plane_approval_request_artifact": stage4_option.get(
                "approval_request_artifact"
            )
            or "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.md",
            "runtime_review_ready": runtime_decision.get("runtime_review_ready"),
            "approval_request_status": approval_request_decision.get("status"),
            "approval_request_blockers": approval_request_blockers,
            "approval_request_ready_for_runtime_approval": (
                approval_request_ready_for_runtime_approval
            ),
            "approval_request_created": approval_request.get("approval_request_created"),
            "implementation_authorized_by_approval_request": approval_request.get(
                "implementation_authorized_by_request"
            ),
            "approval_scope_id": approval_scope.get("sandbox_scope_id"),
            "approval_scope_default_off": approval_scope.get("default_off"),
            "approval_scope_default_enabled": approval_scope.get("default_enabled"),
            "approval_scope_runtime_dtm_or_tablebase_lookup": approval_scope.get(
                "runtime_dtm_or_tablebase_lookup"
            ),
            "approval_scope_hidden_python_controller": approval_scope.get(
                "hidden_python_controller"
            ),
            "approval_scope_selector_training_allowed": approval_scope.get(
                "selector_training_allowed"
            ),
            "implementation_authorized_by_review_packet": runtime_decision.get(
                "implementation_authorized_by_this_packet"
            ),
            "requires_explicit_approval_before_implementation": runtime_decision.get(
                "requires_explicit_approval_before_implementation"
            ),
            "caveat_control_status": caveat_control.get("status"),
            "sequence_review_status": sequence_review.get("decision", {}).get("status"),
            "stratified_validation_status": stratified_validation.get("decision", {}).get(
                "status"
            ),
            "sequence_contrast_status": sequence_contrast.get("decision", {}).get("status"),
        },
        "evidence": {
            "base_control_reproduces_failure": sequence_summary.get(
                "base_control_reproduces_failure_count"
            ),
            "single_unique_failure": sequence_summary.get("single_unique_failure"),
            "target_state_id": sequence_summary.get("target_state_id"),
            "target_fen": sequence_summary.get("target_fen"),
            "target_selected_move": sequence_summary.get("target_selected_move"),
            "stratified_gap_variant_count": stratified_summary.get("gap_variant_count"),
            "stratified_candidate_row_count": stratified_summary.get("candidate_row_count"),
            "stage4_forced_candidate_count": contrast_summary.get("stage4_forced_candidate_count"),
            "stage4_positive_count": contrast_summary.get("stage4_positive_count"),
            "stage4_failure_count": contrast_summary.get("stage4_failure_count"),
        },
        "approved_scope_if_explicitly_approved_later": {
            "scope": "default_off_stage4_candidate_move_first_move_contrast_sandbox_only",
            "candidate_source": "CandidateMoveFrame legal first-move hypotheses",
            "direct_request": False,
            "score_delta": 0.0,
            "default_enabled": False,
            "exact_state_or_exact_move_exception": False,
            "selector_training": False,
            "provider_suppression": False,
            "stage7_promotion": False,
            "stage8_training": False,
        },
        "required_approval_scope_if_user_approves": approval_scope,
        "forbidden_without_later_explicit_approval": [
            "runtime sandbox implementation",
            "default enablement",
            "exact-state or exact-move runtime exception",
            "selector training",
            "broad stage0 penalty",
            "provider suppression",
            "Stage 7 promotion",
            "Stage 8 training",
        ],
        "blockers": blockers,
        "decision": {
            "status": status,
            "recommended_next_step": (
                "explicitly_approve_stage4_first_move_contrast_sandbox_or_defer_stage4_caveat"
                if not blockers
                else "inspect_stage4_caveat_runtime_review_packet"
            ),
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "implementation_allowed_by_this_packet": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    status = payload["current_stage4_status"]
    evidence = payload["evidence"]
    lines = [
        "# KRK Stage 4 Caveat Unblocker Packet v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This packet is non-causal. It consolidates Stage 4 caveat evidence and the reviewed runtime-sandbox approval boundary, but it does not implement or authorize runtime behavior.",
        "",
        "## Current Stage 4 Status",
        "",
    ]
    for key, value in status.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Evidence", ""])
    for key, value in evidence.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Approved Scope If Explicitly Approved Later", ""])
    for key, value in payload["approved_scope_if_explicitly_approved_later"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Forbidden Without Later Explicit Approval", ""])
    for item in payload["forbidden_without_later_explicit_approval"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Blockers", ""])
    for blocker in payload["blockers"]:
        lines.append(f"- `{blocker}`")
    if not payload["blockers"]:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            f"- implementation_allowed_by_this_packet: `{decision['implementation_allowed_by_this_packet']}`",
            "- runtime_changes_allowed: `false`",
            "- label_run_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- stage7_promotion_allowed: `false`",
            "- stage8_training_allowed: `false`",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
