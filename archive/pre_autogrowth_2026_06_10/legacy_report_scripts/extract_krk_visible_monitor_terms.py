#!/usr/bin/env python3
"""Extract non-causal visible KRK monitor terms from existing diagnostics.

The terms produced here are diagnostic evidence only. They are not runtime
TERMINAL nodes, not provider support, not routing rules, and not topology
changes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


TIER1_TERMS = [
    "king_support_improves_after_move",
    "cut_or_fence_restored_after_move",
    "safe_repair_move_exists",
    "box_area_no_longer_decision_relevant",
    "post_plan_stagnation",
    "local_provider_competition_failed",
]


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


def _result_bucket(record: dict[str, Any]) -> str:
    label = record.get("result_label") or {}
    result = label.get("playout_result")
    if result is None:
        result = label.get("current_graph_h40")
    if result is None and isinstance(label.get("closed_loop_capsule"), dict):
        result = label["closed_loop_capsule"].get("result")
    return str(result) if result is not None else "unknown"


def _proposal_terms(record: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    for frame in record.get("strategy_proposals") or []:
        for key in ["source_terms", "move_shape_terms", "post_move_terms", "safety_terms"]:
            terms.update(str(term) for term in frame.get(key) or [])
    return terms


def _has_known_provider_result(record: dict[str, Any], result: str) -> bool:
    for frame in record.get("strategy_proposals") or []:
        label = frame.get("known_outcome_label") or {}
        if label.get("result") == result or label.get("playout_result") == result:
            return True
    return False


def _term_payload(value: bool, source_terms: list[str], confidence: str, scope: str, notes: str) -> dict[str, Any]:
    return {
        "value": value,
        "source_terms": source_terms,
        "confidence": confidence,
        "scope": scope,
        "notes": notes,
        "causal_status": "non_causal",
    }


def _king_support_improves_after_move(record: dict[str, Any]) -> dict[str, Any]:
    active = _active_terms(record)
    proposal_terms = _proposal_terms(record)
    direct_terms = sorted(
        term
        for term in active | proposal_terms
        if "king_support" in term and ("improve" in term or "decrease" in term)
    )
    if direct_terms:
        return _term_payload(
            True,
            direct_terms,
            "extracted_from_existing_candidate_or_context_terms",
            "candidate_move_or_current_state",
            "Action-relevant king-support improvement is present in existing terms.",
        )
    return _term_payload(
        False,
        ["white_king_support_available"] if _context(record).get("white_king_support_available") else [],
        "not_observed",
        "candidate_move_or_current_state",
        "Static support availability alone is not counted as improvement.",
    )


def _cut_or_fence_restored_after_move(record: dict[str, Any]) -> dict[str, Any]:
    proposal_terms = _proposal_terms(record)
    direct_terms = sorted(
        term
        for term in proposal_terms
        if ("cut" in term or "fence" in term) and ("restore" in term or "reestablish" in term or "stabil" in term)
    )
    if direct_terms:
        return _term_payload(
            True,
            direct_terms,
            "extracted_from_candidate_post_move_terms",
            "post_move",
            "Candidate/post-move terms explicitly indicate cut/fence restoration.",
        )
    active = _active_terms(record)
    context = _context(record)
    if "repair_or_reestablish_cut_available" in active and (
        context.get("fence_stable") is False or context.get("cut_stable") is False
    ):
        return _term_payload(
            True,
            ["repair_or_reestablish_cut_available", "not fence_stable/cut_stable"],
            "proxy_from_current_state_repair_availability",
            "current_state",
            "Repair availability exists while cut/fence is unstable; restoration after move is not directly proven.",
        )
    return _term_payload(
        False,
        [],
        "not_observed",
        "post_move",
        "No existing candidate/post-move restoration evidence.",
    )


def _safe_repair_move_exists(record: dict[str, Any]) -> dict[str, Any]:
    active = _active_terms(record)
    context = _context(record)
    has_repair = "repair_or_reestablish_cut_available" in active
    rook_safe = context.get("rook_safe") is True
    draw_risk = context.get("stalemate_or_draw_risk") is True
    value = bool(has_repair and rook_safe and not draw_risk)
    source = []
    if has_repair:
        source.append("repair_or_reestablish_cut_available")
    if rook_safe:
        source.append("rook_safe")
    if draw_risk is not True:
        source.append("not stalemate_or_draw_risk")
    return _term_payload(
        value,
        source,
        "expression_from_current_state_terms",
        "current_state",
        "Bounded diagnostic expression; no worst-reply search.",
    )


def _box_area_no_longer_decision_relevant(record: dict[str, Any]) -> dict[str, Any]:
    context = _context(record)
    edge_bucket = context.get("black_king_edge_bucket")
    box_relevance = context.get("box_area_relevance")
    edge_pressure = bool(context.get("edge_net_pressure_proxy"))
    mate_ready = bool(context.get("mate_basin_readiness"))
    value = bool(edge_bucket in {"at_edge", "near_edge"} and box_relevance in {"low", "medium"} and (edge_pressure or mate_ready))
    source = [
        f"black_king_edge_bucket={edge_bucket}",
        f"box_area_relevance={box_relevance}",
    ]
    if edge_pressure:
        source.append("edge_net_pressure_proxy")
    if mate_ready:
        source.append("mate_basin_readiness")
    return _term_payload(
        value,
        source,
        "expression_from_current_state_terms",
        "current_state",
        "Owner-exit diagnostic only; does not select next provider.",
    )


def _post_plan_stagnation(record: dict[str, Any]) -> dict[str, Any]:
    label = record.get("result_label") or {}
    capsule = label.get("closed_loop_capsule")
    hypotheses = set(record.get("hypothesis_labels") or [])
    if isinstance(capsule, dict) and capsule.get("result") == "max_plies":
        return _term_payload(
            True,
            ["closed_loop_capsule.result=max_plies"],
            "extracted_from_trace_window",
            "trace_window",
            "Closed-loop capsule ownership failed to convert within h40.",
        )
    if {"unresolved_without_new_continuation_policy", "continuation_capacity_candidate"} & hypotheses:
        return _term_payload(
            True,
            sorted({"unresolved_without_new_continuation_policy", "continuation_capacity_candidate"} & hypotheses),
            "proxy_from_failure_family_labels",
            "trace_window",
            "Failure-family labels indicate post-plan or continuation stagnation risk.",
        )
    return _term_payload(False, [], "not_observed", "trace_window", "No post-plan stagnation evidence in current artifacts.")


def _local_provider_competition_failed(record: dict[str, Any]) -> dict[str, Any]:
    result = _result_bucket(record)
    has_alternative_mate = _has_known_provider_result(record, "mate")
    has_strategy_failure_label = bool(
        {"strategy_arbitration_candidate", "already_solved_by_existing_provider_if_arbitrated"}
        & set(record.get("hypothesis_labels") or [])
    )
    value = bool(result == "max_plies" and (has_alternative_mate or has_strategy_failure_label))
    source: list[str] = []
    if result == "max_plies":
        source.append("current_result=max_plies")
    if has_alternative_mate:
        source.append("alternative_provider_known_mate")
    if has_strategy_failure_label:
        source.append("strategy_arbitration_or_forced_success_label")
    return _term_payload(
        value,
        source,
        "expression_from_provider_outcome_evidence",
        "decision_or_family",
        "Non-causal arbitration failure monitor; does not route providers.",
    )


TERM_EXTRACTORS = {
    "king_support_improves_after_move": _king_support_improves_after_move,
    "cut_or_fence_restored_after_move": _cut_or_fence_restored_after_move,
    "safe_repair_move_exists": _safe_repair_move_exists,
    "box_area_no_longer_decision_relevant": _box_area_no_longer_decision_relevant,
    "post_plan_stagnation": _post_plan_stagnation,
    "local_provider_competition_failed": _local_provider_competition_failed,
}


def build_visible_terms(report_root: Path) -> dict[str, Any]:
    dataset = _load_json(report_root / "krk_strategy_arbitration_dataset_v0.json")
    records = [item for item in dataset.get("records") or [] if isinstance(item, dict)]
    term_records: list[dict[str, Any]] = []
    counts: dict[str, Counter[str]] = {term: Counter() for term in TIER1_TERMS}
    scope_counts: Counter[str] = Counter()
    confidence_counts: Counter[str] = Counter()
    for record in records:
        terms: dict[str, dict[str, Any]] = {}
        for term, extractor in TERM_EXTRACTORS.items():
            payload = extractor(record)
            terms[term] = payload
            counts[term][str(payload["value"])] += 1
            scope_counts[payload["scope"]] += 1
            confidence_counts[payload["confidence"]] += 1
        term_records.append(
            {
                "schema_version": "krk_visible_monitor_terms_record.v1",
                "state_id": record.get("state_id"),
                "fen": record.get("fen"),
                "active_landmark_label": record.get("active_landmark_label"),
                "source_stage": record.get("source_stage"),
                "associated_outcome": _result_bucket(record),
                "terms": terms,
                "causal_status": "non_causal",
            }
        )
    result = {
        "schema_version": "krk_visible_monitor_terms.v0",
        "causal_status": "non_causal_diagnostic_terms",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": ["reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json"],
        "summary": {
            "record_count": len(term_records),
            "term_names": TIER1_TERMS,
            "true_false_counts_by_term": {term: dict(counter) for term, counter in counts.items()},
            "scope_counts": dict(scope_counts),
            "confidence_counts": dict(confidence_counts),
        },
        "records": term_records,
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
    validate_visible_terms(result)
    return result


def validate_visible_terms(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "krk_visible_monitor_terms.v0":
        raise ValueError("unexpected visible monitor terms schema")
    if payload.get("causal_status") != "non_causal_diagnostic_terms":
        raise ValueError("visible monitor terms must be non-causal")
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
    for record in payload.get("records") or []:
        if record.get("causal_status") != "non_causal":
            raise ValueError("term records must be non-causal")
        missing = set(TIER1_TERMS) - set(record.get("terms") or {})
        if missing:
            raise ValueError(f"term record missing terms: {sorted(missing)}")
        for term_payload in (record.get("terms") or {}).values():
            if term_payload.get("causal_status") != "non_causal":
                raise ValueError("individual extracted term must be non-causal")


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Visible Monitor Terms v0",
        "",
        "This report extracts Tier 1 diagnostic monitor terms from existing strategy-arbitration artifacts. These terms are non-causal evidence only.",
        "",
        "## Status",
        "",
        f"- Record count: `{summary['record_count']}`",
        f"- Terms: `{summary['term_names']}`",
        f"- True/false counts by term: `{summary['true_false_counts_by_term']}`",
        f"- Scope counts: `{summary['scope_counts']}`",
        f"- Confidence counts: `{summary['confidence_counts']}`",
        f"- Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{payload['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{payload['stage8_training_allowed']}`",
        "",
        "## Term Definitions",
        "",
        "- `king_support_improves_after_move`: candidate/current evidence that support improves, not merely exists.",
        "- `cut_or_fence_restored_after_move`: candidate/post-move or repair-availability evidence that cut/fence can be restored.",
        "- `safe_repair_move_exists`: bounded current-state expression combining repair availability, rook safety, and no known draw risk.",
        "- `box_area_no_longer_decision_relevant`: owner-exit diagnostic when edge/box context suggests box shrink may no longer be the key decision axis.",
        "- `post_plan_stagnation`: trace-window evidence that a plan/capsule/continuation context failed to progress.",
        "- `local_provider_competition_failed`: decision/family evidence that raw local provider competition failed despite alternate conversion evidence.",
        "",
        "## Sample Records",
        "",
    ]
    for record in payload["records"][:8]:
        true_terms = [name for name, item in record["terms"].items() if item["value"]]
        lines.append(
            f"- `{record['state_id']}` stage=`{record['source_stage']}` label=`{record['active_landmark_label']}` "
            f"outcome=`{record['associated_outcome']}` true_terms=`{true_terms}`"
        )
    lines.extend(
        [
            "",
            "## Constraints",
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

    payload = build_visible_terms(args.report_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
