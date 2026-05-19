#!/usr/bin/env python3
"""Propose non-causal KRK strategy terminal/affordance candidates.

This follows the `missing_feature_first` decision gate. It produces candidate
records and a compact separability audit from existing dataset/probe artifacts.
It does not add terminals to runtime, train, route, mutate topology, promote
Stage 7, or train Stage 8.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _result_bucket(record: dict[str, Any]) -> str:
    label = record.get("result_label") or {}
    result = label.get("playout_result")
    if result is None:
        result = label.get("current_graph_h40")
    if result is None and isinstance(label.get("closed_loop_capsule"), dict):
        result = label["closed_loop_capsule"].get("result")
    return str(result) if result is not None else "unknown"


def _has_provider(record: dict[str, Any], provider: str) -> bool:
    return any(frame.get("provider_id") == provider for frame in record.get("strategy_proposals") or [])


def _has_active(record: dict[str, Any], term: str) -> bool:
    context = record.get("terminal_space_context") or {}
    return term in set(context.get("active_terminal_terms") or [])


def _candidate_specs() -> list[dict[str, Any]]:
    return [
        {
            "candidate_id": "cand.krk.strategy.edge_net_affordance.v0",
            "candidate_type": "terminal_affordance_refinement",
            "target_concept": "edge_net_affordance",
            "suggested_terms": [
                "black_king_edge_bucket == at_edge",
                "edge_net_pressure_proxy",
                "edge_trap_shape_available",
                "corner_net_pressure_proxy",
                "rook_safe",
            ],
            "predicate": lambda record: bool((record.get("terminal_space_context") or {}).get("edge_net_pressure_proxy"))
            or (record.get("terminal_space_context") or {}).get("black_king_edge_bucket") == "at_edge",
            "tests_hypotheses": ["strategy_arbitration_phase_boundary", "missing_feature_ontology"],
        },
        {
            "candidate_id": "cand.krk.strategy.king_support_conversion_affordance.v0",
            "candidate_type": "terminal_affordance_refinement",
            "target_concept": "king_support_conversion_affordance",
            "suggested_terms": [
                "white_king_support_available",
                "white_king_can_improve_support",
                "king_support_improvement_move_exists",
                "rook_safe",
            ],
            "predicate": lambda record: bool((record.get("terminal_space_context") or {}).get("white_king_support_available"))
            or bool((record.get("terminal_space_context") or {}).get("white_king_can_improve_support")),
            "tests_hypotheses": ["strategy_arbitration_phase_boundary", "training_objective_model_expression"],
        },
        {
            "candidate_id": "cand.krk.strategy.box_shrink_exit_condition.v0",
            "candidate_type": "terminal_affordance_refinement",
            "target_concept": "box_shrink_exit_condition",
            "suggested_terms": [
                "box_area_relevance == low",
                "black_king_edge_bucket == at_edge",
                "edge_net_pressure_proxy",
                "mate_basin_readiness",
            ],
            "predicate": lambda record: (record.get("terminal_space_context") or {}).get("box_area_relevance") == "low"
            or (record.get("terminal_space_context") or {}).get("black_king_edge_bucket") == "at_edge",
            "tests_hypotheses": ["bad_curriculum_boundary", "strategy_arbitration_phase_boundary"],
        },
        {
            "candidate_id": "cand.krk.strategy.phase_boundary_near_edge.v0",
            "candidate_type": "terminal_affordance_refinement",
            "target_concept": "phase_boundary_near_edge",
            "suggested_terms": [
                "black_king_edge_bucket in {at_edge, near_edge}",
                "box_area_relevance in {low, medium}",
                "edge_net_pressure_proxy or fence_exists",
            ],
            "predicate": lambda record: (record.get("terminal_space_context") or {}).get("black_king_edge_bucket")
            in {"at_edge", "near_edge"},
            "tests_hypotheses": ["bad_curriculum_boundary", "missing_feature_ontology"],
        },
        {
            "candidate_id": "cand.krk.strategy.fence_or_cut_repair_affordance.v0",
            "candidate_type": "terminal_affordance_refinement",
            "target_concept": "fence_or_cut_repair_affordance",
            "suggested_terms": [
                "fence_exists",
                "not fence_stable",
                "not cut_stable",
                "rook_safe",
            ],
            "predicate": lambda record: bool((record.get("terminal_space_context") or {}).get("fence_exists"))
            and not bool((record.get("terminal_space_context") or {}).get("fence_stable")),
            "tests_hypotheses": ["strategy_arbitration_phase_boundary", "continuation_capacity"],
        },
        {
            "candidate_id": "cand.krk.strategy.plan_selection_needed.v0",
            "candidate_type": "terminal_affordance_refinement",
            "target_concept": "plan_selection_needed",
            "suggested_terms": [
                "stage7 residual",
                "no visible heuristic hit",
                "post_box continuation / capsule context",
                "current_graph_h40 == max_plies",
            ],
            "predicate": lambda record: record.get("source_stage") == "stage7"
            and _result_bucket(record) in {"max_plies", "unknown"},
            "tests_hypotheses": ["training_objective_model_expression", "continuation_capacity"],
        },
    ]


def _candidate_record(spec: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    predicate: Callable[[dict[str, Any]], bool] = spec["predicate"]
    matching = [record for record in records if predicate(record)]
    by_result = Counter(_result_bucket(record) for record in matching)
    by_stage = Counter(str(record.get("source_stage")) for record in matching)
    stage7_hypotheses = Counter(
        label
        for record in matching
        if record.get("source_stage") == "stage7"
        for label in record.get("hypothesis_labels") or []
    )
    provider_counts = Counter(
        str(frame.get("provider_id"))
        for record in matching
        for frame in record.get("strategy_proposals") or []
        if frame.get("provider_id")
    )
    return {
        "schema_version": "structural_candidate.v1",
        "candidate_id": spec["candidate_id"],
        "candidate_type": spec["candidate_type"],
        "source_monitor_script": "growth.monitor.krk_strategy_arbitration_missing_feature",
        "source_terms": spec["suggested_terms"],
        "trigger_failure_classes": sorted(stage7_hypotheses),
        "target_skill": "krk.strategy_arbitration",
        "parent_skill": "krk",
        "proposed_change": {
            "kind": "visible_terminal_affordance_audit",
            "target_concept": spec["target_concept"],
            "suggested_terms": spec["suggested_terms"],
            "tests_hypotheses": spec["tests_hypotheses"],
        },
        "evidence_artifacts": [
            "reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json",
            "reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.json",
            "reports/strategy_arbitration/stage7_challenge_set_manifest.json",
        ],
        "separability_evidence": {
            "matching_record_count": len(matching),
            "result_counts": dict(by_result),
            "source_stage_counts": dict(by_stage),
            "provider_counts": dict(provider_counts),
            "sample_state_ids": [record.get("state_id") for record in matching[:8]],
        },
        "promotion_status": "proposed",
        "causal_status": "non_causal",
        "credit": 0.0,
    }


def build_audit(report_root: Path) -> dict[str, Any]:
    dataset_path = report_root / "krk_strategy_arbitration_dataset_v0.json"
    probe_path = report_root / "krk_strategy_arbitration_probe_v0.json"
    manifest_path = report_root / "stage7_challenge_set_manifest.json"
    dataset = _load_json(dataset_path)
    probe = _load_json(probe_path)
    manifest = _load_json(manifest_path)
    records = [record for record in dataset.get("records") or [] if isinstance(record, dict)]
    candidates = [_candidate_record(spec, records) for spec in _candidate_specs()]

    audit = {
        "schema_version": "krk_strategy_missing_feature_audit.v0",
        "causal_status": "non_causal_audit",
        "runtime_behavior_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_decision_status": (probe.get("decision") or {}).get("status"),
        "challenge_family_count": (manifest.get("summary") or {}).get("challenge_family_count"),
        "dataset_summary": dataset.get("summary"),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "recommended_next_step": "stop_for_architecture_review_before_any_terminal_or_affordance_runtime_sandbox",
        "blocked_next_steps": [
            "implement_runtime_arbiter",
            "add_causal_terminal",
            "add_stage7_repair",
            "train_stage8",
            "promote_stage7",
            "use_runtime_dtm_or_tablebase",
            "mutate_topology_during_gameplay",
        ],
    }
    validate_audit(audit)
    return audit


def validate_audit(audit: dict[str, Any]) -> None:
    if audit.get("schema_version") != "krk_strategy_missing_feature_audit.v0":
        raise ValueError("unexpected audit schema")
    if audit.get("causal_status") != "non_causal_audit":
        raise ValueError("audit must be non-causal")
    if audit.get("runtime_behavior_changed") is not False:
        raise ValueError("audit must not change runtime behavior")
    if audit.get("runtime_dtm_or_tablebase_lookup") is not False:
        raise ValueError("audit must not use runtime DTM/tablebase")
    if audit.get("stage7_promotion_allowed") is not False or audit.get("stage8_training_allowed") is not False:
        raise ValueError("Stage 7 promotion and Stage 8 training must remain blocked")
    for candidate in audit.get("candidates") or []:
        if candidate.get("causal_status") != "non_causal":
            raise ValueError("candidate must be non-causal")
        if candidate.get("promotion_status") != "proposed":
            raise ValueError("candidate must remain proposed")


def render_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# KRK Strategy Missing-Feature Candidate Audit",
        "",
        "This audit is non-causal. It proposes terminal/affordance candidates after the `missing_feature_first` decision gate, but implements none of them.",
        "",
        "## Status",
        "",
        f"- Source decision: `{audit['source_decision_status']}`",
        f"- Candidate count: `{audit['candidate_count']}`",
        f"- Recommended next step: {audit['recommended_next_step']}",
        f"- Stage 7 promotion allowed: `{audit['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{audit['stage8_training_allowed']}`",
        "",
        "## Candidates",
        "",
    ]
    for candidate in audit["candidates"]:
        evidence = candidate["separability_evidence"]
        change = candidate["proposed_change"]
        lines.extend(
            [
                f"### {candidate['candidate_id']}",
                "",
                f"- Target concept: `{change['target_concept']}`",
                f"- Suggested terms: `{change['suggested_terms']}`",
                f"- Tests hypotheses: `{change['tests_hypotheses']}`",
                f"- Matching records: `{evidence['matching_record_count']}`",
                f"- Result counts: `{evidence['result_counts']}`",
                f"- Source stage counts: `{evidence['source_stage_counts']}`",
                f"- Promotion status: `{candidate['promotion_status']}`",
                f"- Causal status: `{candidate['causal_status']}`",
                "",
            ]
        )
    lines.extend(["## Blocked Next Steps", ""])
    lines.extend(f"- {item}" for item in audit["blocked_next_steps"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report-root", type=Path, default=Path("reports/strategy_arbitration"))
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    audit = build_audit(args.report_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(audit), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(audit, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
