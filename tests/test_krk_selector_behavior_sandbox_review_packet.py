#!/usr/bin/env python3
"""Tests for narrow selector behavior sandbox review packet v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = (
    ROOT
    / "reports/strategy_arbitration/krk_selector_behavior_sandbox_review_packet_v0.json"
)
MARKDOWN = (
    ROOT
    / "reports/strategy_arbitration/krk_selector_behavior_sandbox_review_packet_v0.md"
)


def _load_module():
    path = ROOT / "scripts/write_krk_selector_behavior_sandbox_review_packet_v0.py"
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


def test_selector_behavior_sandbox_review_packet_parses_and_is_ready():
    payload = _read_json(PACKET)

    assert payload["schema_version"] == "krk_selector_behavior_sandbox_review_packet.v0"
    assert payload["causal_status"] == "non_causal_behavior_sandbox_review_packet"
    assert payload["decision"]["status"] == "selector_behavior_sandbox_review_ready"
    assert payload["possible_statuses"] == [
        "selector_behavior_sandbox_review_ready",
        "selector_behavior_sandbox_needs_more_observation",
        "selector_behavior_sandbox_blocked",
    ]
    assert payload["proposed_sandbox"]["name"] == (
        "default_off_narrow_selector_behavior_sandbox"
    )
    assert payload["proposed_sandbox"]["implementation_status"] == "not_implemented"
    assert payload["proposed_sandbox"]["authorization_status"] == (
        "review_packet_only_not_approved_for_implementation"
    )
    assert payload["proposed_sandbox"]["default_off_required"] is True
    assert payload["proposed_sandbox"]["opt_in_only"] is True
    assert payload["proposed_sandbox"]["opt_in_flag"] == (
        "--enable-krk-selector-behavior-sandbox"
    )


def test_selector_behavior_sandbox_review_packet_does_not_authorize_implementation():
    payload = _read_json(PACKET)
    decision = payload["decision"]

    assert decision["implementation_authorized_by_this_packet"] is False
    assert decision["behavior_changing_implementation_present"] is False
    assert decision["behavior_changing_selector_allowed_by_this_packet"] is False
    assert decision["runtime_changes_allowed_by_this_packet"] is False
    assert decision["default_off_required"] is True
    assert decision["selector_runtime_ready"] is False
    assert decision["selector_training_allowed"] is False
    assert decision["stage7_promotion_allowed"] is False
    assert decision["stage8_training_allowed"] is False
    assert decision["runtime_dtm_or_tablebase_allowed"] is False
    assert decision["gameplay_topology_mutation_allowed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_provider_suppression"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False


def test_selector_behavior_sandbox_scope_is_narrow_switch_only():
    payload = _read_json(PACKET)
    sandbox = payload["proposed_sandbox"]
    allowed = payload["allowed_effect"]
    vetoes = set(payload["required_vetoes"])

    assert sandbox["active_only_when_recommendation"] == "prefer_visible_alternative"
    assert sandbox["preserve_selected_owner_effect"] == "no_op"
    assert sandbox["abstain_context_only_effect"] == "no_op"
    assert sandbox["may_choose_only_already_visible_alternative"] is True
    assert sandbox["new_candidate_generation_allowed"] is False
    assert sandbox["direct_provider_request_allowed"] is False
    assert sandbox["hidden_routing_allowed"] is False
    assert allowed["bounded_switch_from_selected_owner_to_visible_alternative"] is True
    assert allowed["only_when_recommendation"] == "prefer_visible_alternative"
    assert allowed["record_original_selected_owner"] is True
    assert allowed["record_original_selected_move"] is True
    assert allowed["record_replacement_owner"] is True
    assert allowed["record_replacement_move"] is True
    assert allowed["record_source_terms"] is True
    assert allowed["record_explanation_terms"] is True
    assert allowed["direct_request"] is False
    assert allowed["score_delta"] == 0.0
    assert allowed["runtime_dtm_or_tablebase_allowed"] is False
    assert allowed["gameplay_topology_mutation_allowed"] is False

    assert "no_switch_if_recommendation_is_preserve_selected_owner" in vetoes
    assert "no_switch_if_recommendation_is_abstain_context_only" in vetoes
    assert "no_switch_if_no_visible_alternative_exists" in vetoes
    assert "no_switch_if_safe_preservation_veto_fires" in vetoes
    assert "no_switch_if_alternative_lacks_runtime_visible_provenance" in vetoes
    assert "no_switch_if_stage7_row_or_training_context" in vetoes
    assert "no_switch_if_source_terms_missing" in vetoes


def test_selector_behavior_sandbox_review_packet_forbidden_paths_and_validation():
    payload = _read_json(PACKET)
    forbidden = set(payload["explicitly_forbidden"])
    validation = set(payload["required_validation_before_later_implementation"])

    assert "implementation_by_this_packet" in forbidden
    assert "runtime_default_change" in forbidden
    assert "routing_changes" in forbidden
    assert "provider_suppression" in forbidden
    assert "new_candidate_generation" in forbidden
    assert "direct_provider_request" in forbidden
    assert "hidden_routing" in forbidden
    assert "stage7_promotion" in forbidden
    assert "stage8_training" in forbidden
    assert "runtime_dtm_or_tablebase" in forbidden
    assert "gameplay_topology_mutation" in forbidden
    assert "treating_capacity_labels_as_ownership_labels" in forbidden

    assert "explicit_approval" in validation
    assert "default_off_equivalence" in validation
    assert "trace_only_comparison_first" in validation
    assert "tiny_targeted_switch_smoke" in validation
    assert (
        "selected_move_provider_deltas_allowed_only_when_enabled_and_reviewed_switch_case"
        in validation
    )
    assert "score_delta_remains_zero_unless_separately_reviewed" in validation
    assert "target_improvement_before_guardrails" in validation
    assert "guardrails_before_promotion" in validation
    assert "rollback_tag" in validation


def test_selector_behavior_sandbox_review_packet_evidence_from_refined_observability():
    payload = _read_json(PACKET)
    evidence = payload["supporting_evidence"]

    assert evidence["refined_observability_status"] == (
        "refined_selector_observability_ready_for_recommendation_analysis"
    )
    assert evidence["enabled_recommendation_count"] == 14
    assert evidence["recommendation_counts_by_class"] == {
        "abstain_context_only": 6,
        "prefer_visible_alternative": 4,
        "preserve_selected_owner": 4,
    }
    assert evidence["switch_recommendation_count"] == 4
    assert evidence["source_terms"]
    assert evidence["preserve_on_failure_count"] == 0
    assert evidence["abstain_recall"] == 1.0
    assert evidence["switch_on_safe_owner_count"] == 0
    assert evidence["selector_training_row_count"] == 0
    assert evidence["stage7_training_row_count"] == 0
    assert evidence["selected_move_delta_count"] == 0
    assert evidence["selected_provider_delta_count"] == 0
    assert evidence["score_delta_count"] == 0
    assert evidence["routing_delta_count"] == 0
    assert evidence["runtime_behavior_changed"] is False
    assert evidence["runtime_dtm_or_tablebase_use"] is False
    assert evidence["gameplay_topology_mutation"] is False
    assert evidence["capacity_label_used_as_ownership_label_count"] == 0


def test_selector_behavior_sandbox_review_markdown_records_non_authorization():
    text = MARKDOWN.read_text(encoding="utf-8")

    assert "# KRK Selector Behavior Sandbox Review Packet v0" in text
    assert "It does not implement or authorize selector behavior." in text
    assert "- status: `selector_behavior_sandbox_review_ready`" in text
    assert "- implementation_authorized_by_this_packet: `False`" in text
    assert "- behavior_changing_implementation_present: `False`" in text
    assert "- default_off_required: `True`" in text
    assert "- preserve_selected_owner_effect: `no_op`" in text
    assert "- abstain_context_only_effect: `no_op`" in text
    assert "- `runtime_dtm_or_tablebase`" in text
    assert "- `gameplay_topology_mutation`" in text


def test_selector_behavior_sandbox_review_writer_needs_more_observation_without_switches():
    module = _load_module()
    refined = {
        "decision": {"status": "refined_selector_observability_ready_for_recommendation_analysis"},
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "hidden_python_controller": False,
        "summary": {
            "default_off_equivalence_passed": True,
            "runtime_behavior_changed": False,
            "preserve_on_failure_count": 0,
            "abstain_recall": 1.0,
            "switch_on_safe_owner_count": 0,
            "enabled_recommendation_count": 2,
            "recommendation_counts_by_class": {
                "abstain_context_only": 1,
                "prefer_visible_alternative": 0,
                "preserve_selected_owner": 1,
            },
            "source_term_coverage": {"source_terms": ["offline_validated_provider_capacity_evidence"]},
            "selected_move_delta_count": 0,
            "selected_provider_delta_count": 0,
            "score_delta_count": 0,
            "routing_delta_count": 0,
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
            "capacity_label_used_as_ownership_label_count": 0,
            "invalid_metadata_count": 0,
        },
    }
    payload = module.build_payload(
        refined_sandbox=refined,
        runtime_review={
            "decision": {"status": "refined_selector_observability_runtime_review_ready"}
        },
    )

    assert payload["decision"]["status"] == "selector_behavior_sandbox_needs_more_observation"
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["behavior_changing_selector_allowed_by_this_packet"] is False
