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
            )
        )

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
