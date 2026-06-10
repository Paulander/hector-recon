#!/usr/bin/env python3
"""Summarize KRK strategy monitor maturity and utility.

This gate classifies extracted monitor terms and missing backlog terms before
any runtime/sandbox work. It is non-causal and report-only.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


EXPECTED_TERM_CLASSIFICATIONS = {
    "box_area_no_longer_decision_relevant": {
        "maturity_status": "context_feature",
        "use_as": ["context feature", "owner-exit monitor"],
        "rationale": "Broad owner-exit companion; useful context but too common to trigger behavior alone.",
        "required_companion_terms": ["active_landmark_label == box_shrink", "validated_handoff_target_available"],
    },
    "safe_repair_move_exists": {
        "maturity_status": "too_broad",
        "use_as": ["context feature"],
        "rationale": "True across the full current dataset, so it is not separable alone.",
        "required_companion_terms": ["repair_needed", "cut_or_fence_restored_after_move", "box_area_not_expanded_after_reply"],
    },
    "cut_or_fence_restored_after_move": {
        "maturity_status": "monitor_candidate",
        "use_as": ["failure/risk monitor"],
        "rationale": "Useful repair-progress evidence when paired with repair-needed context.",
        "required_companion_terms": ["fence_or_cut_repair_affordance", "safe_repair_move_exists"],
    },
    "post_plan_stagnation": {
        "maturity_status": "internal_terminal_candidate",
        "use_as": ["plan-selection monitor", "growth-pressure monitor"],
        "rationale": "Sparse and semantically strong trace-window signal for plan/capsule failure.",
        "required_companion_terms": ["plan_capsule_context", "handoff_success_after_plan"],
    },
    "local_provider_competition_failed": {
        "maturity_status": "internal_terminal_candidate",
        "use_as": ["growth-pressure monitor", "plan-selection monitor"],
        "rationale": "Sparse but directly expresses provider-arbitration failure.",
        "required_companion_terms": ["current_owner", "alternative_provider_known_mate"],
    },
    "king_support_improves_after_move": {
        "maturity_status": "context_feature",
        "use_as": ["context feature"],
        "rationale": "Action-relevant improvement is better than static support, but still broad.",
        "required_companion_terms": ["king_support_needed_for_current_phase", "king_support_aligned_with_cut_or_edge_net"],
    },
}


BACKLOG_PRIORITIES = {
    "edge_net_pressure_increases_after_move": "high",
    "safe_edge_net_tighten_move_exists": "high",
    "king_support_aligned_with_edge_net": "high",
    "handoff_success_after_plan": "high",
    "multi_step_progress_required": "high",
    "repair_preserves_mate_basin_progress": "lower_defer",
    "king_support_improves_after_reply": "lower_defer",
    "repair_needed_but_no_safe_repair_available": "lower_defer",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _term_value(term_payload: dict[str, Any] | None) -> bool:
    return bool(term_payload and term_payload.get("value") is True)


def _precision(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _classify_shape(support_count: int, total_count: int) -> str:
    if support_count == 0:
        return "absent"
    ratio = support_count / total_count if total_count else 0.0
    if ratio >= 0.75:
        return "broad"
    if ratio <= 0.25:
        return "sparse"
    return "moderate"


def _term_stats(term_name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    matching = [record for record in records if _term_value((record.get("terms") or {}).get(term_name))]
    result_counts = Counter(str(record.get("associated_outcome") or "unknown") for record in matching)
    stage_counts = Counter(str(record.get("source_stage") or "unknown") for record in matching)
    stage7 = [record for record in matching if record.get("source_stage") == "stage7"]
    stage7_result_counts = Counter(str(record.get("associated_outcome") or "unknown") for record in stage7)
    known = result_counts["mate"] + result_counts["max_plies"]
    classification = EXPECTED_TERM_CLASSIFICATIONS[term_name]
    support_count = len(matching)
    total_count = len(records)
    shape = _classify_shape(support_count, total_count)
    causal_blocked = True
    return {
        "term": term_name,
        "support_count": support_count,
        "total_record_count": total_count,
        "support_ratio": _precision(support_count, total_count),
        "mate_max_plies_unknown_distribution": dict(result_counts),
        "source_stage_distribution": dict(stage_counts),
        "stage7_support_count": len(stage7),
        "stage7_result_distribution": dict(stage7_result_counts),
        "success_precision": _precision(result_counts["mate"], known),
        "failure_precision": _precision(result_counts["max_plies"], known),
        "shape": shape,
        "is_broad": shape == "broad",
        "is_sparse": shape == "sparse",
        "is_separable": shape == "sparse" and result_counts["max_plies"] >= result_counts["mate"],
        "maturity_status": classification["maturity_status"],
        "use_as": classification["use_as"],
        "required_companion_terms": classification["required_companion_terms"],
        "causal_use_blocked": causal_blocked,
        "rationale": classification["rationale"],
    }


def _monitor_class_summary(records_payload: dict[str, Any]) -> list[dict[str, Any]]:
    outcomes = (records_payload.get("summary") or {}).get("outcomes_by_monitor_type") or {}
    result: list[dict[str, Any]] = []
    for monitor_type, counts in outcomes.items():
        known = int(counts.get("mate", 0)) + int(counts.get("max_plies", 0))
        failure_precision = _precision(int(counts.get("max_plies", 0)), known)
        success_precision = _precision(int(counts.get("mate", 0)), known)
        if monitor_type in {"RepairNeededMonitor", "PlanSelectionNeededMonitor"}:
            maturity = "monitor_candidate"
        elif monitor_type in {"PhaseBoundaryMonitor", "OwnerExitMonitor"}:
            maturity = "needs_companion_terms"
        else:
            maturity = "needs_companion_terms"
        result.append(
            {
                "monitor_type": monitor_type,
                "outcome_distribution": counts,
                "success_precision": success_precision,
                "failure_precision": failure_precision,
                "maturity_status": maturity,
                "causal_use_blocked": True,
            }
        )
    return result


def _backlog_terms(companion_audit: dict[str, Any]) -> list[dict[str, Any]]:
    missing = (companion_audit.get("summary") or {}).get("still_missing_terms") or []
    result = []
    for term in missing:
        priority = BACKLOG_PRIORITIES.get(term, "backlog")
        result.append(
            {
                "term": term,
                "maturity_status": "backlog_missing_extraction",
                "priority": priority,
                "causal_use_blocked": True,
            }
        )
    return sorted(result, key=lambda item: (item["priority"] != "high", item["term"]))


def build_gate(report_root: Path) -> dict[str, Any]:
    visible_terms = _load_json(report_root / "krk_visible_monitor_terms_v0.json")
    monitor_records = _load_json(report_root / "krk_strategy_monitor_records_v0.json")
    companion_audit = _load_json(report_root / "krk_strategy_monitor_companion_audit_v1.json")
    records = [item for item in visible_terms.get("records") or [] if isinstance(item, dict)]
    term_names = (visible_terms.get("summary") or {}).get("term_names") or []
    term_maturity = [_term_stats(term, records) for term in term_names]
    typed_counts = Counter(item["maturity_status"] for item in term_maturity)
    backlog = _backlog_terms(companion_audit)
    backlog_counts = Counter(item["priority"] for item in backlog)
    gate = {
        "schema_version": "krk_strategy_monitor_maturity_gate.v0",
        "causal_status": "non_causal_maturity_gate",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_strategy_monitor_records_v0.json",
            "reports/strategy_arbitration/krk_strategy_monitor_companion_audit_v1.json",
            "reports/strategy_arbitration/krk_visible_monitor_terms_v0.json",
            "reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json",
        ],
        "term_maturity": term_maturity,
        "monitor_class_maturity": _monitor_class_summary(monitor_records),
        "backlog_missing_extraction": backlog,
        "summary": {
            "term_count": len(term_maturity),
            "maturity_status_counts": dict(typed_counts),
            "backlog_priority_counts": dict(backlog_counts),
            "causal_ready_terms": [],
            "strongest_internal_terminal_candidates": [
                "post_plan_stagnation",
                "local_provider_competition_failed",
            ],
            "broad_context_terms": [
                item["term"] for item in term_maturity if item["shape"] == "broad"
            ],
            "recommended_next_step": "broader_evidence_collection_or_internal_monitor_design_review",
        },
        "blocked_next_steps": [
            "runtime_terminals",
            "causal_affordances",
            "runtime_arbiter",
            "stage7_repair",
            "stage8_training",
            "stage7_promotion",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "monitor_to_provider_routing",
        ],
    }
    validate_gate(gate)
    return gate


def validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("schema_version") != "krk_strategy_monitor_maturity_gate.v0":
        raise ValueError("unexpected maturity gate schema")
    if gate.get("causal_status") != "non_causal_maturity_gate":
        raise ValueError("maturity gate must be non-causal")
    for key in [
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ]:
        if gate.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if gate.get("summary", {}).get("causal_ready_terms"):
        raise ValueError("no extracted monitor term should be causal-ready")
    for item in gate.get("term_maturity") or []:
        if item.get("causal_use_blocked") is not True:
            raise ValueError("term causal use must remain blocked")


def render_markdown(gate: dict[str, Any]) -> str:
    summary = gate["summary"]
    lines = [
        "# KRK Strategy Monitor Maturity Gate v0",
        "",
        "This gate classifies extracted monitor terms and missing backlog terms before any runtime or sandbox work. It is non-causal.",
        "",
        "## Status",
        "",
        f"- Term count: `{summary['term_count']}`",
        f"- Maturity status counts: `{summary['maturity_status_counts']}`",
        f"- Backlog priority counts: `{summary['backlog_priority_counts']}`",
        f"- Causal-ready terms: `{summary['causal_ready_terms']}`",
        f"- Strongest internal-terminal candidates: `{summary['strongest_internal_terminal_candidates']}`",
        f"- Broad context terms: `{summary['broad_context_terms']}`",
        f"- Recommended next step: `{summary['recommended_next_step']}`",
        f"- Runtime behavior changed: `{gate['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{gate['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{gate['stage8_training_allowed']}`",
        "",
        "## Extracted Term Maturity",
        "",
    ]
    for item in gate["term_maturity"]:
        lines.extend(
            [
                f"### {item['term']}",
                "",
                f"- Maturity status: `{item['maturity_status']}`",
                f"- Support: `{item['support_count']}/{item['total_record_count']}`",
                f"- Result distribution: `{item['mate_max_plies_unknown_distribution']}`",
                f"- Source-stage distribution: `{item['source_stage_distribution']}`",
                f"- Stage7 support: `{item['stage7_support_count']}`",
                f"- Success precision: `{item['success_precision']}`",
                f"- Failure precision: `{item['failure_precision']}`",
                f"- Shape: `{item['shape']}`",
                f"- Use as: `{item['use_as']}`",
                f"- Required companion terms: `{item['required_companion_terms']}`",
                f"- Causal use blocked: `{item['causal_use_blocked']}`",
                f"- Rationale: {item['rationale']}",
                "",
            ]
        )
    lines.extend(["## Monitor Class Maturity", ""])
    for item in gate["monitor_class_maturity"]:
        lines.append(
            f"- `{item['monitor_type']}`: maturity=`{item['maturity_status']}`, outcomes=`{item['outcome_distribution']}`, failure_precision=`{item['failure_precision']}`"
        )
    lines.extend(["", "## Backlog Missing Extraction", ""])
    for item in gate["backlog_missing_extraction"]:
        lines.append(f"- `{item['term']}`: priority=`{item['priority']}`, maturity=`{item['maturity_status']}`")
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            "`post_plan_stagnation` and `local_provider_competition_failed` are the strongest internal-monitor candidates, but they remain non-causal and sparse. Broad terms remain context features only. Missing phase-boundary terms remain backlog, not immediate runtime work.",
            "",
            "No runtime terminal, causal affordance, runtime arbiter, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, topology mutation, or monitor-to-provider routing is authorized.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-root", type=Path, default=Path("reports/strategy_arbitration"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    gate = build_gate(args.report_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(gate), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(gate, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
