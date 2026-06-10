#!/usr/bin/env python3
"""Tests for refined initial-owner selector recommendation analysis v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_recommendation_analysis_v0.json"
)
ANALYSIS_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_recommendation_analysis_v0.md"
)
GATE = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_next_gate_v0.json"
)
GATE_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_next_gate_v0.md"
)
REVIEW_PACKET = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_behavior_review_packet_v0.json"
)
REVIEW_PACKET_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_refined_selector_initial_owner_behavior_review_packet_v0.md"
)


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _load_module():
    path = (
        ROOT
        / "scripts/write_krk_refined_selector_initial_owner_recommendation_analysis_v0.py"
    )
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_refined_initial_owner_recommendation_analysis_parses_sandbox_artifact():
    payload = _read_json(ANALYSIS)
    summary = payload["summary"]

    assert payload["schema_version"] == (
        "krk_refined_selector_initial_owner_recommendation_analysis.v0"
    )
    assert payload["causal_status"] == "non_causal_recommendation_analysis_only"
    assert payload["input_statuses"]["sandbox_status"] == (
        "refined_selector_initial_owner_observability_ready_for_recommendation_analysis"
    )
    assert summary["row_count"] == 14
    assert summary["recommendation_counts_by_class"] == {
        "abstain_context_only": 6,
        "prefer_visible_alternative": 4,
        "preserve_selected_owner": 4,
    }
    assert summary["preserve_on_failure_count"] == 0
    assert summary["switch_on_safe_owner_count"] == 0
    assert summary["unsafe_if_causal_count"] == 0
    assert payload["decision_recommendation"] == (
        "refined_selector_initial_owner_ready_for_behavior_review_packet"
    )


def test_refined_initial_owner_recommendation_analysis_abstain_and_alignment():
    payload = _read_json(ANALYSIS)
    summary = payload["summary"]

    assert summary["abstain_count"] == 6
    assert summary["weak_evidence_abstain_count"] == 5
    assert summary["abstain_missed_switch_count"] == 1
    assert summary["abstain_recall"] == 1.0
    assert summary["offline_alignment_count"] == 13
    assert summary["offline_alignment_rate"] == 13 / 14
    assert len(payload["abstain_gap_rows"]) == 1
    assert payload["abstain_gap_rows"][0]["row_id"] == (
        "selector_objective_fresh_diversity.02"
    )


def test_refined_initial_owner_recommendation_analysis_terms_and_visible_alternatives():
    payload = _read_json(ANALYSIS)
    terms = payload["term_coverage"]
    visible = payload["visible_alternatives_coverage"]

    assert terms["unique_source_term_count"] > 0
    assert terms["unique_explanation_term_count"] > 0
    assert "selector_model.combined_simple_rule" in terms["explanation_terms"]
    assert "stage_conditioned_candidate_generation_refresh" in visible[
        "candidate_source_counts"
    ]
    assert visible["row_count_with_visible_alternatives"] == 9
    assert visible["total_visible_alternative_count"] == 75
    assert payload["summary"]["runtime_visible_terms_failure_count"] == 0
    assert payload["summary"]["runtime_visible_terms_only_count"] == 14


def test_refined_initial_owner_recommendation_analysis_hard_invariants():
    payload = _read_json(ANALYSIS)
    summary = payload["summary"]

    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["capacity_label_used_as_ownership_label_count"] == 0
    assert summary["runtime_behavior_changed"] is False
    assert summary["continuation_recommendation_count"] == 0
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["behavior_changing_selector_implemented"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False


def test_refined_initial_owner_capacity_labels_remain_not_ownership_labels():
    payload = _read_json(ANALYSIS)
    semantics = payload["capacity_label_semantics"]

    assert semantics["capacity_labels_are_ownership_labels"] is False
    assert semantics["capacity_label_used_as_ownership_label_count"] == 0
    assert "not treated as selected-owner ground truth" in semantics["note"]
    assert payload["visible_alternatives_coverage"]["label_semantics_counts"][
        "stage_conditioned_capacity_scope_not_ownership_label"
    ] == 60
    assert payload["stage7_holdout"]["stage7_training_row_count"] == 0
    assert payload["stage7_holdout"]["stage7_remains_held_out"] is True


def test_refined_initial_owner_next_gate_ready_but_no_behavior_implementation():
    gate = _read_json(GATE)

    assert gate["schema_version"] == "krk_refined_selector_initial_owner_next_gate.v0"
    assert gate["causal_status"] == "review_gate_only_no_behavior_change"
    assert gate["decision"]["status"] == (
        "refined_selector_initial_owner_ready_for_behavior_review_packet"
    )
    assert gate["decision"]["status"] in gate["possible_decisions"]
    assert gate["decision"]["write_behavior_review_packet_only"] is True
    assert gate["decision"]["implement_behavior_selector"] is False
    assert gate["decision"]["runtime_changes_allowed"] is False
    assert gate["decision"]["provider_selection_changes_allowed"] is False
    assert gate["decision"]["move_selection_changes_allowed"] is False
    assert gate["decision"]["routing_changes_allowed"] is False
    assert gate["decision"]["score_changes_allowed"] is False
    assert gate["decision"]["provider_suppression_allowed"] is False
    assert gate["decision"]["selector_training_allowed"] is False
    assert gate["decision"]["stage7_promotion_allowed"] is False
    assert gate["decision"]["stage8_training_allowed"] is False


def test_refined_initial_owner_behavior_review_packet_is_review_only():
    packet = _read_json(REVIEW_PACKET)

    assert packet["schema_version"] == (
        "krk_refined_selector_initial_owner_behavior_review_packet.v0"
    )
    assert packet["causal_status"] == "future_behavior_sandbox_review_packet_only"
    assert packet["decision"]["status"] == (
        "refined_selector_initial_owner_behavior_review_packet_ready"
    )
    assert packet["decision"]["implementation_authorized_by_this_packet"] is False
    assert packet["decision"]["runtime_changes_allowed_by_this_packet"] is False
    assert packet["decision"]["selector_runtime_ready"] is False
    assert packet["proposed_future_sandbox"]["implementation_status"] == "not_implemented"
    assert packet["proposed_future_sandbox"]["default_off_required"] is True
    assert packet["proposed_future_sandbox"]["initial_owner_only"] is True
    assert packet["proposed_future_sandbox"]["continuation_recommendations_allowed"] is False
    assert packet["proposed_future_sandbox"]["score_delta"] == 0.0
    assert packet["proposed_future_sandbox"]["direct_request"] is False
    assert "no_switch_if_not_initial_owner_decision" in packet[
        "required_vetoes_before_implementation"
    ]
    assert "no_switch_if_capacity_label_would_be_treated_as_ownership_label" in packet[
        "required_vetoes_before_implementation"
    ]


def test_refined_initial_owner_recommendation_analysis_markdown_outputs():
    analysis_text = ANALYSIS_MD.read_text(encoding="utf-8")
    gate_text = GATE_MD.read_text(encoding="utf-8")
    packet_text = REVIEW_PACKET_MD.read_text(encoding="utf-8")

    assert "# KRK Refined Selector Initial Owner Recommendation Analysis v0" in analysis_text
    assert (
        "- decision_recommendation: `refined_selector_initial_owner_ready_for_behavior_review_packet`"
        in analysis_text
    )
    assert "# KRK Refined Selector Initial Owner Next Gate v0" in gate_text
    assert (
        "- status: `refined_selector_initial_owner_ready_for_behavior_review_packet`"
        in gate_text
    )
    assert "# KRK Refined Selector Initial Owner Behavior Review Packet v0" in packet_text
    assert "- implementation_authorized_by_this_packet: `False`" in packet_text


def test_refined_initial_owner_recommendation_analysis_writer_blocks_preserve_failure():
    module = _load_module()
    sandbox = {
        "decision": {
            "status": "refined_selector_initial_owner_observability_ready_for_recommendation_analysis"
        },
        "summary": {
            "default_off_equivalence_passed": True,
            "continuation_recommendation_count": 0,
            "preserve_on_failure_count": 1,
            "switch_on_safe_owner_count": 0,
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
            "capacity_label_used_as_ownership_label_count": 0,
            "runtime_behavior_changed": False,
            "selected_move_delta_count": 0,
            "selected_provider_delta_count": 0,
            "score_delta_count": 0,
            "routing_delta_count": 0,
            "abstain_recall": 1.0,
        },
        "rows": [
            {
                "row_id": "r",
                "offline_target_action": "prefer_visible_alternative",
                "recommendation": "preserve_selected_owner",
                "preserve_on_selected_owner_failure": True,
                "switch_on_safe_owner": False,
                "visible_alternative_count": 1,
                "source_terms": [],
                "explanation_terms": ["selector_model.combined_simple_rule"],
                "enabled_decision": {
                    "selector_recommendation": {
                        "positive_trace_provider_candidate_count": 1,
                    }
                },
            }
        ],
    }
    payload = module.build_analysis_payload(
        sandbox=sandbox,
        preserve_risk={"decision": {"status": "x"}},
        benchmark={"decision": {"status": "x"}},
        seed_manifest={"decision": {"status": "x"}},
        agent_brief_text="Stage 7 remains held out",
    )

    assert payload["decision_recommendation"] == (
        "refined_selector_initial_owner_blocked_by_preserve_failure_risk"
    )
