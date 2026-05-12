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
        "one_ply_status_counts": {"passed": 1},
        "conversion_status_counts": {"failed": 1},
        "semantic_alignment_status_counts": {"reward_contract_mismatch": 1},
        "conversion_by_semantic_alignment_status": {
            "reward_contract_mismatch": {"max_plies": 1}
        },
        "semantic_alignment_confusion_counts": {
            "reward=true|visible_fence=false|fence_survived_reply=false|conversion=max_plies": 1
        },
        "semantic_alignment_snapshots": {
            "reward_contract_mismatch": [
                {
                    "sample": 0,
                    "start_fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "move": "a1a8",
                    "post_reply_fen": "8/8/8/8/8/8/8/8 w - - 1 1",
                    "conversion_result": "max_plies",
                }
            ]
        },
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
                    "selected_despite_contract_mismatch": True,
                    "visible_eligible_successors": {"krk.fence_maintenance": {"score": 0.5}},
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
    assert payload["selected_successor_outcome_counts"] == {"krk.edge_trap_close:max_plies": 1}
    assert payload["failure_class_by_successor_counts"] == {
        "krk.edge_trap_close:successor_conflict": 1
    }
    assert payload["contract_mismatch_count"] == 1
    assert payload["contract_mismatch_by_successor_counts"] == {"krk.edge_trap_close": 1}
    assert payload["visible_eligible_successor_counts"] == {"krk.fence_maintenance": 1}
    assert payload["semantic_alignment_status_counts"] == {"reward_contract_mismatch": 1}
    assert payload["conversion_by_semantic_alignment_status"] == {
        "reward_contract_mismatch": {"max_plies": 1}
    }
    assert payload["semantic_alignment_confusion_counts"] == {
        "reward=true|visible_fence=false|fence_survived_reply=false|conversion=max_plies": 1
    }
    assert "reward_contract_mismatch" in payload["semantic_alignment_snapshots"]
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


def test_analyze_handoff_records_counts_repeated_packets_as_samples():
    packet = {
        "from_skill": "krk.fence_established",
        "phase": "post_opponent_reply",
        "status": "confirmed",
        "observed_outcome": "max_plies",
        "evidence_terms": {
            "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
            "successor_selected_skill": "krk.stage0_basin",
            "handoff_gap": False,
            "route_conflict": False,
            "failure_classes": ["selected_successor_miscalibrated"],
        },
    }
    diagnostic = {
        "total": 2,
        "one_ply_status_counts": {"passed": 2},
        "conversion_status_counts": {"failed": 2},
        "handoff_packets": [dict(packet), dict(packet)],
    }

    analysis = analyze_handoff_records([diagnostic]).to_dict()

    assert analysis["one_ply_status_counts"] == {"passed": 2}
    assert analysis["conversion_status_counts"] == {"failed": 2}
    assert analysis["successor_selected_skill_counts"] == {"krk.stage0_basin": 2}
    assert analysis["failure_class_counts"] == {"selected_successor_miscalibrated": 2}


def test_analyze_handoff_records_summarizes_counterfactual_sweeps():
    diagnostic = {
        "total": 2,
        "counterfactual_successor_sweeps": [
            {
                "actual_selected_successor": "krk.stage0_basin",
                "actual_result": "max_plies",
                "counterfactual_results": {
                    "krk.edge_trap_close": {
                        "result": "mate",
                        "forced_successor_available": True,
                    },
                    "krk.fence_established": {
                        "result": "max_plies",
                        "forced_successor_available": True,
                    },
                },
            },
            {
                "actual_selected_successor": "krk.fence_established",
                "actual_result": "max_plies",
                "counterfactual_results": {
                    "krk.edge_trap_close": {
                        "result": "max_plies",
                        "forced_successor_available": False,
                    },
                    "krk.fence_established": {
                        "result": "max_plies",
                        "forced_successor_available": True,
                    },
                },
            },
        ],
    }

    analysis = analyze_handoff_records([diagnostic]).to_dict()

    assert analysis["counterfactual_successor_sweep_count"] == 2
    assert analysis["counterfactual_sweeps_with_any_mate"] == 1
    assert analysis["counterfactual_sweeps_without_any_mate"] == 1
    assert analysis["counterfactual_best_mating_successor_counts"] == {
        "krk.edge_trap_close": 1
    }
    assert analysis["counterfactual_forced_successor_outcome_counts"] == {
        "krk.edge_trap_close:max_plies": 1,
        "krk.edge_trap_close:mate": 1,
        "krk.fence_established:max_plies": 2,
    }
    assert analysis["counterfactual_forced_successor_available_counts"] == {
        "krk.edge_trap_close:available": 1,
        "krk.edge_trap_close:unavailable": 1,
        "krk.fence_established:available": 2,
    }
    assert analysis["counterfactual_actual_to_forced_outcome_counts"] == {
        "krk.fence_established->krk.edge_trap_close:max_plies": 1,
        "krk.fence_established->krk.fence_established:max_plies": 1,
        "krk.stage0_basin->krk.edge_trap_close:mate": 1,
        "krk.stage0_basin->krk.fence_established:max_plies": 1,
    }


def test_handoff_analysis_markdown_is_human_readable():
    analysis = analyze_handoff_records([{"total": 0, "handoff_packets": []}])

    markdown = analysis.to_markdown()

    assert "# KRK Handoff Analysis" in markdown
    assert "Recommended Next Actions" in markdown
