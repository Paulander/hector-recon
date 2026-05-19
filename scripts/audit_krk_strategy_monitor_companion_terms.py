#!/usr/bin/env python3
"""Audit availability of KRK Strategy Monitor companion terms.

This is a replay-free diagnostic over existing strategy-arbitration artifacts.
It checks whether proposed companion terms are already present as dataset
fields/active terms, have weak proxies, or require new visible extraction. It
does not add runtime terminals, route, train, promote Stage 7, train Stage 8,
use runtime DTM/tablebase, or mutate topology.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


PROXY_TERMS: dict[str, list[str]] = {
    "current_owner": ["active_landmark_label"],
    "successful_next_provider": ["strategy_proposals.known_outcome_label"],
    "safe_check_or_cut_tighten_move_exists": ["safe_check_available", "repair_or_reestablish_cut_available"],
    "draw_risk_absent_after_edge_net_move": ["stalemate_or_draw_risk"],
    "active_landmark_label == box_shrink": ["active_landmark_label"],
    "box_area_no_longer_decision_relevant": ["box_area_relevance"],
    "edge_net_affordance_scoped": ["edge_net_pressure_proxy", "black_king_edge_bucket"],
    "validated_handoff_target_available": ["strategy_proposals.known_outcome_label"],
    "repair_or_reestablish_cut_available": ["repair_or_reestablish_cut_available"],
    "safe_repair_move_exists": ["repair_or_reestablish_cut_available"],
    "rook_safe_after_repair": ["rook_safe"],
    "box_area_not_expanded_after_reply": ["box_area_relevance"],
    "plan_capsule_context": ["role_capsule_context"],
    "local_provider_competition_failed": ["result_label.current_graph_h40", "strategy_proposals"],
    "selected_provider_closed_loop_failed": ["result_label.closed_loop_capsule"],
    "single_move_affordance_insufficient": ["hypothesis_labels"],
    "growth_pressure_repeated_family": ["hypothesis_labels"],
    "king_support_improvement_move_exists": ["king_support_improvement_move_exists"],
    "king_support_needed_for_current_phase": ["white_king_support_available", "black_king_edge_bucket"],
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _context(record: dict[str, Any]) -> dict[str, Any]:
    context = record.get("terminal_space_context")
    return context if isinstance(context, dict) else {}


def _active_terms(record: dict[str, Any]) -> set[str]:
    return set(_context(record).get("active_terminal_terms") or [])


def _has_path(record: dict[str, Any], path: str) -> bool:
    if path == "active_landmark_label":
        return record.get("active_landmark_label") is not None
    if path == "role_capsule_context":
        return bool(record.get("role_capsule_context"))
    if path == "strategy_proposals":
        return bool(record.get("strategy_proposals"))
    if path == "strategy_proposals.known_outcome_label":
        return any((frame.get("known_outcome_label") or {}) for frame in record.get("strategy_proposals") or [])
    if path.startswith("result_label."):
        label_key = path.split(".", 1)[1]
        return (record.get("result_label") or {}).get(label_key) is not None
    if path == "hypothesis_labels":
        return bool(record.get("hypothesis_labels"))
    return path in _context(record) or path in _active_terms(record)


def _exact_availability(term: str, records: list[dict[str, Any]]) -> tuple[int, str]:
    if " == " in term:
        key, expected = [part.strip() for part in term.split(" == ", 1)]
        count = sum(1 for record in records if str(record.get(key) or _context(record).get(key)) == expected)
        return count, "expression"
    count = sum(1 for record in records if _has_path(record, term))
    return count, "exact"


def _availability_for_term(term: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    exact_count, exact_kind = _exact_availability(term, records)
    proxy_hits: dict[str, int] = {}
    for proxy in PROXY_TERMS.get(term, []):
        proxy_hits[proxy] = sum(1 for record in records if _has_path(record, proxy))
    proxy_count = max(proxy_hits.values()) if proxy_hits else 0
    if exact_count:
        status = "available_exact" if exact_kind == "exact" else "available_expression"
    elif proxy_count:
        status = "proxy_available"
    else:
        status = "missing_requires_visible_extraction"
    return {
        "term": term,
        "availability_status": status,
        "exact_or_expression_record_count": exact_count,
        "proxy_record_counts": proxy_hits,
        "best_available_record_count": max(exact_count, proxy_count),
    }


def build_audit(report_root: Path) -> dict[str, Any]:
    companion_plan = _load_json(report_root / "krk_strategy_monitor_companion_terms_v0.json")
    dataset = _load_json(report_root / "krk_strategy_arbitration_dataset_v0.json")
    records = [item for item in dataset.get("records") or [] if isinstance(item, dict)]
    audited_sets: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    for companion_set in companion_plan.get("companion_sets") or []:
        term_results = [_availability_for_term(term, records) for term in companion_set.get("candidate_terms") or []]
        local_counts = Counter(item["availability_status"] for item in term_results)
        status_counts.update(local_counts)
        if local_counts["available_exact"] or local_counts["available_expression"]:
            set_status = "partly_available"
        elif local_counts["proxy_available"]:
            set_status = "proxy_only"
        else:
            set_status = "missing"
        audited_sets.append(
            {
                "set_id": companion_set.get("set_id"),
                "target_monitor_types": companion_set.get("target_monitor_types") or [],
                "source_concepts": companion_set.get("source_concepts") or [],
                "set_availability_status": set_status,
                "term_status_counts": dict(local_counts),
                "terms": term_results,
                "causal_status": "non_causal",
            }
        )

    payload = {
        "schema_version": "krk_strategy_monitor_companion_audit.v0",
        "causal_status": "non_causal_audit",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_strategy_monitor_companion_terms_v0.json",
            "reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json",
        ],
        "dataset_record_count": len(records),
        "summary": {
            "companion_set_count": len(audited_sets),
            "term_status_counts": dict(status_counts),
            "all_terms_available_without_new_extraction": status_counts["missing_requires_visible_extraction"] == 0,
            "recommended_next_step": "architecture_review_before_new_visible_extraction",
        },
        "companion_sets": audited_sets,
        "blocked_next_steps": companion_plan.get("blocked_next_steps") or [],
    }
    validate_audit(payload)
    return payload


def validate_audit(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "krk_strategy_monitor_companion_audit.v0":
        raise ValueError("unexpected companion audit schema")
    if payload.get("causal_status") != "non_causal_audit":
        raise ValueError("companion audit must be non-causal")
    for key in [
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ]:
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    for companion_set in payload.get("companion_sets") or []:
        if companion_set.get("causal_status") != "non_causal":
            raise ValueError("companion-set audit must be non-causal")


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy Monitor Companion Audit v0",
        "",
        "This replay-free audit checks whether proposed companion terms are already available in the existing strategy-arbitration dataset, only proxied, or missing.",
        "",
        "## Status",
        "",
        f"- Dataset records: `{payload['dataset_record_count']}`",
        f"- Companion sets: `{summary['companion_set_count']}`",
        f"- Term status counts: `{summary['term_status_counts']}`",
        f"- All terms available without new extraction: `{summary['all_terms_available_without_new_extraction']}`",
        f"- Recommended next step: `{summary['recommended_next_step']}`",
        f"- Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{payload['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{payload['stage8_training_allowed']}`",
        "",
        "## Companion Sets",
        "",
    ]
    for companion_set in payload["companion_sets"]:
        lines.extend(
            [
                f"### {companion_set['set_id']}",
                "",
                f"- Target monitors: `{companion_set['target_monitor_types']}`",
                f"- Source concepts: `{companion_set['source_concepts']}`",
                f"- Availability status: `{companion_set['set_availability_status']}`",
                f"- Term status counts: `{companion_set['term_status_counts']}`",
                "",
                "| Term | Status | Exact/expression count | Proxies |",
                "| --- | --- | ---: | --- |",
            ]
        )
        for term in companion_set["terms"]:
            lines.append(
                f"| `{term['term']}` | `{term['availability_status']}` | {term['exact_or_expression_record_count']} | `{term['proxy_record_counts']}` |"
            )
        lines.append("")
    lines.extend(
        [
            "## Conclusion",
            "",
            "Several useful companion concepts have only proxies or are missing from the current dataset. This audit does not justify runtime terminals or sandbox behavior. The next step is architecture review before adding new visible extraction terms.",
            "",
            "No runtime arbiter, causal terminal, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, topology mutation, or monitor-to-provider routing is authorized.",
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

    payload = build_audit(args.report_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
