#!/usr/bin/env python3
"""Review whether KRK Stage 8 training is ready for explicit approval.

This is a passive review gate. It never trains Stage 8 and never promotes
Stage 7. Its purpose is to make the downstream requirements explicit once the
Stage 7 held-out controls and sequence-policy benchmark are ready.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "reports/krk_full_suite_readiness_audit_v0.json"
BENCHMARK_REVIEW = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
OUTPUT_JSON = ROOT / "reports/krk_stage8_training_readiness_review_v0.json"
OUTPUT_MD = ROOT / "reports/krk_stage8_training_readiness_review_v0.md"

SCHEMA_VERSION = "krk_stage8_training_readiness_review.v0"

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
    readiness: dict[str, Any] | None = None,
    benchmark_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    readiness = readiness or _load(READINESS)
    benchmark_review = benchmark_review or _load(BENCHMARK_REVIEW)

    protected = readiness.get("protected_stack") or {}
    stage_status = readiness.get("stage_status") or {}
    stage7 = stage_status.get("stage7") or {}
    stage4 = stage_status.get("stage4") or {}
    sequence_decision = benchmark_review.get("decision") or {}

    protected_ready = bool(protected.get("ready"))
    stage7_controls_ready = bool(stage7.get("success_controls_ready"))
    stage7_promoted = bool(stage7.get("ready_for_promotion"))
    sequence_review_ready = sequence_decision.get("status") in {
        "sequence_policy_benchmark_supports_non_causal_sequence_policy_review",
        "sequence_policy_benchmark_mixed_plan_window_underpowered",
    }
    sequence_review_supportive = (
        sequence_decision.get("status")
        == "sequence_policy_benchmark_supports_non_causal_sequence_policy_review"
    )
    stage4_ready = bool(stage4.get("ready_for_current_suite"))

    blockers: list[str] = []
    warnings: list[str] = []
    if not protected_ready:
        blockers.append("protected_stage5_6_stack_not_ready")
    if not stage7_controls_ready:
        blockers.append("stage7_clean_success_controls_missing")
    if not sequence_review_ready:
        blockers.append("sequence_policy_benchmark_review_not_ready")
    elif not sequence_review_supportive:
        blockers.append("sequence_policy_benchmark_mixed_or_underpowered")
    if not stage4_ready:
        warnings.append("stage4_h40_caveat_remains")
    if not stage7_promoted:
        warnings.append("stage7_not_promoted_and_must_remain_held_out_without_explicit_gate")

    if blockers:
        status = "stage8_training_blocked_pending_stage7_sequence_gate"
        next_step = "fill_stage7_success_controls_and_rerun_passive_gate_advancement"
    elif warnings:
        status = "stage8_training_review_blocked_pending_architecture_review"
        next_step = "write_explicit_stage8_training_review_packet_if_warnings_are_accepted"
    else:
        status = "stage8_training_review_ready_pending_explicit_approval"
        next_step = "write_explicit_stage8_training_review_packet"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_stage8_training_readiness_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/krk_full_suite_readiness_audit_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
        ],
        "requirements": {
            "protected_stage5_6_stack_ready": protected_ready,
            "m1_m4_preservation_passed": protected.get("m1_m4_preservation_passed"),
            "kpk_kqk_bridge_preservation_passed": protected.get(
                "kpk_kqk_bridge_preservation_passed"
            ),
            "stage7_clean_success_controls_ready": stage7_controls_ready,
            "stage7_success_controls": stage7.get("success_controls"),
            "stage7_success_controls_required": stage7.get("success_controls_required"),
            "stage7_promoted": stage7_promoted,
            "stage4_ready_for_current_suite": stage4_ready,
            "sequence_policy_benchmark_review_status": sequence_decision.get("status"),
            "sequence_policy_benchmark_review_ready": sequence_review_ready,
            "sequence_policy_benchmark_supportive": sequence_review_supportive,
        },
        "blockers": blockers,
        "warnings": warnings,
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "implementation_allowed_by_this_review": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    decision = payload["decision"]
    lines = [
        "# KRK Stage 8 Training Readiness Review v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This review is non-causal. It does not train Stage 8, promote Stage 7, change runtime behavior, or authorize implementation by itself.",
        "",
        "## Requirements",
        "",
    ]
    for key, value in payload["requirements"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Blockers", ""])
    for blocker in payload["blockers"]:
        lines.append(f"- `{blocker}`")
    if not payload["blockers"]:
        lines.append("- none")
    lines.extend(["", "## Warnings", ""])
    for warning in payload["warnings"]:
        lines.append(f"- `{warning}`")
    if not payload["warnings"]:
        lines.append("- none")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            f"- implementation_allowed_by_this_review: `{decision['implementation_allowed_by_this_review']}`",
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
