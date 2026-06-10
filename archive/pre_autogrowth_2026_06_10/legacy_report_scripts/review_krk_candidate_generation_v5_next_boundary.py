#!/usr/bin/env python3
"""Review the next boundary after the v5 candidate-generation context benchmark."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = Path("reports/strategy_arbitration/krk_candidate_generation_v5_context_benchmark.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_v5_next_boundary_review_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_v5_next_boundary_review_v0.md"
)


def _load(path: Path = BENCHMARK) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _num(value: Any) -> float:
    return float(value or 0.0)


def build_payload(benchmark: dict[str, Any] | None = None) -> dict[str, Any]:
    benchmark = benchmark or _load()
    summary = benchmark.get("summary") or {}
    decision = benchmark.get("decision") or {}
    exact_recall = _num(
        summary.get("exact_positive_capacity_recall_from_candidate_generation_trace")
    )
    exact_delta = _num(summary.get("exact_positive_capacity_recall_delta_vs_v4"))
    policy_cell_recall = _num(
        summary.get("policy_cell_positive_capacity_recall_from_candidate_generation_trace")
    )
    policy_cell_negative_exposure = _num(
        summary.get("policy_cell_negative_capacity_exposure_from_candidate_generation_trace")
    )
    exact_negative_exposure = _num(
        summary.get("exact_negative_capacity_exposure_from_candidate_generation_trace")
    )
    selector_rows = int(summary.get("selector_training_row_count", 0) or 0)
    stage7_rows = int(summary.get("stage7_readiness_training_row_count", 0) or 0)
    context_ready = (
        decision.get("selector_allowed") is False
        and policy_cell_recall >= 0.7
        and policy_cell_negative_exposure == 0.0
        and selector_rows == 0
        and stage7_rows == 0
    )
    exact_coverage_partial = exact_recall < 0.5
    exact_enrichment_helped = exact_delta > 0.0
    return {
        "schema_version": "krk_candidate_generation_v5_next_boundary_review.v1",
        "causal_status": "non_causal_boundary_review",
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
            "capacity_row_count": summary.get("capacity_row_count"),
            "positive_capacity_count": summary.get("positive_capacity_count"),
            "negative_capacity_count": summary.get("negative_capacity_count"),
            "runtime_trace_row_count": summary.get("runtime_trace_row_count"),
            "candidate_generation_trace_row_count": summary.get(
                "candidate_generation_trace_row_count"
            ),
            "exact_trace_enrichment_trace_row_count": summary.get(
                "exact_trace_enrichment_trace_row_count"
            ),
            "exact_positive_capacity_recall_from_candidate_generation_trace": exact_recall,
            "exact_positive_capacity_recall_delta_vs_v4": exact_delta,
            "policy_cell_positive_capacity_recall_from_candidate_generation_trace": (
                policy_cell_recall
            ),
            "exact_negative_capacity_exposure_from_candidate_generation_trace": (
                exact_negative_exposure
            ),
            "policy_cell_negative_capacity_exposure_from_candidate_generation_trace": (
                policy_cell_negative_exposure
            ),
            "selector_training_row_count": selector_rows,
            "stage7_readiness_training_row_count": stage7_rows,
        },
        "boundary_assessment": {
            "candidate_generation_context_is_useful": context_ready,
            "exact_trace_enrichment_helped": exact_enrichment_helped,
            "exact_move_provider_coverage_is_still_partial": exact_coverage_partial,
            "policy_cell_context_is_useful": policy_cell_recall >= 0.7,
            "negative_capacity_exposure_is_clean": policy_cell_negative_exposure == 0.0,
            "selector_training_still_absent": selector_rows == 0,
            "stage7_remains_held_out": stage7_rows == 0,
        },
        "approved_now": {
            "continue_non_causal_context_analysis": context_ready,
            "keep_existing_default_off_observation_sandboxes_available": context_ready,
            "implement_new_runtime_sandbox": False,
            "selector_allowed": False,
            "score_changes_allowed": False,
            "provider_routing_allowed": False,
            "guardrails_allowed": False,
            "stage4_runtime_scope_allowed": False,
        },
        "still_forbidden": [
            "selector_training",
            "score_changes",
            "provider_routing",
            "guardrail_campaign_from_context_only",
            "stage4_runtime_scope_without_separate_review",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "capacity_labels_as_ownership_labels",
        ],
        "interpretation": {
            "candidate_generation_context_is_ready_for_analysis": context_ready,
            "not_a_selector_packet": True,
            "reason": (
                "V5 improves exact candidate-generation trace coverage while keeping "
                "negative exposure clean, but exact coverage is still partial and no "
                "ownership selector labels exist. The next boundary is label/objective "
                "recovery, not another runtime candidate-generation sandbox."
            ),
        },
        "decision": {
            "status": (
                "candidate_generation_v5_next_boundary_context_improved_selector_blocked"
                if context_ready and exact_enrichment_helped
                else "candidate_generation_v5_next_boundary_needs_more_context"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "non_causal_ownership_label_recovery_or_selector_objective_review"
                if context_ready
                else "collect_more_protected_candidate_generation_context"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation v5 Next Boundary Review",
        "",
        "This review decides what the v5 context benchmark permits. It preserves the existing default-off observation sandboxes but does not authorize a selector, score changes, routing, guardrails, or a new runtime sandbox.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Boundary Assessment", ""])
    for key, value in payload["boundary_assessment"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Approved Now", ""])
    for key, value in payload["approved_now"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Still Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["still_forbidden"])
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
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
