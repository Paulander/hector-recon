#!/usr/bin/env python3
"""Quality review for Stage 5/6 candidate-generation refresh observation frames."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_broadened_v0.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_quality_review_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_quality_review_v0.md"
)


def _load(path: Path = SOURCE) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(source: dict[str, Any] | None = None) -> dict[str, Any]:
    source = source or _load()
    summary = dict(source.get("summary") or {})
    frame_count = int(summary.get("refresh_frame_count", 0) or 0)
    case_count = int(summary.get("case_count", 0) or 0)
    stage7_count = int(summary.get("stage7_case_count", 0) or 0)
    invariant_failures = int(summary.get("invariant_failure_count", 0) or 0)
    selected_deltas = int(summary.get("selected_move_provider_delta_count", 0) or 0)
    baseline_leaks = int(summary.get("baseline_refresh_frame_count", 0) or 0)
    provider_counts = dict(summary.get("refresh_provider_counts") or {})
    capacity_counts = dict(summary.get("capacity_evidence_counts") or {})
    source_ok = (
        (source.get("decision") or {}).get("status")
        == "stage5_6_candidate_generation_refresh_broadened_default_off_equivalent"
    )
    trace_usable = (
        source_ok
        and frame_count > 0
        and case_count > 0
        and stage7_count == 0
        and invariant_failures == 0
        and selected_deltas == 0
        and baseline_leaks == 0
    )
    blockers = [
        "capacity_evidence_not_runtime_ownership_label",
        "sample_size_small_for_selector_or_guardrails",
        "negative_capacity_absence_in_refresh_scope_does_not_prove_safe_selection",
        "stage4_stage7_stage8_explicitly_excluded",
    ]
    status = (
        "stage5_6_candidate_generation_refresh_quality_trace_only_retained"
        if trace_usable
        else "stage5_6_candidate_generation_refresh_quality_blocked"
    )
    return {
        "schema_version": "krk_stage5_6_candidate_generation_refresh_quality_review.v0",
        "causal_status": "non_causal_runtime_observation_quality_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(SOURCE),
        "summary": {
            "case_count": case_count,
            "refresh_frame_count": frame_count,
            "stage7_case_count": stage7_count,
            "invariant_failure_count": invariant_failures,
            "selected_move_provider_delta_count": selected_deltas,
            "baseline_refresh_frame_count": baseline_leaks,
            "refresh_provider_counts": provider_counts,
            "capacity_evidence_counts": capacity_counts,
            "trace_usable_for_candidate_generation_context": trace_usable,
        },
        "selector_blockers": blockers,
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "fold_stage5_6_refresh_frames_into_strategy_sequence_dataset"
                if status == "stage5_6_candidate_generation_refresh_quality_trace_only_retained"
                else "quarantine_stage5_6_candidate_generation_refresh_source"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Stage 5/6 Candidate-Generation Refresh Quality Review v0",
        "",
        "This quality review keeps the Stage 5/6 refresh source as trace/candidate-generation context only. It does not authorize selection, scoring, guardrails, or promotion.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- case_count: {summary['case_count']}",
        f"- refresh_frame_count: {summary['refresh_frame_count']}",
        f"- stage7_case_count: {summary['stage7_case_count']}",
        f"- invariant_failure_count: {summary['invariant_failure_count']}",
        f"- selected_move_provider_delta_count: {summary['selected_move_provider_delta_count']}",
        f"- baseline_refresh_frame_count: {summary['baseline_refresh_frame_count']}",
        f"- refresh_provider_counts: `{summary['refresh_provider_counts']}`",
        f"- capacity_evidence_counts: `{summary['capacity_evidence_counts']}`",
        f"- trace_usable_for_candidate_generation_context: `{summary['trace_usable_for_candidate_generation_context']}`",
        "",
        "## Selector Blockers",
        "",
    ]
    lines.extend(f"- `{item}`" for item in payload["selector_blockers"])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
