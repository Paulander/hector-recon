#!/usr/bin/env python3
"""Tests for selector-objective benchmark v0."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "reports/strategy_arbitration/krk_selector_objective_benchmark_v0.json"
DECISION = (
    ROOT
    / "reports/strategy_arbitration/krk_selector_objective_benchmark_decision_v0.json"
)
SEED = ROOT / "reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json"
SEED_PROBE = ROOT / "reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json"


def _load_module():
    path = ROOT / "scripts/benchmark_krk_selector_objective_v0.py"
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


def test_selector_objective_seed_v2_parses_and_preserves_label_semantics():
    seed = _read_json(SEED)
    probe = _read_json(SEED_PROBE)

    assert seed["schema_version"] == "krk_selector_objective_seed_manifest.v2"
    assert seed["summary"]["seed_row_count"] == 21
    assert seed["summary"]["selector_training_row_count"] == 0
    assert seed["summary"]["stage7_training_row_count"] == 0
    assert seed["summary"]["capacity_label_used_as_ownership_label_count"] == 0
    assert seed["summary"]["source_stage_counts"]["stage4"] == 6
    assert seed["summary"]["source_stage_counts"]["stage5"] == 9
    assert seed["summary"]["source_stage_counts"]["stage6"] == 6
    assert all(row["stage7_training_row"] is False for row in seed["seed_rows"])
    assert all(row["usable_for_selector_training"] is False for row in seed["seed_rows"])

    assert probe["schema_version"] == "krk_selector_objective_seed_probe.v2"
    assert probe["summary"]["benchmark_underpowered"] is False
    assert probe["summary"]["target_action_counts"] == {
        "abstain_context_only": 5,
        "prefer_visible_alternative": 5,
        "preserve_selected_owner": 11,
    }
    assert probe["summary"]["runtime_feature_eligible_prediction_count"] == 0


def test_selector_objective_benchmark_v0_reports_required_models_and_metrics():
    payload = _read_json(BENCHMARK)

    assert payload["schema_version"] == "krk_selector_objective_benchmark.v0"
    assert payload["causal_status"] == "non_causal_selector_objective_benchmark"
    assert payload["classes"] == [
        "preserve_selected_owner",
        "prefer_visible_alternative",
        "abstain_context_only",
    ]
    assert payload["summary"]["seed_row_count"] == 21
    assert payload["summary"]["target_action_counts"] == {
        "abstain_context_only": 5,
        "prefer_visible_alternative": 5,
        "preserve_selected_owner": 11,
    }
    assert payload["summary"]["benchmark_underpowered"] is False
    assert payload["summary"]["model_count"] == 8
    assert payload["summary"]["best_model"] == "combined_simple_rule"
    assert payload["summary"]["best_accuracy"] == 0.9523809523809523
    assert payload["summary"]["best_safe_preservation_recall"] == 1.0
    assert payload["summary"]["best_switch_contrast_recall"] == 0.8
    assert payload["summary"]["best_abstain_recall"] == 1.0

    required_models = {
        "majority_baseline",
        "provider_prior",
        "stage_provider_family_prior",
        "trace_context_feature_rule",
        "proposal_count_positive_alternative_rule",
        "combined_simple_rule",
    }
    assert required_models <= set(payload["models"])
    for model in payload["models"].values():
        assert "accuracy" in model
        assert "per_class" in model
        assert "confusion_matrix" in model
        assert "safe_preservation_recall" in model
        assert "switch_contrast_recall" in model
        assert "abstain_recall" in model
        assert model["prediction_uses_offline_only_labels"] is False


def test_selector_objective_benchmark_v0_never_authorizes_runtime_behavior():
    payload = _read_json(BENCHMARK)
    decision = _read_json(DECISION)

    assert payload["decision"]["status"] == "selector_objective_benchmark_promising_non_causal"
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_provider_suppression"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["interpretation"]["runtime_selector_supported"] is False
    assert payload["interpretation"]["runtime_review_packet_is_strongest_allowed_next_step"] is True

    assert decision["schema_version"] == "krk_selector_objective_benchmark_decision.v0"
    assert decision["decision"]["status"] == "selector_objective_benchmark_promising_non_causal"
    assert decision["decision"]["implementation_authorized_by_this_packet"] is False
    assert decision["decision"]["runtime_review_packet_allowed_next"] is True
    assert decision["decision"]["selector_allowed"] is False
    assert decision["decision"]["selector_training_allowed"] is False
    assert decision["decision"]["runtime_changes_allowed"] is False


def test_selector_objective_benchmark_v0_fixture_class_mapping_is_non_causal():
    module = _load_module()
    manifest = {
        "summary": {
            "selector_training_row_count": 0,
            "stage7_training_row_count": 0,
            "runtime_authorization_row_count": 0,
        },
        "seed_rows": [
            {
                "state_id": "safe",
                "source_stage": "stage5",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_converted",
                "objective_channel": "safe_preservation_contrast_seed",
                "positive_trace_provider_candidate_count": 10,
                "stage7_training_row": False,
            },
            {
                "state_id": "switch",
                "source_stage": "stage6",
                "selected_provider": "krk.edge_trap_close",
                "selected_owner_label": "selected_owner_failed",
                "objective_channel": "candidate_switch_contrast_seed",
                "positive_trace_provider_candidate_count": 1,
                "stage7_training_row": False,
            },
            {
                "state_id": "abstain",
                "source_stage": "stage4",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "objective_channel": "failure_context_without_candidate_seed",
                "positive_trace_provider_candidate_count": 0,
                "stage7_training_row": False,
            },
        ],
    }
    payload = module.build_payload(
        manifest=manifest,
        seed_probe={"decision": {"status": "fixture"}},
        ownership_context={"rows": []},
    )

    assert payload["summary"]["target_action_counts"] == {
        "abstain_context_only": 1,
        "prefer_visible_alternative": 1,
        "preserve_selected_owner": 1,
    }
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["decision"]["selector_allowed"] is False
