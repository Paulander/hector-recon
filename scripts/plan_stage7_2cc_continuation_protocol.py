#!/usr/bin/env python3
"""Plan a non-causal Stage 7 2cc continuation repair protocol."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_protocol(alignment: dict[str, Any]) -> dict[str, Any]:
    update = dict(alignment.get("candidate_update", {}) or {})
    diagnosis = str(update.get("diagnosis") or "")
    if diagnosis != "multi_step_continuation_policy_gap_not_single_move_gap":
        status = "blocked_pending_alignment_diagnosis"
        next_action = "do_not_train_or_compile_until_candidate_move_dtm_alignment_classifies_multistep_gap"
    else:
        status = "sandbox_training_protocol_ready"
        next_action = "run bounded sandbox training/evaluation only after explicit validation command"
    candidate_id = "cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1"
    return {
        "schema_version": "stage7_2cc_continuation_protocol.v1",
        "causal_status": "non_causal",
        "stage7_status": "local_valid_composition_quarantined",
        "source_alignment_schema": alignment.get("schema_version"),
        "source_alignment_diagnosis": diagnosis,
        "structural_candidate": {
            "schema_version": "structural_candidate.v1",
            "candidate_id": candidate_id,
            "candidate_type": "narrow_post_box_continuation_overlay_protocol",
            "source_monitor_script": "growth.monitor.candidate_move_dtm_alignment",
            "source_terms": [
                "candidate_move_frames_available",
                "all_legal_first_moves_tablebase_winning",
                "current_graph_legal_first_fails",
                "dtm_reference_trajectory_available",
            ],
            "trigger_failure_classes": [
                "provider_capacity_missing",
                "continuation_topology_underexpressive",
                "multi_step_policy_gap",
            ],
            "target_skill": "krk.box_shrink",
            "parent_skill": "krk.post_box_shrink_continuation",
            "proposed_change": {
                "kind": "sandbox_narrow_post_box_continuation_overlay_or_plan_capsule",
                "scope": "stage7_2cc_like_post_box_continuation",
                "entry_terms": [
                    "active_landmark_label.box_shrink",
                    "plan_capsule_entry_confirmed",
                    "post_reply_state_reached",
                    "rook_safe",
                    "enemy_king_not_at_edge",
                    "fence_or_cut_not_preserved",
                ],
                "progress_terms": [
                    "box_area_decreases_after_move",
                    "box_area_not_increased_after_move",
                    "black_king_escape_count_decreases_after_move",
                    "rook_safe_after_move",
                    "king_moves_toward_enemy",
                    "king_moves_toward_rook_support",
                    "rook_transfer_preserves_safety",
                ],
                "exit_terms": [
                    "fence_exists_after_move",
                    "edge_trap_role_confirmed",
                    "drive_to_edge_role_confirmed",
                    "stage0_finish_licensed",
                    "mate_in_one_available",
                ],
                "abort_terms": [
                    "rook_unsafe_after_move",
                    "draw_or_stalemate_risk",
                    "repeated_abstract_state",
                    "no_progress_after_ttl",
                ],
                "ttl_white_moves": 4,
                "training_source": [
                    "reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json",
                    "reports/structural_candidates/stage7_2cc_candidate_move_frame_audit.json",
                    "reports/structural_candidates/stage7_2cc_candidate_move_dtm_alignment.json",
                ],
                "runtime_forbidden_terms": [
                    "tablebase_lookup",
                    "dtm_oracle_move_selection",
                    "state_hash_exception",
                ],
            },
            "evidence_artifacts": [
                "reports/structural_candidates/stage7_2cc_candidate_move_dtm_alignment.json",
                "reports/structural_candidates/stage7_2cc_candidate_move_frame_audit.json",
                "reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json",
            ],
            "promotion_status": status,
            "causal_status": "non_causal",
            "credit": 0.0,
        },
        "evaluation_phases": [
            {
                "phase": 0,
                "name": "static_sanity",
                "checks": [
                    "visible_source_terms_present",
                    "no_state_hash_exception",
                    "no_runtime_dtm_or_tablebase",
                    "no_direct_role_script_to_provider_sub_edge",
                    "default_off_equivalence",
                ],
            },
            {
                "phase": 1,
                "name": "frozen_weight_probe",
                "checks": [
                    "candidate_can_emit_visible_suggestions_or_plan_steps",
                    "candidate_default_off_no_behavior_change",
                ],
            },
            {
                "phase": 2,
                "name": "bounded_candidate_local_plasticity",
                "checks": [
                    "freeze_validated_stage4_5_6_providers",
                    "allow_only_candidate_local_updates",
                    "record_weight_delta_magnitude",
                    "stop_if_guardrails_regress",
                ],
            },
            {
                "phase": 3,
                "name": "target_validation",
                "checks": [
                    "stage7_target_improves_h40",
                    "shadow_candidates_do_not_increase",
                    "candidate_trace_cites_visible_terms",
                ],
            },
            {
                "phase": 4,
                "name": "protected_guardrails",
                "checks": [
                    "stage6_drive_to_edge",
                    "stage5_fence_established",
                    "stage4_wrong_tempo",
                    "stage1_backchain",
                    "m1_m4_preservation",
                    "kpk_to_kqk_bridge",
                ],
            },
        ],
        "hard_boundaries": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_make_structural_candidates_causal",
            "do_not_mutate_topology_during_gameplay",
            "do_not_use_hidden_python_router",
            "do_not_train_until_protocol_is_explicitly_invoked",
        ],
        "next_action": next_action,
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    candidate = payload["structural_candidate"]
    lines = [
        "# Stage 7 2cc Continuation Protocol",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Candidate: `{candidate['candidate_id']}`",
        f"Promotion status: `{candidate['promotion_status']}`",
        f"Diagnosis: `{payload['source_alignment_diagnosis']}`",
        "",
        "## Evaluation Phases",
        "",
    ]
    for phase in payload["evaluation_phases"]:
        lines.append(f"- Phase {phase['phase']}: `{phase['name']}`")
    lines.extend(["", "## Boundaries", ""])
    for item in payload["hard_boundaries"]:
        lines.append(f"- `{item}`")
    lines.extend(["", f"Next action: `{payload['next_action']}`"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--alignment", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = build_protocol(_load_json(args.alignment))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
