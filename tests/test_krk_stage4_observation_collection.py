#!/usr/bin/env python3
"""Tests for Stage 4 observation-only joined trace/ownership collection."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_collection = _load_module(
    "run_krk_stage4_joined_trace_ownership_collection_v0",
    "scripts/run_krk_stage4_joined_trace_ownership_collection_v0.py",
)
_manifest = _load_module(
    "build_krk_selector_objective_seed_manifest_v2",
    "scripts/build_krk_selector_objective_seed_manifest_v2.py",
)
_probe = _load_module(
    "probe_krk_selector_objective_seed_manifest_v2",
    "scripts/probe_krk_selector_objective_seed_manifest_v2.py",
)
_benchmark = _load_module(
    "benchmark_krk_selector_objective_v2",
    "scripts/benchmark_krk_selector_objective_v2.py",
)
_benchmark_review = _load_module(
    "write_krk_selector_objective_benchmark_review_packet_v2",
    "scripts/write_krk_selector_objective_benchmark_review_packet_v2.py",
)
_independent_validation = _load_module(
    "run_krk_selector_objective_independent_validation_v0",
    "scripts/run_krk_selector_objective_independent_validation_v0.py",
)
_independent_blocker = _load_module(
    "write_krk_selector_objective_independent_validation_blocker_v0",
    "scripts/write_krk_selector_objective_independent_validation_blocker_v0.py",
)
_stage4_failure_discovery = _load_module(
    "summarize_krk_stage4_failure_discovery_v0",
    "scripts/summarize_krk_stage4_failure_discovery_v0.py",
)
_stage4_sequence_review = _load_module(
    "review_krk_stage4_caveat_sequence_v0",
    "scripts/review_krk_stage4_caveat_sequence_v0.py",
)
_stage4_sequence_candidates = _load_module(
    "review_krk_stage4_sequence_candidates_v0",
    "scripts/review_krk_stage4_sequence_candidates_v0.py",
)
_stage4_first_move_features = _load_module(
    "review_krk_stage4_first_move_features_v0",
    "scripts/review_krk_stage4_first_move_features_v0.py",
)
_stage4_stratified_contrast = _load_module(
    "run_krk_stage4_stratified_contrast_validation_v0",
    "scripts/run_krk_stage4_stratified_contrast_validation_v0.py",
)


def _read_report(path: str) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_stage4_collection_report_is_observation_only_and_valid():
    payload = _read_report(
        "reports/strategy_arbitration/krk_stage4_joined_trace_ownership_collection_v0.json"
    )

    assert payload["schema_version"] == "krk_stage4_joined_trace_ownership_collection.v0"
    assert payload["decision"]["status"] == "stage4_joined_trace_ownership_collection_complete"
    assert payload["decision"]["collection_valid"] is True
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    summary = payload["summary"]
    assert summary["stage4_row_count"] == 6
    assert summary["stage7_training_row_count"] == 0
    assert summary["selector_training_row_count"] == 0
    assert summary["default_off_equivalence_passed"] is True
    assert summary["selected_move_delta_count"] == 0
    assert summary["selected_provider_delta_count"] == 0
    assert summary["score_delta_count"] == 0
    assert summary["routing_delta_count"] == 0


def test_stage4_collection_fixture_preserves_boundaries():
    packet = {
        "approved_if_later_explicitly_authorized": {
            "max_rows": 2,
            "protected_stages": ["stage4"],
            "excluded_stages": ["stage5", "stage6", "stage7", "stage8"],
        },
        "review_rows": [
            {
                "state_id": "state.stage4",
                "source_stage": "stage4",
                "selected_provider": "krk.stage0_basin",
                "target_label": "selected_owner_failed",
            },
            {
                "state_id": "state.stage7",
                "source_stage": "stage7",
                "selected_provider": "krk.box_shrink",
                "target_label": "selected_owner_failed",
            },
        ],
    }
    context = {
        "rows": [
            {
                "state_id": "state.stage4",
                "frame_id": "cp.krk.state.stage4",
                "fen": "8/k7/3K4/8/8/1R6/8/8 w - - 2 2",
                "active_landmark_label": "wrong_tempo_control",
            },
            {
                "state_id": "state.stage7",
                "frame_id": "cp.krk.state.stage7",
                "fen": "8/k7/3K4/8/8/1R6/8/8 w - - 2 2",
                "active_landmark_label": "box_shrink",
            },
        ]
    }

    def fake_runner(case, enabled):
        if not enabled:
            return {
                "move": "d6c7",
                "selected_provider": "krk.stage0_basin",
                "confidence": 1.0,
                "observation": {},
            }
        return {
            "move": "d6c7",
            "selected_provider": "krk.stage0_basin",
            "confidence": 1.0,
            "observation": {
                "frames": [
                    {
                        "candidate_source": "validated_provider_pack",
                        "capacity_evidence_kind": "positive_capacity",
                        "causal_status": "observation_only",
                        "direct_request": False,
                        "score_delta": 0.0,
                        "protected_status": "protected_control",
                    }
                ]
            },
        }

    payload = _collection.build_payload(
        packet=packet,
        context=context,
        decision_runner=fake_runner,
    )

    assert payload["summary"]["attempted_row_count"] == 1
    assert payload["summary"]["stage4_row_count"] == 1
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["switch_contrast_with_positive_capacity_count"] == 1
    assert payload["decision"]["collection_valid"] is True
    assert payload["decision"]["selector_allowed"] is False


def test_selector_seed_manifest_v2_adds_stage4_without_training_rows():
    payload = _read_report("reports/strategy_arbitration/krk_selector_objective_seed_manifest_v2.json")

    assert payload["schema_version"] == "krk_selector_objective_seed_manifest.v2"
    assert payload["decision"]["status"] == "selector_objective_seed_manifest_v2_ready_non_causal"
    assert payload["summary"]["added_stage4_seed_row_count"] == 6
    assert payload["summary"]["source_stage_counts"]["stage4"] == 6
    assert payload["summary"]["candidate_switch_contrast_seed_count"] >= 4
    assert payload["summary"]["safe_preservation_contrast_seed_count"] >= 4
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_selector_seed_manifest_v2_fixture_counts_switch_and_preserve():
    seed_v1 = {
        "seed_rows": [
            {
                "state_id": "safe",
                "source_stage": "stage5",
                "selected_provider": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_converted",
                "positive_trace_provider_candidate_count": 1,
                "objective_channel": "safe_preservation_contrast_seed",
            }
        ]
    }
    collection = {
        "decision": {"collection_valid": True},
        "rows": [
            {
                "state_id": "switch",
                "source_stage": "stage4",
                "selected_provider_label": "krk.stage0_basin",
                "selected_owner_label": "selected_owner_failed",
                "enabled_observation_frame_count": 3,
                "positive_capacity_frame_count": 1,
                "recovery_class": "stage4_selected_failure_with_visible_positive_capacity",
                "joined_trace_ownership_row": True,
            }
        ],
    }

    payload = _manifest.build_payload(seed_v1=seed_v1, stage4_collection=collection)

    assert payload["summary"]["added_stage4_seed_row_count"] == 1
    assert payload["summary"]["candidate_switch_contrast_seed_count"] == 1
    assert payload["summary"]["safe_preservation_contrast_seed_count"] == 1
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0


def test_selector_seed_probe_v2_ready_but_non_causal():
    payload = _read_report("reports/strategy_arbitration/krk_selector_objective_seed_probe_v2.json")

    assert payload["schema_version"] == "krk_selector_objective_seed_probe.v2"
    assert (
        payload["decision"]["status"]
        == "selector_objective_seed_probe_v2_ready_for_non_causal_benchmark"
    )
    assert payload["summary"]["has_switch_and_preserve_seeds"] is True
    assert payload["summary"]["benchmark_underpowered"] is False
    assert payload["summary"]["runtime_feature_eligible_prediction_count"] == 0
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["interpretation"]["semantics_confirmed"] is True
    assert payload["interpretation"]["selector_training_supported"] is False
    assert payload["interpretation"]["runtime_selector_supported"] is False
    assert payload["decision"]["selector_allowed"] is False


def test_selector_objective_benchmark_v2_is_non_causal_review_gate():
    payload = _read_report("reports/strategy_arbitration/krk_selector_objective_benchmark_v2.json")

    assert payload["schema_version"] == "krk_selector_objective_benchmark.v2"
    assert payload["causal_status"] == "non_causal_selector_objective_benchmark"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["summary"]["context_row_count"] >= payload["summary"]["seed_row_count"]
    assert payload["interpretation"]["selector_training_supported"] is False
    assert payload["interpretation"]["runtime_selector_supported"] is False
    assert payload["interpretation"]["independent_validation_required_before_runtime"] is True
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_selector_objective_benchmark_fixture_uses_visible_context_without_labels():
    manifest = {
        "summary": {"selector_training_row_count": 0, "stage7_training_row_count": 0},
        "seed_rows": [
            {
                "state_id": "switch",
                "source_stage": "stage6",
                "selected_provider": "krk.stage0_basin",
                "positive_trace_provider_candidate_count": 10,
                "objective_channel": "candidate_switch_contrast_seed",
            },
            {
                "state_id": "preserve",
                "source_stage": "stage6",
                "selected_provider": "krk.stage0_basin",
                "positive_trace_provider_candidate_count": 10,
                "objective_channel": "safe_preservation_contrast_seed",
            },
            {
                "state_id": "abstain",
                "source_stage": "stage4",
                "selected_provider": "krk.stage0_basin",
                "positive_trace_provider_candidate_count": 0,
                "objective_channel": "failure_context_without_candidate_seed",
            },
        ],
    }
    context = {
        "rows": [
            {
                "state_id": "switch",
                "active_landmark_label": "drive_to_edge",
                "context_terms": [
                    "edge_bucket:edge",
                    "box_area_relevance:low",
                    "support_bucket:far",
                ],
                "selected_move_context": {"selected_piece": "rook"},
            },
            {
                "state_id": "preserve",
                "active_landmark_label": "drive_to_edge",
                "context_terms": [
                    "edge_bucket:edge",
                    "box_area_relevance:low",
                    "support_bucket:close",
                ],
                "selected_move_context": {"selected_piece": "rook"},
            },
            {
                "state_id": "abstain",
                "active_landmark_label": "wrong_tempo_control",
                "context_terms": [
                    "edge_bucket:edge",
                    "box_area_relevance:low",
                    "support_bucket:close",
                ],
                "selected_move_context": {"selected_piece": "rook"},
            },
        ]
    }
    payload = _benchmark.build_payload(
        manifest=manifest,
        seed_probe={"decision": {"status": "fixture"}},
        ownership_context=context,
    )

    heuristic = payload["results"]["visible_failure_risk_heuristic_v2"]
    assert heuristic["runtime_feature_eligible"] is True
    assert heuristic["accuracy"] == 1.0
    assert payload["runtime_selector_implemented"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_selector_objective_benchmark_review_packet_blocks_runtime():
    payload = _read_report(
        "reports/strategy_arbitration/krk_selector_objective_benchmark_review_packet_v2.json"
    )

    assert payload["schema_version"] == "krk_selector_objective_benchmark_review_packet.v2"
    assert (
        payload["decision"]["status"]
        == "selector_objective_benchmark_review_ready_for_independent_validation"
    )
    assert payload["decision"]["runtime_review_ready"] is False
    assert payload["decision"]["independent_validation_review_ready"] is True
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["review_observations"]["runtime_selector_supported"] is False
    assert "runtime_selector" in payload["explicitly_forbidden"]
    assert "stage7_training_or_promotion" in payload["explicitly_forbidden"]


def test_selector_objective_benchmark_review_fixture_never_authorizes_runtime():
    benchmark = {
        "decision": {"status": "selector_objective_benchmark_v2_runtime_feature_review_ready"},
        "summary": {
            "best_runtime_model": "probe",
            "runtime_threshold_passing_model_count": 1,
        },
        "results": {
            "probe": {
                "model_kind": "fixture",
                "accuracy": 1.0,
                "switch_precision": 1.0,
                "switch_recall": 1.0,
                "preserve_recall": 1.0,
                "abstain_recall": 1.0,
                "runtime_feature_eligible": True,
            }
        },
    }

    payload = _benchmark_review.build_payload(benchmark=benchmark)

    assert payload["decision"]["independent_validation_review_ready"] is True
    assert payload["decision"]["runtime_review_ready"] is False
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_selector_objective_independent_validation_artifacts_are_non_causal():
    manifest = _read_report(
        "reports/strategy_arbitration/krk_selector_objective_independent_validation_manifest_v0.json"
    )
    labels = _read_report(
        "reports/strategy_arbitration/krk_selector_objective_independent_validation_labels_v0.json"
    )
    validation = _read_report(
        "reports/strategy_arbitration/krk_selector_objective_independent_validation_v0.json"
    )
    blocker = _read_report(
        "reports/strategy_arbitration/krk_selector_objective_independent_validation_blocker_v0.json"
    )

    assert manifest["schema_version"] == "krk_selector_objective_independent_validation_manifest.v0"
    assert labels["schema_version"] == "krk_selector_objective_independent_validation_labels.v0"
    assert validation["schema_version"] == "krk_selector_objective_independent_validation.v0"
    assert blocker["schema_version"] == "krk_selector_objective_independent_validation_blocker.v0"
    for payload in (manifest, labels, validation, blocker):
        assert payload["runtime_behavior_changed"] is False
        assert payload["runtime_defaults_changed"] is False
        assert payload["runtime_selector_implemented"] is False
        assert payload["runtime_score_changes"] is False
        assert payload["runtime_direct_routing"] is False
        assert payload["runtime_dtm_or_tablebase_lookup"] is False
        assert payload["gameplay_topology_mutation"] is False
        assert payload["stage7_promotion_allowed"] is False
        assert payload["stage8_training_allowed"] is False
    assert manifest["selection_policy"]["stage7_training_rows"] == 0
    assert labels["summary"]["selector_training_row_count"] == 0
    assert labels["summary"]["stage7_training_row_count"] == 0
    assert validation["summary"]["selector_training_row_count"] == 0
    assert validation["summary"]["stage7_training_row_count"] == 0
    assert blocker["decision"]["selector_allowed"] is False
    assert blocker["decision"]["runtime_changes_allowed"] is False


def test_selector_objective_independent_blocker_fixture_detects_missing_switch():
    validation = {
        "summary": {
            "target_counts": {"preserve": 8},
            "prediction_counts": {"preserve": 8},
            "accuracy": 1.0,
            "switch_recall": 0.0,
            "preserve_recall": 1.0,
            "stage7_training_row_count": 0,
            "selector_training_row_count": 0,
        },
        "decision": {"status": "selector_objective_independent_validation_underpowered"},
    }
    labels = {"summary": {"label_count": 8}}

    payload = _independent_blocker.build_payload(validation=validation, labels=labels)

    assert payload["blocker"]["blocker_class"] == "independent_switch_contrast_absent"
    assert (
        payload["decision"]["status"]
        == "selector_objective_runtime_blocked_pending_independent_switch_contrasts"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_selector_objective_independent_validation_common_flags():
    payload = {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }

    _independent_validation.validate_common(payload)


def test_stage4_failure_discovery_collapses_to_seed_state():
    payload = _read_report("reports/krk_stage4_failure_discovery_v0.json")

    assert payload["schema_version"] == "krk_stage4_failure_discovery.v0"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["failure_packet_count"] == 32
    assert payload["summary"]["unique_failure_state_move_count"] == 1
    assert payload["summary"]["all_unique_failures_already_in_selector_seed"] is True
    assert payload["interpretation"]["blind_label_farming_recommended"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_stage4_failure_discovery_fixture_identifies_seed_overlap():
    stage4_eval = {
        "total": 2,
        "conversion_failure_count": 2,
        "handoff_packets": [
            {
                "phase": "playout_summary",
                "observed_outcome": "max_plies",
                "evidence_terms": {
                    "fen": "1R6/1K6/8/k7/8/8/8/8 w - - 0 1",
                    "move": "b8h8",
                    "playout_result": "max_plies",
                },
            },
            {
                "phase": "playout_summary",
                "observed_outcome": "max_plies",
                "evidence_terms": {
                    "fen": "1R6/1K6/8/k7/8/8/8/8 w - - 0 1",
                    "move": "b8h8",
                    "playout_result": "max_plies",
                },
            },
        ],
    }
    state_id = _stage4_failure_discovery._state_id_from_fen(
        "1R6/1K6/8/k7/8/8/8/8 w - - 0 1"
    )
    payload = _stage4_failure_discovery.build_payload(
        stage4_eval=stage4_eval,
        seed={"seed_rows": [{"state_id": state_id}]},
        independent_validation={"summary": {"target_counts": {"preserve": 1}}},
    )

    assert payload["summary"]["failure_packet_count"] == 2
    assert payload["summary"]["unique_failure_state_move_count"] == 1
    assert payload["summary"]["all_unique_failures_already_in_selector_seed"] is True
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_stage4_caveat_sequence_review_is_non_causal():
    payload = _read_report("reports/krk_stage4_caveat_sequence_review_v0.json")

    assert payload["schema_version"] == "krk_stage4_caveat_sequence_review.v0"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["single_unique_failure"] is True
    assert payload["summary"]["base_control_reproduces_failure_count"] is True
    assert payload["diagnosis"]["primary"] == "stage4_sequence_followup_gap_single_state"
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_stage4_caveat_sequence_review_fixture_classifies_sequence_gap():
    stage4_eval = {
        "handoff_packets": [
            {
                "phase": "playout_summary",
                "observed_outcome": "max_plies",
                "status": "failed",
                "evidence_terms": {
                    "fen": "1R6/1K6/8/k7/8/8/8/8 w - - 0 1",
                    "move": "b8h8",
                    "playout_result": "max_plies",
                },
            }
        ]
    }
    discovery = {
        "unique_failure_rows": [
            {
                "state_id": "state.44938ccb8ab7",
                "fen": "1R6/1K6/8/k7/8/8/8/8 w - - 0 1",
                "selected_move": "b8h8",
            }
        ]
    }
    payload = _stage4_sequence_review.build_payload(
        stage4_eval=stage4_eval,
        stage4_base=stage4_eval,
        discovery=discovery,
    )

    assert payload["summary"]["single_unique_failure"] is True
    assert payload["summary"]["base_control_reproduces_failure_count"] is True
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_stage4_sequence_candidate_review_identifies_first_move_ranking_gap():
    payload = _read_report("reports/krk_stage4_sequence_candidate_review_v0.json")

    assert payload["schema_version"] == "krk_stage4_sequence_candidate_review.v0"
    assert payload["causal_status"] == "non_causal_forced_first_move_sequence_review"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["legal_first_move_count"] == 12
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["classification"]["primary"] == "stage4_first_move_ranking_gap"
    assert payload["classification"]["selected_first_move_result"] == "max_plies"
    assert payload["classification"]["converting_first_move_count"] >= 1
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["runtime_changes_allowed"] is False


def test_stage4_sequence_candidate_review_fixture_classifies_ranking_gap():
    rows = [
        {"first_move": "b8h8", "result": "max_plies", "total_plies_including_forced_first_move": 40},
        {"first_move": "b8e8", "result": "mate", "total_plies_including_forced_first_move": 25},
    ]

    classification = _stage4_sequence_candidates.classify_candidate_results(rows)

    assert classification["primary"] == "stage4_first_move_ranking_gap"
    assert classification["selected_first_move_result"] == "max_plies"
    assert classification["converting_first_moves"] == ["b8e8"]
    assert classification["recommended_next_step"] == "non_causal_stage4_first_move_feature_review"


def test_stage4_first_move_feature_review_is_single_state_non_causal():
    payload = _read_report("reports/krk_stage4_first_move_feature_review_v0.json")

    assert payload["schema_version"] == "krk_stage4_first_move_feature_review.v0"
    assert payload["causal_status"] == "non_causal_single_state_feature_review"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["row_count"] == 12
    assert payload["summary"]["single_state_only"] is True
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert payload["interpretation"]["runtime_ready"] is False
    assert "rook_mid_rank8_cut_candidate" in payload["interpretation"]["candidate_positive_terms"]
    assert "rook_far_rank8_drift_candidate" in payload["interpretation"]["candidate_failure_terms"]
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False


def test_stage4_first_move_feature_review_fixture_keeps_single_state_boundary():
    candidate_review = {
        "target": {
            "state_id": "state.44938ccb8ab7",
            "fen": "1R6/1K6/8/k7/8/8/8/8 w - - 0 1",
            "selected_move": "b8h8",
            "label": "edge_trap_wrong_tempo",
        },
        "candidate_results": [
            {
                "first_move": "b8h8",
                "result": "max_plies",
                "total_plies_including_forced_first_move": 40,
                "first_reply": {"move": "a5a4"},
                "first_successor_skill": "krk.stage0_basin",
            },
            {
                "first_move": "b8e8",
                "result": "mate",
                "total_plies_including_forced_first_move": 25,
                "first_reply": {"move": "a5a4"},
                "first_successor_skill": "krk.stage0_basin",
            },
        ],
    }

    payload = _stage4_first_move_features.build_payload(candidate_review=candidate_review)

    assert payload["summary"]["single_state_only"] is True
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False


def test_stage4_stratified_contrast_validation_supports_ranking_gap_non_causally():
    payload = _read_report("reports/krk_stage4_stratified_contrast_validation_v0.json")

    assert payload["schema_version"] == "krk_stage4_stratified_contrast_validation.v0"
    assert (
        payload["causal_status"]
        == "non_causal_symmetry_stratified_forced_first_move_validation"
    )
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["runtime_score_changes"] is False
    assert payload["runtime_direct_routing"] is False
    assert payload["runtime_dtm_or_tablebase_lookup"] is False
    assert payload["gameplay_topology_mutation"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["variant_count"] == 4
    assert payload["summary"]["candidate_row_count"] == 48
    assert payload["summary"]["gap_variant_count"] == 4
    assert payload["summary"]["selector_training_row_count"] == 0
    assert payload["summary"]["stage7_training_row_count"] == 0
    assert (
        payload["decision"]["status"]
        == "stage4_stratified_contrast_validation_supports_first_move_ranking_gap"
    )
    assert payload["decision"]["runtime_changes_allowed"] is False
    assert payload["decision"]["selector_training_allowed"] is False


def test_stage4_stratified_contrast_transform_helpers_are_involutions():
    move = "b8h8"
    for _, transform in _stage4_stratified_contrast.TRANSFORMS:
        transformed = _stage4_stratified_contrast.transform_move_uci(move, transform)
        restored = _stage4_stratified_contrast.transform_move_uci(transformed, transform)
        assert restored == move
