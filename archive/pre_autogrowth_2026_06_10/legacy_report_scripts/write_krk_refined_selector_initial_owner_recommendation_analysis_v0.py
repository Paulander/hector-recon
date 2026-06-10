#!/usr/bin/env python3
"""Analyze refined initial-owner selector recommendations and write next gate.

This is analysis/review-packet generation only. It does not implement
behavior-changing selector selection.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SANDBOX = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_observability_sandbox_v0.json"
)
PRESERVE_RISK = Path(
    "reports/strategy_arbitration/krk_selector_preserve_failure_risk_decision_v0.json"
)
BENCHMARK = Path("reports/strategy_arbitration/krk_selector_objective_benchmark_v0.json")
SEED_MANIFEST = Path(
    "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json"
)
AGENT_BRIEF = Path("reports/current_agent_brief.md")

ANALYSIS_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_recommendation_analysis_v0.json"
)
ANALYSIS_MD = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_recommendation_analysis_v0.md"
)
GATE_JSON = Path(
    "reports/strategy_arbitration/krk_refined_selector_initial_owner_next_gate_v0.json"
)
GATE_MD = Path(
    "reports/strategy_arbitration/krk_refined_selector_initial_owner_next_gate_v0.md"
)
REVIEW_PACKET_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_behavior_review_packet_v0.json"
)
REVIEW_PACKET_MD = Path(
    "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_behavior_review_packet_v0.md"
)

DECISION_STATUSES = [
    "refined_selector_initial_owner_ready_for_behavior_review_packet",
    "refined_selector_initial_owner_needs_more_observation_data",
    "refined_selector_initial_owner_blocked_by_preserve_failure_risk",
    "refined_selector_initial_owner_blocked_by_switch_safe_owner_risk",
    "refined_selector_initial_owner_blocked_by_abstain_gap",
    "refined_selector_initial_owner_architecture_review_required",
]

COMMON_FALSE_FLAGS = {
    "runtime_behavior_changed": False,
    "runtime_defaults_changed": False,
    "behavior_changing_selector_implemented": False,
    "runtime_score_changes": False,
    "runtime_provider_suppression": False,
    "runtime_direct_routing": False,
    "runtime_dtm_or_tablebase_lookup": False,
    "hidden_python_controller": False,
    "gameplay_topology_mutation": False,
    "stage7_promotion_allowed": False,
    "stage8_training_allowed": False,
}

RUNTIME_VISIBLE_TERM_PREFIXES = (
    "selector_model.",
    "positive_trace_provider_candidate_count.",
    "positive_trace_count_bucket.",
    "edge_bucket.",
    "support_bucket.",
    "box_area_relevance.",
    "selected_piece.",
    "source_stage.",
    "active_landmark_label.",
    "candidate_strategy_family.",
    "runtime_review_packet.",
    "stage5_6_candidate_generation_refresh_scope",
    "offline_validated_provider_capacity_evidence",
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _term_runtime_visible(term: str) -> bool:
    return any(str(term).startswith(prefix) for prefix in RUNTIME_VISIBLE_TERM_PREFIXES)


def _rec(row: dict[str, Any]) -> dict[str, Any]:
    return (row.get("enabled_decision") or {}).get("selector_recommendation") or {}


def _int_value(mapping: dict[str, Any], key: str, default: int = -1) -> int:
    value = mapping.get(key, default)
    if value is None:
        return default
    return int(value)


def _visible_alt_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = 0
    with_visible = 0
    provider_families: Counter[str] = Counter()
    candidate_sources: Counter[str] = Counter()
    label_semantics: Counter[str] = Counter()
    for row in rows:
        rec = _rec(row)
        alternatives = rec.get("visible_alternatives_considered") or []
        total += len(alternatives)
        if alternatives:
            with_visible += 1
        for item in alternatives:
            if not isinstance(item, dict):
                continue
            provider_families[str(item.get("provider_family") or item.get("provider_id") or "")] += 1
            candidate_sources[str(item.get("candidate_source") or "")] += 1
            label_semantics[str(item.get("label_semantics") or "unspecified")] += 1
    return {
        "row_count_with_visible_alternatives": with_visible,
        "total_visible_alternative_count": total,
        "provider_family_counts": dict(sorted(provider_families.items())),
        "candidate_source_counts": dict(sorted(candidate_sources.items())),
        "label_semantics_counts": dict(sorted(label_semantics.items())),
    }


def _row_analysis(row: dict[str, Any]) -> dict[str, Any]:
    rec = _rec(row)
    target = row.get("offline_target_action")
    recommendation = row.get("recommendation")
    source_terms = list(row.get("source_terms") or rec.get("source_terms") or [])
    explanation_terms = list(row.get("explanation_terms") or rec.get("explanation_terms") or [])
    all_terms = source_terms + explanation_terms
    uses_runtime_visible_terms_only = all(_term_runtime_visible(str(term)) for term in all_terms)
    would_be_unsafe_if_causal = bool(
        row.get("preserve_on_selected_owner_failure") or row.get("switch_on_safe_owner")
    )
    weak_evidence_abstain = (
        recommendation == "abstain_context_only"
        and int(rec.get("positive_trace_provider_candidate_count", 0) or 0) <= 0
    )
    abstain_missed_switch = (
        recommendation == "abstain_context_only" and target == "prefer_visible_alternative"
    )
    return {
        "row_id": row.get("row_id") or row.get("case_id"),
        "source_stage": row.get("source_stage"),
        "selected_owner_label": row.get("selected_owner_label"),
        "offline_target_action": target,
        "recommendation": recommendation,
        "aligns_with_offline_label": recommendation == target,
        "weak_evidence_abstain": weak_evidence_abstain,
        "abstain_missed_switch": abstain_missed_switch,
        "would_be_unsafe_if_causal": would_be_unsafe_if_causal,
        "visible_alternative_count": row.get("visible_alternative_count"),
        "uses_runtime_visible_terms_only": uses_runtime_visible_terms_only,
        "source_terms": source_terms,
        "explanation_terms": explanation_terms,
        "preserve_failure_risk_refinement_status": row.get(
            "preserve_failure_risk_refinement_status"
        ),
        "abstain_guard_status": row.get("abstain_guard_status"),
    }


def build_analysis_payload(
    *,
    sandbox: dict[str, Any] | None = None,
    preserve_risk: dict[str, Any] | None = None,
    benchmark: dict[str, Any] | None = None,
    seed_manifest: dict[str, Any] | None = None,
    agent_brief_text: str | None = None,
) -> dict[str, Any]:
    sandbox = sandbox or _load(SANDBOX)
    preserve_risk = preserve_risk or _load(PRESERVE_RISK)
    benchmark = benchmark or _load(BENCHMARK)
    seed_manifest = seed_manifest or _load(SEED_MANIFEST)
    if agent_brief_text is None:
        agent_brief_text = (ROOT / AGENT_BRIEF).read_text(encoding="utf-8")
    rows = list(sandbox.get("rows") or [])
    analyzed_rows = [_row_analysis(row) for row in rows]
    recommendation_counts = Counter(row.get("recommendation") for row in analyzed_rows)
    target_counts = Counter(row.get("offline_target_action") for row in analyzed_rows)
    align_count = sum(1 for row in analyzed_rows if row["aligns_with_offline_label"])
    unsafe_if_causal = [row for row in analyzed_rows if row["would_be_unsafe_if_causal"]]
    abstain_rows = [row for row in analyzed_rows if row["recommendation"] == "abstain_context_only"]
    weak_abstain_rows = [row for row in abstain_rows if row["weak_evidence_abstain"]]
    abstain_missed_switch_rows = [row for row in abstain_rows if row["abstain_missed_switch"]]
    runtime_visible_term_failures = [
        row for row in analyzed_rows if not row["uses_runtime_visible_terms_only"]
    ]
    source_terms = sorted({term for row in analyzed_rows for term in row["source_terms"]})
    explanation_terms = sorted(
        {term for row in analyzed_rows for term in row["explanation_terms"]}
    )
    summary = sandbox.get("summary") or {}
    preserve_on_failure_count = int(summary.get("preserve_on_failure_count", 0) or 0)
    switch_on_safe_owner_count = int(summary.get("switch_on_safe_owner_count", 0) or 0)
    blocked_by_abstain = len(abstain_missed_switch_rows) > 1 or (
        len(abstain_missed_switch_rows) > 0
        and float(summary.get("abstain_recall", 0.0) or 0.0) < 1.0
    )
    ready = (
        sandbox.get("decision", {}).get("status")
        == "refined_selector_initial_owner_observability_ready_for_recommendation_analysis"
        and summary.get("default_off_equivalence_passed") is True
        and _int_value(summary, "continuation_recommendation_count") == 0
        and preserve_on_failure_count == 0
        and switch_on_safe_owner_count == 0
        and _int_value(summary, "stage7_training_row_count") == 0
        and _int_value(summary, "selector_training_row_count") == 0
        and _int_value(summary, "capacity_label_used_as_ownership_label_count") == 0
        and summary.get("runtime_behavior_changed") is False
        and not unsafe_if_causal
        and not runtime_visible_term_failures
        and not blocked_by_abstain
    )
    if preserve_on_failure_count:
        decision_status = "refined_selector_initial_owner_blocked_by_preserve_failure_risk"
    elif switch_on_safe_owner_count or unsafe_if_causal:
        decision_status = "refined_selector_initial_owner_blocked_by_switch_safe_owner_risk"
    elif blocked_by_abstain:
        decision_status = "refined_selector_initial_owner_blocked_by_abstain_gap"
    elif ready:
        decision_status = "refined_selector_initial_owner_ready_for_behavior_review_packet"
    elif runtime_visible_term_failures:
        decision_status = "refined_selector_initial_owner_architecture_review_required"
    else:
        decision_status = "refined_selector_initial_owner_needs_more_observation_data"
    return {
        "schema_version": "krk_refined_selector_initial_owner_recommendation_analysis.v0",
        "causal_status": "non_causal_recommendation_analysis_only",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(SANDBOX), str(PRESERVE_RISK), str(BENCHMARK), str(SEED_MANIFEST), str(AGENT_BRIEF)],
        "input_statuses": {
            "sandbox_status": sandbox.get("decision", {}).get("status"),
            "preserve_failure_risk_status": preserve_risk.get("decision", {}).get("status"),
            "benchmark_status": benchmark.get("decision", {}).get("status"),
            "seed_manifest_status": seed_manifest.get("decision", {}).get("status"),
        },
        "summary": {
            "row_count": len(rows),
            "recommendation_counts_by_class": dict(sorted(recommendation_counts.items())),
            "offline_target_counts_by_class": dict(sorted(target_counts.items())),
            "offline_alignment_count": align_count,
            "offline_alignment_rate": align_count / len(rows) if rows else 0.0,
            "preserve_on_failure_count": preserve_on_failure_count,
            "switch_on_safe_owner_count": switch_on_safe_owner_count,
            "abstain_count": len(abstain_rows),
            "weak_evidence_abstain_count": len(weak_abstain_rows),
            "abstain_missed_switch_count": len(abstain_missed_switch_rows),
            "abstain_recall": summary.get("abstain_recall"),
            "runtime_visible_terms_only_count": len(rows) - len(runtime_visible_term_failures),
            "runtime_visible_terms_failure_count": len(runtime_visible_term_failures),
            "unsafe_if_causal_count": len(unsafe_if_causal),
            "stage7_training_row_count": summary.get("stage7_training_row_count"),
            "selector_training_row_count": summary.get("selector_training_row_count"),
            "capacity_label_used_as_ownership_label_count": summary.get(
                "capacity_label_used_as_ownership_label_count"
            ),
            "runtime_behavior_changed": summary.get("runtime_behavior_changed"),
            "continuation_recommendation_count": summary.get("continuation_recommendation_count"),
            "selected_move_delta_count": summary.get("selected_move_delta_count"),
            "selected_provider_delta_count": summary.get("selected_provider_delta_count"),
            "score_delta_count": summary.get("score_delta_count"),
            "routing_delta_count": summary.get("routing_delta_count"),
        },
        "term_coverage": {
            "unique_source_term_count": len(source_terms),
            "unique_explanation_term_count": len(explanation_terms),
            "source_terms": source_terms,
            "explanation_terms": explanation_terms,
        },
        "visible_alternatives_coverage": _visible_alt_stats(rows),
        "rows": analyzed_rows,
        "abstain_gap_rows": abstain_missed_switch_rows,
        "unsafe_if_causal_rows": unsafe_if_causal,
        "runtime_visible_term_failure_rows": runtime_visible_term_failures,
        "capacity_label_semantics": {
            "capacity_labels_are_ownership_labels": False,
            "capacity_label_used_as_ownership_label_count": summary.get(
                "capacity_label_used_as_ownership_label_count"
            ),
            "note": "Capacity/provenance evidence is analyzed as candidate visibility only; it is not treated as selected-owner ground truth.",
        },
        "stage7_holdout": {
            "stage7_training_row_count": summary.get("stage7_training_row_count"),
            "stage7_remains_held_out": summary.get("stage7_training_row_count") == 0,
            "agent_brief_mentions_stage7_held_out": "Stage 7 remains held out" in agent_brief_text,
        },
        "decision_recommendation": decision_status,
    }


def build_gate_payload(analysis: dict[str, Any] | None = None) -> dict[str, Any]:
    analysis = analysis or build_analysis_payload()
    status = analysis["decision_recommendation"]
    return {
        "schema_version": "krk_refined_selector_initial_owner_next_gate.v0",
        "causal_status": "review_gate_only_no_behavior_change",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(ANALYSIS_JSON), str(SANDBOX), str(PRESERVE_RISK), str(BENCHMARK), str(SEED_MANIFEST)],
        "possible_decisions": DECISION_STATUSES,
        "decision": {
            "status": status,
            "write_behavior_review_packet_only": status
            == "refined_selector_initial_owner_ready_for_behavior_review_packet",
            "implement_behavior_selector": False,
            "runtime_changes_allowed": False,
            "provider_selection_changes_allowed": False,
            "move_selection_changes_allowed": False,
            "routing_changes_allowed": False,
            "score_changes_allowed": False,
            "provider_suppression_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
            "recommended_next_step": (
                "review_future_default_off_behavior_selector_packet_before_any_implementation"
                if status == "refined_selector_initial_owner_ready_for_behavior_review_packet"
                else "collect_more_initial_owner_observability_or_revisit_architecture"
            ),
        },
        "evidence": {
            "preserve_on_failure_count": analysis["summary"]["preserve_on_failure_count"],
            "switch_on_safe_owner_count": analysis["summary"]["switch_on_safe_owner_count"],
            "abstain_missed_switch_count": analysis["summary"]["abstain_missed_switch_count"],
            "unsafe_if_causal_count": analysis["summary"]["unsafe_if_causal_count"],
            "stage7_training_row_count": analysis["summary"]["stage7_training_row_count"],
            "selector_training_row_count": analysis["summary"]["selector_training_row_count"],
            "capacity_label_used_as_ownership_label_count": analysis["summary"][
                "capacity_label_used_as_ownership_label_count"
            ],
            "runtime_behavior_changed": analysis["summary"]["runtime_behavior_changed"],
            "continuation_recommendation_count": analysis["summary"][
                "continuation_recommendation_count"
            ],
        },
    }


def build_review_packet_payload(gate: dict[str, Any], analysis: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "krk_refined_selector_initial_owner_behavior_review_packet.v0",
        "causal_status": "future_behavior_sandbox_review_packet_only",
        **COMMON_FALSE_FLAGS,
        "source_artifacts": [str(GATE_JSON), str(ANALYSIS_JSON), str(SANDBOX)],
        "proposed_future_sandbox": {
            "name": "default_off_initial_owner_selector_behavior_sandbox",
            "implementation_status": "not_implemented",
            "default_off_required": True,
            "initial_owner_only": True,
            "continuation_recommendations_allowed": False,
            "allowed_behavior_if_separately_approved": "bounded_switch_to_visible_alternative_only_when_recommendation_is_prefer_visible_alternative",
            "preserve_selected_owner_effect": "no_op",
            "abstain_context_only_effect": "no_op",
            "score_delta": 0.0,
            "direct_request": False,
        },
        "required_vetoes_before_implementation": [
            "no_switch_if_not_initial_owner_decision",
            "no_switch_if_recommendation_is_preserve_selected_owner",
            "no_switch_if_recommendation_is_abstain_context_only",
            "no_switch_if_visible_alternative_missing",
            "no_switch_if_capacity_label_would_be_treated_as_ownership_label",
            "no_switch_if_stage7_or_training_row",
            "no_switch_if_source_or_explanation_terms_missing",
        ],
        "decision": {
            "status": (
                "refined_selector_initial_owner_behavior_review_packet_ready"
                if gate["decision"]["status"]
                == "refined_selector_initial_owner_ready_for_behavior_review_packet"
                else "refined_selector_initial_owner_behavior_review_packet_not_ready"
            ),
            "implementation_authorized_by_this_packet": False,
            "runtime_changes_allowed_by_this_packet": False,
            "selector_runtime_ready": False,
            "recommended_next_step": "human_review_before_any_default_off_behavior_sandbox_approval",
        },
        "evidence": dict(gate["evidence"]),
        "residual_risks": [
            "small initial-owner sample",
            "one abstain missed-switch row reduces target recall but is not unsafe as no-op",
            "capacity evidence must remain provenance-only, not ownership evidence",
            "first behavior-changing selector sandbox would require explicit approval",
        ],
    }


def _write_md(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [f"# {title}", ""]
    if "summary" in payload:
        lines.extend(["## Summary", ""])
        for key, value in payload["summary"].items():
            lines.append(f"- {key}: `{value}`")
        lines.extend(["", "## Term Coverage", ""])
        for key, value in payload["term_coverage"].items():
            lines.append(f"- {key}: `{value}`")
        lines.extend(["", "## Visible Alternatives Coverage", ""])
        for key, value in payload["visible_alternatives_coverage"].items():
            lines.append(f"- {key}: `{value}`")
        lines.extend(["", "## Decision Recommendation", ""])
        lines.append(f"- decision_recommendation: `{payload['decision_recommendation']}`")
    else:
        lines.extend(["## Decision", ""])
        for key, value in payload["decision"].items():
            lines.append(f"- {key}: `{value}`")
        if "evidence" in payload:
            lines.extend(["", "## Evidence", ""])
            for key, value in payload["evidence"].items():
                lines.append(f"- {key}: `{value}`")
        if "proposed_future_sandbox" in payload:
            lines.extend(["", "## Proposed Future Sandbox", ""])
            for key, value in payload["proposed_future_sandbox"].items():
                lines.append(f"- {key}: `{value}`")
            lines.extend(["", "## Required Vetoes", ""])
            lines.extend(f"- `{item}`" for item in payload["required_vetoes_before_implementation"])
            lines.extend(["", "## Residual Risks", ""])
            lines.extend(f"- {item}" for item in payload["residual_risks"])
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    analysis = build_analysis_payload()
    gate = build_gate_payload(analysis)
    review_packet = build_review_packet_payload(gate, analysis)
    (ROOT / ANALYSIS_JSON).write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ROOT / GATE_JSON).write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (ROOT / REVIEW_PACKET_JSON).write_text(
        json.dumps(review_packet, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    _write_md(ANALYSIS_MD, "KRK Refined Selector Initial Owner Recommendation Analysis v0", analysis)
    _write_md(GATE_MD, "KRK Refined Selector Initial Owner Next Gate v0", gate)
    _write_md(
        REVIEW_PACKET_MD,
        "KRK Refined Selector Initial Owner Behavior Review Packet v0",
        review_packet,
    )
    print(ANALYSIS_JSON)
    print(ANALYSIS_MD)
    print(GATE_JSON)
    print(GATE_MD)
    print(REVIEW_PACKET_JSON)
    print(REVIEW_PACKET_MD)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
