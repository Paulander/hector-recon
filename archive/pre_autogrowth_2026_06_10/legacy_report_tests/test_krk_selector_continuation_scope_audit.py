#!/usr/bin/env python3
"""Tests for selector continuation scope audit and decision v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "reports/strategy_arbitration/krk_selector_continuation_scope_audit_v0.json"
AUDIT_MD = ROOT / "reports/strategy_arbitration/krk_selector_continuation_scope_audit_v0.md"
DECISION = (
    ROOT / "reports/strategy_arbitration/krk_selector_continuation_scope_decision_v0.json"
)
DECISION_MD = (
    ROOT / "reports/strategy_arbitration/krk_selector_continuation_scope_decision_v0.md"
)


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _load_module():
    path = ROOT / "scripts/write_krk_selector_continuation_scope_audit_v0.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selector_continuation_scope_audit_parses_and_classifies_regression():
    audit = _read_json(AUDIT)
    row = audit["regression_row"]

    assert audit["schema_version"] == "krk_selector_continuation_scope_audit.v0"
    assert audit["causal_status"] == "non_causal_scope_review_no_runtime_change"
    assert audit["summary"]["regression_row_id"] == "joined_trace_ownership_4"
    assert audit["summary"]["regression_ply"] == 4
    assert audit["summary"]["regression_is_initial_owner_choice"] is False

    assert row["fen_at_ply"] == "4R3/5k2/8/8/8/8/4K3/8 w - - 6 4"
    assert row["active_selected_owner_before_switch"] == "krk.fence_established"
    assert row["raw_selected_provider"] == "krk.fence_established"
    assert row["raw_selected_move"] == "e8a8"
    assert row["selector_replacement_provider"] == "krk.edge_trap_close"
    assert row["selector_replacement_move"] == "e8b8"
    assert row["recommendation_class"] == "prefer_visible_alternative"
    assert row["active_landmark"] == "fence_established"
    assert row["plan_context"] == "active_h40_continuation_after_initial_owner_choice"
    assert row["continuation_context"]["is_initial_owner_choice"] is False
    assert row["baseline_continuation_outcome"]["result"] == "mate"
    assert row["baseline_continuation_outcome"]["plies"] == 17
    assert row["enabled_continuation_outcome"]["result"] == "max_plies"
    assert row["enabled_continuation_outcome"]["plies"] == 40


def test_selector_continuation_scope_compares_initial_switches_and_safe_rows():
    audit = _read_json(AUDIT)
    comparison = audit["comparison"]

    assert audit["summary"]["successful_initial_switch_count"] == 2
    assert {
        row["row_id"] for row in comparison["ply0_successful_switch_cases"]
    } == {
        "stage4_joined_trace_ownership_1",
        "selector_objective_fresh_diversity.05",
    }
    assert all(
        row["decision_window"] == "initial_owner_choice" and row["ply"] == 0
        for row in comparison["ply0_successful_switch_cases"]
    )
    assert audit["summary"]["safe_preservation_row_count"] == 6
    assert comparison["preserve_or_abstain_rows_inside_continuation_windows"]
    assert "initial-owner switching" in comparison["finding"]
    assert "later h40 continuation switch" in comparison["finding"]


def test_selector_continuation_scope_rules_support_initial_owner_only_future_review():
    audit = _read_json(AUDIT)
    rules = {
        item["rule"]: item
        for item in audit["non_causal_scope_rule_evaluations"]
    }

    ply0 = rules["selector allowed only at initial decision / ply 0"]
    assert ply0["classification"] == "supported_for_future_review"
    assert ply0["would_preserve_prior_target_improvements"] is True
    assert ply0["would_eliminate_safe_control_regression"] is True
    assert ply0["runtime_feature_eligible"] is True

    assert rules[
        "selector blocked when current provider is in an active continuation window"
    ]["classification"] == "supported_but_needs_monitor_definition"
    assert rules[
        "selector blocked when selected owner has recent progress"
    ]["classification"] == "promising_but_requires_runtime_progress_proxy"
    assert rules[
        "selector blocked when plan/edge/fence continuation is active"
    ]["classification"] == "supported_but_broader_than_ply0_only"
    assert rules[
        "selector may only recommend abstain during continuation unless failure-risk monitor fires"
    ]["classification"] == "needs_more_evidence"
    assert rules["current quarantined selector_behavior path"]["classification"] == (
        "unsafe_as_implemented"
    )


def test_selector_continuation_scope_decision_parses_and_does_not_implement_fix():
    decision = _read_json(DECISION)

    assert decision["schema_version"] == "krk_selector_continuation_scope_decision.v0"
    assert decision["causal_status"] == "future_review_packet_only_no_runtime_change"
    assert decision["decision"]["status"] == "selector_scope_initial_owner_only_supported"
    assert decision["decision"]["status"] in decision["possible_decisions"]
    assert decision["decision"]["promote_selector"] is False
    assert decision["decision"]["make_default"] is False
    assert decision["decision"]["implement_fix_now"] is False
    assert decision["decision"]["write_future_narrowed_sandbox_review_only"] is True
    assert decision["decision"]["runtime_changes_allowed"] is False
    assert decision["selector_unquarantined"] is False
    assert decision["production_fix_implemented"] is False
    assert decision["production_runtime_behavior_changed"] is False
    assert decision["runtime_defaults_changed"] is False


def test_selector_continuation_scope_hard_invariants():
    audit = _read_json(AUDIT)
    decision = _read_json(DECISION)

    for payload in (audit, decision):
        assert payload["production_runtime_behavior_changed"] is False
        assert payload["runtime_defaults_changed"] is False
        assert payload["selector_unquarantined"] is False
        assert payload["production_fix_implemented"] is False
        assert payload["thresholds_tuned"] is False
        assert payload["stage8_training_allowed"] is False
        assert payload["stage7_promotion_allowed"] is False
        assert payload["runtime_dtm_or_tablebase_lookup"] is False
        assert payload["gameplay_topology_mutation"] is False

    assert audit["summary"]["stage7_training_row_count"] == 0
    assert audit["summary"]["selector_training_row_count"] == 0
    assert audit["summary"]["capacity_label_used_as_ownership_label_count"] == 0
    assert decision["evidence"]["stage7_training_row_count"] == 0
    assert decision["evidence"]["selector_training_row_count"] == 0
    assert decision["evidence"]["capacity_label_used_as_ownership_label_count"] == 0
    assert decision["evidence"]["selector_remains_quarantined"] is True


def test_selector_continuation_scope_capacity_labels_not_ownership_labels():
    audit = _read_json(AUDIT)
    row = audit["regression_row"]

    assert "stage_conditioned_capacity_scope_not_ownership_label" in row["source_terms"]
    assert audit["summary"]["capacity_label_used_as_ownership_label_count"] == 0
    assert "offline ownership labels" in audit["evaluation"]["runtime_feature_eligibility_notes"]


def test_selector_continuation_scope_markdown_records_decision():
    audit_text = AUDIT_MD.read_text(encoding="utf-8")
    decision_text = DECISION_MD.read_text(encoding="utf-8")

    assert "# KRK Selector Continuation Scope Audit v0" in audit_text
    assert "- regression_ply: `4`" in audit_text
    assert "- raw_selected_move: `e8a8`" in audit_text
    assert "- selector_replacement_move: `e8b8`" in audit_text
    assert "- decision_recommendation: `selector_scope_initial_owner_only_supported`" in audit_text
    assert "# KRK Selector Continuation Scope Decision v0" in decision_text
    assert "- status: `selector_scope_initial_owner_only_supported`" in decision_text
    assert "- implement_fix_now: `False`" in decision_text


def test_selector_continuation_scope_writer_accepts_fake_payloads():
    module = _load_module()
    root_cause = {
        "minimal_reproduction": {
            "row_id": "joined_trace_ownership_4",
            "state_id": "state.2c1d6da27ea1",
        },
        "first_divergence": {
            "ply": 4,
            "control": {
                "selected_provider": "krk.fence_established",
                "move": "e8a8",
            },
            "enabled": {
                "fen": "fen",
                "original_provider": "krk.fence_established",
                "original_move": "e8a8",
                "replacement_provider": "krk.edge_trap_close",
                "replacement_move": "e8b8",
                "recommendation": "prefer_visible_alternative",
                "recommendation_reason": "reason",
                "why_selected_alternative": "first_current_suggestion_matching_runtime_visible_alternative",
                "selected_provider": "krk.edge_trap_close",
                "move": "e8b8",
                "recommendation_terms": ["source_stage.stage5"],
                "visible_alternatives": [],
            },
        },
        "observed_vs_expected": {
            "control_result": {"result": "mate", "plies": 17},
            "selector_behavior_enabled_result": {"result": "max_plies", "plies": 40},
            "selector_observability_only_result": {"result": "mate", "plies": 17},
        },
        "variant_traces": [
            {
                "variant": "selector_behavior_enabled_cached",
                "white_events": [
                    {
                        "ply": 2,
                        "recommendation": "preserve_selected_owner",
                        "behavior_action": "no_op",
                    }
                ],
            }
        ],
    }
    smoke = {
        "summary": {"target_improvement_count": 1},
        "rows": [
            {
                "row_id": "s",
                "state_id": "state.s",
                "behavior_action": "switch_to_visible_alternative",
                "target_improved": True,
                "selected_owner_label": "selected_owner_failed",
                "flag_off_decision": {"selected_provider": "a", "move": "m"},
                "enabled_decision": {
                    "behavior_sandbox_decision": {
                        "replacement_provider": "b",
                        "replacement_move": "n",
                    },
                    "selector_recommendation": {
                        "recommendation": "prefer_visible_alternative",
                    },
                },
            }
        ],
    }
    validation = {
        "summary": {
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "capacity_label_used_as_ownership_label_count": 0,
            "safe_regression_count": 1,
        },
        "rows": [],
    }

    audit = module.build_audit_payload(
        root_cause=root_cause,
        smoke=smoke,
        validation=validation,
    )
    decision = module.build_decision_payload(audit)

    assert audit["decision_recommendation"] == "selector_scope_initial_owner_only_supported"
    assert audit["summary"]["successful_initial_switch_count"] == 1
    assert decision["decision"]["implement_fix_now"] is False
    assert decision["decision"]["status"] == "selector_scope_initial_owner_only_supported"
