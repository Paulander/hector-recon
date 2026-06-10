#!/usr/bin/env python3
"""Tests for selector_behavior continuation regression root-cause report."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_behavior_continuation_regression_root_cause_v0.json"
)
MARKDOWN = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_behavior_continuation_regression_root_cause_v0.md"
)


def _read_json(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _load_module():
    path = ROOT / "scripts/diagnose_krk_selector_behavior_continuation_regression_v0.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_selector_behavior_continuation_report_parses_and_keeps_quarantine():
    payload = _read_json(REPORT)

    assert payload["schema_version"] == (
        "krk_selector_behavior_continuation_regression_root_cause.v0"
    )
    assert payload["causal_status"] == "diagnostic_only_no_production_behavior_change"
    assert payload["quarantine_status"] == (
        "selector_behavior_quarantined_due_to_safe_regression"
    )
    assert payload["production_runtime_behavior_changed"] is False
    assert payload["selector_unquarantined"] is False
    assert payload["production_fix_implemented"] is False
    assert payload["expected_outputs_weakened"] is False
    assert payload["protected_regression_tests_weakened"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False


def test_selector_behavior_continuation_minimal_reproduction_and_results():
    payload = _read_json(REPORT)
    repro = payload["minimal_reproduction"]
    observed = payload["observed_vs_expected"]

    assert repro["row_id"] == "joined_trace_ownership_4"
    assert repro["state_id"] == "state.2c1d6da27ea1"
    assert repro["fen"] == "5k2/R7/8/8/8/8/4K3/8 w - - 2 2"
    assert repro["active_landmark_label"] == "fence_established"
    assert repro["rng_seed"] == 40
    assert repro["black_policy"] == "adversarial"
    assert repro["max_plies"] == 40
    assert repro["early_stop_stable_suggestions"] == 2

    assert observed["control_result"] == {
        "result": "mate",
        "plies": 17,
        "engine_decision_count": 9,
    }
    assert observed["selector_observability_only_result"] == {
        "result": "mate",
        "plies": 17,
        "engine_decision_count": 9,
    }
    assert observed["selector_behavior_enabled_result"] == {
        "result": "max_plies",
        "plies": 40,
        "engine_decision_count": 20,
    }
    assert observed["selector_behavior_enabled_no_cache_result"] == {
        "result": "max_plies",
        "plies": 40,
        "engine_decision_count": 20,
    }


def test_selector_behavior_continuation_first_divergence_is_later_switch():
    payload = _read_json(REPORT)
    divergence = payload["first_divergence"]
    control = divergence["control"]
    enabled = divergence["enabled"]

    assert divergence["ply"] == 4
    assert divergence["differing_fields"] == [
        "move",
        "selected_provider",
        "resulting_fen",
    ]
    assert control["move"] == "e8a8"
    assert control["selected_provider"] == "krk.fence_established"
    assert enabled["move"] == "e8b8"
    assert enabled["selected_provider"] == "krk.edge_trap_close"
    assert enabled["behavior_action"] == "switch_to_visible_alternative"
    assert enabled["original_provider"] == "krk.fence_established"
    assert enabled["original_move"] == "e8a8"
    assert enabled["replacement_provider"] == "krk.edge_trap_close"
    assert enabled["replacement_move"] == "e8b8"
    assert enabled["recommendation"] == "prefer_visible_alternative"
    assert "source_stage.stage5" in enabled["recommendation_terms"]
    assert "active_landmark_label.fence_established" in enabled["recommendation_terms"]


def test_selector_behavior_continuation_report_explains_not_first_row_switch():
    payload = _read_json(REPORT)
    behavior_trace = {
        event["ply"]: event
        for event in next(
            item
            for item in payload["variant_traces"]
            if item["variant"] == "selector_behavior_enabled_cached"
        )["white_events"]
    }

    assert behavior_trace[0]["move"] == "a7a8"
    assert behavior_trace[0]["behavior_action"] == "no_op"
    assert behavior_trace[0]["recommendation"] == "preserve_selected_owner"
    assert behavior_trace[2]["move"] == "a8e8"
    assert behavior_trace[2]["behavior_action"] == "no_op"
    assert behavior_trace[2]["recommendation"] == "prefer_visible_alternative"
    assert behavior_trace[4]["behavior_action"] == "switch_to_visible_alternative"
    assert "first behavior switch appears at white ply 4" in (
        payload["root_cause"]["why_not_first_row_switch"]
    )


def test_selector_behavior_continuation_hypotheses_classify_cause_and_non_causes():
    payload = _read_json(REPORT)
    hypotheses = {item["name"]: item for item in payload["hypotheses"]}

    assert hypotheses["h40-specific heuristic interaction"]["assessment"] == (
        "primary_cause"
    )
    assert hypotheses["unsafe fallback behavior"]["assessment"] == (
        "contributing_invariant_gap"
    )
    assert hypotheses["another invariant violation"]["assessment"] == (
        "safe_continuation_preservation_invariant_missing"
    )
    assert hypotheses["cache/reuse contamination"]["assessment"] == "unlikely"
    assert hypotheses["selector arbitration state leaking across rows"]["assessment"] == (
        "unlikely"
    )
    assert hypotheses["candidate ordering instability"]["assessment"] == "unlikely"
    assert hypotheses["continuation-state mutation"]["assessment"] == (
        "against_hidden_mutation_for_move_induced_state_change"
    )


def test_selector_behavior_continuation_fix_plan_is_future_only():
    payload = _read_json(REPORT)
    plan = payload["recommended_fix_plan"]
    required_tests = payload["tests_required_before_unquarantine"]
    risks = payload["risks_of_fixing"]

    assert plan[0] == "Keep selector_behavior quarantined."
    assert any("diagnostic-only shadow veto" in item for item in plan)
    assert any("do not use offline ownership labels" in item for item in plan)
    assert any("before any future unquarantine review" in item for item in plan)
    assert "full repository test suite" in required_tests
    assert "default-off equivalence" in required_tests
    assert any("overfit" in item for item in risks)
    assert payload["production_fix_implemented"] is False


def test_selector_behavior_continuation_markdown_records_root_cause():
    text = MARKDOWN.read_text(encoding="utf-8")

    assert "# KRK Selector Behavior Continuation Regression Root Cause v0" in text
    assert "diagnostic-only" in text
    assert "- ply: `4`" in text
    assert "- control: `e8a8 / krk.fence_established`" in text
    assert "- enabled: `e8b8 / krk.edge_trap_close`" in text
    assert "not by the protected row's first selector decision" in text
    assert "Keep selector_behavior quarantined." in text


def test_selector_behavior_continuation_writer_accepts_fake_traces():
    module = _load_module()
    traces = [
        {
            "variant": "control_default_off",
            "result": "mate",
            "plies": 17,
            "engine_decision_count": 9,
            "white_events": [
                {
                    "ply": 0,
                    "fen": "start",
                    "move": "a7a8",
                    "selected_provider": "krk.stage0_basin",
                    "resulting_fen": "after0",
                },
                {
                    "ply": 4,
                    "fen": "same",
                    "move": "e8a8",
                    "selected_provider": "krk.fence_established",
                    "resulting_fen": "control",
                },
            ],
        },
        {
            "variant": "selector_observability_only",
            "result": "mate",
            "plies": 17,
            "engine_decision_count": 9,
            "white_events": [],
        },
        {
            "variant": "selector_behavior_enabled_cached",
            "result": "max_plies",
            "plies": 40,
            "engine_decision_count": 20,
            "white_events": [
                {
                    "ply": 0,
                    "fen": "start",
                    "move": "a7a8",
                    "selected_provider": "krk.stage0_basin",
                    "resulting_fen": "after0",
                },
                {
                    "ply": 4,
                    "fen": "same",
                    "move": "e8b8",
                    "selected_provider": "krk.edge_trap_close",
                    "resulting_fen": "enabled",
                    "behavior_action": "switch_to_visible_alternative",
                },
            ],
        },
        {
            "variant": "selector_behavior_enabled_no_cache",
            "result": "max_plies",
            "plies": 40,
            "engine_decision_count": 20,
            "white_events": [],
        },
    ]

    payload = module.build_payload(run_live=False, traces=traces)

    assert payload["first_divergence"]["ply"] == 4
    assert payload["first_divergence"]["control"]["move"] == "e8a8"
    assert payload["first_divergence"]["enabled"]["move"] == "e8b8"
    assert payload["observed_vs_expected"]["selector_behavior_enabled_result"] == {
        "result": "max_plies",
        "plies": 40,
        "engine_decision_count": 20,
    }
