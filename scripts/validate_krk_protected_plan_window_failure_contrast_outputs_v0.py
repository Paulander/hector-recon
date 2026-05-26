#!/usr/bin/env python3
"""Validate protected plan-window failure-contrast outputs.

This passive validator checks already-created observation outputs against the
reviewed manifest. It does not execute collection, run labels, change runtime
behavior, train selectors, promote Stage 7, or authorize Stage 8.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
)
OUTPUT_JSON = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_output_validation_v0.json"
)
OUTPUT_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_output_validation_v0.md"
)

SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_output_validation.v0"
OUTPUT_SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_output.v0"
OUTPUT_CAUSAL_STATUS = "non_causal_observation_only_collection"
OUTPUT_ROOT = Path("reports/strategy_arbitration/protected_plan_window_failure_contrasts")

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


def _safe_relative_output(path_value: Any) -> bool:
    if not isinstance(path_value, str) or not path_value:
        return False
    path = Path(path_value)
    if path.is_absolute() or ".." in path.parts:
        return False
    return path.parts[: len(OUTPUT_ROOT.parts)] == OUTPUT_ROOT.parts


def _expected_label(result: Any) -> str | None:
    if result == "mate":
        return "conversion_positive"
    if result in {"max_plies", "draw"}:
        return "conversion_failure"
    return None


def _validate_output(job: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if payload.get("schema_version") != OUTPUT_SCHEMA_VERSION:
        issues.append("unexpected_schema_version")
    if payload.get("causal_status") != OUTPUT_CAUSAL_STATUS:
        issues.append("unexpected_causal_status")
    if payload.get("job_id") != job.get("job_id"):
        issues.append("job_id_mismatch")
    if payload.get("source_stage") != job.get("source_stage"):
        issues.append("source_stage_mismatch")
    if payload.get("source_family") != job.get("source_family"):
        issues.append("source_family_mismatch")
    if payload.get("seed_frame_id") != job.get("seed_frame_id"):
        issues.append("seed_frame_id_mismatch")
    if int(payload.get("horizon") or 0) != 40:
        issues.append("horizon_must_be_40")

    result = payload.get("result")
    h40_label = payload.get("h40_outcome_label")
    expected = _expected_label(result)
    if expected is None:
        issues.append("unsupported_result")
    elif h40_label != expected:
        issues.append("h40_outcome_label_result_mismatch")
    if h40_label not in {"conversion_positive", "conversion_failure"}:
        issues.append("unsupported_h40_outcome_label")

    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
        "usable_for_selector_training",
        "usable_for_runtime_authorization",
        "stage7_heldout_challenge",
    ):
        if payload.get(key) is not False:
            issues.append(f"{key}_must_be_false")
    if payload.get("observation_only") is not True:
        issues.append("observation_only_must_be_true")

    return {
        "valid": not issues,
        "issues": issues,
        "result": result,
        "h40_outcome_label": h40_label,
        "is_unique_failure_candidate": h40_label == "conversion_failure",
        "stage7_training_row_count": 0,
        "runtime_authorization_row_count": 0,
    }


def build_payload(*, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    jobs = manifest.get("jobs") or []
    output_checks: list[dict[str, Any]] = []
    issue_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter()
    output_exists_count = 0
    output_valid_count = 0
    parse_error_count = 0
    unique_failure_count = 0
    seen_failure_keys: set[tuple[Any, Any, Any]] = set()

    for job in jobs:
        output = job.get("expected_output_json")
        safe_output = _safe_relative_output(output)
        path = ROOT / str(output) if safe_output else None
        exists = bool(path and path.exists())
        check: dict[str, Any] = {
            "job_id": job.get("job_id"),
            "expected_output_json": output,
            "output_exists": exists,
            "valid": False,
            "issues": [],
            "stage7_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        }
        if not safe_output:
            check["issues"] = ["unsafe_expected_output_json"]
            issue_counts.update(check["issues"])
            output_checks.append(check)
            continue
        if not exists or path is None:
            check["issues"] = ["output_missing"]
            issue_counts.update(check["issues"])
            output_checks.append(check)
            continue
        output_exists_count += 1
        try:
            validation = _validate_output(job, _load(path))
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            parse_error_count += 1
            validation = {
                "valid": False,
                "issues": ["output_parse_error"],
                "parse_error": str(exc),
                "stage7_training_row_count": 0,
                "runtime_authorization_row_count": 0,
            }
        check.update(validation)
        output_valid_count += int(bool(check["valid"]))
        issue_counts.update(check.get("issues") or [])
        label = check.get("h40_outcome_label")
        if label:
            label_counts[str(label)] += 1
        if check.get("valid") and check.get("is_unique_failure_candidate"):
            key = (job.get("seed_frame_id"), job.get("anchor_move_uci"), check.get("result"))
            if key not in seen_failure_keys:
                unique_failure_count += 1
                seen_failure_keys.add(key)
        output_checks.append(check)

    any_outputs_present = output_exists_count > 0
    all_outputs_present = output_exists_count == len(jobs) and len(jobs) > 0
    all_present_outputs_valid = output_exists_count == output_valid_count
    all_outputs_valid = all_outputs_present and all_present_outputs_valid and parse_error_count == 0
    if not any_outputs_present:
        status = "protected_plan_window_failure_contrast_outputs_validation_pending"
        next_step = "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    elif all_outputs_valid:
        status = "protected_plan_window_failure_contrast_outputs_valid_ready_for_integration"
        next_step = "integrate_protected_plan_window_failure_contrasts_passively"
    elif all_present_outputs_valid:
        status = "protected_plan_window_failure_contrast_outputs_partial_valid_pending_remaining_jobs"
        next_step = "complete_remaining_approved_protected_plan_window_failure_contrast_jobs"
    else:
        status = "protected_plan_window_failure_contrast_outputs_invalid_block_integration"
        next_step = "inspect_invalid_protected_plan_window_failure_contrast_outputs"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_output_validation",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
        ],
        "summary": {
            "job_count": len(jobs),
            "output_exists_count": output_exists_count,
            "output_valid_count": output_valid_count,
            "all_outputs_present": all_outputs_present,
            "all_present_outputs_valid": all_present_outputs_valid,
            "all_outputs_valid": all_outputs_valid,
            "parse_error_count": parse_error_count,
            "h40_outcome_label_counts": dict(label_counts),
            "unique_failure_candidate_count": unique_failure_count,
            "issue_counts": dict(issue_counts),
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        },
        "output_checks": output_checks,
        "decision": {
            "status": status,
            "recommended_next_step": next_step,
            "collection_run_allowed": False,
            "label_run_allowed": False,
            "runtime_changes_allowed": False,
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
        "# KRK Protected Plan-Window Failure Contrast Output Validation v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a passive validation gate for already-created protected failure-contrast outputs. It does not execute collection, run labels, change runtime behavior, train selectors, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Outputs", ""])
    for row in payload["output_checks"]:
        lines.append(
            f"- `{row['job_id']}` exists=`{row['output_exists']}` valid=`{row['valid']}` issues=`{row['issues']}`"
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- collection_run_allowed: `false`",
            "- label_run_allowed: `false`",
            "- runtime_changes_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    payload = build_payload()
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUTPUT_MD.write_text(write_markdown(payload), encoding="utf-8")
    print(f"wrote {OUTPUT_JSON.relative_to(ROOT)}")
    print(f"wrote {OUTPUT_MD.relative_to(ROOT)}")
    print(payload["decision"]["status"])


if __name__ == "__main__":
    main()
