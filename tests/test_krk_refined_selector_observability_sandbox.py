#!/usr/bin/env python3
"""Tests for refined selector-objective observability sandbox v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = (
    ROOT
    / "reports/strategy_arbitration/krk_refined_selector_observability_sandbox_v0.json"
)
REPORT = (
    ROOT
    / "reports/strategy_arbitration/krk_refined_selector_observability_sandbox_v0.md"
)


def _load_module():
    path = ROOT / "scripts/run_krk_refined_selector_observability_sandbox_v0.py"
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


def _fake_recommendation(case: dict, recommendation: str = "abstain_context_only") -> dict:
    return {
        "schema_version": "krk_selector_objective_recommendation.v0",
        "sandbox_id": "sandbox.krk.refined_selector_objective_observability_v0",
        "selector_model_id": "combined_simple_rule",
        "selector_refinement_id": "preserve_only_if_no_selected_owner_failure_risk_terms",
        "causal_status": "recommendation_only",
        "recommendation": recommendation,
        "decision_reason": "preserve_failure_risk_refinement_abstain",
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
        "source_terms": ["offline_validated_provider_capacity_evidence"],
        "explanation_terms": ["selector_model.combined_simple_rule"],
        "visible_alternatives_considered": [],
        "visible_alternative_count": 0,
        "preserve_failure_risk_refinement": {
            "enabled": True,
            "status": "triggered_abstain_context_only",
            "risk_detected": True,
            "risk_terms": {
                "active_landmark_label.fence_established": True,
                "selected_piece.king": True,
                "support_bucket.close": True,
                "positive_trace_count_bucket.high": True,
            },
            "uses_offline_only_labels": False,
        },
        "abstain_guard": {
            "enabled": True,
            "status": "triggered",
            "reason": "preserve_failure_risk_refinement_abstain",
            "preserves_existing_abstain_behavior": True,
        },
        "positive_trace_provider_candidate_count": 1,
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


def test_refined_selector_observability_artifacts_parse_and_decision_is_allowed_status():
    payload = _read_json(ARTIFACT)
    markdown = REPORT.read_text(encoding="utf-8")

    assert payload["schema_version"] == "krk_refined_selector_observability_sandbox.v0"
    assert payload["sandbox_id"] == "sandbox.krk.refined_selector_objective_observability_v0"
    assert payload["causal_status"] == "runtime_recommendation_only_observability_sandbox"
    assert payload["approval"]["flag_required"] == (
        "--enable-krk-refined-selector-observability"
    )
    assert payload["decision"]["status"] in payload["possible_statuses"]
    assert payload["decision"]["status"] == (
        "refined_selector_observability_ready_for_recommendation_analysis"
    )
    assert "selector_runtime_ready" not in payload["decision"]
    assert "# KRK Refined Selector Observability Sandbox v0" in markdown
    json.dumps(payload)


def test_refined_selector_observability_default_off_equivalence_summary():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["default_off_equivalence_passed"] is True
    assert summary["default_off_selector_recommendation_count"] == 0
    assert summary["enabled_recommendation_count"] == summary["attempted_row_count"]
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["selected_score_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert summary["runtime_behavior_changed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_provider_suppression"] is False


def test_refined_selector_observability_enabled_metadata_is_recommendation_only():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]
    allowed = {
        "preserve_selected_owner",
        "prefer_visible_alternative",
        "abstain_context_only",
    }

    assert summary["direct_request_false_count"] == summary["enabled_recommendation_count"]
    assert summary["score_delta_zero_count"] == summary["enabled_recommendation_count"]
    assert summary["invalid_metadata_count"] == 0
    assert set(summary["recommendation_counts_by_class"]) == allowed
    assert summary["recommendation_counts_by_class"]["abstain_context_only"] > 0
    assert summary["recommendation_counts_by_class"]["prefer_visible_alternative"] > 0
    assert summary["recommendation_counts_by_class"]["preserve_selected_owner"] > 0

    for row in payload["rows"]:
        assert row["flag_off_selector_recommendation_count"] == 0
        assert row["enabled_selector_recommendation_count"] == 1
        assert row["selected_move_delta"] is False
        assert row["selected_provider_delta"] is False
        assert row["selected_score_delta"] is False
        assert row["routing_delta"] is False
        rec = row["enabled_decision"]["selector_recommendation"]
        assert rec["causal_status"] == "recommendation_only"
        assert rec["direct_request"] is False
        assert rec["score_delta"] == 0.0
        assert rec["recommendation"] in allowed
        assert rec["source_terms"] is not None
        assert rec["explanation_terms"]
        assert rec["selected_owner_before_recommendation"]
        assert isinstance(rec["visible_alternatives_considered"], list)
        assert "selecting_a_move" in rec["forbidden_actions"]
        assert "routing_directly_to_a_provider" in rec["forbidden_actions"]
        assert "runtime_dtm_or_tablebase" in rec["forbidden_actions"]
        assert "gameplay_topology_mutation" in rec["forbidden_actions"]


def test_refined_selector_observability_preserve_refinement_and_abstain_preserved():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["preserve_on_failure_count"] == 0
    assert summary["preserve_failure_risk_refinement_trigger_count"] >= 1
    assert summary["switch_on_safe_owner_count"] == 0
    assert summary["abstain_count"] > 0
    assert summary["abstain_target_count"] > 0
    assert summary["abstain_target_recalled_count"] == summary["abstain_target_count"]
    assert summary["abstain_recall"] == 1.0

    triggered = [
        row
        for row in payload["rows"]
        if row["preserve_failure_risk_refinement_status"]
        == "triggered_abstain_context_only"
    ]
    assert triggered
    for row in triggered:
        rec = row["enabled_decision"]["selector_recommendation"]
        assert rec["recommendation"] == "abstain_context_only"
        assert rec["preserve_failure_risk_refinement"]["enabled"] is True
        assert rec["preserve_failure_risk_refinement"]["uses_offline_only_labels"] is False
        assert row["abstain_guard_status"] == "triggered"


def test_refined_selector_observability_no_training_or_hidden_runtime_paths():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]
    decision = payload["decision"]

    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["runtime_dtm_or_tablebase_use"] is False
    assert summary["gameplay_topology_mutation"] is False
    assert summary["hidden_python_controller"] is False
    assert summary["capacity_label_used_as_ownership_label_count"] == 0
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


def test_refined_selector_observability_runner_flags_equivalence_with_fake_runner():
    runner = _load_module()
    manifest = {
        "cases": [
            {
                "case_id": "case.1",
                "row_id": "case.1",
                "fen": "8/8/8/8/8/8/8/K6k w - - 0 1",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "selected_owner_label": "selected_owner_unknown",
                "selected_provider_label": "krk.stage0_basin",
                "stage7_training_row": False,
                "selector_training_row": False,
                "capacity_label_used_as_ownership_label": False,
            }
        ]
    }

    def fake_decision(case: dict, enabled: bool) -> dict:
        return {
            "move": "a1a2",
            "selected_provider": case["selected_provider_label"],
            "confidence": 1.0,
            "selector_recommendation_present": enabled,
            "selector_recommendation": _fake_recommendation(case) if enabled else {},
            "candidate_generation_observation_present": False,
        }

    payload = runner.build_payload(decision_runner=fake_decision, manifest=manifest)
    summary = payload["summary"]

    assert summary["default_off_equivalence_passed"] is True
    assert summary["default_off_selector_recommendation_count"] == 0
    assert summary["enabled_recommendation_count"] == 1
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert payload["decision"]["status"] == (
        "refined_selector_observability_sandbox_wired_default_off_equivalent"
    )


def test_refined_selector_observability_runtime_flag_on_emits_refined_metadata():
    runner = _load_module()
    manifest = runner.build_manifest()
    case = next(
        item
        for item in manifest["cases"]
        if item["row_id"] == "selector_objective_fresh_diversity.02"
    )

    default_off = runner._run_decision(case, False)
    enabled = runner._run_decision(case, True)
    rec = enabled["selector_recommendation"]

    assert default_off["selector_recommendation_present"] is False
    assert enabled["selector_recommendation_present"] is True
    assert default_off["move"] == enabled["move"]
    assert default_off["selected_provider"] == enabled["selected_provider"]
    assert default_off["confidence"] == enabled["confidence"]
    assert rec["sandbox_id"] == "sandbox.krk.refined_selector_objective_observability_v0"
    assert rec["selector_refinement_id"] == (
        "preserve_only_if_no_selected_owner_failure_risk_terms"
    )
    assert rec["recommendation"] == "abstain_context_only"
    assert rec["preserve_failure_risk_refinement"]["status"] == (
        "triggered_abstain_context_only"
    )
    assert rec["abstain_guard"]["status"] == "triggered"
    assert rec["direct_request"] is False
    assert rec["score_delta"] == 0.0
    assert rec["causal_status"] == "recommendation_only"
