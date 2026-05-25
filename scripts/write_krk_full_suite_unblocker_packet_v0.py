#!/usr/bin/env python3
"""Write the next KRK-suite unblocker packet from the readiness audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
OUT_JSON = ROOT / "reports/krk_full_suite_unblocker_packet_v0.json"
OUT_MD = ROOT / "reports/krk_full_suite_unblocker_packet_v0.md"


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def build_payload() -> dict[str, Any]:
    readiness = _load(READINESS)
    stage7_gate = readiness["stage7_sampling_gate"]
    sequence = readiness["sequence_policy"]
    protected = readiness["protected_stack"]

    primary_ready = (
        stage7_gate["runner_status"] == "stage7_diverse_clean_sampling_runner_dry_run_ready"
        and stage7_gate["executed_job_count"] == 0
        and stage7_gate["success_controls_ready"] is False
    )

    return {
        "schema_version": "krk_full_suite_unblocker_packet.v0",
        "causal_status": "non_causal_approval_packet",
        "source_artifacts": {
            "readiness_audit": "reports/krk_full_suite_readiness_audit_v0.json",
            "stage7_runner": (
                "reports/structural_candidates/stage7_diverse_clean_sampling_runner_v0.json"
            ),
            "stage4_gate": "reports/krk_current_control_plane_gate_v0.json",
        },
        "current_state": {
            "protected_stack_ready": protected["ready"],
            "stage7_success_controls": stage7_gate["combined_success_controls"],
            "stage7_success_controls_required": stage7_gate["success_controls_required"],
            "sequence_policy_inputs_ready": sequence["inputs_ready"],
            "sequence_policy_benchmark_ready": sequence["benchmark_ready"],
            "stage8_training_ready": False,
        },
        "why_agent_stops_here": [
            "The next highest-value action creates new Stage 7 h40 labels or implements a reviewed runtime sandbox.",
            "Those actions are gated by repository reports and architecture policy, not by a hidden disk config that limits session length.",
            "The current /goal authorizes autonomous safe work, but it does not by itself authorize gated label execution, runtime behavior, Stage 7 promotion, or Stage 8 training.",
        ],
        "primary_unblocker": {
            "id": "stage7_diverse_clean_label_execution",
            "status": "ready_pending_explicit_approval" if primary_ready else "not_ready",
            "purpose": "Fill held-out Stage 7 clean success controls so the sequence-policy benchmark can run.",
            "command_if_explicitly_approved": (
                "UV_CACHE_DIR=/tmp/uv-cache uv run python "
                "scripts/run_stage7_diverse_clean_sampling_jobs_v0.py "
                "--execute-reviewed-label-run --refresh-after-run"
            ),
            "scope": {
                "max_jobs": 8,
                "horizon": "h40",
                "stage": "stage7_held_out_evidence_only",
                "runtime_behavior_changed": False,
                "stage7_training_rows": 0,
                "stage7_promotion_allowed": False,
                "stage8_training_allowed": False,
            },
            "approval_required": True,
            "implementation_allowed_by_this_packet": False,
        },
        "secondary_unblocker": {
            "id": "stage4_first_move_contrast_sandbox",
            "status": "runtime_review_ready_pending_explicit_approval",
            "purpose": "Address the separate Stage 4 h40 caveat through a reviewed default-off sandbox path.",
            "why_secondary": (
                "This may reduce Stage 4 debt, but it does not directly fill the Stage 7 clean "
                "success controls currently blocking sequence-policy benchmarking."
            ),
            "approval_required": True,
            "implementation_allowed_by_this_packet": False,
        },
        "low_value_safe_work_remaining": [
            "More passive summaries can be written, but they will not unblock Stage 8 or the sequence-policy benchmark.",
            "Further non-causal candidate-generation analysis is lower leverage until Stage 7 clean success controls are filled.",
        ],
        "decision": {
            "status": "krk_suite_primary_unblocker_ready_pending_explicit_label_approval",
            "recommended_next_step": "explicitly_approve_stage7_diverse_clean_label_execution",
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    primary = payload["primary_unblocker"]
    secondary = payload["secondary_unblocker"]
    state = payload["current_state"]
    lines = [
        "# KRK Full Suite Unblocker Packet v0",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- recommended_next_step: `{decision['recommended_next_step']}`",
        f"- implementation_allowed_by_this_packet: `{primary['implementation_allowed_by_this_packet']}`",
        f"- label_run_allowed: `{decision['label_run_allowed']}`",
        f"- runtime_changes_allowed: `{decision['runtime_changes_allowed']}`",
        "",
        "## Current State",
        "",
        f"- protected_stack_ready: `{state['protected_stack_ready']}`",
        f"- stage7_success_controls: `{state['stage7_success_controls']}`",
        f"- stage7_success_controls_required: `{state['stage7_success_controls_required']}`",
        f"- sequence_policy_inputs_ready: `{state['sequence_policy_inputs_ready']}`",
        f"- sequence_policy_benchmark_ready: `{state['sequence_policy_benchmark_ready']}`",
        f"- stage8_training_ready: `{state['stage8_training_ready']}`",
        "",
        "## Why Work Stops At This Gate",
        "",
    ]
    for reason in payload["why_agent_stops_here"]:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## Primary Unblocker",
            "",
            f"- id: `{primary['id']}`",
            f"- status: `{primary['status']}`",
            f"- purpose: {primary['purpose']}",
            f"- command_if_explicitly_approved: `{primary['command_if_explicitly_approved']}`",
            f"- approval_required: `{primary['approval_required']}`",
            f"- implementation_allowed_by_this_packet: `{primary['implementation_allowed_by_this_packet']}`",
            "",
            "## Secondary Unblocker",
            "",
            f"- id: `{secondary['id']}`",
            f"- status: `{secondary['status']}`",
            f"- purpose: {secondary['purpose']}",
            f"- why_secondary: {secondary['why_secondary']}",
            "",
            "## Low-Value Safe Work Remaining",
            "",
        ]
    )
    for item in payload["low_value_safe_work_remaining"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
