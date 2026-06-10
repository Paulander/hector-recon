#!/usr/bin/env python3
"""Tests for selector behavior branch closure v0."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLOSURE = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_behavior_branch_closure_v0.json"
)
CLOSURE_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_behavior_branch_closure_v0.md"
)
BRIEF = ROOT / "reports/current_agent_brief.md"


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_selector_behavior_branch_closure_artifact_parses():
    payload = _read_json(CLOSURE)

    assert payload["schema_version"] == "krk_selector_behavior_branch_closure.v0"
    assert payload["causal_status"] == "architecture_branch_closure_no_runtime_change"
    assert payload["decision"]["status"] == (
        "selector_behavior_branch_closed_return_to_control_plane"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["implement_selector_behavior"] is False
    assert payload["decision"]["write_behavior_review_packet"] is False


def test_selector_behavior_status_is_quarantined():
    payload = _read_json(CLOSURE)
    final_status = payload["final_branch_status"]
    evidence = payload["evidence_summary"]

    assert final_status["selector_behavior_sandbox"] == "quarantined"
    assert final_status["behavior_changing_selector"] == "blocked"
    assert final_status["trace_only_observability"] == "useful_non_causal"
    assert evidence["protected_safe_regression_count"] == 1
    assert evidence["protected_h40_improvement_count"] == 0


def test_runtime_selector_not_authorized():
    payload = _read_json(CLOSURE)

    assert payload["runtime_selector_authorized"] is False
    assert payload["behavior_changing_selector_authorized"] is False
    assert payload["final_branch_status"]["runtime_selector_authorized"] is False
    assert payload["final_branch_status"]["selector_runtime_ready"] is False
    assert "behavior_changing_selector_implementation" in payload["forbidden_work"]
    assert "runtime_provider_choice_override" in payload["forbidden_work"]


def test_stage7_and_stage8_remain_blocked():
    payload = _read_json(CLOSURE)
    evidence = payload["evidence_summary"]

    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert evidence["stage7_training_row_count"] == 0
    assert evidence["selector_training_row_count"] == 0
    assert "stage7_promotion" in payload["forbidden_work"]
    assert "stage8_training" in payload["forbidden_work"]


def test_capacity_labels_not_ownership_labels():
    payload = _read_json(CLOSURE)

    assert payload["evidence_summary"][
        "capacity_label_used_as_ownership_label_count"
    ] == 0
    assert "using_capacity_labels_as_ownership_labels" in payload["forbidden_work"]


def test_no_runtime_behavior_changes():
    payload = _read_json(CLOSURE)

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_provider_suppression"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["evidence_summary"]["default_off_equivalence_preserved"] is True


def test_closure_markdown_and_brief_updated():
    md_text = CLOSURE_MD.read_text(encoding="utf-8")
    brief_text = BRIEF.read_text(encoding="utf-8")

    assert "# KRK Selector Behavior Branch Closure v0" in md_text
    assert "- decision: `selector_behavior_branch_closed_return_to_control_plane`" in md_text
    assert "behavior-changing selector sandbox is quarantined" in brief_text
    assert "Trace-only selector observability" in brief_text
    assert "broader KRK strategy/sequence control plane" in brief_text


def test_timeline_records_required_gate_statuses():
    payload = _read_json(CLOSURE)
    statuses = {row["status"] for row in payload["timeline"]}

    assert "selector_objective_benchmark_promising_non_causal" in statuses
    assert "refined_selector_initial_owner_ready_for_behavior_review_packet" in statuses
    assert "selector_behavior_sandbox_regresses_safe_controls" in statuses
    assert "selector_behavior_quarantined_due_to_safe_regression" in statuses
    assert "selector_scope_initial_owner_only_supported" in statuses
