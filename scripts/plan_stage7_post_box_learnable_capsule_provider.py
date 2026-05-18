#!/usr/bin/env python3
"""Plan the learnable Stage 7 post-box Plan Capsule provider sandbox.

This is a non-causal protocol artifact. It binds the existing offline DTM
trajectory seed, learned overlay learner, and visible-term candidate model into
one bounded Plan Capsule provider plan without enabling runtime behavior.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROVIDER_SKILL_ID = "krk.post_box_shrink_continuation"
PROVIDER_VERSION = "stage7_post_box_continuation_overlay_v1"
CAPSULE_ID = "krk.post_box_shrink_continuation"
CANDIDATE_ID = "cand.krk.box_shrink.post_box_learnable_capsule_provider.v1"


def _load_json(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _artifact_summary(path: Path | None, payload: dict[str, Any] | None) -> dict[str, Any]:
    if path is None:
        return {"path": None, "present": False}
    summary: dict[str, Any] = {"path": str(path), "present": bool(path.exists())}
    if payload:
        for key in (
            "schema_version",
            "causal_status",
            "promotion_status",
            "provider_version",
            "plan_capsule_id",
            "transition_count",
            "positive_transition_count",
            "negative_transition_count",
            "overlay_actuator_count",
            "train_top1_accuracy",
            "train_position_count",
            "positive_count",
            "negative_count",
        ):
            if key in payload:
                summary[key] = payload[key]
    return summary


def build_plan(
    *,
    trajectory_seed_path: Path,
    overlay_training_summary_path: Path | None = None,
    trajectory_model_path: Path | None = None,
    learned_overlay_topology_path: Path | None = None,
) -> dict[str, Any]:
    seed = _load_json(trajectory_seed_path) or {}
    overlay_summary = _load_json(overlay_training_summary_path)
    trajectory_model = _load_json(trajectory_model_path)
    topology = _load_json(learned_overlay_topology_path)

    trajectory_count = len(seed.get("trajectories") or [])
    white_step_count = sum(
        len(item.get("white_training_steps") or [])
        for item in seed.get("trajectories") or []
        if isinstance(item, dict)
    )
    provider_preservation = (
        (topology or {}).get("meta", {}).get("provider_preservation", {})
        if topology
        else {}
    )

    entry_terms = [
        "active_landmark_label.box_shrink",
        "post_box_shrink_continuation_needed",
        "stage7_post_box_post_reply_context",
        "rook_safe",
        "mate_in_one_available.false",
    ]
    progress_terms = [
        "cut_or_fence_preserved_or_restored",
        "box_area_not_expanded",
        "white_king_support_improves",
        "enemy_king_mobility_decreases",
        "corner_net_pressure_increases",
        "mate_basin_proximity_improves",
        "stagnation_avoided",
    ]
    exit_terms = [
        "mate_in_one_available",
        "stage0_finish_licensed",
        "edge_trap_role_confirmed",
        "drive_to_edge_role_confirmed",
        "fence_or_cut_restored",
        "successful_handoff_to_validated_provider",
    ]
    abort_terms = [
        "rook_unsafe",
        "draw_or_stalemate_risk",
        "box_expansion",
        "cut_or_fence_lost_without_repair",
        "stagnation_loop",
        "no_progress_after_ttl",
        "illegal_or_no_move",
    ]

    return {
        "schema_version": "stage7_post_box_learnable_capsule_provider_plan.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "candidate_id": CANDIDATE_ID,
        "source_candidate_ids": [
            "cand.krk.box_shrink.post_box_continuation_capsule.v1",
            "cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1",
        ],
        "source_monitor_script": "growth.monitor.stage7_post_box_continuation_gap",
        "source_terms": [
            "dtm_won_within_h40",
            "current_graph_downstream_continuation_fails",
            "scripted_provider_can_own_but_max_plies",
            "m3_trainability_no_internal_move_policy_edge",
            "offline_dtm_trajectory_seed_available",
        ],
        "diagnosis": "learnable_multistep_plan_capsule_provider_needed",
        "provider": {
            "provider_skill_id": PROVIDER_SKILL_ID,
            "provider_version": PROVIDER_VERSION,
            "plan_capsule_id": CAPSULE_ID,
            "target_skill": "krk.box_shrink",
            "domain": "KRK",
            "overlay_provider": True,
            "frozen_provider": False,
            "default_enabled": False,
            "causal_status": "sandbox_opt_in",
            "promotion_status": "sandbox_candidate",
            "provider_maturity": "candidate_high_plasticity",
            "plasticity_scope": "candidate_local",
            "can_m3_update": True,
            "can_m4_consolidate": False,
            "ttl_white_moves": 4,
            "entry_terms": entry_terms,
            "progress_terms": progress_terms,
            "exit_terms": exit_terms,
            "abort_terms": abort_terms,
            "owned_roles": ["krk.post_box_shrink_continuation"],
            "owned_providers": [PROVIDER_SKILL_ID],
            "handoff_exports": {
                "krk.stage0_basin": 1.0,
                "krk.edge_trap_close": 1.0,
                "krk.drive_to_edge": 1.0,
                "krk.fence_established": 1.0,
            },
            "trainable_internal_components": [
                "sensor_context_terms",
                "candidate_move_shape_terms",
                "post_move_terms",
                "trajectory_target_memory",
                "actuator_legs",
                "learned_scoring_head",
                "bounded_plan_ownership",
                "exit_abort_monitoring",
            ],
        },
        "training_data": {
            "trajectory_seed": str(trajectory_seed_path),
            "seed_schema_version": seed.get("schema_version"),
            "trajectory_count": trajectory_count,
            "white_training_step_count": white_step_count,
            "runtime_forbidden": [
                "tablebase_lookup",
                "dtm_oracle_move_selection",
                "state_hash_exception",
            ],
        },
        "artifacts": {
            "overlay_training_summary": _artifact_summary(
                overlay_training_summary_path,
                overlay_summary,
            ),
            "trajectory_visible_term_model": _artifact_summary(
                trajectory_model_path,
                trajectory_model,
            ),
            "learned_overlay_topology": {
                "path": str(learned_overlay_topology_path) if learned_overlay_topology_path else None,
                "present": bool(learned_overlay_topology_path and learned_overlay_topology_path.exists()),
                "provider_preservation": provider_preservation,
            },
        },
        "candidate_local_training_protocol": {
            "training_source": "offline_dtm_trajectory_seed_only",
            "freeze_validated_base_providers": True,
            "freeze_stage6_stage5_stage4_protected_providers": True,
            "train_only_provider_internals": True,
            "m4_consolidation_enabled": False,
            "topology_mutation_during_gameplay": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "persistent_legal_move_topology_nodes": False,
        },
        "evaluation_protocol": [
            {
                "phase": 0,
                "name": "default_off_equivalence",
                "description": "compiled topology with provider disabled must match baseline behavior",
            },
            {
                "phase": 1,
                "name": "targeted_unresolved_family_replay",
                "description": "replay DTM-seeded post-box families with sandbox enabled",
            },
            {
                "phase": 2,
                "name": "stage7_smoke_10_h40",
                "description": "10-sample Stage 7 smoke at h40, thin traces",
            },
            {
                "phase": 3,
                "name": "stage7_validation_25_h40",
                "description": "25-sample Stage 7 validation only if smoke improves or classifies cleanly",
            },
            {
                "phase": 4,
                "name": "protected_guardrails",
                "description": "Stage 6/5/4/1 and M1-M4 guardrails only after target improvement",
            },
            {
                "phase": 5,
                "name": "stage7_100_sample_candidate_validation",
                "description": "larger target validation only after guardrails hold",
            },
        ],
        "hard_constraints": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_use_dtm_or_tablebase_at_runtime",
            "do_not_use_hidden_python_routing",
            "do_not_mutate_topology_during_gameplay",
            "do_not_make_handoff_stats_shadow_candidates_structural_candidates_growth_governor_or_plan_capsule_specs_causal",
            "keep_m1_m4_semantics_intact",
            "default_off_sandbox_only",
        ],
        "success_criteria": [
            "dtm_seeded_families_convert_under_capsule",
            "stage7_h40_target_improves_over_current_baseline",
            "shadow_candidates_decrease_or_hold",
            "no_local_one_ply_regression",
            "no_guardrail_regression",
            "trace_shows_plan_entry_progress_exit_abort",
        ],
        "candidate_status_update": {
            "candidate_id": CANDIDATE_ID,
            "promotion_status": "learnable_capsule_provider_protocol_ready",
            "causal_status": "non_causal",
            "credit": 0.0,
            "next_action": "run_default_off_equivalence_then_targeted_unresolved_family_replay",
        },
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    provider = payload["provider"]
    training = payload["training_data"]
    lines = [
        "# Stage 7 Learnable Plan Capsule Provider",
        "",
        "This is a non-causal sandbox protocol. It does not promote Stage 7 and does not enable runtime behavior by default.",
        "",
        "## Provider",
        "",
        f"- provider_skill_id: `{provider['provider_skill_id']}`",
        f"- provider_version: `{provider['provider_version']}`",
        f"- plan_capsule_id: `{provider['plan_capsule_id']}`",
        f"- causal_status: `{provider['causal_status']}`",
        f"- default_enabled: `{provider['default_enabled']}`",
        f"- ttl_white_moves: `{provider['ttl_white_moves']}`",
        f"- can_m3_update: `{provider['can_m3_update']}`",
        f"- can_m4_consolidate: `{provider['can_m4_consolidate']}`",
        "",
        "## Offline Supervision",
        "",
        f"- trajectory_seed: `{training['trajectory_seed']}`",
        f"- trajectory_count: `{training['trajectory_count']}`",
        f"- white_training_step_count: `{training['white_training_step_count']}`",
        "- runtime DTM/tablebase lookup is forbidden.",
        "",
        "## Evaluation Phases",
        "",
    ]
    for phase in payload["evaluation_protocol"]:
        lines.append(f"- Phase {phase['phase']}: `{phase['name']}` - {phase['description']}")
    lines.extend([
        "",
        "## Hard Constraints",
        "",
    ])
    for item in payload["hard_constraints"]:
        lines.append(f"- `{item}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan Stage 7 learnable Plan Capsule provider sandbox")
    parser.add_argument("--trajectory-seed", type=Path, required=True)
    parser.add_argument("--overlay-training-summary", type=Path, default=None)
    parser.add_argument("--trajectory-model", type=Path, default=None)
    parser.add_argument("--learned-overlay-topology", type=Path, default=None)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = build_plan(
        trajectory_seed_path=args.trajectory_seed,
        overlay_training_summary_path=args.overlay_training_summary,
        trajectory_model_path=args.trajectory_model,
        learned_overlay_topology_path=args.learned_overlay_topology,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_markdown(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
