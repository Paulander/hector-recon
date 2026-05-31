#!/usr/bin/env python3
"""Tests for refined selector-observability runtime review packet v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_refined_selector_observability_runtime_review_packet_v0.json"
)
MARKDOWN = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_refined_selector_observability_runtime_review_packet_v0.md"
)


def _load_module():
    path = ROOT / "scripts/write_krk_refined_selector_observability_runtime_review_packet_v0.py"
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


def test_refined_selector_observability_packet_json_parses_and_is_ready():
    payload = _read_json(PACKET)

    assert (
        payload["schema_version"]
        == "krk_refined_selector_observability_runtime_review_packet.v0"
    )
    assert payload["causal_status"] == "non_causal_refined_runtime_review_packet"
    assert payload["decision"]["status"] == (
        "refined_selector_observability_runtime_review_ready"
    )
    assert payload["possible_statuses"] == [
        "refined_selector_observability_runtime_review_ready",
        "refined_selector_observability_needs_more_evidence",
        "refined_selector_observability_blocked",
    ]

    sandbox = payload["proposed_sandbox"]
    assert sandbox["name"] == "default_off_refined_selector_objective_observability_sandbox"
    assert sandbox["implementation_status"] == "not_implemented"
    assert sandbox["authorization_status"] == (
        "review_packet_only_not_approved_for_implementation"
    )
    assert sandbox["default_off"] is True
    assert sandbox["opt_in_only"] is True
    assert sandbox["opt_in_flag"] == (
        "--enable-krk-refined-selector-objective-observability"
    )
    assert sandbox["trace_only"] is True
    assert sandbox["recommendation_only"] is True
    assert sandbox["default_behavior_change"] is False
    assert sandbox["base_model"] == "combined_simple_rule"
    assert sandbox["refinement_id"] == (
        "preserve_only_if_no_selected_owner_failure_risk_terms"
    )
    assert sandbox["may_emit_recommendations"] == [
        "preserve_selected_owner",
        "prefer_visible_alternative",
        "abstain_context_only",
    ]


def test_refined_selector_observability_packet_allows_metadata_only():
    payload = _read_json(PACKET)
    allowed = payload["allowed_effect"]

    assert allowed["emit_recommendation_metadata"] is True
    assert allowed["record_source_terms"] is True
    assert allowed["record_explanation_terms"] is True
    assert allowed["record_selected_owner_before_recommendation"] is True
    assert allowed["record_visible_alternatives"] is True
    assert allowed["direct_request"] is False
    assert allowed["score_delta"] == 0.0
    assert allowed["causal_status"] == "recommendation_only"
    assert allowed["selected_move_delta_allowed"] is False
    assert allowed["selected_provider_delta_allowed"] is False
    assert allowed["routing_delta_allowed"] is False
    assert allowed["provider_suppression_allowed"] is False
    assert allowed["runtime_default_change_allowed"] is False


def test_refined_selector_observability_packet_does_not_authorize_behavior_change():
    payload = _read_json(PACKET)
    decision = payload["decision"]

    assert decision["implementation_authorized_by_this_packet"] is False
    assert decision["behavior_changing_selector_allowed"] is False
    assert decision["runtime_sandbox_authorized_by_this_packet"] is False
    assert decision["runtime_changes_allowed"] is False
    assert decision["selector_training_allowed"] is False
    assert decision["stage7_promotion_allowed"] is False
    assert decision["stage8_training_allowed"] is False
    assert decision["score_changes_allowed"] is False
    assert decision["routing_changes_allowed"] is False
    assert decision["provider_selection_changes_allowed"] is False
    assert decision["provider_suppression_allowed"] is False
    assert decision["runtime_default_changes_allowed"] is False

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


def test_refined_selector_observability_packet_forbids_selection_and_training():
    payload = _read_json(PACKET)
    forbidden = set(payload["explicitly_forbidden"])
    requirements = set(payload["requirements_before_later_implementation"])

    assert "behavior_changing_selection" in forbidden
    assert "routing_changes" in forbidden
    assert "score_changes" in forbidden
    assert "provider_selection_changes" in forbidden
    assert "provider_suppression" in forbidden
    assert "runtime_default_changes" in forbidden
    assert "stage7_promotion" in forbidden
    assert "stage8_training" in forbidden
    assert "runtime_dtm_or_tablebase" in forbidden
    assert "gameplay_topology_mutation" in forbidden
    assert "treating_capacity_labels_as_ownership_labels" in forbidden

    assert "explicit_approval" in requirements
    assert "default_off_equivalence" in requirements
    assert "no_selected_move_or_provider_delta" in requirements
    assert "score_delta_count_equals_zero" in requirements
    assert "recommendation_only_metadata" in requirements
    assert "focused_tests" in requirements


def test_refined_selector_observability_packet_evidence_gates():
    payload = _read_json(PACKET)
    evidence = payload["supporting_evidence"]

    assert evidence["recommendation_class_balance"] == {
        "abstain_context_only": 5,
        "prefer_visible_alternative": 4,
        "preserve_selected_owner": 5,
    }
    assert evidence["preserve_failure_risk_status"] == (
        "preserve_failure_risk_resolved_non_causal"
    )
    assert evidence["recommended_refinement_id"] == (
        "preserve_only_if_no_selected_owner_failure_risk_terms"
    )
    assert evidence["refined_prediction_counts"] == {
        "abstain_context_only": 6,
        "prefer_visible_alternative": 4,
        "preserve_selected_owner": 4,
    }
    assert evidence["refined_preserve_on_failure_count"] == 0
    assert evidence["refined_safe_preservation_recall"] == 1.0
    assert evidence["refined_switch_contrast_recall"] == 0.8
    assert evidence["refined_abstain_recall"] == 1.0
    assert evidence["refined_switch_on_safe_owner_count"] == 0
    assert evidence["selector_training_row_count"] == 0
    assert evidence["stage7_training_row_count"] == 0
    assert evidence["selected_move_delta_count"] == 0
    assert evidence["selected_provider_delta_count"] == 0
    assert evidence["score_delta_count"] == 0
    assert evidence["routing_delta_count"] == 0
    assert evidence["capacity_label_used_as_ownership_label_count"] == 0
    assert "selector_model.combined_simple_rule" in evidence["explanation_terms"]
    assert "offline_validated_provider_capacity_evidence" in evidence["source_terms"]


def test_refined_selector_observability_markdown_records_review_only_decision():
    text = MARKDOWN.read_text(encoding="utf-8")

    assert "# KRK Refined Selector Observability Runtime Review Packet v0" in text
    assert (
        "This packet reviews a possible future default-off refined selector-objective "
        "observability sandbox."
    ) in text
    assert (
        "- status: `refined_selector_observability_runtime_review_ready`"
    ) in text
    assert "- implementation_authorized_by_this_packet: `False`" in text
    assert "- behavior_changing_selector_allowed: `False`" in text
    assert "- direct_request: `False`" in text
    assert "- score_delta: `0.0`" in text
    assert "- causal_status: `recommendation_only`" in text


def test_refined_selector_observability_writer_needs_evidence_if_refinement_fails():
    module = _load_module()
    expanded = {
        "summary": {
            "recommendation_count_by_class": {
                "abstain_context_only": 5,
                "prefer_visible_alternative": 4,
                "preserve_selected_owner": 5,
            }
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
    }
    preserve_audit = {
        "decision": {"status": "preserve_failure_risk_resolved_non_causal"},
        "refinement_results": [
            {
                "refinement_id": "preserve_only_if_no_selected_owner_failure_risk_terms",
                "eliminates_preserve_on_failure": False,
                "preserves_safe_preservation_recall": True,
                "keeps_switch_on_safe_owner_zero": True,
                "runtime_feature_eligible": True,
                "uses_offline_only_labels": False,
                "metrics": {
                    "abstain_recall": 1.0,
                    "preserve_on_failure_count": 1,
                    "switch_on_safe_owner_count": 0,
                },
            }
        ],
    }
    preserve_decision = {
        "decision": {
            "status": "preserve_failure_risk_resolved_non_causal",
            "future_runtime_review_packet_recommended": True,
        },
        "summary": {
            "recommended_refinement_id": "preserve_only_if_no_selected_owner_failure_risk_terms",
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "capacity_label_used_as_ownership_label_count": 0,
            "selected_move_delta_count": 0,
            "selected_provider_delta_count": 0,
            "score_delta_count": 0,
            "routing_delta_count": 0,
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
    }

    payload = module.build_payload(
        expanded=expanded,
        readiness={"decision": {"status": "prior_status"}},
        preserve_audit=preserve_audit,
        preserve_decision=preserve_decision,
    )

    assert (
        payload["decision"]["status"]
        == "refined_selector_observability_needs_more_evidence"
    )
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["behavior_changing_selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
