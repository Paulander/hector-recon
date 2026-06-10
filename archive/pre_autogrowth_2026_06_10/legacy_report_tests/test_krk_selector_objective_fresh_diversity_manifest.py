#!/usr/bin/env python3
"""Tests for the fresh Stage 5/6 selector-objective diversity packet."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_fresh_diversity_manifest_v0.json"
)
REVIEW = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_fresh_diversity_review_packet_v0.json"
)
COLLECTION = (
    ROOT
    / "reports/strategy_arbitration/"
    "krk_selector_objective_fresh_diversity_collection_v0.json"
)


def _load_module():
    path = ROOT / "scripts/write_krk_selector_objective_fresh_diversity_manifest_v0.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_runner_module():
    path = ROOT / "scripts/run_krk_selector_objective_fresh_diversity_collection_v0.py"
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


def test_fresh_diversity_manifest_is_stage5_6_only_and_review_only():
    payload = _read_json(MANIFEST)

    assert payload["schema_version"] == "krk_selector_objective_fresh_diversity_manifest.v0"
    assert payload["causal_status"] == "non_causal_collection_manifest"
    assert payload["decision"]["status"] == (
        "fresh_stage5_stage6_diversity_collection_review_ready"
    )
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["label_run_allowed"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
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
    assert payload["summary"]["stage_counts"] == {"stage5": 4, "stage6": 4}
    assert set(payload["summary"]["stage_counts"]) == {"stage5", "stage6"}
    assert payload["collection_constraints"]["excluded_stages"] == [
        "stage4",
        "stage7",
        "stage8",
    ]
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["summary"]["valid_scope"] is True


def test_fresh_diversity_manifest_preserves_label_semantics_and_duplicate_guards():
    payload = _read_json(MANIFEST)
    rows = payload["candidate_rows"]

    assert payload["summary"]["candidate_row_count"] == 8
    assert payload["summary"]["selected_owner_failed_count"] == 4
    assert payload["summary"]["selected_owner_converted_count"] == 4
    assert payload["summary"]["switch_contrast_count"] == 4
    assert payload["summary"]["safe_preservation_count"] == 4
    assert payload["summary"]["progress_window_failure_contrast_count"] == 2
    assert payload["summary"]["non_stage0_selected_owner_count"] >= 3
    assert payload["summary"]["spent_manifest_duplicate_count"] == 0
    assert payload["summary"]["duplicate_candidate_fen_count"] == 0
    assert payload["summary"]["duplicate_risk_assessment"] == (
        "fresh_against_spent_failure_contrast_manifest_with_known_seed_overlap"
    )

    assert all(row["source_stage"] in {"stage5", "stage6"} for row in rows)
    assert all(row["source_stage"] not in {"stage4", "stage7", "stage8"} for row in rows)
    assert all(row["capacity_label_used_as_ownership_label"] is False for row in rows)
    assert all(row["usable_for_selector_training"] is False for row in rows)
    assert all(row["usable_for_runtime_authorization"] is False for row in rows)
    assert all(row["stage7_training_row"] is False for row in rows)
    assert all(row["collection_run_allowed_by_manifest"] is False for row in rows)
    assert all(
        row["duplicate_risk"]["spent_failure_contrast_manifest_duplicate"] is False
        for row in rows
    )
    assert all(row["why_adds_new_evidence"] for row in rows)

    failed_rows = [row for row in rows if row["selected_owner_label"] == "selected_owner_failed"]
    assert all(row["objective_channel"] == "candidate_switch_contrast_seed" for row in failed_rows)
    assert {
        row["label_source"]
        for row in rows
        if row["source_type"] == "protected_plan_window_frame"
    } == {"protected_plan_window_selected_successor_h40_outcome"}


def test_fresh_diversity_review_packet_repeats_required_counts_without_authorizing_runtime():
    payload = _read_json(REVIEW)

    assert (
        payload["schema_version"]
        == "krk_selector_objective_fresh_diversity_review_packet.v0"
    )
    assert payload["causal_status"] == "non_causal_review_packet"
    assert payload["decision"]["status"] == (
        "fresh_stage5_stage6_diversity_collection_review_ready"
    )
    assert payload["decision"]["collection_run_allowed"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["runtime_ready"] is False
    assert payload["decision"]["selector_ready"] is False
    assert payload["summary"]["candidate_row_count"] == 8
    assert payload["summary"]["stage_counts"] == {"stage5": 4, "stage6": 4}
    assert payload["summary"]["selected_owner_failed_count"] == 4
    assert payload["summary"]["selected_owner_converted_count"] == 4
    assert payload["summary"]["switch_contrast_count"] == 4
    assert payload["summary"]["safe_preservation_count"] == 4
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["review"]["replay_free_recovery_attempted"] is True
    assert payload["review"]["replay_free_recovery_enough"] is False
    assert payload["review"]["capacity_labels_are_not_ownership_labels"] is True
    assert payload["review"]["review_packet_only"] is True
    assert payload["review"]["future_collection_requires_explicit_approval"] is True


def test_fresh_diversity_writer_builds_parseable_artifacts():
    module = _load_module()
    manifest = module.build_manifest()
    review = module.build_review(manifest)

    assert manifest["decision"]["status"] == (
        "fresh_stage5_stage6_diversity_collection_review_ready"
    )
    assert review["decision"]["status"] == (
        "fresh_stage5_stage6_diversity_collection_review_ready"
    )
    json.dumps(manifest)
    json.dumps(review)


def test_fresh_diversity_collection_runner_preserves_observation_only_boundaries():
    runner = _load_runner_module()
    packet = _read_json(REVIEW)

    def fake_decision(case: dict, enabled: bool) -> dict:
        frame = {
            "candidate_source": "stage_conditioned_candidate_generation_refresh",
            "policy": "trace_stage_family_context",
            "direct_request": False,
            "score_delta": 0.0,
            "causal_status": "candidate_generation_only",
            "protected_status": "protected_control",
            "stage": case["source_stage"],
            "provider_family": str(case["selected_provider_label"]).replace("krk.", ""),
            "capacity_evidence_kind": "positive_capacity_alternative",
        }
        return {
            "move": "a1a2",
            "selected_provider": case["selected_provider_label"],
            "confidence": 1.0,
            "observation_present": enabled,
            "observation": {"frames": [frame] if enabled else []},
        }

    payload = runner.build_payload(packet=packet, decision_runner=fake_decision)

    assert payload["schema_version"] == "krk_selector_objective_fresh_diversity_collection.v0"
    assert payload["causal_status"] == "observation_only_collection"
    assert payload["decision"]["status"] == (
        "fresh_stage5_6_selector_objective_collection_complete"
    )
    assert payload["decision"]["collection_valid"] is True
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["stage7_promotion_allowed"] is False
    assert payload["decision"]["stage8_training_allowed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["summary"]["attempted_row_count"] == 8
    assert payload["summary"]["stage_counts"] == {"stage5": 4, "stage6": 4}
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["summary"]["capacity_label_used_as_ownership_label_count"] == 0
    assert payload["summary"]["selected_move_delta_count"] == 0
    assert payload["summary"]["selected_provider_delta_count"] == 0
    assert payload["summary"]["selected_score_delta_count"] == 0
    assert payload["summary"]["score_delta_count"] == 0
    assert payload["summary"]["routing_delta_count"] == 0
    assert payload["summary"]["baseline_refresh_frame_count"] == 0
    assert payload["summary"]["invalid_frame_count"] == 0
    assert all(row["source_stage"] in {"stage5", "stage6"} for row in payload["rows"])
    assert all(row["usable_for_selector_training"] is False for row in payload["rows"])
    assert all(row["usable_for_runtime_authorization"] is False for row in payload["rows"])


def test_fresh_diversity_collection_result_is_valid_and_non_runtime_authorizing():
    payload = _read_json(COLLECTION)

    assert payload["schema_version"] == "krk_selector_objective_fresh_diversity_collection.v0"
    assert payload["causal_status"] == "observation_only_collection"
    assert payload["decision"]["status"] == (
        "fresh_stage5_6_selector_objective_collection_complete"
    )
    assert payload["decision"]["collection_valid"] is True
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
    assert payload["hidden_python_controller"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["attempted_row_count"] == 8
    assert payload["summary"]["collected_row_count"] == 8
    assert payload["summary"]["joined_row_count"] == 8
    assert payload["summary"]["stage_counts"] == {"stage5": 4, "stage6": 4}
    assert payload["summary"]["selected_owner_counts"] == {
        "selected_owner_converted": 4,
        "selected_owner_failed": 4,
    }
    assert payload["summary"]["generated_frame_count"] == 76
    assert payload["summary"]["generated_frame_count_by_stage"] == {
        "stage5": 45,
        "stage6": 31,
    }
    assert payload["summary"]["selected_failure_with_visible_positive_capacity_count"] == 4
    assert payload["summary"]["safe_preservation_with_visible_positive_capacity_count"] == 4
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["runtime_authorization_row_count"] == 0
    assert payload["summary"]["capacity_label_used_as_ownership_label_count"] == 0
    assert payload["summary"]["selected_move_delta_count"] == 0
    assert payload["summary"]["selected_provider_delta_count"] == 0
    assert payload["summary"]["selected_score_delta_count"] == 0
    assert payload["summary"]["score_delta_count"] == 0
    assert payload["summary"]["routing_delta_count"] == 0
    assert payload["summary"]["baseline_refresh_frame_count"] == 0
    assert payload["summary"]["invalid_frame_count"] == 0
    assert payload["summary"]["default_off_equivalence_passed"] is True
    assert all(row["source_stage"] in {"stage5", "stage6"} for row in payload["rows"])
    assert all(row["source_stage"] not in {"stage4", "stage7", "stage8"} for row in payload["rows"])
