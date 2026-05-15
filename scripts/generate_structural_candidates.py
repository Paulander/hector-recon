#!/usr/bin/env python3
"""Generate non-causal structural growth candidates from diagnostic artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from recon_lite_chess.routing import StructuralCandidate


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _shadow_count(payload: dict[str, Any]) -> int:
    count = int(payload.get("shadow_candidate_count", 0) or 0)
    if count:
        return count
    candidates = payload.get("shadow_candidates")
    return len(candidates) if isinstance(candidates, list) else 0


def _playout_count(payload: dict[str, Any], key: str) -> int:
    return int((payload.get("playouts") or {}).get(key, 0) or 0)


def _base_governor_rules() -> dict[str, Any]:
    return {
        "schema_version": "growth_governor_rules.v0",
        "max_active_candidates_per_stage": 3,
        "max_promoted_overlays_per_stage_before_settling": 1,
        "require_candidate_resolution_before_next_overlay": True,
        "block_growth_if_guardrails_regress": True,
        "prefer_settling_if_conversion_rate_improving": True,
        "require_repeated_failure_family_before_growth": True,
    }


def _unique_failed_family_count(payload: dict[str, Any]) -> int:
    signatures = set()
    for packet in payload.get("handoff_packets") or []:
        if not isinstance(packet, dict) or packet.get("phase") != "post_opponent_reply":
            continue
        evidence = packet.get("evidence_terms")
        if not isinstance(evidence, dict):
            continue
        if str(evidence.get("playout_result") or "") == "mate":
            continue
        signature = evidence.get("post_reply_state_signature") or evidence.get("post_reply_fen")
        if signature:
            signatures.add(str(signature))
    return len(signatures)


def _growth_governor_metadata(
    diagnostic: dict[str, Any],
    promotion_eval: dict[str, Any],
    *,
    active_candidate_count: int = 0,
) -> dict[str, Any]:
    total = int(diagnostic.get("total", 0) or 0)
    mate_count = _playout_count(diagnostic, "mate")
    max_plies_count = _playout_count(diagnostic, "max_plies")
    shadow_count = _shadow_count(diagnostic)
    semantic_counts = diagnostic.get("semantic_alignment_status_counts") or {}
    shadow_triggers = diagnostic.get("shadow_trigger_counts") or {}
    guardrails = promotion_eval.get("guardrails") or []
    if isinstance(guardrails, list) and guardrails:
        passed_guardrails = sum(1 for item in guardrails if isinstance(item, dict) and item.get("passed"))
        guardrail_pass_rate = passed_guardrails / len(guardrails)
    else:
        guardrail_pass_rate = 0.0 if promotion_eval.get("promotion_status") == "quarantine" else None
    repeated_failure_family_count = _unique_failed_family_count(diagnostic)
    if not repeated_failure_family_count:
        repeated_failure_family_count = int(shadow_triggers.get("repeated_conversion_failure", 0) or 0)
    return {
        "schema_version": "growth_governor_snapshot.v0",
        "rules": _base_governor_rules(),
        "metrics": {
            "episodes_since_last_structural_change": None,
            "recent_conversion_rate_history": [
                (mate_count / total) if total else 0.0,
            ],
            "recent_shadow_candidate_rate": (shadow_count / total) if total else 0.0,
            "repeated_failure_family_count": repeated_failure_family_count,
            "route_conflict_rate": float(shadow_triggers.get("route_conflict", 0) or 0) / total if total else 0.0,
            "handoff_gap_rate": float(shadow_triggers.get("handoff_gap", 0) or 0) / total if total else 0.0,
            "reward_contract_mismatch_rate": (
                float(semantic_counts.get("reward_contract_mismatch", 0) or 0) / total if total else 0.0
            ),
            "guardrail_pass_rate": guardrail_pass_rate,
            "weight_delta_magnitude": None,
            "weight_saturation_rate": None,
            "plasticity_improvement_slope": None,
            "active_candidate_count": active_candidate_count,
            "provider_maturity": "quarantined_no_plasticity"
            if promotion_eval.get("promotion_status") == "quarantine"
            else "candidate_high_plasticity",
            "promotion_status": promotion_eval.get("promotion_status") or "unknown",
            "mate_count": mate_count,
            "max_plies_count": max_plies_count,
            "shadow_candidate_count": shadow_count,
        },
        "performance": {
            "wall_time": diagnostic.get("wall_time"),
            "samples": total,
            "workers": (diagnostic.get("parallel_validation") or {}).get("workers"),
            "cache_hits_misses": {
                "context_terms_hits": diagnostic.get("context_terms_cache_hits"),
                "context_terms_misses": diagnostic.get("context_terms_cache_misses"),
                "move_shape_audit_hits": diagnostic.get("move_shape_audit_cache_hits"),
                "move_shape_audit_misses": diagnostic.get("move_shape_audit_cache_misses"),
            },
            "engine_decisions": diagnostic.get("playout_engine_decision_count"),
            "engine_ticks": diagnostic.get("playout_engine_ticks_total"),
            "teacher_features_calls": diagnostic.get("teacher_features_calls"),
            "goal_distance_calls": diagnostic.get("goal_distance_calls"),
            "worst_reply_reward_calls": diagnostic.get("worst_reply_reward_calls"),
            "trace_mode": "diagnostic_packets",
        },
    }


def _growth_status_for_candidate(
    *,
    candidate_type: str,
    conversion_failed: bool,
    shadow_support_high: bool,
    promotion_eval: dict[str, Any],
    repeated_failure_family_count: int,
) -> str:
    if promotion_eval.get("promotion_status") == "quarantine" and candidate_type == "quarantine_overlay":
        return "growth_blocked_by_guardrail"
    if conversion_failed and shadow_support_high and repeated_failure_family_count > 0:
        return "growth_allowed"
    if conversion_failed:
        return "needs_more_weight_training"
    return "settling"


def _initial_topology_weight_diagnosis(*, candidate_type: str) -> dict[str, Any]:
    labels: list[str]
    if candidate_type == "contract_refinement":
        labels = ["topology_underbroad"]
    elif candidate_type == "successor_contract_refinement":
        labels = ["parameter_miscalibrated"]
    elif candidate_type == "quarantine_overlay":
        labels = ["quarantined_after_calibration_budget"]
    else:
        labels = []
    return {
        "schema_version": "topology_weight_diagnosis.v0",
        "frozen_weight_probe_result": "not_run",
        "forced_oracle_probe_result": "not_run",
        "bounded_m3_warmup_result": "not_run",
        "bounded_m4_consolidation_result": "not_run",
        "guardrail_delta": None,
        "weight_saturation": "unknown",
        "candidate_locality": "stage7_box_shrink",
        "candidate_complexity": "small",
        "diagnostic_labels": labels,
        "evaluation_phases": {
            "phase_0_static_sanity": "pending",
            "phase_1_frozen_weight_probe": "pending",
            "phase_2_forced_oracle_probe": "pending",
            "phase_3_bounded_plasticity_warmup": "pending",
            "phase_4_bounded_m4_consolidation_probe": "pending",
            "phase_5_guardrail_validation": "pending",
            "phase_6_promote_quarantine_reject": "pending",
        },
    }


def generate_stage7_box_shrink_candidates(
    *,
    diagnostic_path: Path,
    analysis_path: Path | None = None,
    promotion_eval_path: Path | None = None,
    shadow_threshold: int = 1,
) -> list[StructuralCandidate]:
    diagnostic = _load_json(diagnostic_path)
    promotion_eval = _load_json(promotion_eval_path) if promotion_eval_path else {}
    analysis_text = analysis_path.read_text(encoding="utf-8") if analysis_path and analysis_path.exists() else ""
    evidence_artifacts = [str(diagnostic_path)]
    if analysis_path is not None:
        evidence_artifacts.append(str(analysis_path))
    if promotion_eval_path is not None:
        evidence_artifacts.append(str(promotion_eval_path))

    failure_classes = set()
    shadow_triggers = diagnostic.get("shadow_trigger_counts") or {}
    failure_classes.update(str(key) for key, value in shadow_triggers.items() if int(value or 0) > 0)
    failure_class_counts = diagnostic.get("failure_class_counts") or {}
    failure_classes.update(str(key) for key, value in failure_class_counts.items() if int(value or 0) > 0)
    if "selected_successor_miscalibrated" in analysis_text:
        failure_classes.add("selected_successor_miscalibrated")
    if "reward_contract_mismatch" in analysis_text:
        failure_classes.add("reward_contract_mismatch")
    if "repeated_conversion_failure" in analysis_text:
        failure_classes.add("repeated_conversion_failure")

    conversion_failed = str(diagnostic.get("conversion_status")) == "failed" or _playout_count(
        diagnostic, "max_plies"
    ) > 0
    shadow_support_high = _shadow_count(diagnostic) >= int(shadow_threshold)
    target_skill = "krk.box_shrink"
    parent_skill = "krk.drive_to_edge"
    candidates: list[StructuralCandidate] = []
    governor_metadata = _growth_governor_metadata(
        diagnostic,
        promotion_eval,
        active_candidate_count=0,
    )
    repeated_family_count = int(
        governor_metadata.get("metrics", {}).get("repeated_failure_family_count", 0) or 0
    )

    semantic_counts = diagnostic.get("semantic_alignment_status_counts") or {}
    reward_mismatch_count = int(semantic_counts.get("reward_contract_mismatch", 0) or 0)
    if reward_mismatch_count and (conversion_failed or shadow_support_high):
        candidates.append(
            StructuralCandidate(
                candidate_id="cand.krk.box_shrink.reward_contract_refinement.v1",
                candidate_type="contract_refinement",
                source_monitor_script="growth.monitor.reward_contract_mismatch",
                source_terms=[
                    "reward_confirmed",
                    "visible_contract_not_confirmed",
                    "conversion_failed" if conversion_failed else "conversion_not_checked",
                    "shadow_support_high" if shadow_support_high else "shadow_support_low",
                ],
                trigger_failure_classes=sorted(
                    failure_classes
                    | {"reward_contract_mismatch", "selected_successor_miscalibrated", "repeated_conversion_failure"}
                ),
                target_skill=target_skill,
                parent_skill=parent_skill,
                proposed_change={
                    "kind": "visible_contract_audit",
                    "suggested_terms": [
                        "box_area_decreased_after_own_move",
                        "box_area_not_increased_after_reply",
                        "fence_or_cut_preserved",
                        "rook_safe_after_reply",
                        "enemy_king_mobility_reduced",
                    ],
                    "audit_questions": [
                        "Does box_shrink reward confirm true visible box contraction?",
                        "Which post-reply box/fence terms are missing in max_plies cases?",
                    ],
                },
                evidence_artifacts=evidence_artifacts,
                promotion_status="proposed",
                governor_status=_growth_status_for_candidate(
                    candidate_type="contract_refinement",
                    conversion_failed=conversion_failed,
                    shadow_support_high=shadow_support_high,
                    promotion_eval=promotion_eval,
                    repeated_failure_family_count=repeated_family_count,
                ),
                governor_metadata=governor_metadata,
                topology_weight_diagnosis=_initial_topology_weight_diagnosis(
                    candidate_type="contract_refinement"
                ),
                candidate_diagnostic_labels=["topology_underbroad"],
            )
        )

    max_plies = _playout_count(diagnostic, "max_plies")
    if max_plies and (
        "selected_successor_miscalibrated" in failure_classes
        or "high_score_conversion_failure" in failure_classes
        or "repeated_conversion_failure" in failure_classes
    ):
        candidates.append(
            StructuralCandidate(
                candidate_id="cand.krk.box_shrink.handoff_role_refinement.v1",
                candidate_type="successor_contract_refinement",
                source_monitor_script="growth.monitor.successor_miscalibration",
                source_terms=[
                    "selected_successor_miscalibrated",
                    "repeated_conversion_failure",
                    "high_score_conversion_failure",
                ],
                trigger_failure_classes=sorted(
                    failure_classes
                    | {"selected_successor_miscalibrated", "repeated_conversion_failure"}
                ),
                target_skill=target_skill,
                parent_skill=parent_skill,
                proposed_change={
                    "kind": "handoff_role_audit",
                    "suspect_successor": "krk.stage0_basin",
                    "candidate_roles": [
                        "krk.box_shrink_to_edge_trap_handoff",
                        "krk.box_shrink_to_drive_repair",
                        "krk.box_shrink_post_reply_continuation",
                    ],
                    "audit_questions": [
                        "When box_shrink confirms locally, which successor should own continuation?",
                        "Is stage0_basin being selected as a generic fallback after box_shrink?",
                    ],
                },
                evidence_artifacts=evidence_artifacts,
                promotion_status="proposed",
                governor_status=_growth_status_for_candidate(
                    candidate_type="successor_contract_refinement",
                    conversion_failed=conversion_failed,
                    shadow_support_high=shadow_support_high,
                    promotion_eval=promotion_eval,
                    repeated_failure_family_count=repeated_family_count,
                ),
                governor_metadata=governor_metadata,
                topology_weight_diagnosis=_initial_topology_weight_diagnosis(
                    candidate_type="successor_contract_refinement"
                ),
                candidate_diagnostic_labels=["parameter_miscalibrated"],
            )
        )

    promotion_status = str(promotion_eval.get("promotion_status") or "")
    if promotion_status == "quarantine" or shadow_support_high:
        candidates.append(
            StructuralCandidate(
                candidate_id="cand.krk.box_shrink.overlay_quarantine_confirmed.v1",
                candidate_type="quarantine_overlay",
                source_monitor_script="growth.monitor.stage_overlay_quarantine",
                source_terms=[
                    "target_stage_local_success",
                    "target_stage_conversion_failure",
                    "shadow_candidates_above_threshold",
                ],
                trigger_failure_classes=sorted(failure_classes | {"stage_overlay_quarantine"}),
                target_skill=target_skill,
                parent_skill=parent_skill,
                proposed_change={
                    "kind": "promotion_gate_record",
                    "promotion_status": "quarantined",
                    "next_required_action": "candidate_driven_semantic_audit",
                    "guardrail_rule": "do_not_promote_until_target_conversion_and_shadow_candidates_pass",
                },
                evidence_artifacts=evidence_artifacts,
                promotion_status="quarantined",
                governor_status=_growth_status_for_candidate(
                    candidate_type="quarantine_overlay",
                    conversion_failed=conversion_failed,
                    shadow_support_high=shadow_support_high,
                    promotion_eval=promotion_eval,
                    repeated_failure_family_count=repeated_family_count,
                ),
                governor_metadata=governor_metadata,
                topology_weight_diagnosis=_initial_topology_weight_diagnosis(
                    candidate_type="quarantine_overlay"
                ),
                candidate_diagnostic_labels=["quarantined_after_calibration_budget"],
            )
        )

    for candidate in candidates:
        candidate.governor_metadata["metrics"]["active_candidate_count"] = len(candidates)
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate structural growth candidates")
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--analysis", type=Path, default=None)
    parser.add_argument("--promotion-eval", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--shadow-threshold", type=int, default=1)
    args = parser.parse_args()

    candidates = generate_stage7_box_shrink_candidates(
        diagnostic_path=args.diagnostic,
        analysis_path=args.analysis,
        promotion_eval_path=args.promotion_eval,
        shadow_threshold=args.shadow_threshold,
    )
    payload = {
        "schema_version": "structural_candidate_set.v1",
        "source_stage": "stage7_box_shrink",
        "candidate_count": len(candidates),
        "candidates": [candidate.to_dict() for candidate in candidates],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
