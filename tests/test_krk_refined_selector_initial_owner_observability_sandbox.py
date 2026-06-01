#!/usr/bin/env python3
"""Tests for initial-owner-only refined selector observability sandbox v0."""

import importlib.util
import json
import random
import sys
from pathlib import Path

import chess

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_krk_candidate_generation_observation_sandbox_v0 import (
    _new_graph_engine,
    _profile_kwargs,
)
from scripts.test_krk_landmark_progress import choose_move_details, play_to_mate


ARTIFACT = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_observability_sandbox_v0.json"
)
REPORT = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_observability_sandbox_v0.md"
)


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _load_module():
    path = ROOT / "scripts/run_krk_refined_selector_initial_owner_observability_sandbox_v0.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _regression_case() -> dict:
    validation = _read_json(
        ROOT / "reports/strategy_arbitration/krk_selector_behavior_sandbox_validation_v0.json"
    )
    return next(row for row in validation["rows"] if row["row_id"] == "joined_trace_ownership_4")


def test_initial_owner_refined_selector_artifact_parses_and_decision_ready():
    payload = _read_json(ARTIFACT)
    markdown = REPORT.read_text(encoding="utf-8")

    assert payload["schema_version"] == (
        "krk_refined_selector_initial_owner_observability_sandbox.v0"
    )
    assert payload["sandbox_id"] == (
        "sandbox.krk.refined_selector_initial_owner_observability_v0"
    )
    assert payload["causal_status"] == (
        "recommendation_only_initial_owner_observability_sandbox"
    )
    assert payload["approval"]["flag_required"] == (
        "--enable-krk-refined-selector-observability"
    )
    assert payload["decision"]["status"] == (
        "refined_selector_initial_owner_observability_ready_for_recommendation_analysis"
    )
    assert payload["decision"]["status"] in payload["possible_statuses"]
    assert payload["decision"]["selector_runtime_ready"] is False
    assert "# KRK Refined Selector Initial Owner Observability Sandbox v0" in markdown
    json.dumps(payload)


def test_initial_owner_refined_selector_default_off_equivalence_summary():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["default_off_equivalence_passed"] is True
    assert summary["default_off_selector_recommendation_count"] == 0
    assert summary["enabled_recommendation_count"] == summary["attempted_row_count"]
    assert summary["continuation_recommendation_count"] == 0
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["selected_score_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert summary["runtime_behavior_changed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_provider_suppression"] is False


def test_initial_owner_refined_selector_enabled_metadata_scope_and_forbidden_actions():
    payload = _read_json(ARTIFACT)
    allowed = {
        "preserve_selected_owner",
        "prefer_visible_alternative",
        "abstain_context_only",
    }
    summary = payload["summary"]

    assert set(summary["recommendation_counts_by_class"]) == allowed
    assert summary["initial_owner_only_scope_count"] == summary["enabled_recommendation_count"]
    assert summary["direct_request_false_count"] == summary["enabled_recommendation_count"]
    assert summary["score_delta_zero_count"] == summary["enabled_recommendation_count"]
    assert summary["preserve_failure_risk_refinement_present_count"] == (
        summary["enabled_recommendation_count"]
    )
    assert summary["abstain_guard_present_count"] == summary["enabled_recommendation_count"]

    for row in payload["rows"]:
        assert row["flag_off_selector_recommendation_count"] == 0
        assert row["enabled_selector_recommendation_count"] == 1
        assert row["selected_move_delta"] is False
        assert row["selected_provider_delta"] is False
        assert row["routing_delta"] is False
        rec = row["enabled_decision"]["selector_recommendation"]
        assert rec["recommendation"] in allowed
        assert rec["selector_scope"] == "initial_owner_only"
        assert rec["decision_window"] == "initial_owner_choice"
        assert rec["continuation_recommendation"] is False
        assert rec["plan_capsule_continuation_influence"] is False
        assert rec["progress_window_reconsideration_influence"] is False
        assert rec["move_provider_selection_effect"] is False
        assert rec["causal_status"] == "recommendation_only"
        assert rec["direct_request"] is False
        assert rec["score_delta"] == 0.0
        assert rec["selected_owner_before_recommendation"]
        assert isinstance(rec["visible_alternatives_considered"], list)
        assert rec["source_terms"] is not None
        assert rec["explanation_terms"]
        assert "selecting_a_provider" in rec["forbidden_actions"]
        assert "selecting_a_move" in rec["forbidden_actions"]
        assert "routing_directly_to_a_provider" in rec["forbidden_actions"]
        assert "runtime_dtm_or_tablebase" in rec["forbidden_actions"]
        assert "gameplay_topology_mutation" in rec["forbidden_actions"]


def test_initial_owner_refined_selector_preserve_refinement_and_abstain_behavior():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["preserve_on_failure_count"] == 0
    assert summary["switch_on_safe_owner_count"] == 0
    assert summary["abstain_count"] > 0
    assert summary["abstain_target_count"] > 0
    assert summary["abstain_target_recalled_count"] == summary["abstain_target_count"]
    assert summary["abstain_recall"] == 1.0

    for row in payload["rows"]:
        rec = row["enabled_decision"]["selector_recommendation"]
        refinement = rec["preserve_failure_risk_refinement"]
        abstain_guard = rec["abstain_guard"]
        assert refinement["enabled"] is True
        assert refinement["uses_offline_only_labels"] is False
        assert abstain_guard["enabled"] is True
        assert abstain_guard["preserves_existing_abstain_behavior"] is True


def test_initial_owner_refined_selector_no_training_or_hidden_paths():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]
    decision = payload["decision"]

    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["capacity_label_used_as_ownership_label_count"] == 0
    assert summary["runtime_dtm_or_tablebase_use"] is False
    assert summary["gameplay_topology_mutation"] is False
    assert summary["hidden_python_controller"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["hidden_python_controller"] is False
    assert decision["runtime_changes_allowed"] is False
    assert decision["behavior_changing_selector_allowed"] is False
    assert decision["selector_training_allowed"] is False
    assert decision["stage7_promotion_allowed"] is False
    assert decision["stage8_training_allowed"] is False


def test_initial_owner_refined_selector_runtime_flag_off_on_preserves_selection():
    case = _regression_case()
    graph, engine = _new_graph_engine()
    board = chess.Board(str(case["fen"]))
    off = choose_move_details(
        graph,
        engine,
        board,
        max_ticks=200,
        suggestion_limit=10,
        active_landmark_label=str(case["active_landmark_label"]),
        early_stop_stable_suggestions=2,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    graph, engine = _new_graph_engine()
    on = choose_move_details(
        graph,
        engine,
        board,
        max_ticks=200,
        suggestion_limit=10,
        active_landmark_label=str(case["active_landmark_label"]),
        early_stop_stable_suggestions=2,
        krk_refined_selector_initial_owner_observability_enabled=True,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )

    assert "krk_selector_objective_recommendation" not in off
    assert on["move"] == off["move"]
    assert on["selected_suggestion"]["skill_id"] == off["selected_suggestion"]["skill_id"]
    rec = on["krk_selector_objective_recommendation"]
    assert rec["selector_scope"] == "initial_owner_only"
    assert rec["decision_window"] == "initial_owner_choice"
    assert rec["direct_request"] is False
    assert rec["score_delta"] == 0.0


def test_initial_owner_refined_selector_no_continuation_recommendations_in_playout():
    payload = _read_json(ARTIFACT)
    probe = payload["continuation_scope_probe"]

    assert probe["default_off"]["initial_recommendation_count"] == 0
    assert probe["default_off"]["continuation_recommendation_count"] == 0
    assert probe["enabled"]["initial_recommendation_count"] == 1
    assert probe["enabled"]["continuation_recommendation_count"] == 0
    assert probe["enabled"]["white_events"][0]["selector_recommendation_present"] is True
    for event in probe["enabled"]["white_events"][1:]:
        assert event["selector_recommendation_present"] is False


def test_initial_owner_refined_selector_direct_playout_continuation_scope():
    case = _regression_case()
    graph, engine = _new_graph_engine()
    result = play_to_mate(
        graph,
        engine,
        chess.Board(str(case["fen"])),
        random.Random(40),
        str(case["active_landmark_label"]),
        stage_filter=None,
        max_plies=8,
        black_policy="adversarial",
        trace=True,
        trace_max_plies=8,
        max_ticks=200,
        suggestion_limit=10,
        early_stop_stable_suggestions=2,
        krk_refined_selector_initial_owner_observability_enabled=True,
        enable_diagnostic_caches=True,
        **_profile_kwargs(),
    )
    white_recs = [
        event["engine"].get("krk_selector_objective_recommendation")
        for event in result["trace"]
        if event["turn"] == "white"
    ]

    assert bool(white_recs[0]) is True
    assert all(not rec for rec in white_recs[1:])


def test_initial_owner_refined_selector_writer_detects_scope_errors_with_fake_runner():
    module = _load_module()
    manifest = {
        "cases": [
            {
                "case_id": "case.1",
                "row_id": "case.1",
                "fen": "8/8/8/8/8/8/8/K6k w - - 0 1",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "selected_owner_label": "selected_owner_failed",
                "selected_provider_label": "krk.stage0_basin",
            }
        ]
    }

    def fake_decision(case: dict, enabled: bool) -> dict:
        rec = {
            "schema_version": "krk_selector_objective_recommendation.v0",
            "sandbox_id": "sandbox.krk.refined_selector_initial_owner_observability_v0",
            "selector_refinement_id": "preserve_only_if_no_selected_owner_failure_risk_terms",
            "causal_status": "recommendation_only",
            "selector_scope": "continuation",
            "decision_window": "continuation",
            "continuation_recommendation": True,
            "plan_capsule_continuation_influence": False,
            "progress_window_reconsideration_influence": False,
            "move_provider_selection_effect": False,
            "direct_request": False,
            "score_delta": 0.0,
            "recommendation": "prefer_visible_alternative",
            "selected_owner_before_recommendation": "runtime_unknown_offline_owner_label_not_visible",
            "visible_alternatives_considered": [],
            "source_terms": [],
            "explanation_terms": ["selector_model.combined_simple_rule"],
            "positive_trace_provider_candidate_count": 1,
            "preserve_failure_risk_refinement": {
                "enabled": True,
                "uses_offline_only_labels": False,
            },
            "abstain_guard": {
                "enabled": True,
                "preserves_existing_abstain_behavior": True,
            },
            "forbidden_actions": list(module.FORBIDDEN_ACTIONS),
        }
        return {
            "move": "a1a2",
            "selected_provider": "krk.stage0_basin",
            "confidence": 1.0,
            "selector_recommendation_present": enabled,
            "selector_recommendation": rec if enabled else {},
        }

    def fake_continuation(enabled: bool) -> dict:
        return {
            "initial_recommendation_count": int(enabled),
            "continuation_recommendation_count": int(enabled),
            "white_events": [],
        }

    payload = module.build_payload(
        decision_runner=fake_decision,
        continuation_runner=fake_continuation,
        manifest=manifest,
    )

    assert payload["decision"]["status"] == (
        "refined_selector_initial_owner_observability_invalid_scope"
    )
