#!/usr/bin/env python3
"""Tests for selector behavior regression audit and decision v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = (
    ROOT
    / "reports/strategy_arbitration/krk_selector_behavior_regression_audit_v0.json"
)
AUDIT_MD = (
    ROOT
    / "reports/strategy_arbitration/krk_selector_behavior_regression_audit_v0.md"
)
DECISION = (
    ROOT
    / "reports/strategy_arbitration/krk_selector_behavior_regression_decision_v0.json"
)
DECISION_MD = (
    ROOT
    / "reports/strategy_arbitration/krk_selector_behavior_regression_decision_v0.md"
)


def _load_module():
    path = ROOT / "scripts/write_krk_selector_behavior_regression_audit_v0.py"
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


def test_selector_behavior_regression_audit_identifies_safe_control_row():
    audit = _read_json(AUDIT)
    rows = audit["regressed_safe_control_rows"]

    assert audit["schema_version"] == "krk_selector_behavior_regression_audit.v0"
    assert audit["causal_status"] == "non_causal_post_validation_regression_audit"
    assert audit["summary"]["regressed_safe_control_count"] == 1
    assert len(rows) == 1

    regression = rows[0]
    assert regression["row_id"] == "joined_trace_ownership_4"
    assert regression["state_id"] == "state.2c1d6da27ea1"
    assert regression["stage"] == "stage5"
    assert regression["selected_owner_before_sandbox"] == "selected_owner_converted"
    assert regression["selected_provider_before_sandbox"] == "krk.stage0_basin"
    assert regression["selected_move_before_sandbox"] == "a7a8"
    assert regression["sandbox_action"] == "no_op"
    assert regression["sandbox_replacement_owner"] is None
    assert regression["sandbox_replacement_move"] is None
    assert regression["recommendation_class"] == "preserve_selected_owner"
    assert regression["first_row_switch_observed"] is False
    assert regression["baseline_outcome"]["result"] == "mate"
    assert regression["baseline_outcome"]["plies"] == 17
    assert regression["enabled_outcome"]["result"] == "max_plies"
    assert regression["enabled_outcome"]["plies"] == 40
    assert regression["h40_safe_regression"] is True
    assert regression["direct_safe_regression"] is False
    assert regression["visible_alternatives"]
    assert regression["source_terms"]
    assert regression["explanation_terms"]


def test_selector_behavior_regression_audit_classifies_cause_without_bug_claim():
    audit = _read_json(AUDIT)
    classification = audit["regression_cause_classification"]

    assert classification["allowed_classes"] == [
        "recommendation_wrong",
        "alternative_selection_wrong",
        "safe_preservation_veto_missing",
        "visible_alternative_overtrusted",
        "label_semantics_mismatch",
        "horizon/noise issue",
        "implementation bug",
    ]
    assert classification["primary_causes"] == [
        "safe_preservation_veto_missing",
        "visible_alternative_overtrusted",
        "horizon/noise issue",
    ]
    assert "implementation bug" in classification["rejected_or_unproven_causes"]
    assert audit["fix_implemented"] is False
    assert audit["runtime_behavior_changed"] is False
    assert audit["runtime_selector_implemented"] is False


def test_selector_behavior_regression_comparison_separates_successes_but_not_causal_path():
    audit = _read_json(AUDIT)
    comparison = audit["successful_switch_comparison"]
    successes = comparison["successful_switches"]

    assert comparison["successful_switch_count"] == 2
    assert {row["row_id"] for row in successes} == {
        "stage4_joined_trace_ownership_1",
        "selector_objective_fresh_diversity.05",
    }
    assert {row["selected_owner_before_sandbox"] for row in successes} == {
        "selected_owner_failed"
    }
    assert {row["recommendation_class"] for row in successes} == {
        "prefer_visible_alternative"
    }
    assert comparison["observed_separators"]["owner_label"]["regressed_values"] == [
        "selected_owner_converted"
    ]
    assert "later h40 continuation effect" in comparison["separation_assessment"]


def test_selector_behavior_regression_decision_quarantines_without_runtime_changes():
    decision = _read_json(DECISION)

    assert decision["schema_version"] == "krk_selector_behavior_regression_decision.v0"
    assert decision["causal_status"] == "non_causal_regression_decision_no_runtime_fix"
    assert decision["decision"]["status"] == (
        "selector_behavior_quarantined_due_to_safe_regression"
    )
    assert decision["decision"]["status"] in decision["possible_decisions"]
    assert decision["decision"]["promote"] is False
    assert decision["decision"]["make_default"] is False
    assert decision["decision"]["implement_fix_now"] is False
    assert decision["decision"]["write_narrowing_review_packet_now"] is False
    assert decision["decision"]["train_anything"] is False
    assert decision["decision"]["runtime_changes_allowed"] is False
    assert decision["fix_implemented"] is False
    assert decision["runtime_behavior_changed"] is False
    assert decision["runtime_defaults_changed"] is False
    assert decision["runtime_score_changes"] is False
    assert decision["runtime_direct_routing"] is False
    assert decision["runtime_provider_suppression"] is False
    assert decision["runtime_dtm_or_tablebase_lookup"] is False
    assert decision["gameplay_topology_mutation"] is False


def test_selector_behavior_regression_invariants_from_protected_validation():
    audit = _read_json(AUDIT)
    decision = _read_json(DECISION)
    summary = audit["summary"]
    evidence = decision["evidence"]

    assert summary["enabled_switch_count"] == 0
    assert summary["target_improvement_count"] == 0
    assert summary["safe_regression_count"] == 1
    assert summary["h40_regression_count"] == 1
    assert summary["h40_improvement_count"] == 0
    assert summary["preserve_noop_count"] == 6
    assert summary["abstain_noop_count"] == 0
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["capacity_label_used_as_ownership_label_count"] == 0

    assert evidence["enabled_switch_count_on_protected_sample"] == 0
    assert evidence["protected_safe_regression_row_ids"] == [
        "joined_trace_ownership_4"
    ]
    assert evidence["stage7_training_row_count"] == 0
    assert evidence["selector_training_row_count"] == 0
    assert evidence["capacity_label_used_as_ownership_label_count"] == 0


def test_selector_behavior_regression_capacity_labels_remain_non_ownership_labels():
    audit = _read_json(AUDIT)
    regression = audit["regressed_safe_control_rows"][0]

    label_semantics = {
        item["label_semantics"]
        for item in regression["visible_alternatives"]
        if item["label_semantics"]
    }
    assert label_semantics == {"stage_conditioned_capacity_scope_not_ownership_label"}
    assert audit["summary"]["capacity_label_used_as_ownership_label_count"] == 0

    fix_eval = {
        item["fix"]: item["assessment"] for item in audit["non_causal_fix_evaluation"]
    }
    assert fix_eval["require target row class / switch-contrast scope"] == (
        "not_runtime_eligible_as_stated"
    )
    assert fix_eval["quarantine behavior selector if separation is not clean"] == (
        "recommended_now"
    )


def test_selector_behavior_regression_markdown_records_quarantine_and_no_fix():
    audit_text = AUDIT_MD.read_text(encoding="utf-8")
    decision_text = DECISION_MD.read_text(encoding="utf-8")

    assert "# KRK Selector Behavior Regression Audit v0" in audit_text
    assert "- row_id: `joined_trace_ownership_4`" in audit_text
    assert "- recommendation_class: `preserve_selected_owner`" in audit_text
    assert "does not implement a fix" in audit_text
    assert "# KRK Selector Behavior Regression Decision v0" in decision_text
    assert "- status: `selector_behavior_quarantined_due_to_safe_regression`" in decision_text
    assert "- implement_fix_now: `False`" in decision_text
    assert "- runtime_changes_allowed: `False`" in decision_text


def test_selector_behavior_regression_writer_needs_existing_regression_for_quarantine():
    module = _load_module()
    validation = {
        "decision": {"status": "selector_behavior_sandbox_validation_promising"},
        "summary": {
            "sample_scope": "fake",
            "sample_count": 1,
            "enabled_switch_count": 1,
            "target_improvement_count": 1,
            "safe_regression_count": 0,
            "h40_regression_count": 0,
            "h40_improvement_count": 1,
            "preserve_noop_count": 0,
            "abstain_noop_count": 0,
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
            "capacity_label_used_as_ownership_label_count": 0,
        },
        "rows": [],
    }
    smoke = {
        "decision": {"status": "selector_behavior_sandbox_target_improved"},
        "summary": {
            "target_improvement_count": 1,
            "safe_regression_count": 0,
        },
        "rows": [],
    }
    audit = module.build_audit_payload(
        validation_report=validation,
        smoke_report=smoke,
    )
    decision = module.build_decision_payload(audit)

    assert audit["summary"]["regressed_safe_control_count"] == 0
    assert audit["summary"]["stage7_training_row_count"] == 0
    assert decision["decision"]["implement_fix_now"] is False
    assert decision["decision"]["runtime_changes_allowed"] is False
