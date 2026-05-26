#!/usr/bin/env python3
"""Integrate validated protected plan-window failure contrasts.

This gate is passive. It consumes the reviewed manifest and the output
validation report, but it never executes collection, changes runtime behavior,
trains selectors, promotes Stage 7, or trains Stage 8.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.json"
)
MANIFEST = (
    ROOT
    / "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json"
)
OUTPUT_VALIDATION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_output_validation_v0.json"
)
OUTPUT_JSON = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_integration_v0.json"
)
OUTPUT_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_integration_v0.md"
)

SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_integration.v0"

VALIDATION_READY_STATUSES = {
    "protected_plan_window_failure_contrast_outputs_valid_ready_for_integration",
    "protected_plan_window_failure_contrast_outputs_partial_valid_pending_remaining_jobs",
}

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


def _row_id(*parts: Any) -> str:
    digest = hashlib.sha1("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[
        :12
    ]
    return f"protected_failure_contrast.{digest}"


def _job_lookup(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(job.get("job_id")): job
        for job in manifest.get("jobs") or []
        if isinstance(job, dict) and job.get("job_id")
    }


def _integrated_rows(
    *,
    manifest: dict[str, Any],
    output_validation: dict[str, Any],
) -> tuple[list[dict[str, Any]], Counter[str]]:
    jobs = _job_lookup(manifest)
    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    seen: set[tuple[Any, Any, Any]] = set()

    for check in output_validation.get("output_checks") or []:
        if not isinstance(check, dict):
            skipped["malformed_output_check"] += 1
            continue
        if not check.get("valid"):
            skipped["invalid_or_missing_output"] += 1
            continue
        if check.get("h40_outcome_label") != "conversion_failure":
            skipped["not_conversion_failure"] += 1
            continue
        job = jobs.get(str(check.get("job_id")))
        if job is None:
            skipped["job_missing_from_manifest"] += 1
            continue
        key = (job.get("seed_frame_id"), job.get("anchor_move_uci"), check.get("result"))
        if key in seen:
            skipped["duplicate_failure_contrast"] += 1
            continue
        seen.add(key)
        rows.append(
            {
                "schema_version": "krk_protected_plan_window_failure_contrast_row.v0",
                "row_id": _row_id(*key, check.get("job_id")),
                "job_id": check.get("job_id"),
                "source_stage": job.get("source_stage"),
                "source_family": job.get("source_family"),
                "seed_frame_id": job.get("seed_frame_id"),
                "fen": job.get("seed_fen"),
                "anchor_move_uci": job.get("anchor_move_uci"),
                "result": check.get("result"),
                "h40_outcome_label": "conversion_failure",
                "control_role": "protected_plan_window_failure_contrast",
                "causal_status": "non_causal_validated_failure_contrast_integration",
                "stage7_training_row": False,
                "usable_for_selector_training": False,
                "usable_for_runtime_authorization": False,
                "stage7_heldout_challenge": False,
            }
        )
    return rows, skipped


def build_payload(
    *,
    plan: dict[str, Any] | None = None,
    manifest: dict[str, Any] | None = None,
    output_validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = plan or _load(PLAN)
    manifest = manifest or _load(MANIFEST)
    output_validation = output_validation or _load(OUTPUT_VALIDATION)

    validation_status = (output_validation.get("decision") or {}).get("status")
    validation_summary = output_validation.get("summary") or {}
    existing_unique_failures = int(plan.get("summary", {}).get("unique_failure_count") or 0)
    minimum_required_unique_failures = 5
    minimum_new_unique_failures_needed = int(
        plan.get("summary", {}).get("minimum_new_unique_failures_needed") or 0
    )
    if plan.get("collection_units"):
        for unit in plan["collection_units"]:
            if unit.get("unit_id") == "protected_plan_window_failure_contrast_minimum":
                minimum_required_unique_failures = int(
                    unit.get("minimum_required_unique_failures")
                    or minimum_required_unique_failures
                )
                break

    candidate_rows, skipped = _integrated_rows(
        manifest=manifest,
        output_validation=output_validation,
    )
    rows = (
        candidate_rows
        if validation_status in VALIDATION_READY_STATUSES
        else []
    )
    if candidate_rows and validation_status not in VALIDATION_READY_STATUSES:
        skipped["validation_status_not_ready_for_integration"] += len(candidate_rows)
    integrated_new_failure_count = len(rows)
    projected_unique_failure_count = existing_unique_failures + integrated_new_failure_count
    integration_ready = (
        validation_status in VALIDATION_READY_STATUSES
        and integrated_new_failure_count >= minimum_new_unique_failures_needed
        and projected_unique_failure_count >= minimum_required_unique_failures
    )

    if validation_status == "protected_plan_window_failure_contrast_outputs_validation_pending":
        status = "protected_plan_window_failure_contrast_integration_pending_outputs"
        next_step = "explicitly_approve_protected_plan_window_failure_contrast_collection"
    elif validation_status == "protected_plan_window_failure_contrast_outputs_invalid_block_integration":
        status = "protected_plan_window_failure_contrast_integration_blocked_invalid_outputs"
        next_step = "inspect_invalid_protected_plan_window_failure_contrast_outputs"
    elif integration_ready:
        status = "protected_plan_window_failure_contrast_integration_ready_for_passive_benchmark_refresh"
        next_step = "refresh_non_causal_sequence_policy_benchmark_inputs_with_integrated_failure_contrasts"
    elif validation_status in VALIDATION_READY_STATUSES:
        status = "protected_plan_window_failure_contrast_integration_underpowered_needs_more_valid_failures"
        next_step = "collect_additional_reviewed_protected_plan_window_failure_contrasts"
    else:
        status = "protected_plan_window_failure_contrast_integration_blocked_pending_output_validation"
        next_step = "validate_protected_plan_window_failure_contrast_outputs"

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_failure_contrast_integration",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_plan_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_output_validation_v0.json",
        ],
        "summary": {
            "validation_status": validation_status,
            "manifest_job_count": len(manifest.get("jobs") or []),
            "output_exists_count": int(validation_summary.get("output_exists_count") or 0),
            "output_valid_count": int(validation_summary.get("output_valid_count") or 0),
            "validated_unique_failure_candidate_count": int(
                validation_summary.get("unique_failure_candidate_count") or 0
            ),
            "existing_unique_failure_count": existing_unique_failures,
            "minimum_required_unique_failures": minimum_required_unique_failures,
            "minimum_new_unique_failures_needed": minimum_new_unique_failures_needed,
            "integrated_new_failure_count": integrated_new_failure_count,
            "projected_unique_failure_count": projected_unique_failure_count,
            "integration_ready": integration_ready,
            "source_stage_counts": dict(Counter(row["source_stage"] for row in rows)),
            "source_family_counts": dict(Counter(row["source_family"] for row in rows)),
            "skipped_counts": dict(skipped),
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        },
        "integrated_failure_contrasts": rows,
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
        "# KRK Protected Plan-Window Failure Contrast Integration v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a passive integration gate for already-validated protected failure-contrast outputs. It does not execute collection, change runtime behavior, train selectors, promote Stage 7, or train Stage 8.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Integrated Failure Contrasts", ""])
    if payload["integrated_failure_contrasts"]:
        for row in payload["integrated_failure_contrasts"]:
            lines.append(
                f"- `{row['row_id']}` job=`{row['job_id']}` stage=`{row['source_stage']}` family=`{row['source_family']}`"
            )
    else:
        lines.append("- none")
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
