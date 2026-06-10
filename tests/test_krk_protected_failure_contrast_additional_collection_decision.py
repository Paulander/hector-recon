#!/usr/bin/env python3
"""Tests for the additional protected failure-contrast collection decision."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECISION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_protected_failure_contrast_additional_collection_decision_v1.json"
)


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_reports_current_agent_brief_is_canonical_and_root_is_pointer():
    canonical = (ROOT / "reports/current_agent_brief.md").read_text(encoding="utf-8")
    root = (ROOT / "current_agent_brief.md").read_text(encoding="utf-8")

    assert "This report is the canonical current-agent brief" in canonical
    assert "protected_failure_contrast_collection_not_worth_running" in canonical
    assert "reports/current_agent_brief.md" in root
    assert "Do not treat this root file as an independent source of truth." in root
    assert "Current Validated Stack" not in root


def test_additional_collection_decision_does_not_consume_conditional_approval():
    payload = _read_json(DECISION)

    assert (
        payload["schema_version"]
        == "krk_protected_failure_contrast_additional_collection_decision.v1"
    )
    assert payload["causal_status"] == "non_causal_architecture_review"
    assert payload["collection_executed"] is False
    assert payload["conditional_approval_consumed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["decision"]["status"] == (
        "protected_failure_contrast_collection_not_worth_running"
    )
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False


def test_additional_collection_decision_rejects_spent_stage4_mixed_manifest():
    payload = _read_json(DECISION)
    review = payload["review"]

    assert review["prior_collection_status"] == "collection_complete_underpowered"
    assert review["followup_packet_status"] == "blocked_needs_human_approval"
    assert review["current_collection_command_available"] is False
    assert review["current_manifest_stage_counts"] == {
        "stage4": 2,
        "stage5": 2,
        "stage6": 2,
    }
    assert review["current_outputs_h40_label_counts"] == {"conversion_positive": 6}
    assert review["prior_integrated_new_failure_count"] == 0
    assert review["stage5_6_only_required_for_next_manifest"] is True
    assert review["replay_free_unused_stage5_6_candidate_count"] == 6
    assert "manifest_already_spent" in review[
        "current_manifest_not_worth_running_reasons"
    ]
    assert "manifest_includes_stage4_rows" in review[
        "current_manifest_not_worth_running_reasons"
    ]
