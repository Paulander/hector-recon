#!/usr/bin/env python3
"""Export the non-causal Stage 7 0926 move-shape role candidate."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from recon_lite_chess.routing import MoveShapeRoleSpec, StructuralCandidate


CANDIDATE_ID = "cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1"
ROLE_ID = "krk.post_box.king_support_fence_stabilizer"


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _source_candidate(candidate_updates: dict[str, Any]) -> dict[str, Any]:
    for item in candidate_updates.get("structural_candidates") or []:
        if isinstance(item, dict) and item.get("candidate_id") == CANDIDATE_ID:
            StructuralCandidate.from_dict(json.loads(json.dumps(item)))
            return item
    raise ValueError(f"missing candidate {CANDIDATE_ID}")


def build_role_spec(candidate_updates: dict[str, Any]) -> dict[str, Any]:
    candidate = _source_candidate(candidate_updates)
    role = MoveShapeRoleSpec(
        role_id=ROLE_ID,
        source_candidate_id=CANDIDATE_ID,
        source_monitor_script="growth.monitor.stage7_plan_capsule_residual_family_split",
        source_terms=[
            "plan_capsule_entry_confirmed",
            "legal_first_move_converts_h40",
            "candidate_is_king_move",
            "king_moves_toward_enemy",
            "king_moves_toward_rook_support",
            "fence_stable_after_move",
            "cut_preserved_after_move",
        ],
        domain="krk",
        target_skill="krk.box_shrink",
        parent_capsule="krk.post_box_shrink_continuation",
        entry_terms=[
            "active_landmark_label.box_shrink",
            "post_reply_state_reached",
            "conversion_not_immediate",
            "rook_safe",
            "plan_capsule_entry_confirmed",
            "no_mate_in_one_available",
        ],
        move_shape_required_terms=[
            "candidate_is_king_move",
            "king_moves_toward_enemy",
            "king_moves_toward_rook_support",
        ],
        post_move_required_terms=[
            "rook_safe_after_move",
            "box_area_not_increased_after_move",
            "fence_exists_after_move",
            "fence_stable_after_move",
            "cut_preserved_after_move",
            "white_king_distance_to_enemy_decreases",
            "white_king_distance_to_rook_decreases",
        ],
        veto_terms=[
            "mate_in_one_available",
            "rook_unsafe_after_move",
            "draw_or_stalemate_risk",
            "box_area_increases_after_move",
            "cut_or_fence_lost_without_repair",
        ],
        provider_scope=[],
        handoff_exports={
            "krk.post_box_shrink_continuation": 1.0,
            "krk.stage0_basin": 0.25,
        },
        validation_protocol={
            "default_off_equivalence": True,
            "targeted_state": "state.0926f12f8e8f",
            "targeted_expected_move": "e4d3",
            "targeted_expected_result": "mate",
            "targeted_horizon": 40,
            "smoke_samples": 10,
            "target_samples": 25,
            "guardrails_after_target_improves": [
                "stage6_drive_to_edge",
                "stage5_fence_established",
                "stage4_wrong_tempo",
                "stage1_backchain",
                "m1_m4_preservation",
            ],
        },
        guardrails=[
            "no_runtime_default_change",
            "no_direct_request",
            "no_state_hash_exception",
            "no_topology_mutation_during_gameplay",
            "handoff_packets_stats_shadow_candidates_remain_non_causal",
        ],
        notes=[
            "This role is a visible move-shape hypothesis, not a hidden legal-move selector.",
            "Stage 7 0926 is the first test case; the role must generalize by visible terms.",
            "Do not compile this role unless default-off and traceability tests are added first.",
        ],
        promotion_status="proposed",
    )
    return {
        "schema_version": "stage7_0926_move_shape_role_export.v1",
        "causal_status": "non_causal",
        "structural_candidate": candidate,
        "move_shape_role": role.to_dict(),
        "evidence_artifacts": [
            "reports/structural_candidates/stage7_state0926_legal_first_h40.json",
            "reports/structural_candidates/stage7_plan_capsule_residual_forced_provider_h40.json",
            "reports/structural_candidates/stage7_plan_capsule_residual_candidate_updates.json",
        ],
        "next_action": "compile_default_off_sandbox_only_if_runtime_can expose candidate move generation visibly",
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    role = payload["move_shape_role"]
    lines = [
        "# Stage 7 0926 Move-Shape Role Candidate",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Role: `{role['role_id']}`",
        f"Source candidate: `{role['source_candidate_id']}`",
        f"Promotion status: `{role['promotion_status']}`",
        "",
        "## Entry Terms",
        "",
    ]
    for item in role["entry_terms"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Move-Shape Terms", ""])
    for item in role["move_shape_required_terms"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Post-Move Terms", ""])
    for item in role["post_move_required_terms"]:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Guardrails", ""])
    for item in role["guardrails"]:
        lines.append(f"- `{item}`")
    lines.extend(["", f"Next action: `{payload['next_action']}`"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_updates", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = build_role_spec(_load_json(args.candidate_updates))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
