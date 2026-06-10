#!/usr/bin/env python3
"""Define and validate non-causal KRK InternalTerminalSpec candidates.

This script formalizes internal-terminal candidates from the monitor maturity
gate and validates them replay-free against existing artifacts. It does not add
runtime terminals, route, train, promote Stage 7, train Stage 8, use runtime
DTM/tablebase, or mutate topology.
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


def _term(record: dict[str, Any], name: str) -> bool:
    return bool(((record.get("terms") or {}).get(name) or {}).get("value") is True)


def _record_id(record: dict[str, Any]) -> str:
    return str(record.get("state_id") or record.get("family_id") or "unknown")


def _terminal_specs() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "internal_terminal_spec.v1",
            "terminal_id": "terminal.krk.local_provider_competition_failed",
            "monitor_type": "internal_control_arbitration_failure_monitor",
            "source_monitor_candidates": ["local_provider_competition_failed", "PlanSelectionNeededMonitor"],
            "source_terms": [
                "local_provider_competition_failed",
                "selected provider closed-loop failed",
                "current_graph_h40 == max_plies",
                "alternative provider/candidate conversion evidence",
            ],
            "missing_terms": ["current_owner", "alternative_provider_known_mate", "route_conflict"],
            "intended_scope": "KRK strategy arbitration diagnostics and structural-growth evidence",
            "forbidden_causal_uses": [
                "choose_provider",
                "penalize_provider",
                "boost_plan",
                "mutate_topology",
            ],
            "potential_future_consumers": [
                "GrowthMonitor",
                "StrategyArbiter training dataset",
                "PlanCapsule entry/abort/handoff diagnostics",
                "M3/M4 arbitration-weight evidence after later review",
            ],
            "validation_requirements": [
                "broader cross-stage examples",
                "known alternative conversion evidence",
                "no runtime provider routing",
            ],
            "maturity_status": "internal_terminal_candidate",
            "causal_status": "non_causal",
            "promotion_status": "monitoring_only",
        },
        {
            "schema_version": "internal_terminal_spec.v1",
            "terminal_id": "terminal.krk.post_plan_stagnation",
            "monitor_type": "internal_plan_progress_stagnation_monitor",
            "source_monitor_candidates": ["post_plan_stagnation", "PlanSelectionNeededMonitor"],
            "source_terms": [
                "post_plan_stagnation",
                "plan_capsule_context",
                "max_plies after plan",
                "no progress over owned moves",
            ],
            "missing_terms": ["handoff_success_after_plan", "multi_step_progress_required", "repeated_abstract_state"],
            "intended_scope": "PlanCapsule self-monitoring and strategy monitor datasets",
            "forbidden_causal_uses": [
                "force_plan_exit",
                "force_provider_selection",
                "alter_ttl",
                "mutate_topology",
            ],
            "potential_future_consumers": [
                "PlanCapsule self-monitoring",
                "GrowthMonitor",
                "StrategyMonitor datasets",
            ],
            "validation_requirements": [
                "broader plan/capsule windows",
                "handoff success/failure labels",
                "no runtime TTL changes",
            ],
            "maturity_status": "internal_terminal_candidate",
            "causal_status": "non_causal",
            "promotion_status": "monitoring_only",
        },
        {
            "schema_version": "internal_terminal_spec.v1",
            "terminal_id": "terminal.krk.box_shrink_owner_exit_pressure",
            "monitor_type": "owner_exit_monitor_candidate",
            "source_monitor_candidates": ["box_area_no_longer_decision_relevant", "OwnerExitMonitor"],
            "source_terms": [
                "active_landmark_label == box_shrink",
                "box_area_no_longer_decision_relevant",
                "phase boundary near edge",
                "mate_basin_readiness or edge/fence/king-support context",
            ],
            "missing_terms": ["box_shrink_goal_satisfied", "validated_handoff_target_available"],
            "intended_scope": "box_shrink owner-exit diagnostics",
            "forbidden_causal_uses": [
                "select_next_owner",
                "boost_edge_provider",
                "boost_fence_provider",
                "boost_stage0",
            ],
            "potential_future_consumers": [
                "OwnerExitMonitor",
                "StrategyArbiter training dataset",
                "PlanCapsule handoff diagnostics",
            ],
            "validation_requirements": [
                "next-provider handoff labels",
                "active owner labels",
                "successful owner-exit examples",
            ],
            "maturity_status": "needs_more_evidence",
            "causal_status": "non_causal",
            "promotion_status": "proposed",
        },
        {
            "schema_version": "internal_terminal_spec.v1",
            "terminal_id": "terminal.krk.repair_needed_monitor",
            "monitor_type": "repair_risk_monitor",
            "source_monitor_candidates": ["cut_or_fence_restored_after_move", "RepairNeededMonitor"],
            "source_terms": [
                "fence_or_cut_repair_affordance",
                "cut_or_fence_restored_after_move",
                "repair_or_reestablish_cut_available",
                "safe_repair_move_exists",
            ],
            "missing_terms": ["repair_needed_but_no_safe_repair_available", "box_area_not_expanded_after_reply"],
            "intended_scope": "repair-risk and repair-pressure diagnostics",
            "forbidden_causal_uses": [
                "boost_fence_established",
                "play_repair_move",
                "route_to_provider",
            ],
            "potential_future_consumers": [
                "RepairNeededMonitor",
                "GrowthMonitor",
                "StrategyArbiter training dataset",
            ],
            "validation_requirements": [
                "repair-needed context",
                "safe repair availability",
                "post-repair preservation labels",
            ],
            "maturity_status": "monitoring_only",
            "causal_status": "non_causal",
            "promotion_status": "monitoring_only",
        },
    ]


def validate_internal_terminal_spec(spec: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "terminal_id",
        "monitor_type",
        "source_monitor_candidates",
        "source_terms",
        "missing_terms",
        "intended_scope",
        "forbidden_causal_uses",
        "potential_future_consumers",
        "validation_requirements",
        "maturity_status",
        "causal_status",
        "promotion_status",
    }
    missing = required - set(spec)
    if missing:
        raise ValueError(f"InternalTerminalSpec missing keys: {sorted(missing)}")
    if spec["schema_version"] != "internal_terminal_spec.v1":
        raise ValueError("unexpected InternalTerminalSpec schema")
    if spec["causal_status"] != "non_causal":
        raise ValueError("InternalTerminalSpec must be non-causal")
    if not spec["forbidden_causal_uses"]:
        raise ValueError("InternalTerminalSpec must state forbidden causal uses")


def _predicates() -> dict[str, Predicate]:
    return {
        "terminal.krk.local_provider_competition_failed": lambda record: _term(
            record, "local_provider_competition_failed"
        ),
        "terminal.krk.post_plan_stagnation": lambda record: _term(record, "post_plan_stagnation"),
        "terminal.krk.box_shrink_owner_exit_pressure": lambda record: record.get("active_landmark_label")
        == "box_shrink"
        and _term(record, "box_area_no_longer_decision_relevant"),
        "terminal.krk.repair_needed_monitor": lambda record: _term(record, "cut_or_fence_restored_after_move")
        and _term(record, "safe_repair_move_exists"),
    }


def _precision(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _shape(record_count: int, total: int) -> str:
    if record_count == 0:
        return "absent"
    ratio = record_count / total if total else 0.0
    if ratio >= 0.75:
        return "too_broad"
    if ratio <= 0.25:
        return "too_sparse"
    return "moderate"


def _recommended_maturity(spec: dict[str, Any], record_count: int, total: int, stage_counts: Counter[str]) -> str:
    terminal_id = spec["terminal_id"]
    shape = _shape(record_count, total)
    if terminal_id in {"terminal.krk.local_provider_competition_failed", "terminal.krk.post_plan_stagnation"}:
        return "internal_terminal_candidate" if shape == "too_sparse" else "needs_more_evidence"
    if terminal_id == "terminal.krk.box_shrink_owner_exit_pressure":
        return "monitoring_only" if record_count else "needs_more_evidence"
    if terminal_id == "terminal.krk.repair_needed_monitor":
        return "monitoring_only" if shape != "absent" else "needs_more_evidence"
    return spec["maturity_status"]


def _validation_record(spec: dict[str, Any], record: dict[str, Any]) -> dict[str, Any]:
    terms = record.get("terms") or {}
    source_terms_met = [
        term_name for term_name, term_payload in terms.items() if term_payload.get("value") is True
    ]
    return {
        "schema_version": "internal_terminal_validation_record.v1",
        "terminal_id": spec["terminal_id"],
        "state_id": record.get("state_id"),
        "family_id": record.get("state_id"),
        "active_landmark_label": record.get("active_landmark_label"),
        "source_terms_met": source_terms_met,
        "missing_terms": spec.get("missing_terms") or [],
        "associated_outcome": record.get("associated_outcome") or "unknown",
        "stage": record.get("source_stage"),
        "confidence": "replay_free_existing_artifact",
        "false_positive_risk": "high" if record.get("associated_outcome") == "mate" else "unknown",
        "false_negative_risk": "unknown",
        "notes": "Non-causal validation record; does not authorize runtime behavior.",
    }


def validate_internal_terminal_validation_record(record: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "terminal_id",
        "state_id",
        "family_id",
        "active_landmark_label",
        "source_terms_met",
        "missing_terms",
        "associated_outcome",
        "stage",
        "confidence",
        "false_positive_risk",
        "false_negative_risk",
        "notes",
    }
    missing = required - set(record)
    if missing:
        raise ValueError(f"InternalTerminalValidationRecord missing keys: {sorted(missing)}")
    if record["schema_version"] != "internal_terminal_validation_record.v1":
        raise ValueError("unexpected InternalTerminalValidationRecord schema")


def build_candidates(report_root: Path) -> dict[str, Any]:
    specs = _terminal_specs()
    for spec in specs:
        validate_internal_terminal_spec(spec)
    return {
        "schema_version": "krk_internal_terminal_candidates.v0",
        "causal_status": "non_causal_design",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_strategy_monitor_maturity_gate_v0.json",
            "reports/strategy_arbitration/krk_visible_monitor_terms_v0.json",
        ],
        "specs": specs,
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


def build_validation(report_root: Path, candidates: dict[str, Any] | None = None) -> dict[str, Any]:
    if candidates is None:
        candidates = build_candidates(report_root)
    visible_terms = _load_json(report_root / "krk_visible_monitor_terms_v0.json")
    records = [record for record in visible_terms.get("records") or [] if isinstance(record, dict)]
    predicates = _predicates()
    terminal_validations: list[dict[str, Any]] = []
    validation_records: list[dict[str, Any]] = []
    for spec in candidates["specs"]:
        predicate = predicates[spec["terminal_id"]]
        matches = [record for record in records if predicate(record)]
        result_counts = Counter(str(record.get("associated_outcome") or "unknown") for record in matches)
        stage_counts = Counter(str(record.get("source_stage") or "unknown") for record in matches)
        known = result_counts["mate"] + result_counts["max_plies"]
        shape = _shape(len(matches), len(records))
        recommended_maturity = _recommended_maturity(spec, len(matches), len(records), stage_counts)
        terminal_validation_records = [_validation_record(spec, record) for record in matches]
        for item in terminal_validation_records:
            validate_internal_terminal_validation_record(item)
        validation_records.extend(terminal_validation_records)
        terminal_validations.append(
            {
                "terminal_id": spec["terminal_id"],
                "record_count": len(matches),
                "total_record_count": len(records),
                "stage7_count": stage_counts.get("stage7", 0),
                "stage5_6_4_count": sum(stage_counts.get(stage, 0) for stage in ["stage5", "stage6", "stage4"]),
                "mate_max_plies_unknown_distribution": dict(result_counts),
                "source_stage_distribution": dict(stage_counts),
                "failure_precision": _precision(result_counts["max_plies"], known),
                "success_precision": _precision(result_counts["mate"], known),
                "stage7_only": bool(matches) and set(stage_counts) <= {"stage7"},
                "generalizes_across_stages": sum(1 for count in stage_counts.values() if count) > 1,
                "shape": shape,
                "required_missing_terms": spec["missing_terms"],
                "recommended_maturity_status": recommended_maturity,
                "causal_use_blocked": True,
            }
        )
    validation = {
        "schema_version": "krk_internal_terminal_validation.v0",
        "causal_status": "non_causal_validation",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_internal_terminal_candidates_v0.json",
            "reports/strategy_arbitration/krk_visible_monitor_terms_v0.json",
            "reports/strategy_arbitration/krk_strategy_monitor_maturity_gate_v0.json",
        ],
        "terminal_validations": terminal_validations,
        "validation_records": validation_records,
        "summary": {
            "terminal_count": len(terminal_validations),
            "validation_record_count": len(validation_records),
            "causal_ready_terminals": [],
            "strongest_internal_terminal_candidates": [
                "terminal.krk.local_provider_competition_failed",
                "terminal.krk.post_plan_stagnation",
            ],
            "recommended_next_step": "broader_evidence_collection_or_internal_monitor_design_review",
        },
    }
    validate_validation(validation)
    return validation


def validate_candidates(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "krk_internal_terminal_candidates.v0":
        raise ValueError("unexpected candidate payload schema")
    if payload.get("causal_status") != "non_causal_design":
        raise ValueError("candidate payload must be non-causal")
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
    for spec in payload.get("specs") or []:
        validate_internal_terminal_spec(spec)


def validate_validation(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "krk_internal_terminal_validation.v0":
        raise ValueError("unexpected validation payload schema")
    if payload.get("causal_status") != "non_causal_validation":
        raise ValueError("validation payload must be non-causal")
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
    if payload.get("summary", {}).get("causal_ready_terminals"):
        raise ValueError("no internal terminal should be causal-ready")
    for record in payload.get("validation_records") or []:
        validate_internal_terminal_validation_record(record)


def render_candidates_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Internal Terminal Candidates v0",
        "",
        "This report defines non-causal InternalTerminalSpec candidates. They are design/evidence objects only.",
        "",
        "## Status",
        "",
        f"- Candidate count: `{len(payload['specs'])}`",
        f"- Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{payload['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{payload['stage8_training_allowed']}`",
        "",
        "## Candidates",
        "",
    ]
    for spec in payload["specs"]:
        lines.extend(
            [
                f"### {spec['terminal_id']}",
                "",
                f"- Monitor type: `{spec['monitor_type']}`",
                f"- Maturity status: `{spec['maturity_status']}`",
                f"- Promotion status: `{spec['promotion_status']}`",
                f"- Source monitor candidates: `{spec['source_monitor_candidates']}`",
                f"- Source terms: `{spec['source_terms']}`",
                f"- Missing terms: `{spec['missing_terms']}`",
                f"- Intended scope: {spec['intended_scope']}",
                f"- Forbidden causal uses: `{spec['forbidden_causal_uses']}`",
                f"- Potential future consumers: `{spec['potential_future_consumers']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundaries",
            "",
            "No runtime terminal, causal affordance, runtime arbiter, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, topology mutation, or monitor-to-provider routing is authorized.",
            "",
        ]
    )
    return "\n".join(lines)


def render_validation_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Internal Terminal Validation v0",
        "",
        "This replay-free validation evaluates InternalTerminalSpec candidates against existing visible monitor terms.",
        "",
        "## Status",
        "",
        f"- Terminal count: `{payload['summary']['terminal_count']}`",
        f"- Validation records: `{payload['summary']['validation_record_count']}`",
        f"- Causal-ready terminals: `{payload['summary']['causal_ready_terminals']}`",
        f"- Strongest candidates: `{payload['summary']['strongest_internal_terminal_candidates']}`",
        f"- Recommended next step: `{payload['summary']['recommended_next_step']}`",
        f"- Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{payload['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{payload['stage8_training_allowed']}`",
        "",
        "## Terminal Validation",
        "",
    ]
    for item in payload["terminal_validations"]:
        lines.extend(
            [
                f"### {item['terminal_id']}",
                "",
                f"- Record count: `{item['record_count']}/{item['total_record_count']}`",
                f"- Stage 7 count: `{item['stage7_count']}`",
                f"- Stage 5/6/4 count: `{item['stage5_6_4_count']}`",
                f"- Result distribution: `{item['mate_max_plies_unknown_distribution']}`",
                f"- Failure precision: `{item['failure_precision']}`",
                f"- Success precision: `{item['success_precision']}`",
                f"- Stage7-only: `{item['stage7_only']}`",
                f"- Generalizes across stages: `{item['generalizes_across_stages']}`",
                f"- Shape: `{item['shape']}`",
                f"- Recommended maturity: `{item['recommended_maturity_status']}`",
                f"- Missing terms: `{item['required_missing_terms']}`",
                f"- Causal use blocked: `{item['causal_use_blocked']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Conclusion",
            "",
            "`terminal.krk.local_provider_competition_failed` and `terminal.krk.post_plan_stagnation` remain the strongest internal-terminal candidates, but they are sparse and need broader validation. `box_shrink_owner_exit_pressure` and `repair_needed_monitor` remain monitoring-only / companion-dependent. No runtime use is authorized.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-root", type=Path, default=Path("reports/strategy_arbitration"))
    parser.add_argument("--candidates-json-output", type=Path, required=True)
    parser.add_argument("--candidates-markdown-output", type=Path, required=True)
    parser.add_argument("--validation-json-output", type=Path, required=True)
    parser.add_argument("--validation-markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    candidates = build_candidates(args.report_root)
    validation = build_validation(args.report_root, candidates)
    validate_candidates(candidates)
    validate_validation(validation)
    args.candidates_json_output.parent.mkdir(parents=True, exist_ok=True)
    args.candidates_json_output.write_text(json.dumps(candidates, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.candidates_markdown_output.write_text(render_candidates_markdown(candidates), encoding="utf-8")
    args.validation_json_output.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.validation_markdown_output.write_text(render_validation_markdown(validation), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps({"candidates": candidates, "validation": validation}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
