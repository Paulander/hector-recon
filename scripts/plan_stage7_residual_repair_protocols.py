#!/usr/bin/env python3
"""Plan non-causal Stage 7 residual repair sandbox protocols.

This script consumes the residual StructuralCandidate updates emitted from the
Plan Capsule family split and converts them into explicit sandbox protocols.
It does not compile topology, train weights, or change runtime routing.
"""

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


def _candidate_by_id(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for item in payload.get("structural_candidates") or []:
        if isinstance(item, dict) and item.get("candidate_id"):
            # Validate the boundary while normalizing.
            StructuralCandidate.from_dict(json.loads(json.dumps(item)))
            out[str(item["candidate_id"])] = item
    return out


def build_residual_protocols(candidate_payload: dict[str, Any]) -> dict[str, Any]:
    candidates = _candidate_by_id(candidate_payload)
    protocols: list[dict[str, Any]] = []

    drive = candidates.get("cand.krk.box_shrink.family_069.drive_role_refinement.v1")
    if drive:
        protocols.append(
            {
                "protocol_id": "stage7.residual.069.drive_role_refinement.rejected_general_priority",
                "source_candidate_id": drive["candidate_id"],
                "status": "rejected_as_general_priority_rule",
                "causal_status": "non_causal",
                "promotion_status": "rejected",
                "reason": [
                    "targeted_family_improved",
                    "25_sample_target_regressed",
                    "visible_terms_do_not_yet_separate_safe_general_use",
                ],
                "do_not_compile": True,
                "required_before_reconsideration": [
                    "find additional visible terms separating 069-like drive repair from other post-box states",
                    "prove default-off equivalence",
                    "prove 25-sample target non-regression before guardrails",
                ],
            }
        )

    king = candidates.get("cand.krk.box_shrink.family_0926.king_support_fence_stabilizer.v1")
    if king:
        protocols.append(
            {
                "protocol_id": "stage7.residual.0926.king_support_fence_stabilizer.sandbox_design",
                "source_candidate_id": king["candidate_id"],
                "status": "sandbox_design_ready",
                "causal_status": "non_causal",
                "promotion_status": "proposed",
                "repair_kind": "visible_move_shape_role",
                "entry_terms": [
                    "plan_capsule_entry_confirmed",
                    "post_box_shrink_continuation_active",
                    "rook_safe",
                    "conversion_not_immediate",
                    "no_mate_in_one_available",
                ],
                "move_shape_required_terms": [
                    "candidate_is_king_move",
                    "king_moves_toward_enemy",
                    "king_moves_toward_rook_support",
                ],
                "post_move_required_terms": [
                    "rook_safe_after_move",
                    "box_area_not_increased_after_move",
                    "fence_exists_after_move",
                    "fence_stable_after_move",
                    "cut_preserved_after_move",
                    "white_king_distance_to_enemy_decreases",
                    "white_king_distance_to_rook_decreases",
                ],
                "sandbox_validation": [
                    "default_off_equivalence",
                    "targeted_state_0926_replay_h40",
                    "10_sample_stage7_smoke_h40",
                    "25_sample_stage7_target_h40_only_if_smoke_non_regresses",
                    "guardrails_only_if_target_improves",
                ],
                "runtime_constraints_if_later_compiled": [
                    "default_off",
                    "bounded_by_plan_capsule_ttl",
                    "direct_request_false",
                    "trace_selected_move_shape_terms",
                    "no_state_hash_exception",
                ],
            }
        )

    overlay = candidates.get("cand.krk.box_shrink.family_2cc.post_box_continuation_overlay.v1")
    if overlay:
        protocols.append(
            {
                "protocol_id": "stage7.residual.2cc.narrow_post_box_overlay.training_protocol",
                "source_candidate_id": overlay["candidate_id"],
                "status": "training_protocol_ready_not_run",
                "causal_status": "non_causal",
                "promotion_status": "proposed",
                "repair_kind": "narrow_overlay_training_candidate",
                "training_scope": {
                    "include": [
                        "post_box_shrink_continuation_states",
                        "dtm_won_within_h40",
                        "existing_providers_fail_forced_h40",
                        "legal_first_current_continuation_fails_h50",
                    ],
                    "exclude": [
                        "generic_full_krk",
                        "stage8_training",
                        "states_without_plan_capsule_entry",
                    ],
                },
                "plasticity_policy": [
                    "candidate_high_plasticity_only_inside_sandbox",
                    "validated_base_and_stage6_providers_frozen",
                    "no_m4_consolidation_until_target_and_guardrails_pass",
                    "quarantine_if_guardrails_regress",
                ],
                "sandbox_validation": [
                    "static_metadata_sanity",
                    "frozen_weight_probe",
                    "forced_oracle_probe",
                    "bounded_m3_warmup_candidate_local_only",
                    "target_stage7_h40",
                    "stage6_stage5_stage4_stage1_guardrails_only_after_target_improves",
                ],
                "runtime_constraints_if_later_compiled": [
                    "default_off",
                    "domain_scoped_to_krk_stage7_profile",
                    "visible_entry_progress_exit_abort_terms",
                    "no_tablebase_or_dtm_runtime_policy",
                    "no_live_topology_mutation",
                ],
            }
        )

    return {
        "schema_version": "stage7_residual_repair_protocols.v1",
        "causal_status": "non_causal",
        "stage7_status": "local_valid_composition_quarantined",
        "source_candidate_artifact": candidate_payload.get("schema_version"),
        "protocol_count": len(protocols),
        "protocols": protocols,
        "global_boundaries": [
            "do_not_promote_stage7",
            "do_not_train_stage8",
            "do_not_add_broad_provider_bonus",
            "do_not_add_broad_provider_penalty",
            "do_not_mutate_topology_during_gameplay",
            "handoff_packets_stats_shadow_candidates_structural_candidates_remain_non_causal",
        ],
        "recommended_order": [
            "0926_visible_move_shape_role_default_off_sandbox",
            "2cc_narrow_overlay_training_protocol_only_if_0926_does_not_generalize",
        ],
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Residual Repair Protocols",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"Stage 7 status: `{payload['stage7_status']}`",
        f"Protocols: `{payload['protocol_count']}`",
        "",
        "## Protocols",
        "",
    ]
    for protocol in payload.get("protocols") or []:
        lines.append(f"### {protocol['protocol_id']}")
        lines.append("")
        lines.append(f"- Source candidate: `{protocol['source_candidate_id']}`")
        lines.append(f"- Status: `{protocol['status']}`")
        lines.append(f"- Repair kind: `{protocol.get('repair_kind', 'none')}`")
        lines.append(f"- Promotion status: `{protocol['promotion_status']}`")
        if protocol.get("reason"):
            lines.append(f"- Reason: `{', '.join(protocol['reason'])}`")
        lines.append("")
    lines.extend(["## Boundaries", ""])
    for item in payload.get("global_boundaries") or []:
        lines.append(f"- `{item}`")
    lines.extend(["", "## Recommended Order", ""])
    for item in payload.get("recommended_order") or []:
        lines.append(f"- `{item}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate_updates", type=Path)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = build_residual_protocols(_load_json(args.candidate_updates))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
