#!/usr/bin/env python3
"""Write a passive approval-request packet for the Stage 4 sandbox.

This packet is not an approval and does not implement runtime behavior. It
only records the exact narrow scope that a later explicit user approval would
need to reference before any default-off Stage 4 sandbox implementation work.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PACKET = ROOT / "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json"
OUTPUT_JSON = ROOT / "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
OUTPUT_MD = ROOT / "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.md"

SCHEMA_VERSION = "krk_stage4_first_move_contrast_sandbox_approval_request.v0"
APPROVAL_ID = "approve_stage4_first_move_contrast_sandbox"

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "runtime_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def build_payload(
    *,
    runtime_packet: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime_packet = runtime_packet or _load(RUNTIME_PACKET)
    decision = runtime_packet.get("decision") or {}
    approved_scope = runtime_packet.get("approved_if_later_explicitly_authorized") or {}
    implementation_boundaries = runtime_packet.get("implementation_boundaries") or {}
    acceptance = runtime_packet.get("acceptance_if_later_approved") or {}
    review_summary = runtime_packet.get("review_summary") or {}

    runtime_review_ready = (
        decision.get("status")
        == "stage4_first_move_contrast_runtime_review_ready_pending_explicit_approval"
        and decision.get("runtime_review_ready") is True
        and decision.get("implementation_authorized_by_this_packet") is False
        and decision.get("requires_explicit_approval_before_implementation") is True
    )
    status = (
        "stage4_first_move_contrast_sandbox_approval_request_ready"
        if runtime_review_ready
        else "stage4_first_move_contrast_sandbox_approval_request_blocked"
    )
    blockers = [] if runtime_review_ready else ["stage4_runtime_review_packet_not_ready"]
    exact_approval_request = (
        "Approve default-off Stage 4 first-move contrast sandbox implementation "
        "only within krk_stage4_first_move_contrast_runtime_review_packet_v0: "
        "CandidateMoveFrame legal first-move hypotheses in KRK Stage 4 "
        "edge_trap_wrong_tempo contexts; no default enablement, no exact-state "
        "or exact-move exception, no runtime DTM/tablebase lookup, no hidden "
        "controller, no selector training, no provider suppression, no broad "
        "stage0 penalty, no gameplay topology mutation, no Stage 7 promotion, "
        "and no Stage 8 training."
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_runtime_approval_request_packet",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json"
        ],
        "approval_id": APPROVAL_ID,
        "approval_request_created": False,
        "implementation_authorized_by_request": False,
        "runtime_changes_allowed_by_request": False,
        "exact_approval_request": exact_approval_request,
        "required_scope_if_user_approves": {
            "approval_id": APPROVAL_ID,
            "review_packet": "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json",
            "review_packet_status": decision.get("status"),
            "sandbox_id": approved_scope.get("sandbox_id"),
            "default_off": approved_scope.get("default_off"),
            "scope": approved_scope.get("scope"),
            "allowed_runtime_behavior": approved_scope.get("allowed_runtime_behavior"),
            "implementation_boundaries": implementation_boundaries,
            "acceptance_if_later_approved": acceptance,
        },
        "summary": {
            "runtime_review_ready": decision.get("runtime_review_ready"),
            "runtime_review_status": decision.get("status"),
            "evidence_passed": review_summary.get("evidence_passed"),
            "implementation_authorized_by_runtime_packet": decision.get(
                "implementation_authorized_by_this_packet"
            ),
            "requires_explicit_approval_before_implementation": decision.get(
                "requires_explicit_approval_before_implementation"
            ),
            "default_off": approved_scope.get("default_off"),
            "default_enabled": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "hidden_python_controller": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "blockers": blockers,
        "decision": {
            "status": status,
            "recommended_next_step": (
                "user_may_explicitly_approve_stage4_sandbox_only_if_runtime_work_is_intended"
                if runtime_review_ready
                else "inspect_stage4_first_move_contrast_runtime_review_packet"
            ),
            "implementation_allowed_by_this_request": False,
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
    summary = payload["summary"]
    required = payload["required_scope_if_user_approves"]
    lines = [
        "# KRK Stage 4 First-Move Contrast Sandbox Approval Request v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a passive request packet only. It does not approve or implement runtime behavior, change defaults, train selectors, promote Stage 7, or train Stage 8.",
        "",
        "## Exact Approval Request",
        "",
        f"> {payload['exact_approval_request']}",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Required Scope If User Approves",
            "",
            f"- approval_id: `{required['approval_id']}`",
            f"- review_packet: `{required['review_packet']}`",
            f"- review_packet_status: `{required['review_packet_status']}`",
            f"- sandbox_id: `{required['sandbox_id']}`",
            f"- default_off: `{required['default_off']}`",
            "",
            "## Blockers",
            "",
        ]
    )
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
            f"- implementation_allowed_by_this_request: `{decision['implementation_allowed_by_this_request']}`",
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
