#!/usr/bin/env python3
"""Summarize the Stage 7 training-objective benchmark as a hard decision gate.

This is report-only. It does not implement a runtime repair, promote Stage 7,
train Stage 8, add runtime terminals, use runtime DTM/tablebase, or mutate
topology.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ALLOWED_OUTCOMES = {
    "ranked_pairwise_objective_supports_default_off_sandbox",
    "model_expression_gap_persists_stage7_micro_work_stops",
    "internal_monitor_features_justify_non_causal_runtime_visible_monitor_sandbox",
    "curriculum_boundary_reframe_box_shrink_as_exit_handoff",
    "mixed_evidence_freeze_stage7_known_residual",
}


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _model(benchmark: dict[str, Any], model_id: str) -> dict[str, Any]:
    for model in benchmark.get("models") or []:
        if isinstance(model, dict) and model.get("model_id") == model_id:
            return model
    return {}


def _test_metrics(benchmark: dict[str, Any], model_id: str) -> dict[str, Any]:
    return (_model(benchmark, model_id).get("test") or {}) if _model(benchmark, model_id) else {}


def _decide(benchmark: dict[str, Any]) -> dict[str, Any]:
    decision = benchmark.get("decision") or {}
    candidate_status = decision.get("candidate_status")
    current = _test_metrics(benchmark, "current_learned_post_box_scorer")
    visible = _test_metrics(benchmark, "visible_term_log_odds_scorer")
    ranked = _test_metrics(benchmark, "pairwise_ranked_preference_scorer")
    internal = _test_metrics(benchmark, "internal_monitor_augmented_visible_term_scorer")
    oracle = _test_metrics(benchmark, "oracle_dtm_positive_topk_ceiling")
    benchmark_underpowered = bool((benchmark.get("dataset") or {}).get("benchmark_underpowered"))

    evidence = [
        f"benchmark_status={candidate_status}",
        f"ranked_top1_improvement={decision.get('ranked_top1_improvement_over_current')}",
        f"visible_top1_improvement={decision.get('visible_top1_improvement_over_current')}",
        f"internal_monitor_top1_improvement_over_visible={decision.get('internal_monitor_top1_improvement_over_visible')}",
        f"current_hard_negative_rate={current.get('hard_negative_above_positive_rate')}",
        f"ranked_hard_negative_rate={ranked.get('hard_negative_above_positive_rate')}",
        f"internal_hard_negative_rate={internal.get('hard_negative_above_positive_rate')}",
        f"oracle_top1={oracle.get('top1_dtm_positive_accuracy')}",
    ]

    if candidate_status == "ranked_objective_supported":
        return {
            "selected_outcome": "ranked_pairwise_objective_supports_default_off_sandbox",
            "recommended_action_class": "architecture_review_before_default_off_ranked_sequence_sandbox",
            "rationale": "Ranked objective materially improves offline ranking without worsening hard negatives.",
            "evidence": evidence,
        }
    if candidate_status == "internal_monitor_features_help_offline":
        return {
            "selected_outcome": "internal_monitor_features_justify_non_causal_runtime_visible_monitor_sandbox",
            "recommended_action_class": "architecture_review_before_non_causal_runtime_visible_monitor_sandbox",
            "rationale": "Internal-monitor diagnostic features improve offline ranking without becoming causal terminals.",
            "evidence": evidence,
        }
    if candidate_status == "curriculum_boundary_more_likely":
        return {
            "selected_outcome": "curriculum_boundary_reframe_box_shrink_as_exit_handoff",
            "recommended_action_class": "architecture_review_for_box_shrink_curriculum_boundary",
            "rationale": "Evidence favors reframing box_shrink as exit/handoff evidence rather than a standalone owner.",
            "evidence": evidence,
        }
    if candidate_status == "model_expression_gap_persists":
        return {
            "selected_outcome": "model_expression_gap_persists_stage7_micro_work_stops",
            "recommended_action_class": "stop_stage7_micro_work_pending_architecture_review",
            "rationale": "Simple ranked/pairwise objectives underperform, internal monitor features do not improve the visible baseline, and oracle ceiling remains high.",
            "evidence": evidence,
        }
    if benchmark_underpowered or candidate_status == "data_too_small_for_conclusion":
        return {
            "selected_outcome": "mixed_evidence_freeze_stage7_known_residual",
            "recommended_action_class": "freeze_stage7_as_known_residual_until_review",
            "rationale": "Evidence is too small or mixed to justify another Stage 7 branch.",
            "evidence": evidence,
        }
    return {
        "selected_outcome": "mixed_evidence_freeze_stage7_known_residual",
        "recommended_action_class": "freeze_stage7_as_known_residual_until_review",
        "rationale": "Benchmark does not authorize a runtime sandbox, Stage 7 promotion, Stage 8 training, or another broad diagnostic branch.",
        "evidence": evidence,
    }


def build_gate(benchmark_path: Path) -> dict[str, Any]:
    benchmark = _load_json(benchmark_path)
    selected = _decide(benchmark)
    gate = {
        "schema_version": "stage7_training_objective_decision_gate.v1",
        "causal_status": "non_causal_decision_gate",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "runtime_terminals_added": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(benchmark_path)],
        "allowed_outcomes": sorted(ALLOWED_OUTCOMES),
        "selected_outcome": selected["selected_outcome"],
        "recommended_action_class": selected["recommended_action_class"],
        "rationale": selected["rationale"],
        "supporting_evidence": selected["evidence"],
        "benchmark_decision": benchmark.get("decision") or {},
        "stop_conditions_reaffirmed": [
            "no_runtime_repairs",
            "no_stage7_promotion",
            "no_stage8_training",
            "no_runtime_dtm_or_tablebase",
            "no_gameplay_topology_mutation",
            "no_internal_terminal_causal_use",
            "no_new_broad_diagnostic_branch_without_explicit_review",
        ],
        "blocked_next_steps": [
            "implement_runtime_repair",
            "promote_stage7",
            "train_stage8",
            "make_internal_terminals_causal",
            "add_runtime_terminal_topology",
            "use_runtime_dtm_or_tablebase",
            "mutate_topology_during_gameplay",
            "start_broad_diagnostic_branch_without_review",
        ],
    }
    validate_gate(gate)
    return gate


def validate_gate(gate: dict[str, Any]) -> None:
    if gate.get("schema_version") != "stage7_training_objective_decision_gate.v1":
        raise ValueError("unexpected decision gate schema")
    if gate.get("causal_status") != "non_causal_decision_gate":
        raise ValueError("decision gate must be non-causal")
    if gate.get("selected_outcome") not in ALLOWED_OUTCOMES:
        raise ValueError(f"unexpected selected outcome: {gate.get('selected_outcome')}")
    for key in [
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "runtime_terminals_added",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ]:
        if gate.get(key) is not False:
            raise ValueError(f"{key} must be false")


def render_markdown(gate: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Training-Objective Decision Gate",
        "",
        "This report turns the offline benchmark into a hard decision. It is non-causal and does not implement a runtime repair.",
        "",
        "## Decision",
        "",
        f"- Selected outcome: `{gate['selected_outcome']}`",
        f"- Recommended action class: `{gate['recommended_action_class']}`",
        f"- Rationale: {gate['rationale']}",
        f"- Stage 7 status: `{gate['stage7_status']}`",
        f"- Stage 7 promotion allowed: `{gate['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{gate['stage8_training_allowed']}`",
        "",
        "## Supporting Evidence",
        "",
    ]
    lines.extend(f"- `{item}`" for item in gate["supporting_evidence"])
    lines.extend(
        [
            "",
            "## Stop Conditions Reaffirmed",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in gate["stop_conditions_reaffirmed"])
    lines.extend(
        [
            "",
            "## Blocked Next Steps",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in gate["blocked_next_steps"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--benchmark-path",
        type=Path,
        default=Path("reports/structural_candidates/stage7_training_objective_benchmark.json"),
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    gate = build_gate(args.benchmark_path)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_markdown(gate), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps(gate, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
