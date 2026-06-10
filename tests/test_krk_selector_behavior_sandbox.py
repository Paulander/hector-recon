#!/usr/bin/env python3
"""Tests for narrow selector behavior sandbox v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "reports/strategy_arbitration/krk_selector_behavior_sandbox_v0.json"
REPORT = ROOT / "reports/strategy_arbitration/krk_selector_behavior_sandbox_v0.md"


def _load_module():
    path = ROOT / "scripts/run_krk_selector_behavior_sandbox_v0.py"
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


def test_selector_behavior_sandbox_artifacts_parse_and_decision():
    payload = _read_json(ARTIFACT)
    markdown = REPORT.read_text(encoding="utf-8")

    assert payload["schema_version"] == "krk_selector_behavior_sandbox.v0"
    assert payload["sandbox_id"] == "sandbox.krk.selector_behavior_v0"
    assert payload["approval"]["flag_required"] == "--enable-krk-selector-behavior-sandbox"
    assert payload["decision"]["status"] == "selector_behavior_sandbox_target_improved"
    assert payload["decision"]["status"] in payload["possible_statuses"]
    assert payload["decision"]["promote"] is False
    assert payload["decision"]["make_default"] is False
    assert payload["decision"]["train_anything"] is False
    assert "# KRK Selector Behavior Sandbox v0" in markdown
    json.dumps(payload)


def test_selector_behavior_sandbox_default_off_equivalence_and_no_hidden_paths():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["default_off_equivalence_passed"] is True
    assert summary["flag_off_behavior_metadata_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["runtime_dtm_or_tablebase"] is False
    assert summary["topology_mutation"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_provider_suppression"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["hidden_python_controller"] is False


def test_selector_behavior_sandbox_preserve_and_abstain_are_noop():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["preserve_noop_count"] == summary["recommendation_counts_by_class"][
        "preserve_selected_owner"
    ]
    assert summary["abstain_noop_count"] == summary["recommendation_counts_by_class"][
        "abstain_context_only"
    ]
    for row in payload["rows"]:
        if row["recommendation"] in {"preserve_selected_owner", "abstain_context_only"}:
            assert row["behavior_action"] == "no_op"
            assert row["selected_move_delta"] is False
            assert row["selected_provider_delta"] is False


def test_selector_behavior_sandbox_switches_only_on_prefer_visible_alternative():
    payload = _read_json(ARTIFACT)
    summary = payload["summary"]

    assert summary["enabled_switch_count"] == 2
    assert summary["bad_switch_count"] == 0
    assert summary["selected_move_delta_count"] == summary["enabled_switch_count"]
    assert summary["selected_provider_delta_count"] == summary["enabled_switch_count"]
    assert summary["target_improvement_count"] == summary["enabled_switch_count"]
    assert summary["safe_regression_count"] == 0
    for row in payload["rows"]:
        switched = row["behavior_action"] == "switch_to_visible_alternative"
        if switched:
            assert row["recommendation"] == "prefer_visible_alternative"
            assert row["selected_owner_label"] == "selected_owner_failed"
            assert row["target_improved"] is True
            assert row["safe_regression"] is False
            behavior = row["enabled_decision"]["behavior_sandbox_decision"]
            assert behavior["replacement_provider"]
            assert behavior["replacement_move"]
            assert behavior["direct_request"] is False
            assert behavior["score_delta"] == 0.0
            assert behavior["runtime_dtm_or_tablebase"] is False
            assert behavior["gameplay_topology_mutation"] is False
            assert behavior["new_candidate_generation"] is False
            assert behavior["hidden_routing"] is False


def test_selector_behavior_sandbox_alternatives_are_already_visible():
    payload = _read_json(ARTIFACT)

    for row in payload["rows"]:
        if row["behavior_action"] != "switch_to_visible_alternative":
            continue
        behavior = row["enabled_decision"]["behavior_sandbox_decision"]
        rec = row["enabled_decision"]["selector_recommendation"]
        pairs = {
            (item["provider_id"], item["move_id"])
            for item in rec["visible_alternatives_considered"]
        }
        assert (behavior["replacement_provider"], behavior["replacement_move"]) in pairs
        assert behavior["why_selected_alternative"] == (
            "first_current_suggestion_matching_runtime_visible_alternative"
        )
        assert behavior["source_terms"]
        assert behavior["explanation_terms"]


def test_selector_behavior_sandbox_runner_detects_failed_equivalence_with_fake_runner():
    runner = _load_module()
    manifest = {
        "cases": [
            {
                "case_id": "case.1",
                "row_id": "case.1",
                "fen": "8/8/8/8/8/8/8/K6k w - - 0 1",
                "source_stage": "stage5",
                "active_landmark_label": "wrong_tempo_control",
                "selected_owner_label": "selected_owner_failed",
                "selected_provider_label": "krk.stage0_basin",
            }
        ]
    }

    def fake_decision(case: dict, enabled: bool) -> dict:
        return {
            "move": "a1a2",
            "selected_provider": case["selected_provider_label"],
            "confidence": 1.0,
            "selector_recommendation_present": enabled,
            "selector_recommendation": {},
            "behavior_sandbox_decision_present": not enabled,
            "behavior_sandbox_decision": {"action": "no_op"} if not enabled else {},
            "selected_by_selector_behavior_sandbox": False,
        }

    payload = runner.build_payload(decision_runner=fake_decision, manifest=manifest)

    assert payload["summary"]["default_off_equivalence_passed"] is False
    assert payload["decision"]["status"] == "selector_behavior_sandbox_failed_equivalence"


def test_selector_behavior_sandbox_runtime_flag_switches_reviewed_row_only_when_enabled():
    runner = _load_module()
    manifest = runner.build_manifest()
    case = next(
        item
        for item in manifest["cases"]
        if item["row_id"] == "stage4_joined_trace_ownership_1"
    )

    default_off = runner._run_decision(case, False)
    enabled = runner._run_decision(case, True)
    behavior = enabled["behavior_sandbox_decision"]

    assert default_off["behavior_sandbox_decision_present"] is False
    assert enabled["behavior_sandbox_decision_present"] is True
    assert default_off["move"] == "d6c7"
    assert enabled["move"] == "d6d5"
    assert default_off["selected_provider"] == "krk.stage0_basin"
    assert enabled["selected_provider"] == "krk.edge_trap_close"
    assert default_off["confidence"] == enabled["confidence"]
    assert enabled["selector_recommendation"]["recommendation"] == "prefer_visible_alternative"
    assert behavior["action"] == "switch_to_visible_alternative"
    assert behavior["replacement_provider"] == "krk.edge_trap_close"
    assert behavior["replacement_move"] == "d6d5"
    assert behavior["direct_request"] is False
    assert behavior["score_delta"] == 0.0
