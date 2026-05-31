#!/usr/bin/env python3
"""Tests for selector preserve-failure risk audit artifacts."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_preserve_failure_risk_audit_v0.json"
)
DECISION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_preserve_failure_risk_decision_v0.json"
)


def _load_module():
    path = ROOT / "scripts/audit_krk_selector_preserve_failure_risk_v0.py"
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


def test_preserve_failure_audit_identifies_failing_row():
    payload = _read_json(AUDIT)
    failing = payload["failing_rows"]

    assert payload["schema_version"] == "krk_selector_preserve_failure_risk_audit.v0"
    assert payload["decision"]["status"] == "preserve_failure_risk_resolved_non_causal"
    assert len(failing) == 1
    row = failing[0]
    assert row["row_id"] == "selector_objective_fresh_diversity.02"
    assert row["stage"] == "stage5"
    assert row["selected_provider"] == "krk.stage0_basin"
    assert row["selected_move"] == "c6b6"
    assert row["target_label"] == "prefer_visible_alternative"
    assert row["recommendation"] == "preserve_selected_owner"
    assert row["positive_trace_provider_candidate_count"] == 16
    assert row["positive_trace_count_bucket"] == "high"
    assert row["selected_piece"] == "king"
    assert row["support_bucket"] == "close"
    assert row["active_landmark"] == "fence_established"
    assert row["visible_alternative_count"] == 10
    assert row["source_terms"]
    assert row["explanation_terms"]
    assert row["visible_alternatives"]


def test_preserve_failure_audit_compares_safe_preserve_terms():
    payload = _read_json(AUDIT)
    comparison = payload["term_comparison"]

    assert payload["summary"]["safe_preserve_row_count"] == 4
    assert comparison["selected_piece"]["failing_value"] == "king"
    assert comparison["selected_piece"]["collides_with_safe"] is False
    assert comparison["support_bucket"]["failing_value"] == "close"
    assert comparison["support_bucket"]["collides_with_safe"] is True
    assert comparison["positive_trace_count_bucket"]["failing_value"] == "high"
    assert comparison["positive_trace_count_bucket"]["collides_with_safe"] is True
    assert comparison["active_landmark"]["failing_value"] == "fence_established"
    assert comparison["active_landmark"]["collides_with_safe"] is True


def test_preserve_failure_refinement_is_non_causal_and_resolves_risk():
    payload = _read_json(AUDIT)
    viable = {row["refinement_id"]: row for row in payload["viable_refinements"]}

    assert "preserve_only_if_no_selected_owner_failure_risk_terms" in viable
    refined = viable["preserve_only_if_no_selected_owner_failure_risk_terms"]
    assert refined["runtime_feature_eligible"] is True
    assert refined["uses_offline_only_labels"] is False
    assert refined["eliminates_preserve_on_failure"] is True
    assert refined["keeps_switch_on_safe_owner_zero"] is True
    assert refined["preserves_safe_preservation_recall"] is True
    assert refined["does_not_reduce_switch_contrast_recall_too_much"] is True
    assert refined["metrics"]["preserve_on_failure_count"] == 0
    assert refined["metrics"]["switch_on_safe_owner_count"] == 0
    assert refined["metrics"]["safe_preservation_recall"] == 1.0
    assert refined["metrics"]["switch_contrast_recall"] >= 0.75


def test_preserve_failure_audit_preserves_runtime_invariants():
    payload = _read_json(AUDIT)
    summary = payload["summary"]

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert summary["capacity_label_used_as_ownership_label_count"] == 0


def test_preserve_failure_decision_recommends_review_packet_only_not_behavior():
    payload = _read_json(DECISION)
    summary = payload["summary"]

    assert payload["schema_version"] == "krk_selector_preserve_failure_risk_decision.v0"
    assert payload["decision"]["status"] == "preserve_failure_risk_resolved_non_causal"
    assert payload["decision"]["behavior_changing_selector_implemented"] is False
    assert payload["decision"]["future_runtime_review_packet_recommended"] is True
    assert payload["decision"]["selector_runtime_ready"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert summary["recommended_refinement_id"] == (
        "preserve_only_if_no_selected_owner_failure_risk_terms"
    )
    recommendation = summary["future_runtime_review_packet_recommendation"]
    assert recommendation["scope"] == "review_only_default_off_selector_refinement"
    assert recommendation["must_remain_default_off"] is True
    assert recommendation["must_keep_trace_only_until_separately_approved"] is True


def test_preserve_failure_audit_writer_rebuilds_parseable_artifacts():
    module = _load_module()
    audit = module.build_audit()
    decision = module.build_decision(audit)

    assert audit["decision"]["status"] == "preserve_failure_risk_resolved_non_causal"
    assert decision["decision"]["status"] == audit["decision"]["status"]
    assert json.loads(json.dumps(audit))["schema_version"] == (
        "krk_selector_preserve_failure_risk_audit.v0"
    )
    assert json.loads(json.dumps(decision))["schema_version"] == (
        "krk_selector_preserve_failure_risk_decision.v0"
    )
