#!/usr/bin/env python3
"""Tests for protected selector behavior sandbox validation v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = (
    ROOT
    / "reports/strategy_arbitration/krk_selector_behavior_sandbox_validation_v0.json"
)
REPORT = (
    ROOT
    / "reports/strategy_arbitration/krk_selector_behavior_sandbox_validation_v0.md"
)


def _load_module():
    path = ROOT / "scripts/run_krk_selector_behavior_sandbox_validation_v0.py"
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


def test_selector_behavior_validation_artifacts_parse_and_quarantine_progression():
    payload = _read_json(ARTIFACT)
    markdown = REPORT.read_text(encoding="utf-8")

    assert payload["schema_version"] == "krk_selector_behavior_sandbox_validation.v0"
    assert payload["causal_status"] == "protected_behavior_sandbox_validation_no_promotion"
    assert payload["decision"]["status"] == (
        "selector_behavior_sandbox_regresses_safe_controls"
    )
    assert payload["decision"]["status"] in payload["possible_statuses"]
    assert payload["decision"]["promote"] is False
    assert payload["decision"]["make_default"] is False
    assert payload["decision"]["run_full_broad_guardrails"] is False
    assert payload["decision"]["write_guardrail_review_packet_only_if_ready"] is False
    assert payload["decision"]["train_anything"] is False
    assert "# KRK Selector Behavior Sandbox Validation v0" in markdown
    json.dumps(payload)


def test_selector_behavior_validation_default_off_and_hard_constraints():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["sample_count"] == 8
    assert summary["sample_scope"] == "stage5_6_protected_joined_trace_h40"
    assert summary["default_off_equivalence_passed"] is True
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["runtime_dtm_or_tablebase"] is False
    assert summary["topology_mutation"] is False
    assert summary["capacity_label_used_as_ownership_label_count"] == 0
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_provider_suppression"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["gameplay_topology_mutation"] is False


def test_selector_behavior_validation_preserve_abstain_noop_and_switch_scope():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["preserve_noop_count"] == 6
    assert summary["abstain_noop_count"] == 0
    assert summary["enabled_switch_count"] == 0
    assert summary["invalid_switch_count"] == 0
    assert summary["switch_source_term_coverage"] == []
    for row in payload["rows"]:
        if row["recommendation"] in {"preserve_selected_owner", "abstain_context_only"}:
            assert row["behavior_action"] == "no_op"
        if row["behavior_action"] == "switch_to_visible_alternative":
            assert row["recommendation"] == "prefer_visible_alternative"
            assert row["switch_used_visible_alternative"] is True


def test_selector_behavior_validation_records_h40_regression_without_promotion():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["safe_regression_count"] == 1
    assert summary["h40_regression_count"] == 1
    assert summary["h40_improvement_count"] == 0
    assert summary["target_improvement_count"] == 0
    regressions = [row for row in payload["rows"] if row["h40_safe_regression"]]
    assert len(regressions) == 1
    regression = regressions[0]
    assert regression["row_id"] == "joined_trace_ownership_4"
    assert regression["h40_validation_role"] == "safe_preservation"
    assert regression["h40_default_off"]["result"] == "mate"
    assert regression["h40_enabled"]["result"] == "max_plies"
    assert summary["mate_max_plies_before_vs_after"]


def test_selector_behavior_validation_breakdowns_and_h40_fields():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["per_stage_breakdown"] == {"stage5": 5, "stage6": 3}
    assert summary["per_provider_breakdown"] == {"krk.stage0_basin": 8}
    assert summary["shadow_candidate_delta_available"] is False
    assert len(summary["mate_max_plies_before_vs_after"]) == summary["sample_count"]
    for row in payload["rows"]:
        assert row["source_stage"] in {"stage5", "stage6"}
        assert row["stage7_training_row"] is False
        assert row["selector_training_row"] is False
        assert row["h40_default_off"]["result"] in {"mate", "max_plies", "draw", "no_move"}
        assert row["h40_enabled"]["result"] in {"mate", "max_plies", "draw", "no_move"}


def test_selector_behavior_validation_writer_statuses_with_fake_runners():
    module = _load_module()
    manifest = {
        "cases": [
            {
                "case_id": "case.1",
                "row_id": "case.1",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "selected_owner_label": "selected_owner_failed",
                "selected_provider_label": "krk.stage0_basin",
                "h40_validation_role": "switch_contrast",
            }
        ]
    }

    def fake_decision(case: dict, enabled: bool) -> dict:
        return {
            "move": "a1a2" if not enabled else "a1a3",
            "selected_provider": "krk.stage0_basin",
            "confidence": 1.0,
            "selector_recommendation_present": enabled,
            "selector_recommendation": {
                "recommendation": "prefer_visible_alternative",
                "visible_alternatives_considered": [
                    {"provider_id": "krk.stage0_basin", "move_id": "a1a3"}
                ],
            }
            if enabled
            else {},
            "behavior_sandbox_decision_present": enabled,
            "behavior_sandbox_decision": {
                "action": "switch_to_visible_alternative",
                "replacement_provider": "krk.stage0_basin",
                "replacement_move": "a1a3",
                "original_selected_provider": "krk.stage0_basin",
                "score_delta": 0.0,
                "runtime_dtm_or_tablebase": False,
                "gameplay_topology_mutation": False,
                "source_terms": ["offline_validated_provider_capacity_evidence"],
            }
            if enabled
            else {},
        }

    def fake_h40(case: dict, enabled: bool) -> dict:
        return {"result": "max_plies" if not enabled else "mate", "plies": 40 if not enabled else 9}

    payload = module.build_payload(
        decision_runner=fake_decision,
        h40_runner=fake_h40,
        manifest=manifest,
    )

    assert payload["decision"]["status"] == "selector_behavior_sandbox_validation_promising"
    assert payload["summary"]["default_off_equivalence_passed"] is True
    assert payload["summary"]["enabled_switch_count"] == 1
    assert payload["summary"]["target_improvement_count"] == 1
