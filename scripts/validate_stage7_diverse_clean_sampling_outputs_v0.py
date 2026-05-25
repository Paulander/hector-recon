#!/usr/bin/env python3
"""Validate Stage 7 diverse-clean label outputs without executing labels.

This script is a passive post-label gate. It checks whether already-created
Stage 7 diverse-clean output files match the reviewed manifest and are safe to
consume as held-out evidence. It never runs label jobs, changes runtime
behavior, promotes Stage 7, or trains Stage 8.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
OUTPUT_JSON = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.json"
OUTPUT_MD = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_output_validation_v0.md"

SCHEMA_VERSION = "stage7_diverse_clean_sampling_output_validation.v0"

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


def _validate_playout_terms(terms: dict[str, Any], *, max_horizon: int) -> list[str]:
    issues: list[str] = []
    if terms.get("label") != "box_shrink":
        issues.append("non_box_shrink_playout_label")
    if not terms.get("fen"):
        issues.append("missing_fen")
    if not terms.get("move"):
        issues.append("missing_move")
    result = terms.get("playout_result")
    max_plies = terms.get("max_plies")
    plies = terms.get("plies")
    if result not in {"mate", "max_plies", "draw"}:
        issues.append("unsupported_playout_result")
    if isinstance(max_plies, int) and max_plies > max_horizon:
        issues.append("max_plies_above_manifest_horizon")
    if result == "mate" and isinstance(plies, int) and plies > max_horizon:
        issues.append("mate_after_manifest_horizon")
    if result != "mate" and max_plies != max_horizon:
        issues.append("non_mate_not_manifest_horizon")
    return issues


def _validate_output(job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    packets = payload.get("handoff_packets")
    issues = Counter()
    result_counts = Counter()
    playout_count = 0
    companion_count = 0
    max_horizon = int(job.get("playout_max_plies") or 40)

    if not isinstance(packets, list):
        return {
            "valid": False,
            "issues": {"missing_handoff_packets_list": 1},
            "playout_summary_count": 0,
            "post_opponent_reply_count": 0,
            "result_counts": {},
            "stage7_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        }

    for packet in packets:
        if not isinstance(packet, dict):
            issues["non_object_handoff_packet"] += 1
            continue
        phase = packet.get("phase")
        terms = packet.get("evidence_terms") or {}
        if not isinstance(terms, dict):
            issues["missing_evidence_terms"] += 1
            continue
        if phase == "post_opponent_reply" and terms.get("label") == "box_shrink":
            companion_count += 1
        if phase != "playout_summary":
            continue
        playout_count += 1
        for issue in _validate_playout_terms(terms, max_horizon=max_horizon):
            issues[issue] += 1
        result_counts[str(terms.get("playout_result"))] += 1

    if playout_count == 0:
        issues["missing_playout_summary"] += 1

    return {
        "valid": not issues,
        "issues": dict(issues),
        "playout_summary_count": playout_count,
        "post_opponent_reply_count": companion_count,
        "result_counts": dict(result_counts),
        "stage7_training_row_count": 0,
        "runtime_authorization_row_count": 0,
    }


def build_payload(*, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    jobs = manifest.get("jobs") or []
    output_checks = []
    aggregate_issues = Counter()
    aggregate_results = Counter()
    output_exists_count = 0
    output_valid_count = 0
    parsed_playout_count = 0
    parse_error_count = 0

    for job in jobs:
        output = job.get("json_output")
        path = ROOT / str(output) if output else None
        exists = bool(path and path.exists())
        check: dict[str, Any] = {
            "job_id": job.get("job_id"),
            "json_output": output,
            "output_exists": exists,
            "valid": False,
            "issues": {},
            "stage7_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        }
        if not exists or path is None:
            check["issues"] = {"output_missing": 1}
            output_checks.append(check)
            continue

        output_exists_count += 1
        try:
            validation = _validate_output(job, _load(path))
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            parse_error_count += 1
            validation = {
                "valid": False,
                "issues": {"output_parse_error": 1},
                "parse_error": str(exc),
                "playout_summary_count": 0,
                "post_opponent_reply_count": 0,
                "result_counts": {},
                "stage7_training_row_count": 0,
                "runtime_authorization_row_count": 0,
            }
        check.update(validation)
        output_valid_count += int(bool(check["valid"]))
        parsed_playout_count += int(check.get("playout_summary_count") or 0)
        aggregate_issues.update(check.get("issues") or {})
        aggregate_results.update(check.get("result_counts") or {})
        output_checks.append(check)

    all_outputs_present = output_exists_count == len(jobs) and len(jobs) > 0
    any_outputs_present = output_exists_count > 0
    all_present_outputs_valid = output_exists_count == output_valid_count
    all_outputs_valid = all_outputs_present and all_present_outputs_valid and parse_error_count == 0

    if not any_outputs_present:
        status = "stage7_diverse_clean_sampling_outputs_validation_pending"
        next_step = "run_explicitly_approved_stage7_diverse_clean_label_execution"
    elif all_outputs_valid:
        status = "stage7_diverse_clean_sampling_outputs_valid_ready_for_integration"
        next_step = "rerun_passive_sequence_policy_pipeline_refresh"
    elif all_present_outputs_valid:
        status = "stage7_diverse_clean_sampling_outputs_partial_valid_pending_remaining_jobs"
        next_step = "complete_remaining_approved_stage7_diverse_clean_label_jobs"
    else:
        status = "stage7_diverse_clean_sampling_outputs_invalid_block_integration"
        next_step = "inspect_invalid_stage7_diverse_clean_outputs_before_integration"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_output_validation",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
        ],
        "summary": {
            "job_count": len(jobs),
            "output_exists_count": output_exists_count,
            "output_valid_count": output_valid_count,
            "all_outputs_present": all_outputs_present,
            "all_present_outputs_valid": all_present_outputs_valid,
            "all_outputs_valid": all_outputs_valid,
            "parse_error_count": parse_error_count,
            "parsed_playout_count": parsed_playout_count,
            "result_counts": dict(aggregate_results),
            "issue_counts": dict(aggregate_issues),
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        },
        "output_checks": output_checks,
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
            "runtime_changes_allowed": False,
            "label_run_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# Stage 7 Diverse Clean Sampling Output Validation v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a passive validation gate for already-created label outputs. It does not run labels, change runtime behavior, train selectors, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Outputs", ""])
    for row in payload["output_checks"]:
        lines.append(
            f"- `{row['job_id']}` exists=`{row['output_exists']}` valid=`{row['valid']}` playouts=`{row.get('playout_summary_count', 0)}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- runtime_changes_allowed: `false`",
            "- label_run_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
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
