#!/usr/bin/env python3
"""Tests for KRK counterfactual sweep helpers."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from sweep_krk_counterfactual_successors import _audit_term_set, _parse_terms


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
