#!/usr/bin/env python3
"""Close the Stage 7 benchmark branch after the hard decision gate.

This is documentation/evidence packaging only. It verifies that the offline
benchmark and decision gate are internally consistent, then emits a closure
report and a non-causal architecture design note for future sequence-policy
review. It does not implement runtime behavior, train, promote, or mutate
topology.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


EXPECTED_BENCHMARK_STATUS = "model_expression_gap_persists"
EXPECTED_GATE_OUTCOME = "model_expression_gap_persists_stage7_micro_work_stops"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _model_metric(benchmark: dict[str, Any], model_id: str, metric: str) -> Any:
    for model in benchmark.get("models") or []:
        if isinstance(model, dict) and model.get("model_id") == model_id:
            return (model.get("test") or {}).get(metric)
    return None


def verify_artifacts(benchmark: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    benchmark_status = (benchmark.get("decision") or {}).get("candidate_status")
    gate_outcome = gate.get("selected_outcome")
    checks = {
        "benchmark_schema_ok": benchmark.get("schema_version") == "stage7_training_objective_benchmark.v1",
        "gate_schema_ok": gate.get("schema_version") == "stage7_training_objective_decision_gate.v1",
        "benchmark_non_causal": benchmark.get("causal_status") == "non_causal_offline_benchmark",
        "gate_non_causal": gate.get("causal_status") == "non_causal_decision_gate",
        "benchmark_status_matches_expected": benchmark_status == EXPECTED_BENCHMARK_STATUS,
        "gate_outcome_matches_expected": gate_outcome == EXPECTED_GATE_OUTCOME,
        "stage7_quarantined": benchmark.get("stage7_status") == "local_valid_composition_quarantined"
        and gate.get("stage7_status") == "local_valid_composition_quarantined",
        "stage7_promotion_blocked": benchmark.get("stage7_promotion_allowed") is False
        and gate.get("stage7_promotion_allowed") is False,
        "stage8_training_blocked": benchmark.get("stage8_training_allowed") is False
        and gate.get("stage8_training_allowed") is False,
        "runtime_behavior_unchanged": benchmark.get("runtime_behavior_changed") is False
        and gate.get("runtime_behavior_changed") is False,
    }
    return {
        "all_checks_passed": all(checks.values()),
        "checks": checks,
        "benchmark_status": benchmark_status,
        "gate_outcome": gate_outcome,
    }


def build_closure(artifact_root: Path) -> dict[str, Any]:
    benchmark_path = artifact_root / "stage7_training_objective_benchmark.json"
    gate_path = artifact_root / "stage7_training_objective_decision_gate.json"
    benchmark = _load_json(benchmark_path)
    gate = _load_json(gate_path)
    verification = verify_artifacts(benchmark, gate)
    if not verification["all_checks_passed"]:
        raise ValueError(f"Stage 7 closure checks failed: {verification['checks']}")
    closure = {
        "schema_version": "stage7_post_decision_closure.v1",
        "causal_status": "non_causal_closure_report",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(benchmark_path), str(gate_path)],
        "artifact_verification": verification,
        "decision": {
            "selected_outcome": gate["selected_outcome"],
            "benchmark_status": verification["benchmark_status"],
            "required_conclusion": "Stage 7 micro-work is stopped pending architecture review.",
            "next_implementation_requires_explicit_review": True,
        },
        "evidence_summary": {
            "current_top1": _model_metric(
                benchmark, "current_learned_post_box_scorer", "top1_dtm_positive_accuracy"
            ),
            "visible_top1": _model_metric(
                benchmark, "visible_term_log_odds_scorer", "top1_dtm_positive_accuracy"
            ),
            "ranked_top1": _model_metric(
                benchmark, "pairwise_ranked_preference_scorer", "top1_dtm_positive_accuracy"
            ),
            "internal_monitor_top1": _model_metric(
                benchmark, "internal_monitor_augmented_visible_term_scorer", "top1_dtm_positive_accuracy"
            ),
            "oracle_top1": _model_metric(
                benchmark, "oracle_dtm_positive_topk_ceiling", "top1_dtm_positive_accuracy"
            ),
            "ranked_hard_negative_rate": _model_metric(
                benchmark, "pairwise_ranked_preference_scorer", "hard_negative_above_positive_rate"
            ),
            "internal_monitor_features_improve_offline": (benchmark.get("decision") or {}).get(
                "internal_monitor_features_improve_offline"
            ),
        },
        "minimum_future_data_requirements": [
            "more_family_held_out_post_box_trajectories",
            "successful_post_box_control_trajectories",
            "closed_loop_labels_beyond_stage7",
            "hard_negative_contrast_sets",
        ],
        "blocked_next_steps": [
            "stage7_runtime_repair",
            "stage7_promotion",
            "stage8_training",
            "causal_internal_terminals",
            "support_adapters_or_score_bonuses",
            "new_broad_stage7_diagnostic_branch_without_review",
        ],
    }
    validate_closure(closure)
    return closure


def build_sequence_policy_note(closure: dict[str, Any]) -> dict[str, Any]:
    note = {
        "schema_version": "stage7_sequence_policy_redesign_note.v1",
        "causal_status": "non_causal_design_note",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_status": "local_valid_composition_quarantined",
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": closure["source_artifacts"]
        + ["reports/structural_candidates/stage7_post_decision_closure.json"],
        "design_scope": "future ranked sequence-policy / model-expression redesign only",
        "not_authorized": [
            "training_new_model_in_this_slice",
            "runtime_sandbox",
            "runtime_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
        "design_principles": [
            "optimize multi-step sequence behavior rather than one-ply local score only",
            "train against state-local hard negatives that share broad visible terms",
            "separate move ranking from ownership/routing decisions",
            "keep DTM/tablebase labels offline-only",
            "preserve frozen Stage 5/6 providers and M1-M4 semantics",
            "require default-off sandbox plus guardrails before any future causal use",
        ],
        "candidate_objective_classes": [
            {
                "class": "state_local_contrastive_sequence_ranking",
                "purpose": "rank DTM-positive or conversion-positive continuation moves above winning-nonoptimal hard negatives within the same state family",
            },
            {
                "class": "closed_loop_sequence_loss",
                "purpose": "penalize compounding drift across a bounded plan window, not just first-move mismatch",
            },
            {
                "class": "hard_negative_curriculum",
                "purpose": "explicitly contrast positive moves with safe-looking but slow/stagnating moves",
            },
            {
                "class": "handoff_exit_supervision",
                "purpose": "label when a sequence policy should hand off to validated providers rather than continue owning",
            },
        ],
        "minimum_future_data_requirements": closure["minimum_future_data_requirements"],
        "future_review_questions": [
            "Can a state-local contrastive objective improve top-1 without increasing hard-negative ranking?",
            "Does sequence-level supervision reduce closed-loop drift on held-out families?",
            "Which data should be collected outside Stage 7 so the model is not overfit to the post-box residual set?",
            "What default-off sandbox and guardrails would be required before any future causal evaluation?",
        ],
        "recommended_next_status": "architecture_review_required_before_implementation",
    }
    validate_sequence_policy_note(note)
    return note


def validate_closure(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "stage7_post_decision_closure.v1":
        raise ValueError("unexpected closure schema")
    if payload.get("causal_status") != "non_causal_closure_report":
        raise ValueError("closure must be non-causal")
    if not (payload.get("artifact_verification") or {}).get("all_checks_passed"):
        raise ValueError("closure requires passing artifact verification")
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


def validate_sequence_policy_note(payload: dict[str, Any]) -> None:
    if payload.get("schema_version") != "stage7_sequence_policy_redesign_note.v1":
        raise ValueError("unexpected sequence-policy note schema")
    if payload.get("causal_status") != "non_causal_design_note":
        raise ValueError("sequence-policy note must be non-causal")
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


def render_closure_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Post-Decision Closure",
        "",
        "This report closes the Stage 7 benchmark branch. It is non-causal and does not start another diagnostic branch.",
        "",
        "## Decision",
        "",
        f"- Selected outcome: `{payload['decision']['selected_outcome']}`",
        f"- Benchmark status: `{payload['decision']['benchmark_status']}`",
        f"- Required conclusion: {payload['decision']['required_conclusion']}",
        f"- Stage 7 status: `{payload['stage7_status']}`",
        f"- Stage 7 promotion allowed: `{payload['stage7_promotion_allowed']}`",
        f"- Stage 8 training allowed: `{payload['stage8_training_allowed']}`",
        "",
        "## Artifact Verification",
        "",
        f"- All checks passed: `{payload['artifact_verification']['all_checks_passed']}`",
    ]
    for key, value in payload["artifact_verification"]["checks"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Evidence Summary",
            "",
        ]
    )
    for key, value in payload["evidence_summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## Minimum Future Data Requirements",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in payload["minimum_future_data_requirements"])
    lines.extend(
        [
            "",
            "## Blocked Next Steps",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in payload["blocked_next_steps"])
    lines.append("")
    return "\n".join(lines)


def render_sequence_policy_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Sequence-Policy Redesign Note",
        "",
        "This is a non-causal architecture design note for future review. It does not train, sandbox, or change runtime behavior.",
        "",
        "## Scope",
        "",
        f"- Design scope: {payload['design_scope']}",
        f"- Recommended next status: `{payload['recommended_next_status']}`",
        f"- Stage 7 status: `{payload['stage7_status']}`",
        "",
        "## Not Authorized",
        "",
    ]
    lines.extend(f"- `{item}`" for item in payload["not_authorized"])
    lines.extend(
        [
            "",
            "## Design Principles",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["design_principles"])
    lines.extend(
        [
            "",
            "## Candidate Objective Classes",
            "",
        ]
    )
    for item in payload["candidate_objective_classes"]:
        lines.append(f"- `{item['class']}`: {item['purpose']}")
    lines.extend(
        [
            "",
            "## Minimum Future Data Requirements",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in payload["minimum_future_data_requirements"])
    lines.extend(
        [
            "",
            "## Future Review Questions",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in payload["future_review_questions"])
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", type=Path, default=Path("reports/structural_candidates"))
    parser.add_argument("--closure-json-output", type=Path, required=True)
    parser.add_argument("--closure-markdown-output", type=Path, required=True)
    parser.add_argument("--design-json-output", type=Path, required=True)
    parser.add_argument("--design-markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    closure = build_closure(args.artifact_root)
    design = build_sequence_policy_note(closure)
    args.closure_json_output.parent.mkdir(parents=True, exist_ok=True)
    args.closure_json_output.write_text(json.dumps(closure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.closure_markdown_output.write_text(render_closure_markdown(closure), encoding="utf-8")
    args.design_json_output.write_text(json.dumps(design, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    args.design_markdown_output.write_text(render_sequence_policy_markdown(design), encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps({"closure": closure, "design": design}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
