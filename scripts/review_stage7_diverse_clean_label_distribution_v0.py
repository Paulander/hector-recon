#!/usr/bin/env python3
"""Review Stage 7 diverse-clean label distribution before any follow-up manifest.

This is a passive post-run review. It reads the already produced held-out label
outputs and explains why the clean success gate remains short. It does not
execute labels, change runtime behavior, train selectors, promote Stage 7, or
train Stage 8.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
OUTPUT_VALIDATION = (
    ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
)
INTEGRATION = (
    ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json"
)
CLEAN_RECOVERY = (
    ROOT / "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json"
)
OUT_JSON = (
    ROOT / "reports/structural_candidates/stage7_diverse_clean_label_distribution_review_v0.json"
)
OUT_MD = (
    ROOT / "reports/structural_candidates/stage7_diverse_clean_label_distribution_review_v0.md"
)

SCHEMA_VERSION = "stage7_diverse_clean_label_distribution_review.v0"

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


def _output_key(terms: dict[str, Any]) -> tuple[str, str, str] | None:
    fen = terms.get("fen")
    move = terms.get("move")
    result = terms.get("playout_result")
    if not fen or not move or result not in {"mate", "max_plies", "draw"}:
        return None
    return str(fen), str(move), str(result)


def _control_key(control: dict[str, Any]) -> tuple[str, str, str] | None:
    fen = control.get("fen")
    move = control.get("move_uci")
    result = control.get("result")
    if not fen or not move or result not in {"mate", "max_plies", "draw"}:
        return None
    return str(fen), str(move), str(result)


def _is_diverse_output_source(control: dict[str, Any]) -> bool:
    source = str(control.get("source_artifact") or "")
    return source.startswith("reports/structural_candidates/stage7_diverse_clean_")


def _playout_rows(job: dict[str, Any], output: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for packet in output.get("handoff_packets") or []:
        if not isinstance(packet, dict) or packet.get("phase") != "playout_summary":
            continue
        terms = packet.get("evidence_terms") or {}
        if not isinstance(terms, dict) or terms.get("label") != "box_shrink":
            continue
        key = _output_key(terms)
        if key is None:
            continue
        rows.append(
            {
                "job_id": job.get("job_id"),
                "json_output": job.get("json_output"),
                "source_stage_names": job.get("source_stage_names") or [],
                "fen": key[0],
                "move_uci": key[1],
                "result": key[2],
                "control_role": (
                    "clean_sequence_success_control"
                    if key[2] == "mate"
                    else "clean_sequence_hard_negative"
                ),
                "plies": terms.get("plies"),
                "max_plies": terms.get("max_plies"),
                "semantic_alignment_status": terms.get("semantic_alignment_status"),
                "failure_classes": terms.get("failure_classes") or [],
                "key": key,
            }
        )
    return rows


def build_payload(
    *,
    manifest: dict[str, Any] | None = None,
    output_validation: dict[str, Any] | None = None,
    integration: dict[str, Any] | None = None,
    clean_recovery: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    output_validation = output_validation or _load(OUTPUT_VALIDATION)
    integration = integration or _load(INTEGRATION)
    clean_recovery = clean_recovery or _load(CLEAN_RECOVERY)

    validation_status = (output_validation.get("decision") or {}).get("status")
    integration_summary = integration.get("summary") or {}
    success_controls = int(integration_summary.get("combined_success_controls") or 0)
    success_required = int(integration_summary.get("success_controls_required") or 5)
    success_gap = max(success_required - success_controls, 0)

    pre_existing_keys = {
        key
        for control in clean_recovery.get("controls") or []
        if not _is_diverse_output_source(control)
        for key in [_control_key(control)]
        if key is not None
    }
    pre_existing_success_keys = {key for key in pre_existing_keys if key[2] == "mate"}

    current_clean_keys = {
        key
        for control in clean_recovery.get("controls") or []
        for key in [_control_key(control)]
        if key is not None
    }
    current_success_keys = {key for key in current_clean_keys if key[2] == "mate"}

    rows: list[dict[str, Any]] = []
    job_reviews = []
    for job in manifest.get("jobs") or []:
        output_path = ROOT / str(job.get("json_output"))
        output = _load(output_path) if output_path.exists() else {}
        job_rows = _playout_rows(job, output)
        rows.extend(job_rows)
        unique_keys = {row["key"] for row in job_rows}
        unique_success_keys = {key for key in unique_keys if key[2] == "mate"}
        unique_new_keys = unique_keys - pre_existing_keys
        unique_new_success_keys = unique_success_keys - pre_existing_success_keys
        result_counts = Counter(row["result"] for row in job_rows)
        job_reviews.append(
            {
                "job_id": job.get("job_id"),
                "json_output": job.get("json_output"),
                "source_stage_names": job.get("source_stage_names") or [],
                "raw_playout_count": len(job_rows),
                "result_counts": dict(result_counts),
                "unique_key_count": len(unique_keys),
                "unique_success_key_count": len(unique_success_keys),
                "unique_new_key_count_vs_pre_run": len(unique_new_keys),
                "unique_new_success_key_count_vs_pre_run": len(unique_new_success_keys),
                "duplicate_within_or_across_manifest_count": max(
                    len(job_rows) - len(unique_keys), 0
                ),
            }
        )

    raw_result_counts = Counter(row["result"] for row in rows)
    key_counts = Counter(row["key"] for row in rows)
    unique_output_keys = set(key_counts)
    unique_output_success_keys = {key for key in unique_output_keys if key[2] == "mate"}
    unique_new_keys = unique_output_keys - pre_existing_keys
    unique_new_success_keys = unique_output_success_keys - pre_existing_success_keys

    duplicate_keys = [
        {
            "fen": key[0],
            "move_uci": key[1],
            "result": key[2],
            "occurrence_count": count,
            "already_clean_before_run": key in pre_existing_keys,
            "clean_after_run": key in current_clean_keys,
        }
        for key, count in key_counts.most_common()
        if count > 1
    ][:12]

    source_cell_yield = sorted(
        job_reviews,
        key=lambda row: (
            -int(row["unique_new_success_key_count_vs_pre_run"]),
            -int(row["unique_new_key_count_vs_pre_run"]),
            str(row["job_id"]),
        ),
    )

    findings = []
    if validation_status == "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration":
        findings.append("all_reviewed_outputs_valid")
    if unique_new_success_keys:
        findings.append("approved_run_added_unique_clean_success_controls")
    if success_gap:
        findings.append("success_gate_still_short_after_valid_label_run")
    if duplicate_keys:
        findings.append("label_distribution_duplicate_dominated")

    if validation_status != "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration":
        status = "stage7_label_distribution_review_blocked_pending_valid_outputs"
        next_step = "rerun_stage7_output_validation_before_distribution_review"
    elif success_gap:
        status = "stage7_label_distribution_review_ready_for_additional_sampling_plan"
        next_step = "write_additional_stage7_clean_sampling_manifest_for_remaining_success_gap"
    else:
        status = "stage7_label_distribution_review_success_gate_closed"
        next_step = "rerun_passive_sequence_policy_gate_stack"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_label_distribution_review",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_integration_v0.json",
            "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json",
        ],
        "summary": {
            "validation_status": validation_status,
            "job_count": len(manifest.get("jobs") or []),
            "raw_playout_count": len(rows),
            "raw_result_counts": dict(raw_result_counts),
            "unique_output_key_count": len(unique_output_keys),
            "unique_output_success_key_count": len(unique_output_success_keys),
            "pre_existing_clean_key_count": len(pre_existing_keys),
            "pre_existing_success_key_count": len(pre_existing_success_keys),
            "unique_new_key_count_vs_pre_run": len(unique_new_keys),
            "unique_new_success_key_count_vs_pre_run": len(unique_new_success_keys),
            "current_clean_key_count": len(current_clean_keys),
            "current_success_key_count": len(current_success_keys),
            "success_controls": success_controls,
            "success_controls_required": success_required,
            "success_gap": success_gap,
            "duplicate_key_count": sum(1 for count in key_counts.values() if count > 1),
            "duplicate_playout_count": sum(count - 1 for count in key_counts.values() if count > 1),
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        },
        "job_reviews": job_reviews,
        "source_cell_yield_rank": source_cell_yield,
        "duplicate_keys": duplicate_keys,
        "findings": findings,
        "followup_sampling_guidance": {
            "recommended_source_bias": (
                "favor_source_cells_with_unique_new_success_yield_and_avoid_duplicate_dominated_cells"
            ),
            "highest_yield_job_ids": [
                row["job_id"]
                for row in source_cell_yield
                if row["unique_new_success_key_count_vs_pre_run"]
            ],
            "minimum_additional_unique_success_controls_needed": success_gap,
            "reuse_same_manifest_without_overwrite_expected_to_help": False,
            "requires_explicit_approval_before_any_label_execution": True,
        },
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
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# Stage 7 Diverse Clean Label Distribution Review v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This passive review analyzes already produced Stage 7 held-out labels before any follow-up manifest. It does not execute labels, change runtime behavior, train selectors, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Highest-Yield Source Cells", ""])
    for row in payload["source_cell_yield_rank"][:5]:
        lines.append(
            f"- `{row['job_id']}` new_success=`{row['unique_new_success_key_count_vs_pre_run']}` "
            f"new_keys=`{row['unique_new_key_count_vs_pre_run']}` results=`{row['result_counts']}`"
        )
    lines.extend(["", "## Findings", ""])
    for finding in payload["findings"] or ["none"]:
        lines.append(f"- `{finding}`")
    lines.extend(
        [
            "",
            "## Follow-Up Guidance",
            "",
        ]
    )
    for key, value in payload["followup_sampling_guidance"].items():
        lines.append(f"- {key}: `{value}`")
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
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
