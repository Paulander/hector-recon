#!/usr/bin/env python3
"""Review runtime boundary after candidate-generation v3 context benchmark."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = Path("reports/strategy_arbitration/krk_candidate_generation_v3_context_benchmark.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_generation_v3_runtime_boundary_review.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_generation_v3_runtime_boundary_review.md")


def _load(path: Path = BENCHMARK) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(benchmark: dict[str, Any] | None = None) -> dict[str, Any]:
    benchmark = benchmark or _load()
    summary = benchmark.get("summary") or {}
    exact_recall = float(summary.get("exact_positive_capacity_recall_from_trace", 0.0) or 0.0)
    stage_family_recall = float(
        summary.get("stage_family_positive_capacity_recall_from_trace", 0.0) or 0.0
    )
    negative_exposure = float(
        summary.get("stage_family_negative_capacity_exposure_from_trace", 0.0) or 0.0
    )
    context_ready = (
        (benchmark.get("decision") or {}).get("selector_allowed") is False
        and stage_family_recall >= 0.7
        and negative_exposure == 0.0
        and int(summary.get("selector_training_row_count", 0) or 0) == 0
        and int(summary.get("stage7_readiness_training_row_count", 0) or 0) == 0
    )
    return {
        "schema_version": "krk_candidate_generation_v3_runtime_boundary_review.v1",
        "causal_status": "non_causal_runtime_boundary_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(BENCHMARK)],
        "summary": {
            "exact_positive_capacity_recall_from_trace": exact_recall,
            "stage_family_positive_capacity_recall_from_trace": stage_family_recall,
            "stage_family_negative_capacity_exposure_from_trace": negative_exposure,
            "runtime_trace_row_count": summary.get("runtime_trace_row_count"),
            "selector_training_row_count": summary.get("selector_training_row_count"),
            "stage7_readiness_training_row_count": summary.get(
                "stage7_readiness_training_row_count"
            ),
        },
        "approved_runtime_boundary": {
            "current_observation_sources_remain_allowed": context_ready,
            "new_runtime_behavior_allowed": False,
            "selector_allowed": False,
            "score_changes_allowed": False,
            "provider_routing_allowed": False,
            "guardrails_allowed": False,
        },
        "interpretation": {
            "candidate_generation_context_is_useful": context_ready,
            "exact_state_provider_move_recall_is_partial": exact_recall < 0.7,
            "stage_family_context_is_promising": stage_family_recall >= 0.7,
            "runtime_selection_still_blocked": True,
            "reason": (
                "V3 trace context supports candidate-generation coverage analysis, "
                "but it is not ownership evidence. The next runtime step cannot be "
                "a selector; it would require explicit ownership labels or a separate "
                "review packet."
            ),
        },
        "still_forbidden": [
            "selector_training",
            "score_changes",
            "provider_routing",
            "guardrail_campaign_from_context_only",
            "stage7_promotion",
            "stage8_training",
        ],
        "decision": {
            "status": (
                "candidate_generation_v3_runtime_boundary_context_ready_selector_blocked"
                if context_ready
                else "candidate_generation_v3_runtime_boundary_needs_more_context"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "candidate_generation_v3_context_to_training_refresh_review"
                if context_ready
                else "collect_more_protected_context_before_runtime_review"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    boundary = payload["approved_runtime_boundary"]
    lines = [
        "# KRK Candidate-Generation v3 Runtime Boundary Review",
        "",
        "This review decides what the v3 context benchmark permits. It keeps the existing observation sources allowed but blocks selector/scoring/routing changes.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- guardrails_allowed: `{payload['decision']['guardrails_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- exact_positive_capacity_recall_from_trace: {summary['exact_positive_capacity_recall_from_trace']}",
        f"- stage_family_positive_capacity_recall_from_trace: {summary['stage_family_positive_capacity_recall_from_trace']}",
        f"- stage_family_negative_capacity_exposure_from_trace: {summary['stage_family_negative_capacity_exposure_from_trace']}",
        f"- runtime_trace_row_count: {summary['runtime_trace_row_count']}",
        f"- selector_training_row_count: {summary['selector_training_row_count']}",
        f"- stage7_readiness_training_row_count: {summary['stage7_readiness_training_row_count']}",
        "",
        "## Runtime Boundary",
        "",
    ]
    for key, value in boundary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Still Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["still_forbidden"])
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
