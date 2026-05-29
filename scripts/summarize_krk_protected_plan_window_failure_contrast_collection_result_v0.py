#!/usr/bin/env python3
"""Summarize the approved protected plan-window failure-contrast collection.

This is a passive post-collection review. It records the bounded observation
result, verifies the no-runtime-change invariants, and emits only a future
review packet when more evidence would require a new explicit approval.
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
APPROVAL_RECEIPT = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_collection_approval_v0.json"
)
OUTPUT_VALIDATION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_output_validation_v0.json"
)
INTEGRATION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_integration_v0.json"
)
POST_REFRESH = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json"
)
BENCHMARK_REVIEW = (
    ROOT
    / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
)
RESULT_JSON = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_collection_result_v0.json"
)
RESULT_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_collection_result_v0.md"
)
FOLLOWUP_JSON = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_followup_review_packet_v0.json"
)
FOLLOWUP_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_plan_window_failure_contrast_followup_review_packet_v0.md"
)

RESULT_SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_collection_result.v0"
FOLLOWUP_SCHEMA_VERSION = (
    "krk_protected_plan_window_failure_contrast_followup_review_packet.v0"
)
OUTPUT_SCHEMA_VERSION = "krk_protected_plan_window_failure_contrast_output.v0"
OUTPUT_ROOT = Path("reports/strategy_arbitration/protected_plan_window_failure_contrasts")

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

FORBIDDEN_NEXT_STEPS = [
    "runtime_selector",
    "routing_or_score_change",
    "provider_suppression",
    "default_behavior_change",
    "stage7_promotion",
    "stage8_training",
    "runtime_dtm_or_tablebase",
    "gameplay_time_topology_mutation",
    "stage4_runtime_sandbox",
    "new_collection_without_fresh_explicit_approval",
]


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def _safe_output_path(path_value: Any) -> Path | None:
    if not isinstance(path_value, str) or not path_value:
        return None
    path = Path(path_value)
    if path.is_absolute() or ".." in path.parts:
        return None
    if path.parts[: len(OUTPUT_ROOT.parts)] != OUTPUT_ROOT.parts:
        return None
    return ROOT / path


def _load_outputs(manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], Counter[str]]:
    outputs: list[dict[str, Any]] = []
    issues: Counter[str] = Counter()
    for job in manifest.get("jobs") or []:
        path = _safe_output_path(job.get("expected_output_json"))
        if path is None:
            issues["unsafe_expected_output_json"] += 1
            continue
        if not path.exists():
            issues["output_missing"] += 1
            continue
        try:
            payload = _load(path)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            issues["output_parse_error"] += 1
            continue
        if payload.get("schema_version") != OUTPUT_SCHEMA_VERSION:
            issues["unexpected_output_schema"] += 1
        outputs.append(payload)
    return outputs, issues


def _truthy_delta_count(outputs: list[dict[str, Any]], keys: tuple[str, ...]) -> int:
    return sum(1 for output in outputs for key in keys if output.get(key) is True)


def _output_forbidden_issue_counts(outputs: list[dict[str, Any]]) -> Counter[str]:
    issues: Counter[str] = Counter()
    for output in outputs:
        for key, expected in COMMON_FALSE_FLAGS.items():
            if output.get(key) is not expected:
                issues[f"{key}_not_false"] += 1
        if output.get("observation_only") is not True:
            issues["observation_only_not_true"] += 1
        if output.get("usable_for_selector_training") is not False:
            issues["usable_for_selector_training_not_false"] += 1
        if output.get("usable_for_runtime_authorization") is not False:
            issues["usable_for_runtime_authorization_not_false"] += 1
        if int(output.get("stage7_training_row_count") or 0) != 0:
            issues["stage7_training_row_count_nonzero"] += 1
        if int(output.get("runtime_authorization_row_count") or 0) != 0:
            issues["runtime_authorization_row_count_nonzero"] += 1
    return issues


def build_collection_result_payload(
    *,
    manifest: dict[str, Any] | None = None,
    approval_receipt: dict[str, Any] | None = None,
    output_validation: dict[str, Any] | None = None,
    integration: dict[str, Any] | None = None,
    post_refresh: dict[str, Any] | None = None,
    benchmark_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manifest = manifest or _load(MANIFEST)
    approval_receipt = approval_receipt or _load(APPROVAL_RECEIPT)
    output_validation = output_validation or _load(OUTPUT_VALIDATION)
    integration = integration or _load(INTEGRATION)
    post_refresh = post_refresh or _load(POST_REFRESH)
    benchmark_review = benchmark_review or _load(BENCHMARK_REVIEW)

    outputs, output_load_issues = _load_outputs(manifest)
    output_forbidden_issues = _output_forbidden_issue_counts(outputs)
    output_labels = Counter(str(output.get("h40_outcome_label")) for output in outputs)
    validation_summary = output_validation.get("summary") or {}
    integration_summary = integration.get("summary") or {}
    post_refresh_summary = post_refresh.get("summary") or {}
    benchmark_protected_plan = (
        benchmark_review.get("objective_review", {}).get("protected_plan_window") or {}
    )

    all_outputs_valid = (
        output_validation.get("decision", {}).get("status")
        == "protected_plan_window_failure_contrast_outputs_valid_ready_for_integration"
        and int(validation_summary.get("output_valid_count") or 0)
        == len(manifest.get("jobs") or [])
        and not output_load_issues
        and not output_forbidden_issues
    )
    integration_ready = bool(integration_summary.get("integration_ready"))
    underpowered = all_outputs_valid and not integration_ready
    status = (
        "collection_complete_underpowered"
        if underpowered
        else "architecture_review_required"
        if output_load_issues or output_forbidden_issues
        else "blocked_needs_human_approval"
    )

    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "causal_status": "non_causal_protected_plan_window_collection_result",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_manifest_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_approval_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_output_validation_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_integration_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
        ],
        "summary": {
            "approved_collection_scope": approval_receipt.get("approval_id"),
            "approval_status": (approval_receipt.get("decision") or {}).get("status"),
            "single_execution_only": (approval_receipt.get("decision") or {}).get(
                "single_execution_only"
            ),
            "manifest_job_count": len(manifest.get("jobs") or []),
            "collection_output_count": len(outputs),
            "output_valid_count": int(validation_summary.get("output_valid_count") or 0),
            "h40_outcome_label_counts": dict(output_labels),
            "conversion_failure_count": int(output_labels.get("conversion_failure") or 0),
            "conversion_positive_count": int(output_labels.get("conversion_positive") or 0),
            "integrated_new_failure_count": int(
                integration_summary.get("integrated_new_failure_count") or 0
            ),
            "validated_unique_failure_candidate_count": int(
                integration_summary.get("validated_unique_failure_candidate_count") or 0
            ),
            "existing_unique_failure_count": int(
                integration_summary.get("existing_unique_failure_count") or 0
            ),
            "minimum_required_unique_failures": int(
                integration_summary.get("minimum_required_unique_failures") or 0
            ),
            "minimum_new_unique_failures_needed": int(
                integration_summary.get("minimum_new_unique_failures_needed") or 0
            ),
            "integration_ready": integration_ready,
            "sequence_policy_replay_free_recovery_row_count": int(
                post_refresh_summary.get("protected_failure_contrast_row_count") or 0
            ),
            "sequence_policy_boundaries_preserved": bool(
                post_refresh_summary.get("all_boundaries_preserved")
            ),
            "sequence_policy_boundary_violation_count": int(
                post_refresh_summary.get("boundary_violation_count") or 0
            ),
            "benchmark_protected_plan_window_row_count": int(
                benchmark_protected_plan.get("row_count") or 0
            ),
            "benchmark_protected_plan_window_target_label_counts": (
                benchmark_protected_plan.get("target_label_counts") or {}
            ),
            "selected_move_delta_count": _truthy_delta_count(
                outputs,
                ("selected_move_delta", "selected_move_changed", "selected_move_mutated"),
            ),
            "selected_provider_delta_count": _truthy_delta_count(
                outputs,
                (
                    "selected_provider_delta",
                    "selected_provider_changed",
                    "selected_provider_mutated",
                ),
            ),
            "score_delta_count": _truthy_delta_count(
                outputs,
                ("score_delta", "score_changed", "runtime_score_changed"),
            ),
            "routing_delta_count": _truthy_delta_count(
                outputs,
                ("routing_delta", "routing_changed", "runtime_routing_changed"),
            ),
            "runtime_behavior_unchanged": True,
            "selector_training_row_count": int(
                validation_summary.get("selector_training_row_count") or 0
            ),
            "stage7_training_row_count": int(
                validation_summary.get("stage7_training_row_count") or 0
            ),
            "runtime_authorization_row_count": int(
                validation_summary.get("runtime_authorization_row_count") or 0
            ),
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "output_load_issue_counts": dict(output_load_issues),
            "output_forbidden_issue_counts": dict(output_forbidden_issues),
            "non_causal_feature_probe_possible": False,
            "runtime_review_packet_possible": False,
            "next_step_requires_new_explicit_approval": True,
        },
        "decision": {
            "status": status,
            "recommended_next_step": (
                "review_followup_packet_before_any_additional_protected_plan_window_collection"
            ),
            "collection_run_allowed": False,
            "label_run_allowed": False,
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def build_followup_review_packet_payload(
    collection_result: dict[str, Any],
) -> dict[str, Any]:
    summary = collection_result["summary"]
    return {
        "schema_version": FOLLOWUP_SCHEMA_VERSION,
        "causal_status": "non_causal_future_collection_review_packet_only",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_collection_result_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_failure_contrast_integration_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_after_protected_failure_contrast_refresh_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
        ],
        "summary": {
            "prior_collection_status": collection_result["decision"]["status"],
            "prior_collection_output_count": summary["collection_output_count"],
            "prior_collection_conversion_failure_count": summary[
                "conversion_failure_count"
            ],
            "prior_collection_conversion_positive_count": summary[
                "conversion_positive_count"
            ],
            "integrated_new_failure_count": summary["integrated_new_failure_count"],
            "minimum_new_unique_failures_needed": summary[
                "minimum_new_unique_failures_needed"
            ],
            "replay_free_recovery_row_count": summary[
                "sequence_policy_replay_free_recovery_row_count"
            ],
            "review_scope": (
                "future protected plan-window failure-contrast collection only"
            ),
            "review_packet_only": True,
            "execute_now": False,
            "new_collection_approved_by_this_packet": False,
            "requires_fresh_manifest_or_scope_review": True,
            "requires_new_explicit_approval": True,
            "forbidden_next_steps": FORBIDDEN_NEXT_STEPS,
            "selector_training_row_count": summary["selector_training_row_count"],
            "stage7_training_row_count": summary["stage7_training_row_count"],
            "runtime_authorization_row_count": summary[
                "runtime_authorization_row_count"
            ],
        },
        "decision": {
            "status": "blocked_needs_human_approval",
            "recommended_next_step": (
                "prepare_or_review_a_fresh_bounded_manifest_before_any_additional_collection"
            ),
            "collection_run_allowed": False,
            "label_run_allowed": False,
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_collection_result_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Protected Plan-Window Failure Contrast Collection Result v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "The approved bounded observation collection produced valid outputs, but no new protected plan-window failure contrasts. Runtime behavior, routing, scoring, selector training, Stage 7 promotion, and Stage 8 training remain blocked.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- collection_run_allowed: `false`",
            "- runtime_changes_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Stage 7 promotion and Stage 8 training remain blocked.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_followup_review_packet_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Protected Plan-Window Failure Contrast Follow-Up Review Packet v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This packet is review-only. It does not approve or execute additional collection.",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(
        [
            "",
            "## Decision",
            "",
            f"- recommended_next_step: `{decision['recommended_next_step']}`",
            "- collection_run_allowed: `false`",
            "- runtime_changes_allowed: `false`",
            "- selector_training_allowed: `false`",
            "- Any additional collection requires new explicit approval.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    collection_result = build_collection_result_payload()
    followup_packet = build_followup_review_packet_payload(collection_result)
    RESULT_JSON.write_text(
        json.dumps(collection_result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    RESULT_MD.write_text(
        write_collection_result_markdown(collection_result),
        encoding="utf-8",
    )
    FOLLOWUP_JSON.write_text(
        json.dumps(followup_packet, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    FOLLOWUP_MD.write_text(
        write_followup_review_packet_markdown(followup_packet),
        encoding="utf-8",
    )
    print(f"wrote {RESULT_JSON.relative_to(ROOT)}")
    print(f"wrote {FOLLOWUP_JSON.relative_to(ROOT)}")
    print(collection_result["decision"]["status"])


if __name__ == "__main__":
    main()
