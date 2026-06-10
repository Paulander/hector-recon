#!/usr/bin/env python3
"""Define the next bounded KRK strategy/sequence evidence plan."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ARCH_REVIEW = Path("reports/krk_strategy_sequence_architecture_review_v0.json")
OUT_JSON = Path("reports/krk_strategy_sequence_evidence_plan_v0.json")
OUT_MD = Path("reports/krk_strategy_sequence_evidence_plan_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_plan() -> dict[str, Any]:
    _load(ARCH_REVIEW)
    return {
        "schema_version": "krk_strategy_sequence_evidence_plan.v0",
        "causal_status": "non_causal_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(ARCH_REVIEW)],
        "purpose": "Collect enough non-causal evidence to evaluate strategy ownership and multi-step sequence policy without resuming Stage 7 local repair.",
        "tracks": [
            {
                "track_id": "strategy_ownership",
                "stage_scope": ["stage4_wrong_tempo", "stage5_fence", "stage6_drive_to_edge"],
                "stage7_usage": "held_out_challenge_only",
                "target_rows": {
                    "protected_states": 12,
                    "max_forced_provider_labels": 36,
                    "min_positive_provider_families": 3,
                    "min_negative_provider_families": 2,
                },
                "required_fields": [
                    "StrategyProposalFrame-compatible provider rows",
                    "provider_local_rank",
                    "normalized_score",
                    "provider_version",
                    "provider_maturity",
                    "forced_provider_h40_result",
                    "same-move compatibility where available",
                ],
            },
            {
                "track_id": "sequence_policy",
                "stage_scope": ["protected_stage5_6_success_controls", "stage7_heldout_residuals"],
                "stage7_usage": "evaluation_only_no_training_rows",
                "target_rows": {
                    "clean_success_controls": 8,
                    "hard_negative_controls": 8,
                    "heldout_stage7_challenge_rows": 4,
                },
                "required_fields": [
                    "closed_loop_h40_result",
                    "selected_provider",
                    "first_move",
                    "handoff_success",
                    "plan_progress_or_stagnation",
                    "family_id",
                    "source_bias_flag",
                ],
            },
            {
                "track_id": "curriculum_boundary",
                "stage_scope": ["stage7_heldout", "near_edge_protected_controls"],
                "stage7_usage": "held_out_boundary_probe",
                "target_rows": {
                    "phase_boundary_examples": 8,
                    "box_shrink_exit_examples": 4,
                },
                "required_fields": [
                    "box_area_relevance",
                    "black_king_edge_distance",
                    "edge_net_or_king_support_context",
                    "validated_handoff_target_available",
                    "owner_exit_pressure",
                ],
            },
        ],
        "collection_phases": [
            {
                "phase_id": "replay_free_inventory",
                "description": "Join existing ranked proposal frames, forced-provider labels, and sequence controls before any new run.",
                "executes_labels": False,
            },
            {
                "phase_id": "bounded_manifest_only",
                "description": "If gaps remain, write a concrete h40 label manifest with topology/provider bindings before executing.",
                "executes_labels": False,
                "max_new_states": 12,
                "max_new_labels": 36,
            },
            {
                "phase_id": "reviewed_label_execution",
                "description": "Execute only after manifest review; trace failures only and keep Stage 7 out of training rows.",
                "executes_labels": "requires_future_review",
            },
            {
                "phase_id": "state_heldout_probe",
                "description": "Probe ownership and sequence signals with state/family holdout; report source bias explicitly.",
                "executes_labels": False,
            },
        ],
        "readiness_requirements_before_runtime": [
            "protected Stage 4/5/6 coverage",
            "no Stage 7 training leakage",
            "provider-family diversity across positives and negatives",
            "state-heldout performance above simple provenance/rank baselines",
            "negative suppression measured",
            "sequence-policy controls not sourced only from Stage 7 repair artifacts",
            "source-bias audit passes",
            "default-off runtime design review passes separately",
        ],
        "blocked_actions": [
            "runtime selector implementation",
            "Stage 7 repair or promotion",
            "Stage 8 training",
            "unreviewed label execution",
            "runtime DTM/tablebase use",
            "gameplay-time topology mutation",
        ],
        "decision": {
            "status": "strategy_sequence_evidence_plan_defined",
            "recommended_next_step": "run_replay_free_strategy_sequence_inventory",
            "runtime_work_allowed": False,
        },
    }


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Strategy / Sequence Evidence Plan v0",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        payload["purpose"],
        "",
        "## Tracks",
        "",
    ]
    for track in payload["tracks"]:
        lines.append(f"- `{track['track_id']}`: stage7_usage=`{track['stage7_usage']}` targets=`{track['target_rows']}`")
    lines.extend(["", "## Collection Phases", ""])
    for phase in payload["collection_phases"]:
        lines.append(f"- `{phase['phase_id']}`: {phase['description']}")
    lines.extend(["", "## Readiness Before Runtime", ""])
    for item in payload["readiness_requirements_before_runtime"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Blocked Actions", ""])
    for item in payload["blocked_actions"]:
        lines.append(f"- `{item}`")
    lines.extend(["", f"Recommended next step: `{payload['decision']['recommended_next_step']}`", ""])
    return "\n".join(lines)


def main() -> None:
    payload = build_plan()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")


if __name__ == "__main__":
    main()
