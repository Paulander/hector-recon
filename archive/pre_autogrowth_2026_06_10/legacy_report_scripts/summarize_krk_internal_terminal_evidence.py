#!/usr/bin/env python3
"""Aggregate non-causal KRK internal-terminal evidence and design review.

This script is replay-free. It summarizes existing monitor and strategy
arbitration artifacts; it does not add runtime terminals, route providers,
train Stage 8, promote Stage 7, use runtime DTM/tablebase, or mutate topology.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable


Predicate = Callable[[dict[str, Any]], bool]


TERMINAL_COMPANION_TERMS = {
    "terminal.krk.local_provider_competition_failed": [
        "current_owner",
        "failed_owner",
        "alternative_provider_known_mate",
        "alternative_provider_known_conversion",
        "route_conflict",
        "selected_owner_failed_h40",
        "forced_alternative_succeeded_h40",
        "provider_score_scale_gap",
    ],
    "terminal.krk.post_plan_stagnation": [
        "plan_id",
        "plan_ttl_expired",
        "plan_owned_move_count",
        "plan_progress_window",
        "handoff_success_after_plan",
        "multi_step_progress_required",
        "repeated_abstract_state",
        "post_plan_max_plies",
        "no_progress_after_owned_window",
    ],
    "terminal.krk.box_shrink_owner_exit_pressure": [
        "box_shrink_goal_satisfied",
        "box_area_relevance_low",
        "black_king_near_edge",
        "edge_net_affordance_high",
        "king_support_affordance_high",
        "validated_handoff_target_available",
        "box_shrink_should_handoff",
        "box_shrink_low_affordance",
    ],
    "terminal.krk.repair_needed_monitor": [
        "repair_needed_but_no_safe_repair_available",
        "safe_repair_move_exists",
        "box_area_not_expanded_after_reply",
        "repair_move_preserves_rook_safety",
        "repair_move_leads_to_conversion",
        "cut_or_fence_broken_after_reply",
    ],
}


TERMINAL_CONSUMER_MAP = {
    "terminal.krk.local_provider_competition_failed": [
        "GrowthMonitor",
        "StrategyArbiter training dataset",
        "PlanCapsule entry/abort/handoff diagnostics",
        "M3/M4 arbitration-weight evidence after later review",
    ],
    "terminal.krk.post_plan_stagnation": [
        "PlanCapsule self-monitoring",
        "GrowthMonitor",
        "StrategyMonitor datasets",
    ],
    "terminal.krk.box_shrink_owner_exit_pressure": [
        "OwnerExitMonitor",
        "StrategyArbiter training dataset",
        "PlanCapsule handoff diagnostics",
    ],
    "terminal.krk.repair_needed_monitor": [
        "RepairNeededMonitor",
        "GrowthMonitor",
        "StrategyArbiter training dataset",
    ],
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return _load_json(path)


def _term(record: dict[str, Any], name: str) -> bool:
    return bool(((record.get("terms") or {}).get(name) or {}).get("value") is True)


def _outcome(record: dict[str, Any]) -> str:
    outcome = record.get("associated_outcome")
    if isinstance(outcome, str) and outcome:
        return outcome
    result_label = record.get("result_label") or {}
    if isinstance(result_label, dict):
        current = result_label.get("current_graph_h40")
        if current:
            return str(current)
        capsule = result_label.get("closed_loop_capsule")
        if isinstance(capsule, dict) and capsule.get("result"):
            return str(capsule["result"])
    return "unknown"


def _state_id(record: dict[str, Any]) -> str:
    return str(record.get("state_id") or record.get("family_id") or "unknown")


def _stage(record: dict[str, Any]) -> str:
    return str(record.get("source_stage") or record.get("stage") or "unknown")


def _active_label(record: dict[str, Any]) -> str:
    return str(record.get("active_landmark_label") or "unknown")


def _known_count(counts: Counter[str]) -> int:
    return int(counts.get("mate", 0)) + int(counts.get("max_plies", 0))


def _precision(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _shape(count: int, total: int) -> str:
    if count <= 0:
        return "absent"
    ratio = count / total if total else 0.0
    if ratio >= 0.75:
        return "overbroad"
    if ratio <= 0.25:
        return "sparse"
    return "moderate"


def _predicates() -> dict[str, Predicate]:
    return {
        "terminal.krk.local_provider_competition_failed": lambda record: _term(
            record, "local_provider_competition_failed"
        ),
        "terminal.krk.post_plan_stagnation": lambda record: _term(record, "post_plan_stagnation"),
        "terminal.krk.box_shrink_owner_exit_pressure": lambda record: _active_label(record) == "box_shrink"
        and _term(record, "box_area_no_longer_decision_relevant"),
        "terminal.krk.repair_needed_monitor": lambda record: _term(record, "cut_or_fence_restored_after_move")
        and _term(record, "safe_repair_move_exists"),
    }


def _relevant_failure_predicates() -> dict[str, Predicate]:
    def labels(record: dict[str, Any]) -> set[str]:
        values = record.get("hypothesis_labels") or record.get("shadow_failure_labels") or []
        return {str(value) for value in values}

    def outcome_failed(record: dict[str, Any]) -> bool:
        return _outcome(record) == "max_plies"

    return {
        "terminal.krk.local_provider_competition_failed": lambda record: outcome_failed(record)
        and bool(
            labels(record)
            & {
                "strategy_arbitration_candidate",
                "already_solved_by_existing_provider_if_arbitrated",
                "phase_boundary_candidate",
            }
        ),
        "terminal.krk.post_plan_stagnation": lambda record: outcome_failed(record)
        and bool(
            labels(record)
            & {
                "continuation_capacity_candidate",
                "training_objective_model_expression_candidate",
                "unresolved_without_new_continuation_policy",
            }
        ),
        "terminal.krk.box_shrink_owner_exit_pressure": lambda record: outcome_failed(record)
        and _active_label(record) == "box_shrink"
        and bool(labels(record) & {"bad_curriculum_boundary_candidate", "phase_boundary_candidate"}),
        "terminal.krk.repair_needed_monitor": lambda record: outcome_failed(record)
        and (
            "fence_or_cut_not_preserved"
            in ((record.get("terminal_space_context") or {}).get("active_terminal_terms") or [])
            or (record.get("terminal_space_context") or {}).get("fence_stable") is False
            or (record.get("terminal_space_context") or {}).get("cut_stable") is False
        ),
    }


def _provider_patterns(records: list[dict[str, Any]], dataset_by_state: dict[str, dict[str, Any]]) -> dict[str, Any]:
    provider_counts: Counter[str] = Counter()
    raw_top_counts: Counter[str] = Counter()
    selected_move_counts: Counter[str] = Counter()
    for record in records:
        dataset_record = dataset_by_state.get(_state_id(record)) or {}
        proposals = dataset_record.get("strategy_proposals") or []
        if proposals:
            raw_top = max(
                (proposal for proposal in proposals if isinstance(proposal, dict)),
                key=lambda proposal: float(proposal.get("raw_score") or 0.0),
                default=None,
            )
            if raw_top:
                raw_top_counts[str(raw_top.get("provider_id") or "unknown")] += 1
        for proposal in proposals:
            if not isinstance(proposal, dict):
                continue
            provider_counts[str(proposal.get("provider_id") or "unknown")] += 1
            move = proposal.get("move_uci")
            if move:
                selected_move_counts[str(move)] += 1
    return {
        "providers_seen": dict(provider_counts),
        "raw_top_provider_counts": dict(raw_top_counts),
        "move_counts": dict(selected_move_counts),
    }


def _examples(records: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    return [
        {
            "state_id": _state_id(record),
            "stage": _stage(record),
            "active_landmark_label": _active_label(record),
            "outcome": _outcome(record),
            "fen": record.get("fen"),
        }
        for record in records[:limit]
    ]


def _stage_from_merge_row(row: dict[str, Any]) -> str:
    sources = (row.get("state_identity") or {}).get("source_artifacts") or []
    if any("stage5" in str(source) for source in sources):
        return "stage5"
    if any("stage6" in str(source) for source in sources):
        return "stage6"
    if any("stage4" in str(source) for source in sources):
        return "stage4"
    return "stage7"


def _merge_rows_to_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for row in rows:
        identity = row.get("state_identity") or {}
        context = row.get("terminal_space_context") or {}
        continuation = row.get("continuation_evidence") or {}
        provider = row.get("strategy_provider_evidence") or {}
        outcome = continuation.get("current_graph_result_h40")
        if not outcome and isinstance(continuation.get("closed_loop_capsule_result"), dict):
            outcome = continuation["closed_loop_capsule_result"].get("result")
        result.append(
            {
                "state_id": identity.get("state_signature"),
                "fen": identity.get("post_reply_fen"),
                "source_stage": _stage_from_merge_row(row),
                "active_landmark_label": "box_shrink",
                "associated_outcome": outcome or "unknown",
                "hypothesis_labels": row.get("hypothesis_labels") or [],
                "terminal_space_context": {
                    **context,
                    "active_terminal_terms": context.get("active_terminal_terms") or [],
                },
                "strategy_proposals": provider.get("provider_local_rank_info") or [],
            }
        )
    return result


def _combined_records(report_root: Path, structural_root: Path) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    visible = _load_json(report_root / "krk_visible_monitor_terms_v0.json")
    dataset = _load_json(report_root / "krk_strategy_arbitration_dataset_v0.json")
    merge = _load_optional_json(structural_root / "stage7_evidence_merge_table.json")
    visible_records = [record for record in visible.get("records") or [] if isinstance(record, dict)]
    dataset_records = [record for record in dataset.get("records") or [] if isinstance(record, dict)]
    merge_records = _merge_rows_to_records([row for row in merge.get("rows") or [] if isinstance(row, dict)])
    by_state: dict[str, dict[str, Any]] = {}
    for record in dataset_records:
        by_state[_state_id(record)] = record
    combined: dict[str, dict[str, Any]] = {}
    for record in merge_records + dataset_records + visible_records:
        key = _state_id(record)
        if key == "unknown":
            continue
        current = combined.get(key, {})
        merged = {**current, **record}
        if current.get("terms") and not record.get("terms"):
            merged["terms"] = current["terms"]
        if current.get("strategy_proposals") and not record.get("strategy_proposals"):
            merged["strategy_proposals"] = current["strategy_proposals"]
        combined[key] = merged
    return list(combined.values()), by_state


def _monitor_class_evidence(report_root: Path) -> dict[str, Any]:
    monitor_records = _load_json(report_root / "krk_strategy_monitor_records_v0.json")
    outcomes = (monitor_records.get("summary") or {}).get("outcomes_by_monitor_type") or {}
    records_by_type = (monitor_records.get("summary") or {}).get("records_by_monitor_type") or {}
    result: dict[str, Any] = {}
    for monitor_type, counts in outcomes.items():
        known = int(counts.get("mate", 0)) + int(counts.get("max_plies", 0))
        result[monitor_type] = {
            "record_count": int(records_by_type.get(monitor_type, 0)),
            "outcome_distribution": counts,
            "failure_precision": _precision(int(counts.get("max_plies", 0)), known),
            "success_precision": _precision(int(counts.get("mate", 0)), known),
        }
    return result


def _maturity(
    terminal_id: str,
    fire_count: int,
    total: int,
    result_counts: Counter[str],
    stage_counts: Counter[str],
) -> str:
    if terminal_id in {
        "terminal.krk.local_provider_competition_failed",
        "terminal.krk.post_plan_stagnation",
    }:
        if fire_count <= 0:
            return "needs_more_evidence"
        if set(stage_counts) <= {"stage7"}:
            return "internal_terminal_candidate"
        return "runtime_visible_noncausal_candidate"
    if terminal_id == "terminal.krk.box_shrink_owner_exit_pressure":
        return "monitoring_only" if fire_count else "needs_more_evidence"
    if terminal_id == "terminal.krk.repair_needed_monitor":
        if _shape(fire_count, total) == "overbroad":
            return "monitoring_only"
        if result_counts.get("mate", 0) > 0:
            return "monitoring_only"
        return "needs_more_evidence"
    return "needs_more_evidence"


def build_evidence(report_root: Path, structural_root: Path) -> dict[str, Any]:
    candidates = _load_json(report_root / "krk_internal_terminal_candidates_v0.json")
    validation = _load_json(report_root / "krk_internal_terminal_validation_v0.json")
    combined_records, dataset_by_state = _combined_records(report_root, structural_root)
    predicates = _predicates()
    relevant_predicates = _relevant_failure_predicates()
    validation_by_terminal = {
        item["terminal_id"]: item for item in validation.get("terminal_validations") or []
    }
    terminal_evidence = []
    for spec in candidates.get("specs") or []:
        if not isinstance(spec, dict):
            continue
        terminal_id = str(spec["terminal_id"])
        predicate = predicates[terminal_id]
        relevant_predicate = relevant_predicates[terminal_id]
        firing = [record for record in combined_records if predicate(record)]
        non_firing_relevant = [
            record for record in combined_records if not predicate(record) and relevant_predicate(record)
        ]
        result_counts = Counter(_outcome(record) for record in firing)
        stage_counts = Counter(_stage(record) for record in firing)
        label_counts = Counter(_active_label(record) for record in firing)
        failure_classes: Counter[str] = Counter()
        for record in firing:
            for label in record.get("hypothesis_labels") or []:
                failure_classes[str(label)] += 1
        known = _known_count(result_counts)
        fire_count = len(firing)
        total_count = len(combined_records)
        stage7_count = int(stage_counts.get("stage7", 0))
        false_positives = [record for record in firing if _outcome(record) == "mate"]
        terminal_evidence.append(
            {
                "terminal_id": terminal_id,
                "monitor_type": spec.get("monitor_type"),
                "fire_count": fire_count,
                "total_record_count": total_count,
                "success_count": int(result_counts.get("mate", 0)),
                "failure_count": int(result_counts.get("max_plies", 0)),
                "unknown_count": int(result_counts.get("unknown", 0)),
                "failure_precision": _precision(int(result_counts.get("max_plies", 0)), known),
                "success_precision": _precision(int(result_counts.get("mate", 0)), known),
                "stage_distribution": dict(stage_counts),
                "label_scope_distribution": dict(label_counts),
                "stage7_only": bool(firing) and set(stage_counts) <= {"stage7"},
                "stage7_fire_count": stage7_count,
                "cross_stage_fire_count": fire_count - stage7_count,
                "associated_failure_classes": dict(failure_classes),
                "associated_provider_strategy_patterns": _provider_patterns(firing, dataset_by_state),
                "sparsity_or_overbreadth": _shape(fire_count, total_count),
                "false_positive_count": len(false_positives),
                "false_positive_examples": _examples(false_positives, 3),
                "false_negative_where_inferable_count": len(non_firing_relevant),
                "false_negative_examples": _examples(non_firing_relevant, 5),
                "examples_of_firing_states": _examples(firing, 5),
                "examples_of_non_firing_relevant_failure_states": _examples(non_firing_relevant, 5),
                "missing_companion_terms": TERMINAL_COMPANION_TERMS[terminal_id],
                "candidate_maturity": _maturity(
                    terminal_id, fire_count, total_count, result_counts, stage_counts
                ),
                "previous_v0_validation": validation_by_terminal.get(terminal_id, {}),
                "causal_ready": False,
            }
        )
    evidence = {
        "schema_version": "krk_internal_terminal_evidence.v1",
        "causal_status": "non_causal_evidence",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_internal_terminal_candidates_v0.json",
            "reports/strategy_arbitration/krk_internal_terminal_validation_v0.json",
            "reports/strategy_arbitration/krk_visible_monitor_terms_v0.json",
            "reports/strategy_arbitration/krk_strategy_monitor_records_v0.json",
            "reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json",
            "reports/structural_candidates/stage7_neutral_diagnostic_matrix.json",
            "reports/structural_candidates/stage7_evidence_merge_table.json",
        ],
        "terminal_evidence": terminal_evidence,
        "monitor_class_evidence": _monitor_class_evidence(report_root),
        "summary": {
            "combined_record_count": len(combined_records),
            "terminal_count": len(terminal_evidence),
            "causal_ready_terminals": [],
            "strongest_internal_terminal_candidates": [
                item["terminal_id"]
                for item in terminal_evidence
                if item["candidate_maturity"] in {"internal_terminal_candidate", "runtime_visible_noncausal_candidate"}
            ],
            "stage7_only_candidates": [
                item["terminal_id"] for item in terminal_evidence if item["stage7_only"]
            ],
            "monitoring_only_candidates": [
                item["terminal_id"] for item in terminal_evidence if item["candidate_maturity"] == "monitoring_only"
            ],
            "recommended_next_step": "internal_terminal_design_review_before_any_runtime_work",
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
    validate_evidence(evidence)
    return evidence


def build_design_review(evidence: dict[str, Any]) -> dict[str, Any]:
    terminal_by_id = {item["terminal_id"]: item for item in evidence["terminal_evidence"]}
    closest = [
        "terminal.krk.local_provider_competition_failed",
        "terminal.krk.post_plan_stagnation",
    ]
    review_items = {
        "closest_to_runtime_visible_noncausal_promotion": [
            {
                "terminal_id": terminal_id,
                "reason": "Semantically direct internal-control signal, but currently sparse and Stage7-only; promotion would require broader validation and a defined non-causal consumer.",
                "causal_ready": False,
            }
            for terminal_id in closest
            if terminal_id in terminal_by_id
        ],
        "too_sparse": [
            item["terminal_id"]
            for item in evidence["terminal_evidence"]
            if item["sparsity_or_overbreadth"] == "sparse"
        ],
        "too_broad_or_noisy": [
            item["terminal_id"]
            for item in evidence["terminal_evidence"]
            if item["sparsity_or_overbreadth"] == "overbroad" or item["success_count"] > 0
        ],
        "merge_split_rename": [
            {
                "terminal_id": "terminal.krk.local_provider_competition_failed",
                "recommendation": "keep name, later split selected-owner failure from forced-alternative success if more evidence appears",
            },
            {
                "terminal_id": "terminal.krk.post_plan_stagnation",
                "recommendation": "keep name, later split TTL expiry, no-progress, and failed-handoff variants",
            },
            {
                "terminal_id": "terminal.krk.box_shrink_owner_exit_pressure",
                "recommendation": "keep as owner-exit pressure, but require companion handoff-target terms before any promotion",
            },
            {
                "terminal_id": "terminal.krk.repair_needed_monitor",
                "recommendation": "split repair-needed risk from repair-available progress; current definition is too noisy for control",
            },
        ],
        "krk_specific_vs_domain_general": {
            "domain_general_pattern": [
                "terminal.krk.local_provider_competition_failed",
                "terminal.krk.post_plan_stagnation",
            ],
            "krk_specific_instantiation": [
                "terminal.krk.box_shrink_owner_exit_pressure",
                "terminal.krk.repair_needed_monitor",
            ],
        },
    }
    consumers = {}
    for terminal_id, consumer_list in TERMINAL_CONSUMER_MAP.items():
        consumers[terminal_id] = {
            "useful_for": consumer_list,
            "m3_m4_note": "May become M3/M4 arbitration-weight evidence only after later review; this slice changes no M3/M4 inputs.",
        }
    checklist = [
        "fires_on_enough_examples",
        "validated_across_multiple_seeds_or_artifacts",
        "false_positive_rate_measured",
        "false_negative_examples_reviewed",
        "companion_terms_defined",
        "source_terms_are_graph_visible",
        "consumer_is_defined",
        "sandbox_default_off_test_exists",
        "guardrails_pass",
        "no_hidden_controller",
        "no_direct_provider_routing_from_monitor",
        "no_topology_mutation_during_gameplay",
    ]
    review = {
        "schema_version": "krk_internal_terminal_design_review.v1",
        "causal_status": "non_causal_design_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_internal_terminal_evidence_v1.json",
        ],
        "answers": {
            "closest_to_runtime_visible_noncausal_promotion": review_items[
                "closest_to_runtime_visible_noncausal_promotion"
            ],
            "too_sparse": review_items["too_sparse"],
            "too_broad_or_noisy": review_items["too_broad_or_noisy"],
            "merge_split_or_rename": review_items["merge_split_rename"],
            "krk_specific_vs_domain_general": review_items["krk_specific_vs_domain_general"],
            "consumer_fit": consumers,
            "future_causal_uses_forbidden": [
                "choosing providers directly",
                "penalizing or boosting providers",
                "forcing plan exit or altering TTL",
                "routing to a repair move",
                "mutating topology during gameplay",
                "feeding M4 edge deltas without explicit later review",
            ],
            "safest_next_evidence_step": "Broaden replay-free evidence by exporting the same non-causal monitor fields from future Stage 5/6/4/7 validations; do not add runtime terminals.",
        },
        "runtime_promotion_readiness_checklist": checklist,
        "terminal_readiness": [
            {
                "terminal_id": item["terminal_id"],
                "maturity": item["candidate_maturity"],
                "causal_ready": False,
                "blocking_gaps": item["missing_companion_terms"],
                "evidence_summary": {
                    "fire_count": item["fire_count"],
                    "failure_precision": item["failure_precision"],
                    "success_precision": item["success_precision"],
                    "stage7_only": item["stage7_only"],
                    "shape": item["sparsity_or_overbreadth"],
                },
            }
            for item in evidence["terminal_evidence"]
        ],
        "summary": {
            "causal_ready_terminals": [],
            "main_conclusion": "Internal terminals are useful monitor/evidence objects, not runtime controls. local_provider_competition_failed and post_plan_stagnation are the strongest but remain sparse and Stage7-only; repair_needed_monitor is broader but noisy; box_shrink_owner_exit_pressure needs companion handoff-target evidence.",
            "recommended_next_step": "broader_replay_free_monitor_evidence_collection_or_review",
        },
        "blocked_next_steps": evidence["blocked_next_steps"],
    }
    validate_design_review(review)
    return review


def validate_evidence(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "krk_internal_terminal_evidence.v1":
        raise ValueError("unexpected evidence schema")
    if payload.get("causal_status") != "non_causal_evidence":
        raise ValueError("evidence must be non-causal")
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
        raise ValueError("no terminal may be causal-ready in this slice")
    for item in payload.get("terminal_evidence") or []:
        if item.get("causal_ready") is not False:
            raise ValueError("terminal evidence must keep causal_ready false")
        for required in [
            "terminal_id",
            "fire_count",
            "failure_count",
            "stage_distribution",
            "missing_companion_terms",
            "candidate_maturity",
        ]:
            if required not in item:
                raise ValueError(f"terminal evidence missing {required}")


def validate_design_review(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "krk_internal_terminal_design_review.v1":
        raise ValueError("unexpected design review schema")
    if payload.get("causal_status") != "non_causal_design_review":
        raise ValueError("design review must be non-causal")
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
        raise ValueError("no terminal may be causal-ready in design review")
    if "no_hidden_controller" not in payload.get("runtime_promotion_readiness_checklist", []):
        raise ValueError("promotion readiness checklist must include no_hidden_controller")
    for item in payload.get("terminal_readiness") or []:
        if item.get("causal_ready") is not False:
            raise ValueError("terminal readiness must keep causal_ready false")


def render_evidence_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Internal Terminal Evidence v1",
        "",
        "This report broadens InternalTerminalSpec evidence replay-free from existing artifacts only. It is evidence-only and does not authorize runtime terminals.",
        "",
        "## Status",
        "",
        f"- Combined records: `{payload['summary']['combined_record_count']}`",
        f"- Terminal count: `{payload['summary']['terminal_count']}`",
        f"- Causal-ready terminals: `{payload['summary']['causal_ready_terminals']}`",
        f"- Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{payload['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{payload['stage8_training_allowed']}`",
        "",
        "## Terminal Evidence",
        "",
    ]
    for item in payload["terminal_evidence"]:
        lines.extend(
            [
                f"### {item['terminal_id']}",
                "",
                f"- Maturity: `{item['candidate_maturity']}`",
                f"- Fires: `{item['fire_count']}/{item['total_record_count']}`",
                f"- Counts: success=`{item['success_count']}`, failure=`{item['failure_count']}`, unknown=`{item['unknown_count']}`",
                f"- Failure precision: `{item['failure_precision']}`",
                f"- Success precision: `{item['success_precision']}`",
                f"- Stage distribution: `{item['stage_distribution']}`",
                f"- Label/scope distribution: `{item['label_scope_distribution']}`",
                f"- Shape: `{item['sparsity_or_overbreadth']}`",
                f"- False positives: `{item['false_positive_count']}`",
                f"- Inferable false negatives: `{item['false_negative_where_inferable_count']}`",
                f"- Missing companion terms: `{item['missing_companion_terms']}`",
                f"- Causal ready: `{item['causal_ready']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Monitor Class Evidence",
            "",
        ]
    )
    for monitor_type, item in payload["monitor_class_evidence"].items():
        lines.extend(
            [
                f"### {monitor_type}",
                "",
                f"- Records: `{item['record_count']}`",
                f"- Outcome distribution: `{item['outcome_distribution']}`",
                f"- Failure precision: `{item['failure_precision']}`",
                f"- Success precision: `{item['success_precision']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Conclusion",
            "",
            "`local_provider_competition_failed` and `post_plan_stagnation` remain the strongest internal-terminal candidates, but they are sparse and Stage7-only. `repair_needed_monitor` has broader evidence but is noisy. `box_shrink_owner_exit_pressure` remains monitoring-only and needs companion handoff-target terms. No terminal is causal-ready.",
            "",
        ]
    )
    return "\n".join(lines)


def render_design_review_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Internal Terminal Design Review v1",
        "",
        "This review interprets non-causal internal-terminal evidence. It does not implement runtime terminals or authorize causal use.",
        "",
        "## Status",
        "",
        f"- Causal-ready terminals: `{payload['summary']['causal_ready_terminals']}`",
        f"- Runtime behavior changed: `{payload['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{payload['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{payload['stage8_training_allowed']}`",
        "",
        "## Answers",
        "",
        f"- Closest to runtime-visible non-causal promotion: `{[item['terminal_id'] for item in payload['answers']['closest_to_runtime_visible_noncausal_promotion']]}`",
        f"- Too sparse: `{payload['answers']['too_sparse']}`",
        f"- Too broad/noisy: `{payload['answers']['too_broad_or_noisy']}`",
        f"- Domain-general pattern: `{payload['answers']['krk_specific_vs_domain_general']['domain_general_pattern']}`",
        f"- KRK-specific instantiation: `{payload['answers']['krk_specific_vs_domain_general']['krk_specific_instantiation']}`",
        "",
        "## Terminal Readiness",
        "",
    ]
    for item in payload["terminal_readiness"]:
        summary = item["evidence_summary"]
        lines.extend(
            [
                f"### {item['terminal_id']}",
                "",
                f"- Maturity: `{item['maturity']}`",
                f"- Causal ready: `{item['causal_ready']}`",
                f"- Fire count: `{summary['fire_count']}`",
                f"- Failure precision: `{summary['failure_precision']}`",
                f"- Success precision: `{summary['success_precision']}`",
                f"- Stage7-only: `{summary['stage7_only']}`",
                f"- Shape: `{summary['shape']}`",
                f"- Blocking gaps: `{item['blocking_gaps']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Promotion Readiness Checklist",
            "",
        ]
    )
    for item in payload["runtime_promotion_readiness_checklist"]:
        lines.append(f"- `{item}`")
    lines.extend(
        [
            "",
            "## Forbidden Future Causal Uses",
            "",
        ]
    )
    for item in payload["answers"]["future_causal_uses_forbidden"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Conclusion",
            "",
            payload["summary"]["main_conclusion"],
            "",
            f"Recommended next step: `{payload['summary']['recommended_next_step']}`.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-root", type=Path, default=Path("reports/strategy_arbitration"))
    parser.add_argument("--structural-root", type=Path, default=Path("reports/structural_candidates"))
    parser.add_argument("--evidence-json-output", type=Path, required=True)
    parser.add_argument("--evidence-markdown-output", type=Path, required=True)
    parser.add_argument("--review-json-output", type=Path, required=True)
    parser.add_argument("--review-markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    evidence = build_evidence(args.report_root, args.structural_root)
    review = build_design_review(evidence)
    args.evidence_json_output.parent.mkdir(parents=True, exist_ok=True)
    args.evidence_json_output.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.evidence_markdown_output.write_text(render_evidence_markdown(evidence), encoding="utf-8")
    args.review_json_output.write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    args.review_markdown_output.write_text(render_design_review_markdown(review), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps({"evidence": evidence, "review": review}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
