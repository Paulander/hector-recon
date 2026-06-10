#!/usr/bin/env python3
"""Validate and type non-causal KRK strategy feature candidates.

This consumes the missing-feature candidate audit and strategy arbitration
dataset. It produces a replay-free typing/separability report only. It does
not add runtime terminals, train, route, promote Stage 7, train Stage 8, or
mutate topology.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any, Callable


CandidatePredicate = Callable[[dict[str, Any]], bool]


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


def _candidate_predicates() -> dict[str, CandidatePredicate]:
    return {
        "edge_net_affordance": lambda record: bool(_context(record).get("edge_net_pressure_proxy"))
        or _context(record).get("black_king_edge_bucket") == "at_edge",
        "king_support_conversion_affordance": lambda record: bool(
            _context(record).get("white_king_support_available")
        )
        or bool(_context(record).get("white_king_can_improve_support")),
        "box_shrink_exit_condition": lambda record: _context(record).get("box_area_relevance") == "low"
        or _context(record).get("black_king_edge_bucket") == "at_edge",
        "phase_boundary_near_edge": lambda record: _context(record).get("black_king_edge_bucket")
        in {"at_edge", "near_edge"},
        "fence_or_cut_repair_affordance": lambda record: bool(_context(record).get("fence_exists"))
        and not bool(_context(record).get("fence_stable")),
        "plan_selection_needed": lambda record: record.get("source_stage") == "stage7"
        and _result_bucket(record) in {"max_plies", "unknown"},
    }


def _candidate_target_concept(candidate: dict[str, Any]) -> str:
    change = candidate.get("proposed_change") or {}
    concept = change.get("target_concept")
    if isinstance(concept, str):
        return concept
    candidate_id = str(candidate.get("candidate_id", ""))
    return candidate_id.rsplit(".", 2)[-2] if "." in candidate_id else candidate_id


def _safe_precision(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return numerator / denominator


def _precision_label(value: float | None) -> str:
    if value is None:
        return "unknown"
    return f"{value:.3f}"


def _stage7_precision(matches: list[dict[str, Any]]) -> dict[str, Any]:
    stage7 = [record for record in matches if record.get("source_stage") == "stage7"]
    counts = Counter(_result_bucket(record) for record in stage7)
    known = counts["mate"] + counts["max_plies"]
    return {
        "matching_record_count": len(stage7),
        "result_distribution": dict(counts),
        "mate_precision": _safe_precision(counts["mate"], known),
        "failure_precision": _safe_precision(counts["max_plies"], known),
        "unknown_count": counts["unknown"],
    }


def _cross_stage_generality(source_counts: Counter[str]) -> dict[str, Any]:
    nonzero_stages = sorted(stage for stage, count in source_counts.items() if count)
    non_stage7_count = sum(count for stage, count in source_counts.items() if stage != "stage7")
    if len(nonzero_stages) <= 1 and source_counts.get("stage7", 0):
        label = "stage7_only"
    elif non_stage7_count >= source_counts.get("stage7", 0) and len(nonzero_stages) >= 3:
        label = "cross_stage_broad"
    elif non_stage7_count > 0:
        label = "cross_stage_limited"
    else:
        label = "insufficient_cross_stage_evidence"
    return {
        "label": label,
        "source_stage_count": len(nonzero_stages),
        "non_stage7_matching_count": non_stage7_count,
    }


def _association(mate_precision: float | None, failure_precision: float | None, known_count: int) -> str:
    if known_count == 0:
        return "unknown"
    if mate_precision is not None and mate_precision >= 0.75:
        return "success"
    if failure_precision is not None and failure_precision >= 0.75:
        return "failure"
    return "both"


def _typing_for_candidate(
    concept: str,
    mate_precision: float | None,
    failure_precision: float | None,
    known_count: int,
    stage7: dict[str, Any],
    generality: dict[str, Any],
) -> tuple[str, str, list[str], list[str], str]:
    suggested_refinements: list[str] = []
    companion_terms: list[str] = []

    if known_count == 0:
        return (
            "needs_more_evidence",
            "non-causal only",
            ["add small h40 labels before typing"],
            ["known outcome label"],
            "no labeled mate/max_plies evidence",
        )

    if concept == "plan_selection_needed":
        return (
            "growth-pressure/internal monitor",
            "non-causal only",
            [
                "separate plan-entry marker from plan-policy quality",
                "add post-plan handoff success/failure companion label",
            ],
            ["plan_capsule_context", "handoff_success_after_plan", "post_plan_stagnation"],
            "stage7-only failure-oriented term; useful as a monitor, not a move-support affordance",
        )

    if concept == "fence_or_cut_repair_affordance" and failure_precision is not None and failure_precision >= 0.7:
        return (
            "risk/failure monitor",
            "sandbox-blocked",
            [
                "split broken-fence detection from safe repair availability",
                "require explicit repair move existence before calling it an affordance",
            ],
            ["repair_or_reestablish_cut_available", "rook_safe_after_repair", "box_area_not_expanded_after_reply"],
            "failure-correlated; currently better as repair-pressure evidence than positive affordance",
        )

    if concept == "box_shrink_exit_condition":
        if mate_precision is not None and 0.35 <= mate_precision <= 0.65:
            return (
                "exit condition",
                "needs-more-evidence",
                [
                    "distinguish box-shrink exit from edge-net success",
                    "add current owner and next-provider success labels",
                ],
                ["active_landmark_label == box_shrink", "edge_net_affordance", "mate_basin_readiness"],
                "mixed success/failure near edge; potential owner-release signal, not provider boost",
            )

    if concept == "phase_boundary_near_edge":
        return (
            "needs refinement / companion terms",
            "sandbox-blocked",
            [
                "add owner-specific phase-boundary labels",
                "pair edge bucket with box relevance and edge-net pressure",
            ],
            ["box_area_relevance", "edge_net_pressure_proxy", "current_owner", "successful_next_provider"],
            "near-edge context is broadly cross-stage and mixed-outcome",
        )

    if concept == "edge_net_affordance":
        if mate_precision is not None and 0.35 <= mate_precision <= 0.65:
            return (
                "needs refinement / companion terms",
                "sandbox-blocked",
                [
                    "separate edge-net pressure from edge-net action availability",
                    "require specific net-tightening or safe checking/cut move existence",
                ],
                ["safe_edge_net_tighten_move_exists", "king_support_conversion_affordance", "draw_risk_absent"],
                "matches successful and failed edge states similarly; not a positive affordance yet",
            )

    if concept == "king_support_conversion_affordance":
        return (
            "too broad / reject",
            "sandbox-blocked",
            [
                "split static support availability from action-relevant support improvement",
                "require move-level king-support improvement or provider ownership label",
            ],
            ["king_support_improvement_move_exists", "white_king_distance_to_enemy_decreases_after_move"],
            "matches nearly all records and is not separable enough as currently defined",
        )

    if mate_precision is not None and mate_precision >= 0.75 and generality["label"] != "stage7_only":
        return (
            "positive affordance",
            "needs-more-evidence",
            ["validate on a larger stratified cross-stage set"],
            ["successful_handoff_label"],
            "high success precision in current sample, but remains non-causal",
        )
    if failure_precision is not None and failure_precision >= 0.7:
        return (
            "risk/failure monitor",
            "non-causal only",
            ["add failure family companion labels"],
            ["failure_class"],
            "failure-correlated in current sample",
        )
    return (
        "needs refinement / companion terms",
        "sandbox-blocked",
        ["add companion terms and rerun separability audit"],
        ["owner_context", "next_provider_success"],
        "mixed or ambiguous evidence",
    )


def _validate_candidate(candidate: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    concept = _candidate_target_concept(candidate)
    predicates = _candidate_predicates()
    predicate = predicates.get(concept)
    if predicate is None:
        raise ValueError(f"no validation predicate for candidate concept: {concept}")

    matches = [record for record in records if predicate(record)]
    result_counts = Counter(_result_bucket(record) for record in matches)
    source_counts = Counter(str(record.get("source_stage")) for record in matches)
    known_count = result_counts["mate"] + result_counts["max_plies"]
    mate_precision = _safe_precision(result_counts["mate"], known_count)
    failure_precision = _safe_precision(result_counts["max_plies"], known_count)
    stage7 = _stage7_precision(matches)
    generality = _cross_stage_generality(source_counts)
    association = _association(mate_precision, failure_precision, known_count)
    feature_type, causal_recommendation, refinements, companion_terms, rationale = _typing_for_candidate(
        concept=concept,
        mate_precision=mate_precision,
        failure_precision=failure_precision,
        known_count=known_count,
        stage7=stage7,
        generality=generality,
    )
    return {
        "candidate_id": candidate.get("candidate_id"),
        "target_concept": concept,
        "candidate_type": candidate.get("candidate_type"),
        "matching_record_count": len(matches),
        "mate_max_plies_unknown_distribution": dict(result_counts),
        "known_outcome_count": known_count,
        "mate_precision": mate_precision,
        "max_plies_failure_precision": failure_precision,
        "source_stage_distribution": dict(source_counts),
        "stage7_only_precision": stage7,
        "cross_stage_generality": generality,
        "association": association,
        "typed_as": feature_type,
        "suggested_refinement_terms": refinements,
        "required_scope_or_companion_terms": companion_terms,
        "causal_recommendation": causal_recommendation,
        "typing_rationale": rationale,
        "sample_state_ids": [record.get("state_id") for record in matches[:8]],
    }


def build_validation(report_root: Path) -> dict[str, Any]:
    candidates_path = report_root / "krk_strategy_missing_feature_candidates.json"
    dataset_path = report_root / "krk_strategy_arbitration_dataset_v0.json"
    probe_path = report_root / "krk_strategy_arbitration_probe_v0.json"
    candidate_audit = _load_json(candidates_path)
    dataset = _load_json(dataset_path)
    probe = _load_json(probe_path)
    candidates = [item for item in candidate_audit.get("candidates") or [] if isinstance(item, dict)]
    records = [item for item in dataset.get("records") or [] if isinstance(item, dict)]
    validations = [_validate_candidate(candidate, records) for candidate in candidates]

    typed_counts = Counter(item["typed_as"] for item in validations)
    causal_counts = Counter(item["causal_recommendation"] for item in validations)
    sandbox_ready = [
        item["candidate_id"]
        for item in validations
        if item["causal_recommendation"] not in {"non-causal only", "sandbox-blocked", "needs-more-evidence"}
    ]

    validation = {
        "schema_version": "krk_feature_candidate_validation.v0",
        "causal_status": "non_causal_validation",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [
            "reports/strategy_arbitration/krk_strategy_missing_feature_candidates.json",
            "reports/strategy_arbitration/krk_strategy_arbitration_dataset_v0.json",
            "reports/strategy_arbitration/krk_strategy_arbitration_probe_v0.json",
        ],
        "source_decision_status": (probe.get("decision") or {}).get("status"),
        "dataset_summary": dataset.get("summary"),
        "summary": {
            "candidate_count": len(validations),
            "typed_counts": dict(typed_counts),
            "causal_recommendation_counts": dict(causal_counts),
            "sandbox_ready_candidate_ids": sandbox_ready,
            "all_candidates_remain_non_causal": True,
        },
        "candidate_validations": validations,
        "overall_conclusion": (
            "No candidate is causal-ready. The current candidates are useful as monitors, exit/handoff "
            "hypotheses, or scoped ontology candidates, but their current predicates are either mixed-outcome, "
            "failure-correlated, Stage7-only, or too broad."
        ),
        "recommended_next_step": "architecture_review_or_refine_companion_terms_before_any_runtime_sandbox",
    }
    validate_validation(validation)
    return validation


def validate_validation(validation: dict[str, Any]) -> None:
    if validation.get("schema_version") != "krk_feature_candidate_validation.v0":
        raise ValueError("unexpected validation schema")
    if validation.get("causal_status") != "non_causal_validation":
        raise ValueError("validation must be non-causal")
    if validation.get("runtime_behavior_changed") is not False:
        raise ValueError("validation must not change runtime behavior")
    if validation.get("runtime_defaults_changed") is not False:
        raise ValueError("validation must not change runtime defaults")
    if validation.get("runtime_dtm_or_tablebase_lookup") is not False:
        raise ValueError("validation must not use runtime DTM/tablebase")
    if validation.get("gameplay_topology_mutation") is not False:
        raise ValueError("validation must not mutate topology")
    if validation.get("stage7_promotion_allowed") is not False:
        raise ValueError("Stage 7 promotion must remain blocked")
    if validation.get("stage8_training_allowed") is not False:
        raise ValueError("Stage 8 training must remain blocked")
    for item in validation.get("candidate_validations") or []:
        if item.get("causal_recommendation") not in {
            "non-causal only",
            "sandbox-blocked",
            "needs-more-evidence",
        }:
            raise ValueError(f"candidate unexpectedly appears sandbox-ready: {item.get('candidate_id')}")


def render_markdown(validation: dict[str, Any]) -> str:
    summary = validation["summary"]
    lines = [
        "# KRK Feature Candidate Validation v0",
        "",
        "This report validates and types the six missing-feature candidates from the KRK strategy-arbitration audit. It is replay-free and non-causal.",
        "",
        "## Status",
        "",
        f"- Source decision: `{validation['source_decision_status']}`",
        f"- Candidate count: `{summary['candidate_count']}`",
        f"- Typed counts: `{summary['typed_counts']}`",
        f"- Causal recommendation counts: `{summary['causal_recommendation_counts']}`",
        f"- Sandbox-ready candidates: `{summary['sandbox_ready_candidate_ids']}`",
        f"- Runtime behavior changed: `{validation['runtime_behavior_changed']}`",
        f"- Stage 7 promotion allowed: `{validation['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{validation['stage8_training_allowed']}`",
        "",
        "## Overall Conclusion",
        "",
        validation["overall_conclusion"],
        "",
        "## Candidate Typing",
        "",
    ]
    for item in validation["candidate_validations"]:
        lines.extend(
            [
                f"### {item['candidate_id']}",
                "",
                f"- Target concept: `{item['target_concept']}`",
                f"- Matching records: `{item['matching_record_count']}`",
                f"- Result distribution: `{item['mate_max_plies_unknown_distribution']}`",
                f"- Mate precision: `{_precision_label(item['mate_precision'])}`",
                f"- Max-plies/failure precision: `{_precision_label(item['max_plies_failure_precision'])}`",
                f"- Source-stage distribution: `{item['source_stage_distribution']}`",
                f"- Stage 7-only precision: `{item['stage7_only_precision']}`",
                f"- Cross-stage generality: `{item['cross_stage_generality']}`",
                f"- Associated with: `{item['association']}`",
                f"- Typed as: `{item['typed_as']}`",
                f"- Causal recommendation: `{item['causal_recommendation']}`",
                f"- Rationale: {item['typing_rationale']}",
                f"- Suggested refinement terms: `{item['suggested_refinement_terms']}`",
                f"- Required scope/companion terms: `{item['required_scope_or_companion_terms']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Next Step",
            "",
            validation["recommended_next_step"],
            "",
            "No runtime arbiter, causal terminal, Stage 7 repair, Stage 8 training, Stage 7 promotion, runtime DTM/tablebase, or topology mutation is authorized by this report.",
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

    validation = build_validation(args.report_root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(validation, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(validation), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(validation, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
