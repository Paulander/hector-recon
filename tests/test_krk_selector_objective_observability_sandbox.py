#!/usr/bin/env python3
"""Tests for selector-objective observability sandbox v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_observability_sandbox_v0.json"
)
REPORT = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_observability_sandbox_v0.md"
)


def _load_module():
    path = ROOT / "scripts/run_krk_selector_objective_observability_sandbox_v0.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _fake_recommendation(case: dict) -> dict:
    return {
        "schema_version": "krk_selector_objective_recommendation.v0",
        "sandbox_id": "sandbox.krk.selector_objective_observability_v0",
        "selector_model_id": "combined_simple_rule",
        "causal_status": "recommendation_only",
        "recommendation": "prefer_visible_alternative",
        "decision_reason": "near_edge_or_medium_box_relevance",
        "confidence": 1.0,
        "direct_request": False,
        "score_delta": 0.0,
        "selected_provider_before_recommendation": case["selected_provider_label"],
        "selected_move_before_recommendation": "a1a2",
        "selected_owner_before_recommendation": "runtime_unknown_offline_owner_label_not_visible",
        "selected_owner_observation": {
            "owner_label": None,
            "source": "runtime_visible_selected_provider_only",
            "label_semantics": "offline_selected_owner_labels_not_runtime_visible",
        },
        "active_landmark_label": case["active_landmark_label"],
        "source_stage": case["source_stage"],
        "positive_trace_provider_candidate_count": 1,
        "positive_trace_count_bucket": "low",
        "edge_bucket": "near_edge",
        "support_bucket": "close",
        "box_area_relevance": "medium",
        "selected_piece": "rook",
        "source_terms": ["stage5_6_candidate_generation_refresh_scope"],
        "explanation_terms": [
            "selector_model.combined_simple_rule",
            "positive_trace_provider_candidate_count.1",
            "edge_bucket.near_edge",
        ],
        "visible_alternatives_considered": [
            {
                "candidate_source": "stage_conditioned_candidate_generation_refresh",
                "provider_id": "krk.fence_established",
                "move_id": "a1a2",
                "capacity_evidence_kind": "positive_capacity",
                "direct_request": False,
                "score_delta": 0.0,
                "causal_status": "candidate_generation_only",
            }
        ],
        "visible_alternative_count": 1,
        "forbidden_actions": [
            "selecting_a_provider",
            "selecting_a_move",
            "changing_scores",
            "suppressing_providers",
            "routing_directly_to_a_provider",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
            "stage7_promotion",
            "stage8_training",
        ],
    }


def test_selector_objective_observability_runner_preserves_default_off_equivalence():
    runner = _load_module()

    def fake_decision(case: dict, enabled: bool) -> dict:
        return {
            "move": "a1a2",
            "selected_provider": case["selected_provider_label"],
            "confidence": 1.0,
            "selector_recommendation_present": enabled,
            "selector_recommendation": _fake_recommendation(case) if enabled else {},
            "candidate_generation_observation_present": False,
        }

    payload = runner.build_payload(decision_runner=fake_decision)
    summary = payload["summary"]

    assert payload["schema_version"] == "krk_selector_objective_observability_sandbox.v0"
    assert payload["causal_status"] == "runtime_recommendation_only_observability_sandbox"
    assert payload["decision"]["status"] == (
        "selector_observability_sandbox_wired_default_off_equivalent"
    )
    assert payload["decision"]["selector_runtime_ready"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert summary["default_off_equivalence_passed"] is True
    assert summary["flag_off_selector_recommendation_count"] == 0
    assert summary["enabled_recommendation_count"] == summary["attempted_row_count"]
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["selected_score_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert summary["runtime_behavior_changed"] is False


def test_selector_objective_observability_metadata_is_recommendation_only():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert payload["decision"]["status"] == (
        "selector_observability_sandbox_wired_default_off_equivalent"
    )
    assert summary["default_off_equivalence_passed"] is True
    assert summary["enabled_recommendation_count"] > 0
    assert summary["direct_request_false_count"] == summary["enabled_recommendation_count"]
    assert summary["score_delta_zero_count"] == summary["enabled_recommendation_count"]
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert summary["stage7_rows_remain_held_out"] is True
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["runtime_dtm_or_tablebase_use"] is False
    assert summary["gameplay_topology_mutation"] is False
    assert summary["invalid_metadata_count"] == 0
    assert summary["source_term_coverage"]["unique_explanation_term_count"] > 0
    assert summary["source_term_coverage"]["visible_alternative_count"] > 0

    allowed = {
        "preserve_selected_owner",
        "prefer_visible_alternative",
        "abstain_context_only",
    }
    assert set(summary["recommendation_counts_by_class"]).issubset(allowed)
    for row in payload["rows"]:
        assert row["flag_off_selector_recommendation_count"] == 0
        assert row["enabled_selector_recommendation_count"] == 1
        rec = row["enabled_decision"]["selector_recommendation"]
        assert rec["selector_model_id"] == "combined_simple_rule"
        assert rec["causal_status"] == "recommendation_only"
        assert rec["direct_request"] is False
        assert rec["score_delta"] == 0.0
        assert rec["recommendation"] in allowed
        assert rec["selected_owner_before_recommendation"]
        assert rec["source_terms"]
        assert rec["explanation_terms"]
        assert rec["visible_alternatives_considered"]
        assert "selecting_a_move" in rec["forbidden_actions"]
        assert "routing_directly_to_a_provider" in rec["forbidden_actions"]
        assert "runtime_dtm_or_tablebase" in rec["forbidden_actions"]
        assert "gameplay_topology_mutation" in rec["forbidden_actions"]


def test_selector_objective_observability_artifacts_parse():
    payload = _read_json(ARTIFACT)
    markdown = REPORT.read_text(encoding="utf-8")

    assert payload["approval"]["flag_required"] == (
        "--enable-krk-selector-objective-observability"
    )
    assert payload["approval"]["benchmark_model"] == "combined_simple_rule"
    assert "selector_runtime_ready" in payload["decision"]
    assert payload["decision"]["selector_runtime_ready"] is False
    assert "# KRK Selector Objective Observability Sandbox v0" in markdown
    json.dumps(payload)


def test_selector_objective_observability_runtime_flag_on_emits_metadata():
    runner = _load_module()
    case = runner.load_cases(runner._load(runner.FRESH_DIVERSITY_PACKET))[0]

    default_off = runner._run_decision(case, False)
    enabled = runner._run_decision(case, True)
    rec = enabled["selector_recommendation"]

    assert default_off["selector_recommendation_present"] is False
    assert enabled["selector_recommendation_present"] is True
    assert default_off["move"] == enabled["move"]
    assert default_off["selected_provider"] == enabled["selected_provider"]
    assert default_off["confidence"] == enabled["confidence"]
    assert enabled["candidate_generation_observation_present"] is False
    assert rec["causal_status"] == "recommendation_only"
    assert rec["direct_request"] is False
    assert rec["score_delta"] == 0.0
    assert rec["selector_model_id"] == "combined_simple_rule"
