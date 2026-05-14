#!/usr/bin/env python3
"""Tests for KRK counterfactual sweep helpers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from sweep_krk_counterfactual_successors import (
    _audit_term_set,
    _parse_terms,
    _summarize_continuation_trace,
    summarize_continuation_trace_audits,
    summarize_provider_suggestion_audits,
)


def test_parse_terms_ignores_empty_items():
    assert _parse_terms("rook_transfer_vertical,, rook_to_edge_rank ") == (
        "rook_transfer_vertical",
        "rook_to_edge_rank",
    )


def test_audit_term_set_combines_visible_move_shape_sections():
    terms = _audit_term_set({
        "current_terms": ["fence_exists"],
        "move_shape_terms": ["candidate_is_rook_transfer"],
        "post_move_terms": ["rook_safe_after_move"],
        "worst_reply_terms": ["no_draw_after_worst_reply"],
    })

    assert terms == {
        "fence_exists",
        "candidate_is_rook_transfer",
        "rook_safe_after_move",
        "no_draw_after_worst_reply",
    }


def test_provider_suggestion_audit_summary_counts_failure_classes():
    summary = summarize_provider_suggestion_audits([
        {
            "provider_suggestion_audit": {
                "failure_class": "converting_move_not_proposed",
                "converting_not_proposed": ["h7e7", "h7f7"],
                "converting_suggested": [],
                "selected_converts": False,
            }
        },
        {
            "provider_suggestion_audit": {
                "failure_class": "selected_converting_move",
                "converting_not_proposed": [],
                "converting_suggested": ["h7h1"],
                "selected_converts": True,
            }
        },
    ])

    assert summary["total_audits"] == 2
    assert summary["failure_class_counts"]["converting_move_not_proposed"] == 1
    assert summary["converting_not_proposed_count"] == 2
    assert summary["converting_proposed_not_selected_count"] == 1
    assert summary["selected_converting_count"] == 1


def test_continuation_trace_summary_extracts_selected_skill():
    trace = [
        {
            "ply": 0,
            "turn": "white",
            "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
            "move": "h7d7",
            "resulting_fen": "8/8/8/8/8/8/8/8 b - - 1 1",
            "engine": {
                "move": "h7d7",
                "confidence": 0.14,
                "ticks": 8,
                "early_stopped": True,
                "suggestions": [
                    {
                        "move": "h7d7",
                        "score": 0.14,
                        "meta": {"curriculum_label": "edge_trap_close"},
                    }
                ],
            },
        }
    ]

    summary = _summarize_continuation_trace(trace)

    assert summary[0]["selected_skill"] == "krk.edge_trap_close"
    assert summary[0]["top_suggestions"][0]["move"] == "h7d7"


def test_continuation_trace_audit_summary_counts_results():
    summary = summarize_continuation_trace_audits([
        {"continuation_trace_audit": {"result": "mate", "first_move": "h7d7"}},
        {"continuation_trace_audit": {"result": "max_plies", "first_move": "h7d7"}},
    ])

    assert summary["total_audits"] == 2
    assert summary["result_counts"] == {"mate": 1, "max_plies": 1}
    assert summary["first_move_counts"] == {"h7d7": 2}
