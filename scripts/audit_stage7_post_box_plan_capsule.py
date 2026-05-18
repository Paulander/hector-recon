#!/usr/bin/env python3
"""Non-causal Stage 7 post-box plan capsule candidate and trajectory audit."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from recon_lite_chess.routing import PlanCapsuleSpec, StructuralCandidate


CANDIDATE_ID = "cand.krk.box_shrink.post_box_continuation_capsule.v1"
CAPSULE_ID = "krk.post_box_shrink_continuation"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_plan_capsule_candidate(*, evidence_artifacts: list[str]) -> dict[str, Any]:
    structural_candidate = StructuralCandidate(
        candidate_id=CANDIDATE_ID,
        candidate_type="plan_capsule",
        source_monitor_script="growth.monitor.stage7_post_box_continuation_gap",
        source_terms=[
            "local_valid_composition_quarantined",
            "learned_provider_selected_but_conversion_failed",
            "dtm_won_within_h40",
            "single_move_repairs_exhausted",
        ],
        trigger_failure_classes=[
            "selected_provider_still_cannot_convert",
            "repeated_conversion_failure",
            "continuation_topology_underexpressive",
        ],
        target_skill="krk.box_shrink",
        parent_skill="krk.skill_hub",
        proposed_change={
            "kind": "plan_capsule_commitment_bias",
            "capsule_id": CAPSULE_ID,
            "not_fixed_curriculum_stage": True,
            "bounded_ttl_white_moves": 3,
            "runtime_default": "disabled",
        },
        evidence_artifacts=evidence_artifacts,
        governor_status="structure_insufficient",
        governor_metadata={
            "stage_status": "local_valid_composition_quarantined",
            "growth_policy": "candidate_requires_trajectory_gap_audit_before_sandbox",
            "default_runtime_behavior_changed": False,
        },
        topology_weight_diagnosis={
            "frozen_weight_probe_result": "learned_overlay_can_win_ownership_but_still_max_plies",
            "forced_oracle_probe_result": "dtm_reference_trajectories_convert_h40",
            "bounded_m3_warmup_result": "not_run_for_plan_capsule",
            "bounded_m4_consolidation_result": "not_run_for_plan_capsule",
            "diagnosis": "multi_step_commitment_gap",
        },
        candidate_diagnostic_labels=[
            "continuation_topology_underexpressive",
            "selected_provider_still_cannot_convert",
            "expressive_but_untrained_or_undercommitted",
        ],
        promotion_status="proposed",
    )
    capsule = PlanCapsuleSpec(
        capsule_id=CAPSULE_ID,
        source_candidate_id=CANDIDATE_ID,
        source_monitor_script="growth.monitor.stage7_post_box_continuation_gap",
        source_terms=[
            "local_valid_composition_quarantined",
            "learned_provider_selected_but_conversion_failed",
            "dtm_won_within_h40",
            "single_move_repairs_exhausted",
        ],
        domain="krk",
        target_skill="krk.box_shrink",
        entry_terms=[
            "active_landmark_label.box_shrink",
            "box_shrink_attempt_confirmed_or_candidate_confirmed",
            "post_reply_state_reached",
            "conversion_not_immediate",
            "rook_safe",
            "enemy_king_constrained_or_recoverable",
            "no_stronger_mate_or_tactic_interrupt_available",
        ],
        progress_terms=[
            "box_area_decreases_or_does_not_expand",
            "cut_or_fence_preserved_or_restored",
            "white_king_support_improves",
            "enemy_king_mobility_decreases",
            "corner_net_pressure_increases",
            "mate_basin_proximity_improves",
            "safe_check_or_cut_created",
            "stagnation_avoided",
        ],
        exit_terms=[
            "mate_in_one_available",
            "mate_basin_or_stage0_finish_visibly_licensed",
            "edge_trap_role_confirmed",
            "drive_to_edge_role_confirmed",
            "fence_or_cut_restored",
            "full_krk_continuation_role_confirmed",
            "ttl_expired_with_successful_handoff",
        ],
        abort_terms=[
            "rook_unsafe",
            "draw_or_stalemate_risk",
            "box_expands_badly",
            "cut_or_fence_lost_without_repair",
            "repeated_abstract_state_or_stagnation_loop",
            "no_progress_after_owned_moves",
            "stronger_interrupt_available",
            "illegal_or_no_move_failure",
        ],
        ttl_white_moves=3,
        owned_roles=[
            "krk.post_box_shrink_continuation",
            "krk.post_box_drive_repair",
            "krk.post_box_fence_or_cut_repair",
            "krk.post_box_king_support",
        ],
        owned_providers=[
            "krk.post_box_shrink_continuation",
            "krk.drive_to_edge",
            "krk.fence_established",
            "krk.edge_trap_close",
        ],
        handoff_exports={
            "krk.edge_trap_close": 0.4,
            "krk.drive_to_edge": 0.3,
            "krk.fence_established": 0.2,
            "krk.stage0_basin": 0.1,
        },
        training_source="reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json",
        validation_protocol={
            "target": "Stage 7 box_shrink conversion h40",
            "first_validation": "25 samples seed 7",
            "large_validation": "100+ samples if 25-sample target improves",
            "default": "disabled",
        },
        guardrails=[
            "stage6_drive_to_edge",
            "stage5_fence_established",
            "stage4_wrong_tempo",
            "stage1_backchain",
            "krk_entry",
            "kpk_to_kqk_bridge",
            "m1_m4_preservation",
        ],
        notes=[
            "This is not a fixed Stage 7.5 curriculum stage.",
            "This is a general bounded plan capsule / commitment-bias candidate.",
            "Stage 7 is the first test case because single-move providers and ownership repairs failed.",
            "The capsule is non-causal until sandboxed and promoted through visible topology.",
        ],
    )
    return {
        "schema_version": "plan_capsule_candidate.v1",
        "causal_status": "non_causal",
        "candidate_id": CANDIDATE_ID,
        "candidate_type": "plan_capsule",
        "promotion_status": "proposed",
        "structural_candidate": structural_candidate.to_dict(),
        "plan_capsule": capsule.to_dict(),
        "evidence_artifacts": evidence_artifacts,
        "candidate_status_updates": [
            {
                "candidate_id": "cand.krk.box_shrink.post_box_continuation_overlay_probe.v1",
                "status": "quarantined",
                "diagnosis": "selected_provider_still_cannot_convert / continuation_topology_underexpressive",
            },
            {
                "candidate_id": "cand.krk.box_shrink_to_drive_repair.visible_provider_support.v1",
                "status": "quarantined_or_overbroad",
                "diagnosis": "adapter fires but supported provider outcome remains max_plies",
            },
            {
                "candidate_id": "cand.krk.box_shrink.local_semantic_repairs.v1",
                "status": "local_semantic_alignment_improved_but_conversion_insufficient",
                "diagnosis": "local move quality no longer explains remaining conversion failures",
            },
            {
                "candidate_id": CANDIDATE_ID,
                "status": "proposed",
                "next_action": "trajectory_gap_audit",
            },
        ],
        "hard_blocks": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_add_causal_capsule_runtime",
            "do_not_make_candidates_causal",
            "do_not_mutate_topology_during_gameplay",
        ],
    }


def _post_reply_rows(diagnostic: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for packet in diagnostic.get("handoff_packets") or []:
        if not isinstance(packet, dict) or packet.get("phase") != "post_opponent_reply":
            continue
        evidence = packet.get("evidence_terms")
        if not isinstance(evidence, dict):
            continue
        rows.append({
            "packet_id": packet.get("packet_id"),
            "fen": evidence.get("fen"),
            "post_reply_fen": evidence.get("post_reply_fen"),
            "state_signature": evidence.get("post_reply_state_signature"),
            "selected_successor": evidence.get("successor_selected_skill"),
            "playout_result": evidence.get("playout_result"),
            "failure_classes": evidence.get("failure_classes") or [],
            "semantic_alignment_status": evidence.get("semantic_alignment_status"),
            "successor_skills": evidence.get("successor_skills") or {},
            "reward_contract_mismatch": bool(evidence.get("reward_contract_mismatch")),
            "stagnation_summary": evidence.get("stagnation_summary"),
        })
    return rows


def _trajectory_terms(trajectory_seed: dict[str, Any]) -> dict[str, Any]:
    move_terms = Counter()
    post_terms = Counter()
    by_fen = {}
    for trajectory in trajectory_seed.get("trajectories") or []:
        if not isinstance(trajectory, dict):
            continue
        white_steps = trajectory.get("white_training_steps") or []
        for step in white_steps:
            if not isinstance(step, dict):
                continue
            move_terms.update(step.get("move_shape_terms") or [])
            post_terms.update(step.get("post_move_terms") or [])
        by_fen[str(trajectory.get("start_fen"))] = {
            "start_dtm": trajectory.get("start_dtm"),
            "ply_count": trajectory.get("ply_count"),
            "white_training_step_count": trajectory.get("white_training_step_count"),
            "ended_in_checkmate": trajectory.get("ended_in_checkmate"),
            "first_white_moves": [
                {
                    "move": step.get("move"),
                    "child_dtm": step.get("child_dtm"),
                    "move_shape_terms": step.get("move_shape_terms") or [],
                    "post_move_terms": step.get("post_move_terms") or [],
                }
                for step in white_steps[:5]
                if isinstance(step, dict)
            ],
        }
    return {
        "common_reference_move_shape_terms": dict(move_terms.most_common(12)),
        "common_reference_post_move_terms": dict(post_terms.most_common(12)),
        "reference_by_start_fen": by_fen,
    }


def build_audit(
    *,
    diagnostics: list[tuple[str, dict[str, Any]]],
    trajectory_seed: dict[str, Any],
    learned_overlay_model: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = []
    for name, diagnostic in diagnostics:
        for row in _post_reply_rows(diagnostic):
            row["diagnostic_source"] = name
            rows.append(row)
    outcome_by_successor = Counter(
        f"{row.get('selected_successor') or 'none'}:{row.get('playout_result') or 'unknown'}"
        for row in rows
    )
    failure_by_state = defaultdict(Counter)
    for row in rows:
        if row.get("playout_result") != "mate":
            failure_by_state[str(row.get("state_signature") or row.get("post_reply_fen"))].update(
                row.get("failure_classes") or ["unclassified_max_plies"]
            )
    reference = _trajectory_terms(trajectory_seed)
    learned_summary = {}
    if learned_overlay_model:
        learned_summary = {
            "model_kind": learned_overlay_model.get("model_kind"),
            "train_top1_accuracy": learned_overlay_model.get("train_top1_accuracy"),
            "train_position_count": learned_overlay_model.get("train_position_count"),
            "diagnosis": "simple visible-term model underfits trajectory labels",
        }
    return {
        "schema_version": "stage7_post_box_plan_capsule_audit.v1",
        "causal_status": "non_causal",
        "candidate_id": CANDIDATE_ID,
        "capsule_id": CAPSULE_ID,
        "post_reply_record_count": len(rows),
        "outcome_by_successor": dict(outcome_by_successor),
        "failure_by_state": {key: dict(value) for key, value in failure_by_state.items()},
        "reference_trajectory_summary": reference,
        "learned_overlay_model_summary": learned_summary,
        "diagnosis": {
            "wrong_first_post_box_move": "not_sufficient",
            "wrong_second_or_third_move": "likely",
            "loss_of_cut_or_fence": "possible_context_dependent",
            "missing_king_support": "possible_context_dependent",
            "premature_stage0_fallback": "observed_but_not_sufficient_after_ownership_tests",
            "missing_plan_commitment": "likely",
            "stagnation_or_repetition": "possible_downstream",
            "provider_capacity_gap": "likely_for_current_providers",
        },
        "visible_distinguishing_terms": {
            "reference_move_shape_terms": reference["common_reference_move_shape_terms"],
            "reference_post_move_terms": reference["common_reference_post_move_terms"],
        },
        "useful_existing_subroles": [
            "krk.drive_to_edge",
            "krk.fence_established",
            "krk.edge_trap_close",
            "krk.stage0_basin_as_exit_only",
        ],
        "capsule_ownership_recommendation": {
            "own_until": [
                "ttl_white_moves_exhausted",
                "exit_role_confirmed",
                "abort_term_confirmed",
            ],
            "owned_move_count": "3_or_4_white_moves_initially",
            "do_not_own": [
                "mate_in_one_finish",
                "tactical_interrupt",
                "rook_unsafe_state",
            ],
        },
        "hard_blocks": [
            "do_not_implement_causal_capsule_from_this_audit",
            "do_not_train_stage8",
            "do_not_promote_stage7",
        ],
    }


def _write_candidate_md(payload: dict[str, Any], path: Path) -> None:
    capsule = payload["plan_capsule"]
    lines = [
        "# Stage 7 Post-Box Continuation Plan Capsule Candidate",
        "",
        f"Candidate: `{payload['candidate_id']}`",
        f"Capsule: `{capsule['capsule_id']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Promotion status: `{payload['promotion_status']}`",
        "",
        "This is not a new fixed curriculum stage. It is a proposed bounded",
        "Plan Capsule / Commitment Bias structure for multi-step continuation.",
        "",
        "## Why",
        "",
        "Single-move providers, support adapters, score ownership, and learned",
        "post-box overlays did not solve Stage 7 conversion. The remaining",
        "failure appears to require short multi-ply commitment with visible",
        "entry/progress/exit/abort terms.",
        "",
        "## TTL",
        "",
        f"`{capsule['ttl_white_moves']}` white moves",
        "",
        "## Guardrails",
        "",
    ]
    for guardrail in capsule.get("guardrails") or []:
        lines.append(f"- `{guardrail}`")
    lines.extend(["", "## Hard Blocks", ""])
    for block in payload.get("hard_blocks") or []:
        lines.append(f"- `{block}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_audit_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Post-Box Plan Capsule Audit",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Post-reply records: `{payload['post_reply_record_count']}`",
        "",
        "## Outcome By Successor",
        "",
    ]
    for key, value in sorted((payload.get("outcome_by_successor") or {}).items()):
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## Diagnosis", ""])
    for key, value in sorted((payload.get("diagnosis") or {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Recommendation", ""])
    rec = payload.get("capsule_ownership_recommendation") or {}
    lines.append(f"- Owned move count: `{rec.get('owned_move_count')}`")
    for item in rec.get("own_until") or []:
        lines.append(f"- Own until: `{item}`")
    lines.extend(["", "This audit is non-causal and does not change runtime behavior."])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Stage 7 post-box plan capsule candidate")
    parser.add_argument("--diagnostic", action="append", default=[], help="name=path or path")
    parser.add_argument(
        "--trajectory-seed",
        type=Path,
        default=Path("reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json"),
    )
    parser.add_argument(
        "--learned-model",
        type=Path,
        default=Path("reports/structural_candidates/stage7_post_box_trajectory_provider_model.json"),
    )
    parser.add_argument(
        "--candidate-output",
        type=Path,
        default=Path("reports/structural_candidates/stage7_post_box_continuation_capsule_candidate.json"),
    )
    parser.add_argument(
        "--candidate-md-output",
        "--candidate-markdown-output",
        dest="candidate_md_output",
        type=Path,
        default=Path("reports/structural_candidates/stage7_post_box_continuation_capsule_candidate.md"),
    )
    parser.add_argument(
        "--audit-output",
        type=Path,
        default=Path("reports/structural_candidates/stage7_post_box_plan_capsule_audit.json"),
    )
    parser.add_argument(
        "--audit-md-output",
        "--audit-markdown-output",
        dest="audit_md_output",
        type=Path,
        default=Path("reports/structural_candidates/stage7_post_box_plan_capsule_audit.md"),
    )
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    diagnostics = []
    evidence_artifacts = []
    for raw in args.diagnostic:
        if "=" in raw:
            name, path_str = raw.split("=", 1)
        else:
            path_str = raw
            name = Path(path_str).name
        diagnostics.append((name, _load_json(Path(path_str))))
        evidence_artifacts.append(path_str)
    evidence_artifacts.append(str(args.trajectory_seed))
    if args.learned_model:
        evidence_artifacts.append(str(args.learned_model))
    if not diagnostics:
        default_diagnostics = [
            ("learned_overlay_bonus001_10_h40", Path("reports/structural_candidates/stage7_post_box_learned_overlay_bonus001_10_h40.json")),
            ("learned_overlay_default_off_10_h40", Path("reports/structural_candidates/stage7_post_box_learned_overlay_default_off_10_h40.json")),
            ("narrow_on_25_h40", Path("reports/structural_candidates/stage7_post_box_narrow_on_25_h40.json")),
        ]
        for name, path in default_diagnostics:
            if path.exists():
                diagnostics.append((name, _load_json(path)))
                evidence_artifacts.append(str(path))
    trajectory_seed = _load_json(args.trajectory_seed)
    learned_model = _load_json(args.learned_model) if args.learned_model and args.learned_model.exists() else None

    candidate = build_plan_capsule_candidate(evidence_artifacts=evidence_artifacts)
    audit = build_audit(
        diagnostics=diagnostics,
        trajectory_seed=trajectory_seed,
        learned_overlay_model=learned_model,
    )
    args.candidate_output.parent.mkdir(parents=True, exist_ok=True)
    args.candidate_output.write_text(json.dumps(candidate, indent=2) + "\n", encoding="utf-8")
    args.audit_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_output.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    _write_candidate_md(candidate, args.candidate_md_output)
    _write_audit_md(audit, args.audit_md_output)
    if not args.no_json_stdout:
        print(json.dumps({"candidate": candidate, "audit": audit}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
