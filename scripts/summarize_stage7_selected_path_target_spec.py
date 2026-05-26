#!/usr/bin/env python3
"""Write a non-causal target spec for Stage 7 selected failure paths."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUDIT = Path("reports/structural_candidates/stage7_selected_failure_path_audit_v0.json")
OUT_JSON = Path("reports/structural_candidates/stage7_selected_path_target_spec_v0.json")
OUT_MD = Path("reports/structural_candidates/stage7_selected_path_target_spec_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_spec() -> dict[str, Any]:
    audit = _load(AUDIT)
    rows = audit.get("rows") or []
    ownership_rows = [
        row for row in rows
        if row.get("selected_failure_path_class") == "strategy_ownership_gap_existing_provider_can_convert"
    ]
    sequence_rows = [
        row for row in rows
        if row.get("selected_failure_path_class") == "continuation_capacity_or_sequence_policy_gap"
    ]
    payload = {
        "schema_version": "stage7_selected_path_target_spec.v0",
        "causal_status": "non_causal_design_spec",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "hidden_python_controller": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(AUDIT)],
        "status": "split_targets_required",
        "target_specs": [
            {
                "target_id": "stage7.selected_path.strategy_ownership_gap.v0",
                "target_type": "strategy_ownership_training_target",
                "state_count": len(ownership_rows),
                "states": [
                    {
                        "state_id": row.get("state_id"),
                        "selected_provider": row.get("raw_selected_provider"),
                        "selected_move": row.get("raw_selected_move"),
                        "target_provider": row.get("forced_mating_provider") or row.get("best_forced_provider"),
                        "target_evidence": "forced_provider_mates_h40",
                        "recommended_label": "selected_owner_failed_alternative_provider_converts",
                    }
                    for row in ownership_rows
                ],
                "positive_label_definition": "existing provider converts under forced ownership while selected provider max-plies",
                "negative_or_control_definition": "validated protected states where selected provider converts or forced alternatives do not improve outcome",
                "required_features": [
                    "current_owner",
                    "selected_owner_failed_h40",
                    "alternative_provider_known_conversion_h40",
                    "local_provider_competition_failed",
                    "provider_score_scale_gap",
                    "provider_family",
                    "active_landmark_label",
                    "repair_or_phase_monitor_signature",
                ],
                "minimum_future_evidence": [
                    "more than two ownership-gap states",
                    "protected Stage 5/6 controls with safe stage0/edge/fence ownership",
                    "paired no-change default-off check before any sandbox",
                    "false-positive review where alternate provider should not own",
                ],
                "future_consumer_if_validated": "strategy arbiter or owner-exit monitor dataset",
                "forbidden_now": [
                    "boost target provider",
                    "penalize stage0_basin",
                    "make local_provider_competition_failed causal",
                    "promote Stage 7",
                ],
            },
            {
                "target_id": "stage7.selected_path.sequence_continuation_gap.v0",
                "target_type": "sequence_policy_or_continuation_capacity_target",
                "state_count": len(sequence_rows),
                "states": [
                    {
                        "state_id": row.get("state_id"),
                        "selected_provider": row.get("raw_selected_provider"),
                        "selected_move": row.get("raw_selected_move"),
                        "target_provider": None,
                        "target_evidence": "forced_providers_and_legal_first_h40_no_mate",
                        "recommended_label": "current_provider_set_insufficient_or_sequence_policy_gap",
                    }
                    for row in sequence_rows
                ],
                "positive_label_definition": "multi-step trajectory or continuation policy converts from state without runtime oracle",
                "negative_or_control_definition": "provider-best and legal-first h40 labels that remain max_plies or draw",
                "required_features": [
                    "post_plan_stagnation",
                    "plan_selection_needed",
                    "repair_needed_monitor",
                    "handoff_success_after_plan",
                    "multi_step_progress_required",
                    "trajectory_progress_terms",
                    "closed_loop_drift_class",
                ],
                "minimum_future_evidence": [
                    "offline successful trajectories for the unresolved states or nearby controls",
                    "hard-negative contrast moves from current failed selected paths",
                    "teacher-forced and closed-loop split metrics",
                    "successful post-box controls outside Stage 7 residuals",
                ],
                "future_consumer_if_validated": "ranked sequence-policy benchmark or plan-capsule model-expression redesign",
                "forbidden_now": [
                    "train Stage 8",
                    "use DTM/tablebase at runtime",
                    "add full-KRK continuation overlay",
                    "tune current plan capsule micro-repair",
                ],
            },
        ],
        "decision_gate": {
            "status": "non_causal_targets_defined_no_runtime_work",
            "next_allowed_action": "build_replay_free_selected_path_target_dataset_or_request_architecture_review",
            "why": "The selected failure path is mixed; a single selector, penalty, or provider boost would conflate ownership errors with continuation-capacity/sequence errors.",
            "blocked_actions": [
                "runtime arbiter implementation",
                "abstention threshold tuning",
                "Stage 7 promotion",
                "Stage 8 training",
                "causal internal terminals",
            ],
        },
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Stage 7 Selected Path Target Spec v0",
        "",
        f"Status: `{payload['status']}`",
        "",
        "This is a non-causal design spec. It does not implement a runtime selector, terminal, repair, or training run.",
        "",
        "## Target Specs",
        "",
    ]
    for spec in payload["target_specs"]:
        lines.extend([
            f"### `{spec['target_id']}`",
            "",
            f"- Type: `{spec['target_type']}`",
            f"- State count: `{spec['state_count']}`",
            f"- Positive label: {spec['positive_label_definition']}",
            f"- Control label: {spec['negative_or_control_definition']}",
            f"- Future consumer if validated: `{spec['future_consumer_if_validated']}`",
            "",
            "| State | Selected provider | Selected move | Target provider | Evidence |",
            "| --- | --- | --- | --- | --- |",
        ])
        for state in spec["states"]:
            lines.append(
                "| "
                f"`{state['state_id']}` | "
                f"`{state['selected_provider']}` | "
                f"`{state['selected_move']}` | "
                f"`{state['target_provider']}` | "
                f"`{state['target_evidence']}` |"
            )
        lines.extend([
            "",
            "Required features:",
            "",
        ])
        for feature in spec["required_features"]:
            lines.append(f"- `{feature}`")
        lines.extend([
            "",
            "Minimum future evidence:",
            "",
        ])
        for item in spec["minimum_future_evidence"]:
            lines.append(f"- {item}")
        lines.extend([
            "",
            "Forbidden now:",
            "",
        ])
        for item in spec["forbidden_now"]:
            lines.append(f"- `{item}`")
        lines.append("")
    lines.extend([
        "## Decision Gate",
        "",
        f"- Status: `{payload['decision_gate']['status']}`",
        f"- Next allowed action: `{payload['decision_gate']['next_allowed_action']}`",
        f"- Why: {payload['decision_gate']['why']}",
        "",
    ])
    return "\n".join(lines)


def main() -> None:
    payload = build_spec()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
