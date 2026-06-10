#!/usr/bin/env python3
"""Tests for selector-objective runtime review packet v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = (
    ROOT
    / "reports/strategy_arbitration/krk_selector_objective_runtime_review_packet_v0.json"
)


def _load_module():
    path = ROOT / "scripts/write_krk_selector_objective_runtime_review_packet_v0.py"
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


def test_selector_objective_runtime_review_packet_json_parses_and_is_ready():
    payload = _read_json(PACKET)

    assert payload["schema_version"] == "krk_selector_objective_runtime_review_packet.v0"
    assert payload["causal_status"] == "non_causal_runtime_review_packet"
    assert payload["decision"]["status"] == "selector_runtime_review_packet_ready"
    assert payload["possible_statuses"] == [
        "selector_runtime_review_packet_ready",
        "selector_runtime_review_needs_more_evidence",
        "selector_runtime_review_blocked",
    ]
    assert payload["proposed_sandbox"] == {
        "authorization_status": "review_packet_only_not_approved_for_implementation",
        "default_behavior_change": False,
        "default_off": True,
        "implementation_status": "not_implemented",
        "name": "default_off_selector_objective_sandbox",
        "opt_in_only": True,
        "reversible": True,
        "traceable": True,
    }
    first = payload["first_sandbox_scope_if_separately_approved_later"]
    assert first["name"] == "trace_only_selector_objective_recommendation"
    assert first["implementation_status"] == "not_implemented"
    assert first["authorization_status"] == "not_authorized_by_this_packet"
    assert first["may_compute"] == "combined_simple_rule_selector_objective"
    assert first["may_emit_recommendations"] == [
        "preserve_selected_owner",
        "prefer_visible_alternative",
        "abstain_context_only",
    ]
    assert "explanation_terms" in first["may_record"]
    assert "source_terms" in first["may_record"]
    assert first["direct_request"] is False
    assert first["score_delta"] == 0.0
    assert first["selected_move_delta_allowed"] is False
    assert first["selected_provider_delta_allowed"] is False
    assert first["routing_delta_allowed"] is False
    assert first["provider_suppression_allowed"] is False
    assert first["runtime_default_change_allowed"] is False
    assert first["runtime_effect"] == "recommendation_only_no_selection"


def test_selector_objective_runtime_review_packet_does_not_authorize_runtime():
    payload = _read_json(PACKET)

    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["runtime_sandbox_authorized_by_this_packet"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["score_changes_allowed"] is False
    assert payload["decision"]["routing_changes_allowed"] is False
    assert payload["decision"]["provider_selection_changes_allowed"] is False
    assert payload["decision"]["provider_suppression_allowed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_provider_suppression"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False


def test_selector_objective_runtime_review_packet_evidence_and_label_semantics():
    payload = _read_json(PACKET)
    evidence = payload["supporting_evidence"]

    assert evidence["benchmark_status"] == "selector_objective_benchmark_promising_non_causal"
    assert evidence["seed_row_count"] == 21
    assert evidence["target_action_counts"] == {
        "abstain_context_only": 5,
        "prefer_visible_alternative": 5,
        "preserve_selected_owner": 11,
    }
    assert evidence["best_model"] == "combined_simple_rule"
    assert evidence["best_accuracy"] == 0.9523809523809523
    assert evidence["safe_preservation_recall"] == 1.0
    assert evidence["switch_contrast_recall"] == 0.8
    assert evidence["abstain_recall"] == 1.0
    assert evidence["selector_training_row_count"] == 0
    assert evidence["stage7_training_row_count"] == 0
    assert evidence["runtime_authorization_row_count"] == 0
    assert evidence["capacity_labels_are_not_ownership_labels"] is True
    assert "capacity_labels_are_not_ownership_labels" in payload["remaining_risks"]


def test_selector_objective_runtime_review_packet_forbidden_actions_and_envelope():
    payload = _read_json(PACKET)
    forbidden = set(payload["explicitly_forbidden"])
    envelope = set(payload["future_sandbox_envelope_before_implementation"])

    assert "score_changes" in forbidden
    assert "routing_changes" in forbidden
    assert "provider_selection_changes" in forbidden
    assert "provider_suppression" in forbidden
    assert "broad_provider_penalties" in forbidden
    assert "runtime_default_changes" in forbidden
    assert "stage7_promotion" in forbidden
    assert "stage8_training" in forbidden
    assert "runtime_dtm_or_tablebase" in forbidden
    assert "gameplay_time_topology_mutation" in forbidden
    assert "state_hash_exceptions" in forbidden
    assert "treating_capacity_labels_as_ownership_labels" in forbidden

    assert "explicit_flag" in envelope
    assert "default_off_equivalence" in envelope
    assert "no_selected_move_delta_in_observation_mode" in envelope
    assert "no_selected_provider_delta_in_observation_mode" in envelope
    assert "trace_only_first" in envelope
    assert "report_recommendation_only" in envelope
    assert "no_score_changes" in envelope
    assert "no_routing_changes" in envelope
    assert "target_smoke_before_any_guardrails" in envelope
    assert "guardrails_before_promotion" in envelope
    assert "rollback_plan" in envelope


def test_selector_objective_runtime_review_writer_blocks_if_evidence_missing():
    module = _load_module()
    payload = module.build_payload(
        benchmark={"summary": {}},
        decision={
            "decision": {
                "status": "selector_objective_benchmark_needs_features",
                "selector_allowed": False,
                "runtime_changes_allowed": False,
            },
            "summary": {
                "best_model": "combined_simple_rule",
                "selector_training_row_count": 0,
                "stage7_training_row_count": 0,
                "runtime_authorization_row_count": 0,
            },
            "runtime_behavior_changed": False,
            "runtime_defaults_changed": False,
            "runtime_selector_implemented": False,
            "runtime_score_changes": False,
            "runtime_direct_routing": False,
            "runtime_provider_suppression": False,
            "hidden_python_controller": False,
            "runtime_dtm_or_tablebase_lookup": False,
            "gameplay_topology_mutation": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    )

    assert payload["decision"]["status"] == "selector_runtime_review_needs_more_evidence"
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
