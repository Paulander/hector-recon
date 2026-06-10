#!/usr/bin/env python3
"""Extract non-causal KRK StrategyMonitorRecord evidence.

This is the replay-free follow-up to the KRK Strategy Monitor v0 plan. It reads
existing strategy-arbitration records and feature-candidate validation results,
then emits monitor evidence records. It does not add runtime terminals, route,
train, promote Stage 7, train Stage 8, use runtime DTM/tablebase, or mutate
topology.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


Predicate = Callable[[dict[str, Any]], bool]


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _context(record: dict[str, Any]) -> dict[str, Any]:
    context = record.get("terminal_space_context")
    return context if isinstance(context, dict) else {}


def _result_bucket(record: dict[str, Any]) -> str:
    label = record.get("result_label") or {}
    result = label.get("playout_result")
    if result is None:
        result = label.get("current_graph_h40")
    if result is None and isinstance(label.get("closed_loop_capsule"), dict):
        result = label["closed_loop_capsule"].get("result")
    return str(result) if result is not None else "unknown"


def _candidate_predicates() -> dict[str, Predicate]:
    return {
        "edge_net_affordance": lambda record: bool(_context(record).get("edge_net_pressure_proxy"))
        or _context(record).get("black_king_edge_bucket") == "at_edge",
        "box_shrink_exit_condition": lambda record: _context(record).get("box_area_relevance") == "low"
        or _context(record).get("black_king_edge_bucket") == "at_edge",
        "phase_boundary_near_edge": lambda record: _context(record).get("black_king_edge_bucket")
        in {"at_edge", "near_edge"},
        "fence_or_cut_repair_affordance": lambda record: bool(_context(record).get("fence_exists"))
        and not bool(_context(record).get("fence_stable")),
        "plan_selection_needed": lambda record: record.get("source_stage") == "stage7"
        and _result_bucket(record) in {"max_plies", "unknown"},
    }


def _source_terms_by_concept(candidate_audit: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for candidate in candidate_audit.get("candidates") or []:
        if not isinstance(candidate, dict):
            continue
        change = candidate.get("proposed_change") or {}
        concept = change.get("target_concept")
        if isinstance(concept, str):
            result[concept] = list(candidate.get("source_terms") or change.get("suggested_terms") or [])
    return result


def _monitor_type_for(item: dict[str, Any]) -> str | None:
    concept = item.get("target_concept")
    typed_as = item.get("typed_as")
    if typed_as == "too broad / reject":
        return None
    if concept in {"edge_net_affordance", "phase_boundary_near_edge"}:
        return "PhaseBoundaryMonitor"
    if concept == "box_shrink_exit_condition":
        return "OwnerExitMonitor"
    if concept == "fence_or_cut_repair_affordance":
        return "RepairNeededMonitor"
    if concept == "plan_selection_needed":
        return "PlanSelectionNeededMonitor"
    return None


def _suggested_action_class(monitor_type: str) -> str:
    return {
        "PhaseBoundaryMonitor": "audit_owner_phase",
        "OwnerExitMonitor": "audit_owner_exit",
        "RepairNeededMonitor": "record_repair_pressure",
        "PlanSelectionNeededMonitor": "audit_plan_selection",
        "GrowthPressureMonitor": "record_growth_pressure",
    }[monitor_type]


def _promotion_status(item: dict[str, Any]) -> str:
    if item.get("typed_as") == "growth-pressure/internal monitor":
        return "monitoring_only"
    if item.get("typed_as") in {"risk/failure monitor", "exit condition", "needs refinement / companion terms"}:
        return "proposed"
    return "rejected"


def _confidence(item: dict[str, Any]) -> float:
    typed_as = item.get("typed_as")
    mate = item.get("mate_precision")
    failure = item.get("max_plies_failure_precision")
    if typed_as in {"risk/failure monitor", "growth-pressure/internal monitor"} and isinstance(failure, (int, float)):
        return float(failure)
    if typed_as == "exit condition" and isinstance(mate, (int, float)) and isinstance(failure, (int, float)):
        return min(float(mate), float(failure))
    if typed_as == "needs refinement / companion terms" and isinstance(mate, (int, float)) and isinstance(
        failure, (int, float)
    ):
        return min(float(mate), float(failure))
    return 0.0


def _monitor_definitions(
    validation: dict[str, Any], candidate_audit: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_terms = _source_terms_by_concept(candidate_audit)
    definitions: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for item in validation.get("candidate_validations") or []:
        if not isinstance(item, dict):
            continue
        monitor_type = _monitor_type_for(item)
        record = {
            "candidate_id": item.get("candidate_id"),
            "target_concept": item.get("target_concept"),
            "typed_as": item.get("typed_as"),
            "monitor_type": monitor_type or "RejectedFeatureDefinition",
            "source_terms": source_terms.get(str(item.get("target_concept")), []),
            "missing_terms": item.get("required_scope_or_companion_terms") or [],
            "confidence": _confidence(item),
            "causal_status": "non_causal",
            "promotion_status": _promotion_status(item),
            "notes": item.get("typing_rationale"),
        }
        if monitor_type is None:
            rejected.append(record)
        else:
            definitions.append(record)
    return definitions, rejected


def _monitor_record(definition: dict[str, Any], record: dict[str, Any], index: int) -> dict[str, Any]:
    monitor_type = definition["monitor_type"]
    state_id = str(record.get("state_id"))
    monitor_id = f"monitor.krk.{definition['target_concept']}.{state_id}.{index}"
    return {
        "schema_version": "strategy_monitor_record.v1",
        "monitor_id": monitor_id,
        "monitor_type": monitor_type,
        "source_candidate_id": definition["candidate_id"],
        "active_landmark_label": record.get("active_landmark_label"),
        "state_id": record.get("state_id"),
        "fen": record.get("fen"),
        "source_terms": definition["source_terms"],
        "missing_terms": definition["missing_terms"],
        "confidence": definition["confidence"],
        "associated_outcome": _result_bucket(record),
        "suggested_action_class": _suggested_action_class(monitor_type),
        "causal_status": "non_causal",
        "promotion_status": definition["promotion_status"],
        "notes": definition["notes"],
    }


def build_monitor_records(report_root: Path) -> dict[str, Any]:
    dataset = _load_json(report_root / "krk_strategy_arbitration_dataset_v0.json")
    validation = _load_json(report_root / "krk_feature_candidate_validation_v0.json")
    candidate_audit = _load_json(report_root / "krk_strategy_missing_feature_candidates.json")
    records = [item for item in dataset.get("records") or [] if isinstance(item, dict)]
    definitions, rejected_definitions = _monitor_definitions(validation, candidate_audit)
    predicates = _candidate_predicates()

    monitor_records: list[dict[str, Any]] = []
    for definition in definitions:
        concept = str(definition["target_concept"])
        predicate = predicates.get(concept)
        if predicate is None:
            continue
        for record in records:
            if predicate(record):
                monitor_records.append(_monitor_record(definition, record, len(monitor_records)))

    by_type = Counter(item["monitor_type"] for item in monitor_records)
    by_stage = Counter(str(item.get("active_landmark_label")) for item in monitor_records)
    by_outcome = Counter(str(item.get("associated_outcome")) for item in monitor_records)
    type_outcomes: dict[str, dict[str, int]] = {}
    for item in monitor_records:
        type_outcomes.setdefault(item["monitor_type"], {})
        type_outcomes[item["monitor_type"]][item["associated_outcome"]] = (
            type_outcomes[item["monitor_type"]].get(item["associated_outcome"], 0) + 1
        )

    result = {
        "schema_version": "krk_strategy_monitor_records.v0",
        "causal_status": "non_causal_monitor_extraction",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json",
            "reports/strategy_arbitration/krk_feature_candidate_validation_v0.json",
            "reports/strategy_arbitration/krk_strategy_missing_feature_candidates.json",
            "reports/strategy_arbitration/krk_strategy_monitor_v0_plan.json",
        ],
        "monitor_definitions": definitions,
        "rejected_definitions": rejected_definitions,
        "records": monitor_records,
        "summary": {
            "dataset_record_count": len(records),
            "monitor_definition_count": len(definitions),
            "rejected_definition_count": len(rejected_definitions),
            "monitor_record_count": len(monitor_records),
            "records_by_monitor_type": dict(by_type),
            "records_by_active_landmark_label": dict(by_stage),
            "records_by_associated_outcome": dict(by_outcome),
            "outcomes_by_monitor_type": type_outcomes,
        },
        "answers": {
            "monitor_activations_are_stage7_only": False,
            "repair_and_plan_monitors_are_failure_oriented": True,
            "records_authorize_runtime_behavior": False,
            "next_step": "architecture_review_or_targeted_companion_term_design",
        },
    }
    validate_monitor_records(result)
    return result


def validate_strategy_monitor_record(record: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "monitor_id",
        "monitor_type",
        "source_candidate_id",
        "state_id",
        "source_terms",
        "missing_terms",
        "confidence",
        "associated_outcome",
        "suggested_action_class",
        "causal_status",
        "promotion_status",
    }
    missing = required - set(record)
    if missing:
        raise ValueError(f"missing StrategyMonitorRecord fields: {sorted(missing)}")
    if record["schema_version"] != "strategy_monitor_record.v1":
        raise ValueError("unexpected StrategyMonitorRecord schema")
    if record["causal_status"] != "non_causal":
        raise ValueError("StrategyMonitorRecord must be non-causal")
    if record["monitor_type"] not in {
        "PhaseBoundaryMonitor",
        "OwnerExitMonitor",
        "RepairNeededMonitor",
        "PlanSelectionNeededMonitor",
        "GrowthPressureMonitor",
    }:
        raise ValueError(f"unexpected monitor type: {record['monitor_type']}")


def validate_monitor_records(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "krk_strategy_monitor_records.v0":
        raise ValueError("unexpected monitor extraction schema")
    if payload.get("causal_status") != "non_causal_monitor_extraction":
        raise ValueError("monitor extraction must be non-causal")
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
        validate_strategy_monitor_record(record)


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy Monitor Records v0",
        "",
        "This extraction is replay-free and non-causal. It converts typed feature candidates into StrategyMonitorRecord evidence over existing strategy-arbitration records.",
        "",
        "## Status",
        "",
        f"- Monitor definitions: `{summary['monitor_definition_count']}`",
        f"- Rejected definitions: `{summary['rejected_definition_count']}`",
        f"- Monitor records: `{summary['monitor_record_count']}`",
        f"- Records by monitor type: `{summary['records_by_monitor_type']}`",
        f"- Records by active landmark label: `{summary['records_by_active_landmark_label']}`",
        f"- Records by associated outcome: `{summary['records_by_associated_outcome']}`",
        f"- Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{payload['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{payload['stage8_training_allowed']}`",
        "",
        "## Monitor Definitions",
        "",
    ]
    for definition in payload["monitor_definitions"]:
        lines.extend(
            [
                f"### {definition['target_concept']}",
                "",
                f"- Monitor type: `{definition['monitor_type']}`",
                f"- Candidate: `{definition['candidate_id']}`",
                f"- Promotion status: `{definition['promotion_status']}`",
                f"- Confidence: `{definition['confidence']:.3f}`",
                f"- Source terms: `{definition['source_terms']}`",
                f"- Missing terms: `{definition['missing_terms']}`",
                f"- Notes: {definition['notes']}",
                "",
            ]
        )
    lines.extend(["## Rejected Definitions", ""])
    for definition in payload["rejected_definitions"]:
        lines.extend(
            [
                f"- `{definition['target_concept']}`: `{definition['typed_as']}`; {definition['notes']}",
            ]
        )
    lines.extend(["", "## Outcomes By Monitor Type", ""])
    for monitor_type, outcomes in payload["summary"]["outcomes_by_monitor_type"].items():
        lines.append(f"- `{monitor_type}`: `{outcomes}`")
    lines.extend(
        [
            "",
            "## Answers",
            "",
            f"- Monitor activations are Stage7-only: `{payload['answers']['monitor_activations_are_stage7_only']}`",
            f"- Repair and plan monitors are failure-oriented: `{payload['answers']['repair_and_plan_monitors_are_failure_oriented']}`",
            f"- Records authorize runtime behavior: `{payload['answers']['records_authorize_runtime_behavior']}`",
            f"- Next step: `{payload['answers']['next_step']}`",
            "",
            "No runtime arbiter, causal terminal, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, or topology mutation is authorized by these records.",
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

    payload = build_monitor_records(args.report_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(payload), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
