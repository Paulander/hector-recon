#!/usr/bin/env python3
"""Tests for offline handoff diagnostic aggregation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from recon_lite_chess.routing import analyze_handoff_records


def test_analyze_handoff_records_surfaces_successor_failure_motifs():
    diagnostic = {
        "total": 1,
        "no_move": 0,
        "one_ply_status": "passed",
        "conversion_status": "failed",
        "playouts": {"max_plies": 1},
        "handoff_packets": [
            {
                "from_skill": "krk.fence_established",
                "phase": "post_own_move",
                "status": "confirmed",
                "observed_outcome": "local_landmark_confirmed",
                "evidence_terms": {
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "move": "a1a8",
                },
            },
            {
                "from_skill": "krk.fence_established",
                "phase": "post_opponent_reply",
                "status": "failed",
                "observed_outcome": "max_plies",
                "evidence_terms": {
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "successor_selected_skill": "krk.edge_trap_close",
                    "handoff_gap": True,
                    "route_conflict": True,
                    "failure_classes": ["successor_conflict"],
                },
            },
            {
                "from_skill": "krk.fence_established",
                "phase": "playout_summary",
                "status": "failed",
                "observed_outcome": "max_plies",
                "evidence_terms": {
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "conversion_status": "failed",
                    "playout_result": "max_plies",
                },
            },
        ],
    }
    shadow = {
        "trigger": "handoff_gap",
        "parent_skill": "krk.fence_established",
        "observed_outcome": "max_plies",
    }

    analysis = analyze_handoff_records([diagnostic], shadow_candidates=[shadow])
    payload = analysis.to_dict()

    assert payload["total_evaluated"] == 1
    assert payload["one_ply_status_counts"] == {"passed": 1}
    assert payload["conversion_status_counts"] == {"failed": 1}
    assert payload["playout_counts"] == {"max_plies": 1}
    assert payload["post_reply_failure_count"] == 1
    assert payload["handoff_gap_count"] == 1
    assert payload["route_conflict_count"] == 1
    assert payload["successor_selected_skill_counts"] == {"krk.edge_trap_close": 1}
    assert payload["failed_successor_skill_counts"] == {"krk.edge_trap_close": 1}
    assert payload["failure_class_counts"] == {"successor_conflict": 1}
    assert payload["shadow_trigger_counts"] == {"handoff_gap": 1}
    assert payload["top_failure_motifs"][0]["from_skill"] == "krk.fence_established"
    assert payload["top_failure_motifs"][0]["successor_skill"] == "krk.edge_trap_close"
    assert payload["recommended_next_actions"]


def test_analyze_handoff_records_counts_embedded_shadow_candidates():
    diagnostic = {
        "total": 1,
        "handoff_packets": [],
        "shadow_candidates": [
            {"trigger": "route_conflict", "parent_skill": "krk.fence_established"}
        ],
    }

    analysis = analyze_handoff_records([diagnostic])

    assert analysis.to_dict()["shadow_trigger_counts"] == {"route_conflict": 1}


def test_handoff_analysis_markdown_is_human_readable():
    analysis = analyze_handoff_records([{"total": 0, "handoff_packets": []}])

    markdown = analysis.to_markdown()

    assert "# KRK Handoff Analysis" in markdown
    assert "Recommended Next Actions" in markdown
