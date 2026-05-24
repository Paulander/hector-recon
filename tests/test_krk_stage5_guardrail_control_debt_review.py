#!/usr/bin/env python3
"""Tests for the Stage 5 guardrail control-debt review."""

import importlib.util
import json
from pathlib import Path


_spec = importlib.util.spec_from_file_location(
    "review_krk_stage5_guardrail_control_debt_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_stage5_guardrail_control_debt_v0.py",
)
assert _spec is not None
assert _spec.loader is not None
_review = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_review)


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _stage5_payload() -> dict:
    return {
        "total": 4,
        "no_move": 0,
        "improved": 2,
        "worsened": 2,
        "optimal": 2,
        "playouts": {"mate": 4},
        "one_ply_status": "failed",
        "conversion_status": "passed",
        "shadow_candidate_count": 0,
        "label": "fence_established",
        "stagnation_breaker_king_support_bonus": 2.0,
        "early_stop_stable_suggestions": 2,
        "handoff_packet_counts_by_phase": {
            "post_own_move": {"failed": 2, "confirmed": 2},
            "playout_summary": {"confirmed": 4},
        },
        "handoff_packets": [
            {
                "phase": "post_own_move",
                "status": "failed",
                "achieved": ["visible_fence_contract_confirmed"],
                "failed": ["reward_confirmed.fence_established"],
                "evidence_terms": {
                    "fen": "7k/8/8/8/R7/8/5K2/8 w - - 0 1",
                    "move": "f2g3",
                    "chosen_reward": -0.75,
                    "oracle_reward": 0.149,
                    "reward_confirmed": False,
                    "visible_fence_contract_confirmed": True,
                    "fence_exists_after_own_move": True,
                    "fence_stable_after_own_move": False,
                    "cut_axis_after_own_move": "edge",
                    "rook_safe_after_own_move": True,
                    "box_area_after_own_move": 28,
                },
            },
            {
                "phase": "post_own_move",
                "status": "confirmed",
                "achieved": [
                    "reward_confirmed.fence_established",
                    "visible_fence_contract_confirmed",
                ],
                "failed": [],
                "evidence_terms": {
                    "fen": "4k3/R7/K7/8/8/8/8/8 w - - 0 1",
                    "move": "a7h7",
                    "chosen_reward": 0.074,
                    "oracle_reward": 0.074,
                    "reward_confirmed": True,
                    "visible_fence_contract_confirmed": True,
                    "fence_exists_after_own_move": True,
                    "fence_stable_after_own_move": False,
                    "cut_axis_after_own_move": "edge",
                    "rook_safe_after_own_move": True,
                    "box_area_after_own_move": 7,
                },
            },
        ],
    }


def test_stage5_control_debt_review_splits_conversion_from_one_ply_debt(tmp_path: Path):
    overlay = _write_json(tmp_path / "overlay.json", _stage5_payload())
    control = _write_json(tmp_path / "control.json", _stage5_payload())
    promotion = _write_json(
        tmp_path / "promotion.json",
        {
            "promotion_status": "overlay_only",
            "failures": [],
            "guardrail_control_debt": [{"kind": "guardrail_control_debt"}],
            "guardrail_deltas_vs_control": [{"regressed_vs_control": False}],
        },
    )
    inspection = _write_json(
        tmp_path / "inspection.json",
        {"status": "stage6_gap_explained_by_validation_profile_mismatch"},
    )

    review = _review.build_review(
        overlay_artifact=overlay,
        base_control_artifact=control,
        promotion_eval_artifact=promotion,
        inspection_artifact=inspection,
    )

    assert review["status"] == "stage5_one_ply_guardrail_control_debt_confirmed"
    assert review["decision"]["stage5_conversion_preserved"] is True
    assert review["decision"]["stage5_one_ply_debt_reproduces_in_base_control"] is True
    assert review["decision"]["stage5_overlay_regressed_vs_base_control"] is False
    assert review["decision"]["should_quarantine_stage6_overlay_for_stage5_one_ply_debt"] is False
    assert review["decision"]["should_replace_protected_stack_now"] is False
    assert review["guardrail_definition_recommendation"]["split_required"] is True
    assert review["invariants"]["runtime_defaults_changed"] is False
    assert review["invariants"]["stage7_promotion"] is False
    assert review["invariants"]["stage8_training"] is False


def test_generated_stage5_control_debt_review_artifact_preserves_decision():
    path = Path("reports/krk_stage5_guardrail_control_debt_review_v0.json")
    assert path.exists()
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "krk_stage5_guardrail_control_debt_review.v0"
    assert payload["decision"]["stage5_overlay_regressed_vs_base_control"] is False
    assert payload["decision"]["stage5_conversion_preserved"] is True
    assert payload["decision"]["stage5_one_ply_debt_reproduces_in_base_control"] is True
    assert payload["decision"]["should_replace_protected_stack_now"] is False
    assert payload["guardrail_definition_recommendation"]["split_required"] is True
    assert payload["stage5_overlay"]["mate_rate"] == 1.0
    assert payload["stage5_base_control"]["mate_rate"] == 1.0
