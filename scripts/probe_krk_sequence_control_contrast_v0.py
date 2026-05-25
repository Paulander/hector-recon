#!/usr/bin/env python3
"""Probe the non-causal KRK sequence-control contrast dataset v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
INPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.json"
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.md"

SCHEMA_VERSION = "krk_sequence_control_contrast_probe.v0"


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


def _rows_by(dataset: dict[str, Any], **criteria: Any) -> list[dict[str, Any]]:
    rows = []
    for row in dataset.get("rows", []):
        if all(row.get(key) == value for key, value in criteria.items()):
            rows.append(row)
    return rows


def build_payload(dataset: dict[str, Any] | None = None) -> dict[str, Any]:
    dataset = dataset or _load(INPUT_JSON)
    rows = dataset.get("rows", [])
    stage4_forced = _rows_by(dataset, source_stage="stage4", row_type="forced_first_move_candidate")
    stage7_controls = _rows_by(dataset, source_stage="stage7", row_type="stage7_clean_sequence_control")
    selector_rows = _rows_by(dataset, row_type="ownership_seed_context")
    stage7_success = [row for row in stage7_controls if row.get("target_label") == "conversion_positive"]
    stage7_fail = [row for row in stage7_controls if row.get("target_label") == "conversion_failure"]
    selector_switch = [
        row for row in selector_rows if row.get("target_label") == "candidate_switch_contrast_seed"
    ]
    selector_preserve = [
        row for row in selector_rows if row.get("target_label") == "safe_preservation_contrast_seed"
    ]
    stage4_positive = [
        row for row in stage4_forced if row.get("target_label") == "conversion_positive"
    ]
    stage4_failure = [
        row for row in stage4_forced if row.get("target_label") == "conversion_failure"
    ]

    stage4_review_ready = bool(
        dataset.get("stage4_review_gate", {}).get("runtime_review_ready")
        and not dataset.get("stage4_review_gate", {}).get("implementation_authorized_by_packet")
    )
    stage7_success_met = len(stage7_success) >= 5
    stage7_negative_met = len(stage7_fail) >= 5
    protected_selector_seed_balanced = len(selector_switch) >= 4 and len(selector_preserve) >= 4

    if stage4_review_ready and not stage7_success_met:
        status = "sequence_control_stage4_review_ready_stage7_success_controls_insufficient"
        recommended_next = "choose_stage4_sandbox_approval_or_design_diverse_stage7_sampling_manifest"
    elif stage7_success_met and stage7_negative_met and protected_selector_seed_balanced:
        status = "sequence_control_dataset_ready_for_broader_sequence_policy_review"
        recommended_next = "design_non_causal_sequence_policy_benchmark"
    else:
        status = "sequence_control_dataset_underpowered"
        recommended_next = "collect_reviewed_non_causal_controls"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_sequence_control_contrast_probe",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": ["reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.json"],
        "summary": {
            "row_count": len(rows),
            "stage4_forced_candidate_count": len(stage4_forced),
            "stage4_positive_count": len(stage4_positive),
            "stage4_failure_count": len(stage4_failure),
            "stage4_review_ready_pending_approval": stage4_review_ready,
            "selector_switch_seed_count": len(selector_switch),
            "selector_preserve_seed_count": len(selector_preserve),
            "protected_selector_seed_balanced": protected_selector_seed_balanced,
            "stage7_control_count": len(stage7_controls),
            "stage7_success_control_count": len(stage7_success),
            "stage7_failure_control_count": len(stage7_fail),
            "stage7_success_controls_met": stage7_success_met,
            "stage7_failure_controls_met": stage7_negative_met,
            "selector_training_row_count": dataset.get("summary", {}).get("selector_training_row_count"),
            "runtime_authorization_row_count": dataset.get("summary", {}).get("runtime_authorization_row_count"),
        },
        "readiness": {
            "stage4_first_move_contrast_sandbox_review_ready": stage4_review_ready,
            "stage7_sequence_policy_benchmark_ready": stage7_success_met and stage7_negative_met,
            "broader_runtime_selector_ready": False,
            "stage8_training_ready": False,
        },
        "decision": {
            "status": status,
            "recommended_next_step": recommended_next,
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
        "blockers": [
            "Stage 4 first-move contrast sandbox still requires explicit approval before implementation.",
            "Stage 7 clean success controls remain below the minimum threshold for sequence-policy benchmarking.",
            "No row in this dataset is an ownership-training row or runtime-authorization row.",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    readiness = payload["readiness"]
    lines = [
        "# KRK Sequence-Control Contrast Probe v0",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "- runtime_changes_allowed: `false`",
        "- selector_training_allowed: `false`",
        "",
        "## Summary",
        "",
        f"- row_count: `{summary['row_count']}`",
        f"- stage4_forced_candidate_count: `{summary['stage4_forced_candidate_count']}`",
        f"- stage4_positive_count: `{summary['stage4_positive_count']}`",
        f"- stage4_failure_count: `{summary['stage4_failure_count']}`",
        f"- stage4_review_ready_pending_approval: `{summary['stage4_review_ready_pending_approval']}`",
        f"- selector_switch_seed_count: `{summary['selector_switch_seed_count']}`",
        f"- selector_preserve_seed_count: `{summary['selector_preserve_seed_count']}`",
        f"- stage7_success_control_count: `{summary['stage7_success_control_count']}`",
        f"- stage7_failure_control_count: `{summary['stage7_failure_control_count']}`",
        "",
        "## Readiness",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in readiness.items())
    lines.extend(["", "## Blockers", ""])
    lines.extend(f"- {item}" for item in payload["blockers"])
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
