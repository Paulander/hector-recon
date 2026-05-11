#!/usr/bin/env python3
"""Tests for offline shadow stem queue construction."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recon_lite_chess.routing import build_shadow_stem_queue


def test_build_shadow_stem_queue_deduplicates_and_prioritizes():
    candidates = [
        {
            "candidate_id": "cand.low",
            "trigger": "low_affordance_state",
            "parent_skill": "krk.fence_established",
            "state_signature": "state.a",
            "observed_outcome": "max_plies",
            "priority": 4,
            "packet_id": "packet.1",
        },
        {
            "candidate_id": "cand.loop",
            "trigger": "same_skill_loop_after_confirmation",
            "parent_skill": "krk.fence_established",
            "state_signature": "state.c",
            "observed_outcome": "max_plies",
            "packet_id": "packet.0",
        },
        {
            "candidate_id": "cand.reward_contract",
            "trigger": "reward_contract_mismatch",
            "parent_skill": "krk.fence_established",
            "state_signature": "state.e",
            "observed_outcome": "max_plies",
            "packet_id": "packet.5",
        },
        {
            "candidate_id": "cand.repeat",
            "trigger": "repeated_conversion_failure",
            "parent_skill": "krk.fence_established",
            "state_signature": "state.b",
            "observed_outcome": "max_plies",
            "priority": 1,
            "packet_id": "packet.2",
            "route_scores": {"krk.edge_trap_close": 0.01},
        },
        {
            "candidate_id": "cand.repeat.dup",
            "trigger": "repeated_conversion_failure",
            "parent_skill": "krk.fence_established",
            "state_signature": "state.b",
            "observed_outcome": "max_plies",
            "priority": 1,
            "packet_id": "packet.3",
        },
        {
            "candidate_id": "cand.maintenance",
            "trigger": "maintenance_needed_but_not_detected",
            "parent_skill": "krk.fence_established",
            "state_signature": "state.d",
            "observed_outcome": "max_plies",
            "packet_id": "packet.4",
        },
    ]

    queue = build_shadow_stem_queue(candidates).to_dict()

    assert queue["schema_version"] == "shadow_stem_queue.v1"
    assert queue["trigger_counts"] == {
        "repeated_conversion_failure": 2,
        "same_skill_loop_after_confirmation": 1,
        "reward_contract_mismatch": 1,
        "maintenance_needed_but_not_detected": 1,
        "low_affordance_state": 1,
    }
    assert len(queue["queue"]) == 5
    assert queue["queue"][0]["trigger"] == "repeated_conversion_failure"
    assert queue["queue"][0]["support"] == 2
    assert queue["queue"][0]["packet_ids"] == ["packet.2", "packet.3"]
    assert {
        queue["queue"][1]["trigger"],
        queue["queue"][2]["trigger"],
    } == {"reward_contract_mismatch", "same_skill_loop_after_confirmation"}
    assert queue["queue"][3]["trigger"] == "maintenance_needed_but_not_detected"
    assert queue["queue"][4]["trigger"] == "low_affordance_state"
