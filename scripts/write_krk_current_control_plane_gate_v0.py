#!/usr/bin/env python3
"""Summarize the current KRK control-plane approval gates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE4_PACKET = ROOT / "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json"
STAGE7_MANIFEST = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
SEQUENCE_PROBE = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json"
OUTPUT_JSON = ROOT / "reports/krk_current_control_plane_gate_v0.json"
OUTPUT_MD = ROOT / "reports/krk_current_control_plane_gate_v0.md"

SCHEMA_VERSION = "krk_current_control_plane_gate.v0"


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
    return json.loads(path.read_text(encoding="utf-8"))


def build_payload(
    *,
    stage4_packet: dict[str, Any] | None = None,
    stage7_manifest: dict[str, Any] | None = None,
    sequence_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    stage4_packet = stage4_packet or _load(STAGE4_PACKET)
    stage7_manifest = stage7_manifest or _load(STAGE7_MANIFEST)
    sequence_probe = sequence_probe or _load(SEQUENCE_PROBE)
    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_current_gate_summary",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json",
            "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json",
        ],
        "current_state": {
            "protected_stack": "retry1_stage5_6_active_manifest_validated",
            "stage4": "first_move_contrast_runtime_review_ready_pending_explicit_approval",
            "stage7": "heldout_clean_success_controls_insufficient_sampling_manifest_ready",
            "stage8": "blocked",
            "runtime_selector": "blocked",
        },
        "approval_options": [
            {
                "option_id": "approve_stage4_first_move_contrast_sandbox",
                "artifact": "reports/krk_stage4_first_move_contrast_runtime_review_packet_v0.md",
                "status": stage4_packet.get("decision", {}).get("status"),
                "what_it_allows": "default-off Stage 4 CandidateMoveFrame first-move contrast sandbox only",
                "what_it_does_not_allow": [
                    "default enablement",
                    "exact-state or exact-move runtime exception",
                    "selector training",
                    "broad stage0 penalty",
                    "provider suppression",
                    "Stage 7 promotion",
                    "Stage 8 training",
                ],
                "recommended_if": "you want to reduce the known Stage 4 h40 caveat now",
            },
            {
                "option_id": "approve_stage7_diverse_clean_label_run",
                "artifact": "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.md",
                "status": stage7_manifest.get("decision", {}).get("status"),
                "what_it_allows": "run 8 bounded h40 clean Stage 7 label jobs, 64 samples total",
                "what_it_does_not_allow": [
                    "runtime behavior",
                    "selector training",
                    "Stage 7 promotion",
                    "Stage 8 training",
                    "Stage 7 repair flags",
                ],
                "recommended_if": "you want to fill the Stage 7 clean success-control gap before broader sequence-policy benchmarking",
            },
            {
                "option_id": "defer_both_and_design_broader_sequence_policy",
                "artifact": "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.md",
                "status": sequence_probe.get("decision", {}).get("status"),
                "what_it_allows": "non-causal design only",
                "what_it_does_not_allow": [
                    "runtime selector",
                    "Stage 7 promotion",
                    "Stage 8 training",
                ],
                "recommended_if": "you prefer architecture design before any more runtime or label runs",
            },
        ],
        "recommendation": {
            "preferred_next_if_no_user_approval": "stop_at_gate_and_report",
            "preferred_next_if_user_approves_runtime": "implement_stage4_default_off_first_move_contrast_sandbox",
            "preferred_next_if_user_approves_labels": "run_stage7_diverse_clean_sampling_manifest_and_recover_controls",
            "reason": "All remaining immediate progress crosses either a runtime sandbox approval gate or a Stage 7 label-run approval gate.",
        },
        "decision": {
            "status": "krk_control_plane_waiting_on_explicit_gate_choice",
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Current Control-Plane Gate v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "## Current State",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in payload["current_state"].items())
    lines.extend(["", "## Approval Options", ""])
    for option in payload["approval_options"]:
        lines.extend([
            f"### {option['option_id']}",
            "",
            f"- artifact: `{option['artifact']}`",
            f"- status: `{option['status']}`",
            f"- allows: {option['what_it_allows']}",
            f"- recommended_if: {option['recommended_if']}",
            "- does_not_allow:",
        ])
        lines.extend(f"  - {item}" for item in option["what_it_does_not_allow"])
        lines.append("")
    lines.extend([
        "## Recommendation",
        "",
        f"- if_no_user_approval: `{payload['recommendation']['preferred_next_if_no_user_approval']}`",
        f"- if_runtime_approved: `{payload['recommendation']['preferred_next_if_user_approves_runtime']}`",
        f"- if_labels_approved: `{payload['recommendation']['preferred_next_if_user_approves_labels']}`",
        f"- reason: {payload['recommendation']['reason']}",
    ])
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(json.dumps({
        "decision": payload["decision"]["status"],
        "approval_options": [option["option_id"] for option in payload["approval_options"]],
    }, indent=2))


if __name__ == "__main__":
    main()
