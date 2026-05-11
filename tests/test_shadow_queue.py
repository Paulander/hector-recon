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
    ]

    queue = build_shadow_stem_queue(candidates).to_dict()

    assert queue["schema_version"] == "shadow_stem_queue.v1"
    assert queue["trigger_counts"] == {
        "repeated_conversion_failure": 2,
        "low_affordance_state": 1,
    }
    assert len(queue["queue"]) == 2
    assert queue["queue"][0]["trigger"] == "repeated_conversion_failure"
    assert queue["queue"][0]["support"] == 2
    assert queue["queue"][0]["packet_ids"] == ["packet.2", "packet.3"]
    assert queue["queue"][1]["trigger"] == "low_affordance_state"
