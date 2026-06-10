#!/usr/bin/env python3
"""Tests for selector-objective recommendation analysis and next gate."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_recommendation_analysis_v0.json"
)
ANALYSIS_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_recommendation_analysis_v0.md"
)
NEXT_GATE = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_next_gate_v0.json"
)
NEXT_GATE_MD = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_next_gate_v0.md"
)


def _load_module():
    path = ROOT / "scripts/analyze_krk_selector_objective_recommendations_v0.py"
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


def test_recommendation_analysis_parses_artifacts_and_blocks_runtime_review_packet():
    payload = _read_json(ANALYSIS)
    summary = payload["summary"]

    assert payload["schema_version"] == "krk_selector_objective_recommendation_analysis.v0"
    assert payload["causal_status"] == "non_causal_recommendation_analysis"
    assert payload["decision"]["status"] == "selector_recommendations_need_more_observation_data"
    assert payload["decision"]["future_behavior_changing_selector_review_packet_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_runtime_ready"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert summary["observed_row_count"] == 8
    assert summary["recommendation_count_by_class"] == {
        "abstain_context_only": 0,
        "prefer_visible_alternative": 3,
        "preserve_selected_owner": 5,
    }
    assert summary["rows_with_visible_alternatives"] == 8
    assert summary["offline_label_mismatch_count"] == 1
    assert summary["preserve_on_selected_owner_failure_count"] == 1
    assert summary["unsafe_if_made_causal_count"] == 1
    assert summary["abstain_recommendation_count"] == 0
    assert summary["benchmark_best_model"] == "combined_simple_rule"


def test_recommendation_analysis_preserves_non_causal_boundaries():
    payload = _read_json(ANALYSIS)
    summary = payload["summary"]

    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_provider_suppression"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert summary["no_runtime_behavior_changes"] is True
    assert summary["runtime_behavior_changed"] is False
    assert summary["runtime_dtm_or_tablebase_use"] is False
    assert summary["gameplay_topology_mutation"] is False


def test_recommendation_analysis_excludes_stage7_training_and_capacity_ownership():
    payload = _read_json(ANALYSIS)
    summary = payload["summary"]

    assert summary["stage7_remains_held_out"] is True
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["capacity_label_used_as_ownership_label_count"] == 0
    assert payload["capacity_label_used_as_ownership_label_rows"] == []
    for row in payload["rows"]:
        assert row["capacity_label_used_as_ownership_label"] is False
        assert row["seed_manifest_capacity_label_used_as_ownership_label"] is False
        assert row["seed_manifest_runtime_usable"] is False
        assert row["seed_manifest_training_usable"] is False
        assert row["seed_probe_runtime_feature_eligible"] is False


def test_next_gate_recommends_bounded_observation_not_behavior_change():
    payload = _read_json(NEXT_GATE)
    findings = payload["gate_findings"]
    next_step = payload["next_bounded_evidence_recommendation"]

    assert payload["schema_version"] == "krk_selector_objective_next_gate.v0"
    assert payload["decision"]["status"] == "selector_recommendations_need_more_observation_data"
    assert payload["decision"]["future_behavior_changing_selector_review_packet_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_runtime_ready"] is False
    assert findings["abstain_recommendation_count"] == 0
    assert findings["preserve_on_selected_owner_failure_count"] == 1
    assert findings["unsafe_if_made_causal_count"] == 1
    assert findings["rows_without_visible_alternatives"] == 0
    assert findings["capacity_label_used_as_ownership_label_count"] == 0
    assert findings["stage7_remains_held_out"] is True
    assert findings["no_runtime_behavior_changes"] is True
    assert next_step["execute_without_separate_approval"] is False
    assert "behavior_changing_selector_implementation" in next_step["forbidden_actions"]
    assert "treating_capacity_labels_as_ownership_labels" in next_step["forbidden_actions"]


def test_recommendation_analysis_writer_rebuilds_parseable_artifacts():
    module = _load_module()
    analysis = module.build_analysis()
    gate = module.build_next_gate(analysis)

    assert analysis["decision"]["status"] == "selector_recommendations_need_more_observation_data"
    assert gate["decision"]["status"] == analysis["decision"]["status"]
    assert json.loads(json.dumps(analysis))["schema_version"] == (
        "krk_selector_objective_recommendation_analysis.v0"
    )
    assert json.loads(json.dumps(gate))["schema_version"] == (
        "krk_selector_objective_next_gate.v0"
    )


def test_recommendation_analysis_markdown_artifacts_exist():
    analysis_md = ANALYSIS_MD.read_text(encoding="utf-8")
    gate_md = NEXT_GATE_MD.read_text(encoding="utf-8")

    assert "# KRK Selector Objective Recommendation Analysis v0" in analysis_md
    assert "selector_recommendations_need_more_observation_data" in analysis_md
    assert "# KRK Selector Objective Next Gate v0" in gate_md
    assert "selector_objective_recommendation_observation_expansion_v0" in gate_md
