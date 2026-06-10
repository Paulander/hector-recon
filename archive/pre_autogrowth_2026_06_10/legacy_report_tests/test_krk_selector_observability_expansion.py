#!/usr/bin/env python3
"""Tests for selector observability expansion artifacts."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_observability_expansion_manifest_v0.json"
)
EXPANDED = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_observability_expanded_recommendations_v0.json"
)
REVIEW = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_observability_readiness_review_v0.json"
)


def _load_module():
    path = ROOT / "scripts/run_krk_selector_observability_expansion_v0.py"
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


def test_selector_observability_expansion_manifest_targets_stage4_5_6_only():
    payload = _read_json(MANIFEST)
    summary = payload["summary"]

    assert payload["schema_version"] == "krk_selector_observability_expansion_manifest.v0"
    assert payload["causal_status"] == "non_causal_observation_manifest"
    assert payload["decision"]["status"] == "selector_observability_expansion_manifest_ready"
    assert payload["decision"]["behavior_changing_selector_allowed"] is False
    assert set(summary["stage_counts"]) == {"stage4", "stage5", "stage6"}
    assert summary["case_count"] == 14
    assert summary["objective_channel_counts"]["failure_context_without_candidate_seed"] == 5
    assert summary["objective_channel_counts"]["candidate_switch_contrast_seed"] == 5
    assert summary["non_stage0_owner_count"] >= 1
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["capacity_label_used_as_ownership_label_count"] == 0
    assert summary["replay_free_recovery_used_first"] is True
    assert all(case["source_stage"] in {"stage4", "stage5", "stage6"} for case in payload["cases"])
    assert all(case["stage7_training_row"] is False for case in payload["cases"])
    assert all(case["selector_training_row"] is False for case in payload["cases"])
    assert all(case["capacity_label_used_as_ownership_label"] is False for case in payload["cases"])


def test_expanded_recommendations_remain_trace_only_and_default_off_equivalent():
    payload = _read_json(EXPANDED)
    summary = payload["summary"]

    assert payload["schema_version"] == "krk_selector_observability_expanded_recommendations.v0"
    assert payload["causal_status"] == "non_causal_expanded_recommendation_observation"
    assert payload["decision"]["behavior_changing_selector_allowed"] is False
    assert summary["attempted_row_count"] == 14
    assert summary["trace_only_recommendation_count"] == 14
    assert summary["default_off_selector_recommendation_count"] == 0
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["selected_score_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0
    assert summary["runtime_behavior_changed"] is False
    assert summary["runtime_dtm_or_tablebase_use"] is False
    assert summary["gameplay_topology_mutation"] is False
    for row in payload["rows"]:
        assert row["flag_off_selector_recommendation_count"] == 0
        assert row["enabled_selector_recommendation_count"] == 1
        assert row["causal_status"] == "recommendation_only"
        assert row["direct_request"] is False
        assert row["score_delta"] == 0.0
        assert row["selected_move_delta"] is False
        assert row["selected_provider_delta"] is False
        assert row["selected_score_delta"] is False
        assert row["routing_delta"] is False


def test_expanded_recommendations_cover_abstain_but_preserve_risk_remains():
    payload = _read_json(EXPANDED)
    summary = payload["summary"]

    assert summary["recommendation_count_by_class"] == {
        "abstain_context_only": 5,
        "prefer_visible_alternative": 4,
        "preserve_selected_owner": 5,
    }
    assert summary["abstain_recommendation_count"] == 5
    assert summary["abstain_weak_evidence_count"] == 5
    assert summary["preserve_on_failure_count"] == 1
    assert summary["switch_on_safe_owner_count"] == 0
    assert summary["offline_label_mismatch_count"] == 1
    assert summary["rows_with_visible_alternatives"] == 9
    assert summary["source_term_coverage"]["unique_explanation_term_count"] > 0


def test_readiness_review_blocks_runtime_packet_on_preserve_failure_risk():
    payload = _read_json(REVIEW)
    summary = payload["summary"]

    assert payload["schema_version"] == "krk_selector_observability_readiness_review.v0"
    assert payload["decision"]["status"] == (
        "selector_observability_blocked_by_preserve_failure_risk"
    )
    assert payload["decision"]["future_behavior_changing_selector_review_packet_allowed"] is False
    assert payload["decision"]["selector_runtime_ready"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert summary["evidence_improved_over_prior"] is True
    assert summary["ready_for_runtime_review_packet"] is False
    assert summary["no_runtime_deltas"] is True
    assert summary["stage7_remains_held_out"] is True
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["capacity_label_used_as_ownership_label_count"] == 0
    assert "preserve_selected_owner still appears on selected-owner failure rows" in (
        payload["missing_or_blocking_evidence"]
    )


def test_selector_observability_expansion_writer_rebuilds_parseable_artifacts():
    module = _load_module()
    manifest = module.build_manifest()
    expanded = module.build_expanded(
        manifest,
        decision_runner=lambda case, enabled: {
            "move": "a1a2",
            "selected_provider": case["selected_provider_label"],
            "confidence": 1.0,
            "selector_recommendation_present": enabled,
            "selector_recommendation": (
                {
                    "recommendation": "abstain_context_only",
                    "decision_reason": "no_positive_trace_provider_candidates",
                    "positive_trace_provider_candidate_count": 0,
                    "visible_alternative_count": 0,
                    "source_terms": [],
                    "explanation_terms": ["selector_model.combined_simple_rule"],
                    "direct_request": False,
                    "causal_status": "recommendation_only",
                    "score_delta": 0.0,
                }
                if enabled
                else {}
            ),
        },
    )
    review = module.build_review(expanded)

    assert manifest["decision"]["status"] == "selector_observability_expansion_manifest_ready"
    assert expanded["summary"]["selected_move_delta_count"] == 0
    assert review["summary"]["stage7_training_row_count"] == 0
    assert json.loads(json.dumps(manifest))["schema_version"] == (
        "krk_selector_observability_expansion_manifest.v0"
    )
    assert json.loads(json.dumps(expanded))["schema_version"] == (
        "krk_selector_observability_expanded_recommendations.v0"
    )
    assert json.loads(json.dumps(review))["schema_version"] == (
        "krk_selector_observability_readiness_review.v0"
    )
