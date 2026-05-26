#!/usr/bin/env python3
"""Write non-causal KRK sequence-policy benchmark design/readiness v0."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTRAST_PROBE = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json"
CONTRAST_DATASET = ROOT / "reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.json"
PLAN_CAPSULE_REVIEW = ROOT / "reports/strategy_arbitration/krk_plan_capsule_sequence_candidate_observation_review_v1.json"
STAGE7_POST_BOX_CONTROLS = ROOT / "reports/structural_candidates/stage7_post_box_sequence_control_recovery_v0.json"
STAGE7_CLEAN_CONTROLS = ROOT / "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json"
STAGE7_SAMPLING_MANIFEST = ROOT / "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json"
PROTECTED_PLAN_WINDOWS = ROOT / "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json"
BENCHMARK_REVIEW = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json"
STAGE4_APPROVAL_REQUEST = (
    ROOT / "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json"
)
OUTPUT_JSON = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.json"
OUTPUT_MD = ROOT / "reports/strategy_arbitration/krk_sequence_policy_benchmark_design_v0.md"

SCHEMA_VERSION = "krk_sequence_policy_benchmark_design.v0"

FORBIDDEN_INPUT_BLOCKERS = {
    "selector_training_rows_forbidden",
    "runtime_authorization_rows_forbidden",
}

FORBIDDEN_INPUT_STATUSES = {
    "sequence_policy_benchmark_blocked_forbidden_training_or_runtime_rows",
    "sequence_policy_benchmark_review_blocked_forbidden_training_or_runtime_rows",
}


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


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load(path)


def build_payload(
    *,
    contrast_probe: dict[str, Any] | None = None,
    contrast_dataset: dict[str, Any] | None = None,
    plan_capsule_review: dict[str, Any] | None = None,
    post_box_controls: dict[str, Any] | None = None,
    clean_controls: dict[str, Any] | None = None,
    sampling_manifest: dict[str, Any] | None = None,
    protected_plan_windows: dict[str, Any] | None = None,
    benchmark_review: dict[str, Any] | None = None,
    stage4_approval_request: dict[str, Any] | None = None,
) -> dict[str, Any]:
    loading_repo_defaults = all(
        item is None
        for item in (
            contrast_probe,
            contrast_dataset,
            plan_capsule_review,
            post_box_controls,
            clean_controls,
            sampling_manifest,
            protected_plan_windows,
            stage4_approval_request,
        )
    )
    contrast_probe = contrast_probe or _load(CONTRAST_PROBE)
    contrast_dataset = contrast_dataset or _load(CONTRAST_DATASET)
    plan_capsule_review = plan_capsule_review or _load(PLAN_CAPSULE_REVIEW)
    post_box_controls = post_box_controls or _load(STAGE7_POST_BOX_CONTROLS)
    clean_controls = clean_controls or _load(STAGE7_CLEAN_CONTROLS)
    sampling_manifest = sampling_manifest or _load(STAGE7_SAMPLING_MANIFEST)
    protected_plan_windows = protected_plan_windows or _load_optional(PROTECTED_PLAN_WINDOWS)
    stage4_approval_request = stage4_approval_request or _load_optional(
        STAGE4_APPROVAL_REQUEST
    )
    if benchmark_review is None:
        benchmark_review = _load_optional(BENCHMARK_REVIEW) if loading_repo_defaults else {}

    clean_success = int(
        clean_controls.get("summary", {})
        .get("role_counts", {})
        .get("clean_sequence_success_control", 0)
    )
    clean_fail = int(
        clean_controls.get("summary", {})
        .get("role_counts", {})
        .get("clean_sequence_hard_negative", 0)
    )
    post_box_count = int(post_box_controls.get("summary", {}).get("control_count", 0) or 0)
    stage4_review_ready = bool(
        contrast_probe.get("readiness", {}).get("stage4_first_move_contrast_sandbox_review_ready")
    )
    stage4_approval_request_status = stage4_approval_request.get("decision", {}).get(
        "status"
    )
    stage4_approval_request_blockers = stage4_approval_request.get("blockers") or []
    stage4_approval_request_ready_value = stage4_approval_request.get(
        "approval_request_ready_for_runtime_approval"
    )
    stage4_approval_request_ready = (
        bool(stage4_approval_request_ready_value)
        if stage4_approval_request_ready_value is not None
        else (
            stage4_approval_request_status
            == "stage4_first_move_contrast_sandbox_approval_request_ready"
            and not stage4_approval_request_blockers
        )
    )
    plan_capsule_stage7_only = bool(
        plan_capsule_review.get("readiness", {}).get("stage7_only_evidence")
    )
    protected_plan_window_count = int(
        protected_plan_windows.get("summary", {}).get("frame_count", 0) or 0
    )
    protected_plan_window_met = bool(
        protected_plan_windows.get("summary", {}).get("protected_cross_stage_evidence_met", False)
    )
    clean_success_met = clean_success >= 5
    clean_fail_met = clean_fail >= 5
    cross_stage_sequence_evidence_met = (not plan_capsule_stage7_only) or protected_plan_window_met
    benchmark_ready = clean_success_met and clean_fail_met and cross_stage_sequence_evidence_met
    benchmark_review_status = benchmark_review.get("decision", {}).get("status")
    benchmark_review_next_step = benchmark_review.get("decision", {}).get("recommended_next_step")
    benchmark_review_gate = benchmark_review.get("current_control_plane_gate") or {}
    protected_collection_recommended = (
        benchmark_review_next_step
        == "obtain_matching_approval_receipt_before_protected_failure_contrast_collection"
    )
    protected_collection_command_available_value = benchmark_review_gate.get(
        "protected_failure_contrast_collection_command_available"
    )
    protected_collection_command_available = (
        bool(protected_collection_command_available_value)
        if protected_collection_command_available_value is not None
        else None
    )
    protected_collection_gate_review_required = (
        benchmark_ready
        and
        protected_collection_recommended
        and protected_collection_command_available is False
    )
    forbidden_input_blockers = sorted(
        FORBIDDEN_INPUT_BLOCKERS & set(benchmark_review.get("blockers") or [])
    )
    forbidden_training_or_runtime_inputs = bool(forbidden_input_blockers) or (
        benchmark_review_status in FORBIDDEN_INPUT_STATUSES
    )
    benchmark_review_current = benchmark_review_status in {
        "sequence_policy_benchmark_supports_non_causal_sequence_policy_review",
        "sequence_policy_benchmark_mixed_plan_window_underpowered",
        "sequence_policy_benchmark_mixed_or_insufficient",
    }
    passive_continuation_status = (
        "non_causal_sequence_policy_design_blocked_forbidden_training_or_runtime_rows"
        if forbidden_training_or_runtime_inputs
        else "non_causal_sequence_policy_design_blocked_pending_ready_inputs"
        if not benchmark_ready
        else "non_causal_sequence_policy_review_packet_ready"
        if benchmark_review_status
        == "sequence_policy_benchmark_supports_non_causal_sequence_policy_review"
        else "non_causal_sequence_policy_design_without_new_labels_ready"
        if benchmark_review_status == "sequence_policy_benchmark_mixed_plan_window_underpowered"
        else "non_causal_sequence_policy_design_review_needed"
    )
    status = (
        "sequence_policy_benchmark_design_blocked_forbidden_training_or_runtime_rows"
        if forbidden_training_or_runtime_inputs
        else
        "sequence_policy_benchmark_design_blocked_pending_protected_failure_contrast_control_plane_gate_review"
        if protected_collection_gate_review_required
        else
        "sequence_policy_benchmark_blocked_pending_clean_stage7_controls"
        if not clean_success_met
        else "sequence_policy_benchmark_blocked_pending_cross_stage_sequence_evidence"
        if not cross_stage_sequence_evidence_met
        else "sequence_policy_benchmark_design_ready_non_causal"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "causal_status": "non_causal_sequence_policy_design",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_sequence_control_contrast_probe_v0.json",
            "reports/strategy_arbitration/krk_sequence_control_contrast_dataset_v0.json",
            "reports/strategy_arbitration/krk_plan_capsule_sequence_candidate_observation_review_v1.json",
            "reports/structural_candidates/stage7_post_box_sequence_control_recovery_v0.json",
            "reports/structural_candidates/stage7_clean_sequence_control_recovery_v0.json",
            "reports/structural_candidates/stage7_diverse_clean_sampling_manifest_v0.json",
            "reports/strategy_arbitration/krk_protected_plan_window_frames_v0.json",
            "reports/strategy_arbitration/krk_sequence_policy_benchmark_review_v0.json",
            "reports/krk_stage4_first_move_contrast_sandbox_approval_request_v0.json",
        ],
        "readiness": {
            "stage4_first_move_contrast_sandbox_review_ready": stage4_review_ready,
            "stage4_first_move_contrast_sandbox_approval_request_status": (
                stage4_approval_request_status
            ),
            "stage4_first_move_contrast_sandbox_approval_request_blockers": (
                stage4_approval_request_blockers
            ),
            "stage4_first_move_contrast_sandbox_approval_request_ready": (
                stage4_approval_request_ready
            ),
            "stage4_first_move_contrast_sandbox_approval_request_ready_for_runtime_approval": (
                stage4_approval_request_ready
            ),
            "stage7_clean_success_controls": clean_success,
            "stage7_clean_failure_controls": clean_fail,
            "stage7_clean_success_controls_required": 5,
            "stage7_clean_success_controls_met": clean_success_met,
            "stage7_clean_failure_controls_met": clean_fail_met,
            "post_box_sandbox_sourced_success_controls": post_box_count,
            "post_box_controls_runtime_authorization_eligible": False,
            "plan_capsule_stage7_only_evidence": plan_capsule_stage7_only,
            "protected_plan_window_frame_count": protected_plan_window_count,
            "protected_plan_window_evidence_met": protected_plan_window_met,
            "cross_stage_sequence_evidence_met": cross_stage_sequence_evidence_met,
            "plan_capsule_policy_succeeded": bool(
                plan_capsule_review.get("readiness", {}).get("policy_succeeded")
            ),
            "benchmark_ready": benchmark_ready,
            "current_benchmark_review_status": benchmark_review_status,
            "current_benchmark_review_next_step": benchmark_review_next_step,
            "current_benchmark_review_available": benchmark_review_current,
            "current_control_plane_gate_status": benchmark_review_gate.get("status"),
            "current_control_plane_approval_option_ids": (
                benchmark_review_gate.get("approval_option_ids") or []
            ),
            "protected_failure_contrast_collection_option_available": (
                benchmark_review_gate.get(
                    "protected_failure_contrast_collection_option_available"
                )
            ),
            "protected_failure_contrast_collection_command_available": (
                protected_collection_command_available
            ),
            "protected_failure_contrast_collection_option_id": benchmark_review_gate.get(
                "protected_failure_contrast_collection_option_id"
            ),
            "protected_failure_contrast_collection_blocked_by_option_id": (
                benchmark_review_gate.get(
                    "protected_failure_contrast_collection_blocked_by_option_id"
                )
            ),
            "protected_failure_contrast_control_plane_gate_review_required": (
                protected_collection_gate_review_required
            ),
            "forbidden_training_or_runtime_input_blocked": (
                forbidden_training_or_runtime_inputs
            ),
            "forbidden_training_or_runtime_input_blockers": forbidden_input_blockers,
        },
        "benchmark_design": {
            "name": "krk_sequence_policy_benchmark_v0",
            "purpose": "evaluate sequence-policy objectives without routing, scoring, promotion, or Stage 8 training",
            "candidate_objectives": [
                {
                    "objective_id": "state_local_first_move_contrast",
                    "uses": "Stage 4 forced-first-move contrast rows",
                    "target": "rank converting visible candidate moves above h40-failing drift moves within same state family",
                    "runtime_ready": False,
                },
                {
                    "objective_id": "post_box_sequence_success_vs_hard_negative",
                    "uses": "clean Stage 7 controls when enough success controls exist",
                    "target": "distinguish closed-loop sequence controls from hard negatives without using Stage 7 as promotion base",
                    "runtime_ready": False,
                },
                {
                    "objective_id": "plan_capsule_entry_progress_exit_abort",
                    "uses": "PlanCapsule marker/source terms plus protected plan-window frames where available",
                    "target": "predict when a bounded plan should enter, continue, hand off, or abort",
                    "runtime_ready": False,
                },
                {
                    "objective_id": "cross_stage_owner_preservation_vs_switch",
                    "uses": "protected Stage 4/5/6 ownership-seed context rows",
                    "target": "preserve safe owners while identifying switch/abstain contexts",
                    "runtime_ready": False,
                },
            ],
            "minimum_data_before_benchmark": [
                "at least 5 clean Stage 7 success controls and 5 clean Stage 7 hard negatives",
                "explicit held-out split by source family and state id",
                "PlanCapsule sequence fields represented outside Stage 7 or protected plan-window evidence marked as non-causal",
                "no row marked as selector-training or runtime-authorization evidence",
            ],
            "metrics": [
                "family-held-out top1/top3 conversion-positive ranking",
                "hard-negative suppression",
                "safe-owner preservation",
                "plan entry/progress/exit/abort classification",
                "first miss per sequence",
                "stage7 held-out challenge result",
            ],
        },
        "passive_design_without_new_labels": {
            "status": passive_continuation_status,
            "depends_on_new_label_execution": False,
            "depends_on_protected_failure_contrast_collection": False,
            "current_evidence_limit": (
                "protected_plan_window_failure_evidence_sparse"
                if benchmark_review_status == "sequence_policy_benchmark_mixed_plan_window_underpowered"
                else None
            ),
            "allowed_work": [
                "refine objective definitions against existing non-causal benchmark rows",
                "draft abstain-or-review criteria for plan-window entry/progress/exit/abort",
                "define held-out reporting tables and failure-slice diagnostics",
                "prepare a review packet template for a future explicit runtime-or-training decision",
            ],
            "blocked_work_without_explicit_approval": [
                "protected plan-window failure-contrast collection",
                "new Stage 7 label execution",
                "selector training",
                "runtime selector implementation",
                "runtime default or score changes",
                "Stage 7 promotion",
                "Stage 8 training",
            ],
            "exit_criteria_for_causal_work": [
                "matching approval receipt and completed protected failure-contrast integration, or separate explicit runtime sandbox approval",
                "separate reviewed packet authorizing any training or runtime change",
                "no selector-training or runtime-authorization rows in passive benchmark inputs",
            ],
        },
        "blocked_or_pending": [
            {
                "item": "stage4_first_move_contrast_sandbox",
                "status": (
                    "review_ready_pending_explicit_approval"
                    if stage4_review_ready and stage4_approval_request_ready
                    else "approval_request_blocked_pending_repair"
                    if stage4_review_ready
                    and stage4_approval_request_status
                    and not stage4_approval_request_ready
                    else "not_ready"
                ),
                "approval_request_status": stage4_approval_request_status,
                "approval_request_blockers": stage4_approval_request_blockers,
                "approval_request_ready_for_runtime_approval": (
                    stage4_approval_request_ready
                ),
            },
            {
                "item": "stage7_diverse_clean_sampling_manifest",
                "status": sampling_manifest.get("decision", {}).get("status"),
            },
            {
                "item": "sequence_policy_benchmark",
                "status": "blocked_until_clean_success_controls_or_cross_stage_evidence"
                if not benchmark_ready
                else "ready_non_causal",
            },
            {
                "item": "protected_plan_window_frames",
                "status": "available_non_causal"
                if protected_plan_window_met
                else "missing_or_underpowered",
            },
        ],
        "decision": {
            "status": status,
            "recommended_next_step": (
                "repair_sequence_policy_inputs_remove_training_or_runtime_rows"
                if forbidden_training_or_runtime_inputs
                else
                "review_current_control_plane_gate_for_protected_failure_contrast_collection"
                if protected_collection_gate_review_required
                else
                "approve_stage7_diverse_clean_label_run_or_defer_to_non_causal_design"
                if not clean_success_met
                else "collect_cross_stage_sequence_evidence"
                if not cross_stage_sequence_evidence_met
                else benchmark_review_next_step
                if benchmark_review_current and benchmark_review_next_step
                else "implement_non_causal_sequence_policy_benchmark"
            ),
            "runtime_changes_allowed": False,
            "selector_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }


def write_markdown(payload: dict[str, Any]) -> str:
    readiness = payload["readiness"]
    decision = payload["decision"]
    lines = [
        "# KRK Sequence-Policy Benchmark Design v0",
        "",
        f"Status: `{decision['status']}`",
        "",
        "This is a non-causal benchmark design/readiness artifact. It does not train a model, implement a sandbox, or authorize runtime behavior.",
        "",
        "## Readiness",
        "",
    ]
    for key, value in readiness.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend([
        "",
        "## Candidate Objectives",
        "",
    ])
    for item in payload["benchmark_design"]["candidate_objectives"]:
        lines.extend([
            f"### {item['objective_id']}",
            "",
            f"- uses: {item['uses']}",
            f"- target: {item['target']}",
            f"- runtime_ready: `{item['runtime_ready']}`",
            "",
        ])
    lines.extend([
        "## Minimum Data Before Benchmark",
        "",
    ])
    lines.extend(f"- {item}" for item in payload["benchmark_design"]["minimum_data_before_benchmark"])
    lines.extend([
        "",
        "## Metrics",
        "",
    ])
    lines.extend(f"- {item}" for item in payload["benchmark_design"]["metrics"])
    passive = payload["passive_design_without_new_labels"]
    lines.extend(
        [
            "",
            "## Passive Design Without New Labels",
            "",
            f"- status: `{passive['status']}`",
            f"- depends_on_new_label_execution: `{passive['depends_on_new_label_execution']}`",
            f"- depends_on_protected_failure_contrast_collection: `{passive['depends_on_protected_failure_contrast_collection']}`",
            f"- current_evidence_limit: `{passive['current_evidence_limit']}`",
            "",
            "Allowed work:",
        ]
    )
    lines.extend(f"- {item}" for item in passive["allowed_work"])
    lines.extend(["", "Blocked without explicit approval:"])
    lines.extend(f"- {item}" for item in passive["blocked_work_without_explicit_approval"])
    lines.extend(["", "Exit criteria for causal work:"])
    lines.extend(f"- {item}" for item in passive["exit_criteria_for_causal_work"])
    lines.extend([
        "",
        "## Decision",
        "",
        f"- recommended_next_step: `{decision['recommended_next_step']}`",
        "- runtime_changes_allowed: `false`",
        "- selector_training_allowed: `false`",
        "- Stage 7 promotion and Stage 8 training remain blocked.",
    ])
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
