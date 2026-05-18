#!/usr/bin/env python3
"""JSON round-trip tests for routing and handoff records."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recon_lite_chess.routing import (
    HandoffPacket,
    PlanCapsuleSpec,
    RouteDecision,
    ShadowStemCandidate,
    SkillContractSpec,
    SkillContractStats,
)


def _round_trip(record, cls):
    payload = record.to_dict()
    restored = cls.from_dict(json.loads(json.dumps(payload)))
    assert restored.to_dict() == payload
    assert payload["schema_version"].endswith(".v1")


def test_schema_round_trips():
    _round_trip(
        SkillContractSpec(
            skill_id="krk.fence_established",
            source_node_id="skill.krk.fence_established",
            scope="krk",
            affordance_terms=["affordance.krk.fence_established"],
            request_terms=["request.krk.fence_established"],
            confirmation_terms=["confirm.krk.fence_established"],
            continuation_exports={"krk.drive_to_edge": 0.4},
        ),
        SkillContractSpec,
    )
    _round_trip(SkillContractStats(skill_id="krk.fence_established"), SkillContractStats)
    _round_trip(
        RouteDecision(
            router_id="endgame_gate",
            router_kind="domain_endgame_gate",
            selected_route="kqk",
            route_scores={"kpk": 0.0, "kqk": 1.0},
            domain_approach_affordance={"kqk": 1.0},
            domain_execution_eligibility={"kqk": True},
            route_evidence={"kqk": {"material_is_kqk": True}},
        ),
        RouteDecision,
    )
    _round_trip(
        HandoffPacket.create(
            from_skill="kpk.promotion",
            to_skill="domain.kqk",
            phase="post_own_move",
            status="confirmed",
            evidence_terms={"pawn_promoted": True},
            continuation_exports={"domain.kqk": 1.0},
        ),
        HandoffPacket,
    )
    _round_trip(
        ShadowStemCandidate(
            trigger="handoff_gap",
            owner_router="krk.skill_hub",
            scope="krk",
            parent_skill="krk.fence_established",
            state_signature="fen:abc",
            route_scores={"krk.drive_to_edge": 0.1},
            packet_id="packet.test",
            observed_outcome="draw_loop",
            priority=2,
        ),
        ShadowStemCandidate,
    )
    _round_trip(
        PlanCapsuleSpec(
            capsule_id="krk.post_box_shrink_continuation",
            source_candidate_id="cand.krk.box_shrink.post_box_continuation_capsule.v1",
            source_monitor_script="growth.monitor.stage7_post_box_continuation_gap",
            source_terms=["local_valid_composition_quarantined"],
            domain="krk",
            target_skill="krk.box_shrink",
            entry_terms=["active_landmark_label.box_shrink", "post_reply_state_reached"],
            progress_terms=["box_area_decreases_or_does_not_expand"],
            exit_terms=["edge_trap_role_confirmed"],
            abort_terms=["rook_unsafe", "no_progress_after_owned_moves"],
            ttl_white_moves=3,
            owned_roles=["krk.post_box_shrink_continuation"],
            owned_providers=["krk.drive_to_edge", "krk.edge_trap_close"],
            handoff_exports={"krk.edge_trap_close": 0.4},
            training_source="reports/structural_candidates/stage7_post_box_dtm_trajectory_seed_h40.json",
            validation_protocol={"target": "Stage 7 h40"},
            guardrails=["stage6_drive_to_edge", "stage5_fence_established"],
            notes=["non-causal candidate only"],
        ),
        PlanCapsuleSpec,
    )


def main():
    test_schema_round_trips()
    print("routing contract schema round-trips passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
