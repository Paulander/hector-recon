#!/usr/bin/env python3
"""Review PlanCapsule and broader-strategy observation sources for KRK."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DESIGN = Path(
    "reports/strategy_arbitration/"
    "krk_broader_strategy_sequence_candidate_source_design_v1.json"
)
SEQUENCE_FRAMES = Path("reports/strategy_arbitration/krk_strategy_sequence_candidate_frames_v1.json")
MONITOR_RECORDS = Path("reports/strategy_arbitration/krk_strategy_monitor_records_v0.json")
INTERNAL_TERMINALS = Path("reports/strategy_arbitration/krk_internal_terminal_evidence_v1.json")
PLAN_SPEC = Path("reports/structural_candidates/stage7_post_box_continuation_capsule_candidate.json")
PLAN_FAILURE = Path("reports/structural_candidates/stage7_plan_capsule_owned_failure_analysis_50_h40.json")
PLAN_AUDIT = Path("reports/structural_candidates/stage7_post_box_plan_capsule_audit.json")

OUT_PLAN_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_plan_capsule_sequence_candidate_observation_review_v1.json"
)
OUT_PLAN_MD = Path(
    "reports/strategy_arbitration/"
    "krk_plan_capsule_sequence_candidate_observation_review_v1.md"
)
OUT_STRATEGY_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_broader_strategy_candidate_observation_review_v1.json"
)
OUT_STRATEGY_MD = Path(
    "reports/strategy_arbitration/"
    "krk_broader_strategy_candidate_observation_review_v1.md"
)
OUT_COMBINED_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_broader_strategy_sequence_candidate_source_review_v1.json"
)
OUT_COMBINED_MD = Path(
    "reports/strategy_arbitration/"
    "krk_broader_strategy_sequence_candidate_source_review_v1.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def plan_capsule_review(
    *,
    source_design: dict[str, Any] | None = None,
    plan_spec: dict[str, Any] | None = None,
    plan_failure: dict[str, Any] | None = None,
    plan_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_design = source_design or _load(SOURCE_DESIGN)
    plan_spec = plan_spec or _load(PLAN_SPEC)
    plan_failure = plan_failure or _load(PLAN_FAILURE)
    plan_audit = plan_audit or _load(PLAN_AUDIT)
    capsule = plan_spec.get("plan_capsule") or {}
    counters = plan_failure.get("summary_counters") or {}
    required_fields = []
    for contract in source_design.get("candidate_source_contracts") or []:
        if contract.get("candidate_source") == "plan_capsule_sequence_candidate":
            required_fields = list(contract.get("required_fields") or [])
    supported_count = int(counters.get("plan_capsule_selected_supported_count") or 0)
    selected_count = int(counters.get("plan_capsule_owned_arbitration_selected_count") or 0)
    diagnosis = list(plan_failure.get("diagnosis") or [])
    audit_diagnosis = plan_audit.get("diagnosis") or {}
    status = "plan_capsule_sequence_observation_source_review_blocked_stage7_only"
    if supported_count > 0 and capsule:
        status = "plan_capsule_sequence_observation_source_schema_ready_but_stage7_only"
    return {
        "schema_version": "krk_plan_capsule_sequence_candidate_observation_review.v1",
        "causal_status": "non_causal_source_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_candidate_generator_changes_implemented": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(SOURCE_DESIGN), str(PLAN_SPEC), str(PLAN_FAILURE), str(PLAN_AUDIT)],
        "required_observation_fields": required_fields,
        "evidence": {
            "capsule_id": capsule.get("capsule_id"),
            "capsule_causal_status": capsule.get("causal_status"),
            "capsule_promotion_status": capsule.get("promotion_status"),
            "ttl_white_moves": capsule.get("ttl_white_moves"),
            "entry_term_count": len(capsule.get("entry_terms") or []),
            "progress_term_count": len(capsule.get("progress_terms") or []),
            "exit_term_count": len(capsule.get("exit_terms") or []),
            "abort_term_count": len(capsule.get("abort_terms") or []),
            "handoff_export_count": len(capsule.get("handoff_exports") or {}),
            "selected_supported_count": supported_count,
            "owned_arbitration_selected_count": selected_count,
            "plan_failure_diagnosis": diagnosis,
            "plan_audit_diagnosis": audit_diagnosis,
        },
        "readiness": {
            "source_terms_visible_in_existing_artifacts": bool(capsule),
            "has_bounded_ttl": capsule.get("ttl_white_moves") is not None,
            "has_entry_progress_exit_abort_terms": all(
                capsule.get(key)
                for key in ("entry_terms", "progress_terms", "exit_terms", "abort_terms")
            ),
            "stage7_only_evidence": True,
            "protected_cross_stage_evidence": False,
            "policy_succeeded": False,
            "runtime_observation_expansion_allowed": False,
        },
        "decision": {
            "status": status,
            "implementation_allowed_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "non_causal_plan_capsule_source_contract_fixture_or_cross_stage_evidence",
        },
    }


def broader_strategy_review(
    *,
    source_design: dict[str, Any] | None = None,
    sequence_frames: dict[str, Any] | None = None,
    monitor_records: dict[str, Any] | None = None,
    internal_terminals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_design = source_design or _load(SOURCE_DESIGN)
    sequence_frames = sequence_frames or _load(SEQUENCE_FRAMES)
    monitor_records = monitor_records or _load(MONITOR_RECORDS)
    internal_terminals = internal_terminals or _load(INTERNAL_TERMINALS)
    frames = [
        frame
        for frame in sequence_frames.get("frames") or []
        if frame.get("frame_type") == "broader_krk_strategy_candidate"
    ]
    required_fields = []
    for contract in source_design.get("candidate_source_contracts") or []:
        if contract.get("candidate_source") == "broader_strategy_candidate":
            required_fields = list(contract.get("required_fields") or [])
    source_stage_counts = Counter(str(frame.get("source_stage") or "unknown") for frame in frames)
    family_counts = Counter(str(frame.get("candidate_strategy_family") or "unknown") for frame in frames)
    monitor_summary = monitor_records.get("summary") or {}
    terminal_summary = internal_terminals.get("summary") or {}
    protected_frames = sum(1 for frame in frames if not frame.get("stage7_challenge_row"))
    status = (
        "broader_strategy_observation_source_schema_ready_but_stage7_only"
        if frames and protected_frames == 0
        else "broader_strategy_observation_source_review_blocked"
    )
    return {
        "schema_version": "krk_broader_strategy_candidate_observation_review.v1",
        "causal_status": "non_causal_source_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_candidate_generator_changes_implemented": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            str(SOURCE_DESIGN),
            str(SEQUENCE_FRAMES),
            str(MONITOR_RECORDS),
            str(INTERNAL_TERMINALS),
        ],
        "required_observation_fields": required_fields,
        "evidence": {
            "broader_strategy_candidate_frame_count": len(frames),
            "protected_frame_count": protected_frames,
            "stage7_challenge_frame_count": len(frames) - protected_frames,
            "source_stage_counts": dict(sorted(source_stage_counts.items())),
            "candidate_strategy_family_counts": dict(sorted(family_counts.items())),
            "monitor_record_count": monitor_summary.get("monitor_record_count"),
            "monitor_records_by_type": monitor_summary.get("records_by_monitor_type"),
            "strongest_internal_terminal_candidates": terminal_summary.get(
                "strongest_internal_terminal_candidates"
            ),
            "causal_ready_terminals": terminal_summary.get("causal_ready_terminals"),
        },
        "readiness": {
            "strategy_monitor_frames_exist": bool(frames),
            "protected_cross_stage_strategy_frames_exist": protected_frames > 0,
            "stage7_only_evidence": bool(frames) and protected_frames == 0,
            "internal_terminals_causal_ready": bool(terminal_summary.get("causal_ready_terminals")),
            "runtime_observation_expansion_allowed": False,
        },
        "decision": {
            "status": status,
            "implementation_allowed_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "non_causal_protected_strategy_monitor_frame_expansion",
        },
    }


def combined_review(plan: dict[str, Any], strategy: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "krk_broader_strategy_sequence_candidate_source_review.v1",
        "causal_status": "non_causal_source_review_decision",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_candidate_generator_changes_implemented": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OUT_PLAN_JSON), str(OUT_STRATEGY_JSON)],
        "plan_capsule_source_status": plan["decision"]["status"],
        "broader_strategy_source_status": strategy["decision"]["status"],
        "shared_blockers": [
            "evidence_is_stage7_only_or_stage7_dominated",
            "source_contracts_are_defined_but_runtime_expansion_needs_separate_review",
            "candidate_generation_remains_separate_from_selection",
            "capacity_or_monitor_evidence_is_not_ownership_label",
        ],
        "decision": {
            "status": "source_reviews_complete_runtime_expansion_not_authorized",
            "implementation_allowed_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "build_protected_cross_stage_strategy_monitor_frame_expansion_non_causal",
        },
    }


def _write_md(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        "This artifact is non-causal and does not implement runtime source expansion.",
        "",
        "## Decision",
        "",
    ]
    for key, value in (payload.get("decision") or {}).items():
        lines.append(f"- {key}: `{value}`")
    if "evidence" in payload:
        lines.extend(["", "## Evidence", ""])
        for key, value in payload["evidence"].items():
            lines.append(f"- {key}: `{value}`")
    if "readiness" in payload:
        lines.extend(["", "## Readiness", ""])
        for key, value in payload["readiness"].items():
            lines.append(f"- {key}: `{value}`")
    if "shared_blockers" in payload:
        lines.extend(["", "## Shared Blockers", ""])
        lines.extend(f"- `{blocker}`" for blocker in payload["shared_blockers"])
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Do not implement selector behavior, score changes, provider routing, guardrails, Stage 7 promotion, or Stage 8 training from this review.",
        ]
    )
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    plan = plan_capsule_review()
    strategy = broader_strategy_review()
    combined = combined_review(plan, strategy)
    for path, payload in (
        (OUT_PLAN_JSON, plan),
        (OUT_STRATEGY_JSON, strategy),
        (OUT_COMBINED_JSON, combined),
    ):
        (ROOT / path).write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    _write_md(OUT_PLAN_MD, "KRK PlanCapsule Sequence Candidate Observation Review v1", plan)
    _write_md(OUT_STRATEGY_MD, "KRK Broader Strategy Candidate Observation Review v1", strategy)
    _write_md(OUT_COMBINED_MD, "KRK Broader Strategy/Sequence Candidate Source Review v1", combined)
    print(json.dumps(combined["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
