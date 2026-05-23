#!/usr/bin/env python3
"""Tests for non-causal KRK candidate-generation control-plane artifacts."""

import importlib.util
from pathlib import Path


_spec = importlib.util.spec_from_file_location(
    "build_krk_candidate_generation_control_plane_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_candidate_generation_control_plane_v0.py",
)
assert _spec is not None
assert _spec.loader is not None
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

_populate_spec = importlib.util.spec_from_file_location(
    "populate_krk_strategy_sequence_candidate_frames_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "populate_krk_strategy_sequence_candidate_frames_v1.py",
)
assert _populate_spec is not None
assert _populate_spec.loader is not None
_populate = importlib.util.module_from_spec(_populate_spec)
_populate_spec.loader.exec_module(_populate)

_benchmark_spec = importlib.util.spec_from_file_location(
    "benchmark_krk_candidate_frame_sources_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "benchmark_krk_candidate_frame_sources_v1.py",
)
assert _benchmark_spec is not None
assert _benchmark_spec.loader is not None
_benchmark = importlib.util.module_from_spec(_benchmark_spec)
_benchmark_spec.loader.exec_module(_benchmark)

_sandbox_review_spec = importlib.util.spec_from_file_location(
    "write_krk_candidate_generation_sandbox_review_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_candidate_generation_sandbox_review_v0.py",
)
assert _sandbox_review_spec is not None
assert _sandbox_review_spec.loader is not None
_sandbox_review = importlib.util.module_from_spec(_sandbox_review_spec)
_sandbox_review_spec.loader.exec_module(_sandbox_review)

_observation_smoke_spec = importlib.util.spec_from_file_location(
    "run_krk_candidate_generation_observation_sandbox_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_candidate_generation_observation_sandbox_v0.py",
)
assert _observation_smoke_spec is not None
assert _observation_smoke_spec.loader is not None
_observation_smoke = importlib.util.module_from_spec(_observation_smoke_spec)
_observation_smoke_spec.loader.exec_module(_observation_smoke)

_observation_analysis_spec = importlib.util.spec_from_file_location(
    "analyze_krk_candidate_generation_observation_frames_v0",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_krk_candidate_generation_observation_frames_v0.py",
)
assert _observation_analysis_spec is not None
assert _observation_analysis_spec.loader is not None
_observation_analysis = importlib.util.module_from_spec(_observation_analysis_spec)
_observation_analysis_spec.loader.exec_module(_observation_analysis)

_observation_broadened_spec = importlib.util.spec_from_file_location(
    "run_krk_candidate_generation_observation_broadened_sample_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_candidate_generation_observation_broadened_sample_v1.py",
)
assert _observation_broadened_spec is not None
assert _observation_broadened_spec.loader is not None
_observation_broadened = importlib.util.module_from_spec(_observation_broadened_spec)
_observation_broadened_spec.loader.exec_module(_observation_broadened)

_observation_gap_review_spec = importlib.util.spec_from_file_location(
    "analyze_krk_candidate_generation_observation_gap_review_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "analyze_krk_candidate_generation_observation_gap_review_v1.py",
)
assert _observation_gap_review_spec is not None
assert _observation_gap_review_spec.loader is not None
_observation_gap_review = importlib.util.module_from_spec(_observation_gap_review_spec)
_observation_gap_review_spec.loader.exec_module(_observation_gap_review)

_candidate_move_annotation_spec = importlib.util.spec_from_file_location(
    "annotate_krk_candidate_move_capacity_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "annotate_krk_candidate_move_capacity_v1.py",
)
assert _candidate_move_annotation_spec is not None
assert _candidate_move_annotation_spec.loader is not None
_candidate_move_annotation = importlib.util.module_from_spec(_candidate_move_annotation_spec)
_candidate_move_annotation_spec.loader.exec_module(_candidate_move_annotation)

_candidate_move_manifest_spec = importlib.util.spec_from_file_location(
    "build_krk_candidate_move_capacity_label_manifest_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_candidate_move_capacity_label_manifest_v1.py",
)
assert _candidate_move_manifest_spec is not None
assert _candidate_move_manifest_spec.loader is not None
_candidate_move_manifest = importlib.util.module_from_spec(_candidate_move_manifest_spec)
_candidate_move_manifest_spec.loader.exec_module(_candidate_move_manifest)

_candidate_move_label_spec = importlib.util.spec_from_file_location(
    "run_krk_candidate_move_capacity_labels_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_candidate_move_capacity_labels_v1.py",
)
assert _candidate_move_label_spec is not None
assert _candidate_move_label_spec.loader is not None
_candidate_move_label = importlib.util.module_from_spec(_candidate_move_label_spec)
_candidate_move_label_spec.loader.exec_module(_candidate_move_label)

_candidate_move_merge_spec = importlib.util.spec_from_file_location(
    "merge_krk_candidate_move_capacity_annotations_v2",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "merge_krk_candidate_move_capacity_annotations_v2.py",
)
assert _candidate_move_merge_spec is not None
assert _candidate_move_merge_spec.loader is not None
_candidate_move_merge = importlib.util.module_from_spec(_candidate_move_merge_spec)
_candidate_move_merge_spec.loader.exec_module(_candidate_move_merge)

_candidate_label_blocker_spec = importlib.util.spec_from_file_location(
    "review_krk_candidate_generation_label_blockers_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_candidate_generation_label_blockers_v1.py",
)
assert _candidate_label_blocker_spec is not None
assert _candidate_label_blocker_spec.loader is not None
_candidate_label_blocker = importlib.util.module_from_spec(_candidate_label_blocker_spec)
_candidate_label_blocker_spec.loader.exec_module(_candidate_label_blocker)

_candidate_quality_review_spec = importlib.util.spec_from_file_location(
    "write_krk_candidate_proposal_quality_prioritization_review_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_candidate_proposal_quality_prioritization_review_v1.py",
)
assert _candidate_quality_review_spec is not None
assert _candidate_quality_review_spec.loader is not None
_candidate_quality_review = importlib.util.module_from_spec(_candidate_quality_review_spec)
_candidate_quality_review_spec.loader.exec_module(_candidate_quality_review)

_candidate_quality_dataset_spec = importlib.util.spec_from_file_location(
    "build_krk_candidate_proposal_quality_dataset_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_candidate_proposal_quality_dataset_v1.py",
)
assert _candidate_quality_dataset_spec is not None
assert _candidate_quality_dataset_spec.loader is not None
_candidate_quality_dataset = importlib.util.module_from_spec(_candidate_quality_dataset_spec)
_candidate_quality_dataset_spec.loader.exec_module(_candidate_quality_dataset)

_candidate_quality_probe_spec = importlib.util.spec_from_file_location(
    "probe_krk_candidate_proposal_quality_axes_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_candidate_proposal_quality_axes_v1.py",
)
assert _candidate_quality_probe_spec is not None
assert _candidate_quality_probe_spec.loader is not None
_candidate_quality_probe = importlib.util.module_from_spec(_candidate_quality_probe_spec)
_candidate_quality_probe_spec.loader.exec_module(_candidate_quality_probe)

_candidate_quality_decision_spec = importlib.util.spec_from_file_location(
    "write_krk_candidate_proposal_quality_decision_v1",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "write_krk_candidate_proposal_quality_decision_v1.py",
)
assert _candidate_quality_decision_spec is not None
assert _candidate_quality_decision_spec.loader is not None
_candidate_quality_decision = importlib.util.module_from_spec(_candidate_quality_decision_spec)
_candidate_quality_decision_spec.loader.exec_module(_candidate_quality_decision)

_landmark_spec = importlib.util.spec_from_file_location(
    "test_krk_landmark_progress",
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "test_krk_landmark_progress.py",
)
assert _landmark_spec is not None
assert _landmark_spec.loader is not None
_landmark = importlib.util.module_from_spec(_landmark_spec)
_landmark_spec.loader.exec_module(_landmark)


def test_candidate_proposal_coverage_preserves_capacity_label_semantics():
    capacity_rows = [
        {
            "state_id": "state.a",
            "frame_id": "frame.a",
            "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
            "source_stage": "stage5",
            "provider_id": "krk.fence_established",
            "provider_family": "fence_established",
            "capacity_label": "positive_capacity",
            "forced_result": "mate",
            "existing_frame_providers": ["krk.stage0_basin"],
            "stage7_challenge_row": False,
        }
    ]
    ranked_rows = [
        {
            "state_id": "state.a",
            "provider_id": "krk.stage0_basin",
        }
    ]

    rows = _module._coverage_rows(capacity_rows, ranked_rows)

    assert rows[0]["provider_visible_in_current_proposals"] is False
    assert rows[0]["candidate_generation_channel"] == (
        "missing_validated_provider_capacity_candidate"
    )
    assert rows[0]["label_semantics"] == "forced_provider_capacity_label"
    assert rows[0]["usable_for_selector_training"] is False
    assert rows[0]["causal_status"] == "non_causal_capacity_coverage_evidence"


def test_candidate_proposal_coverage_summary_excludes_stage7_training_readiness():
    rows = [
        {
            "capacity_label": "positive_capacity",
            "provider_visible_in_current_proposals": False,
            "provider_family": "fence_established",
            "source_stage": "stage5",
            "stage7_challenge_row": False,
        },
        {
            "capacity_label": "negative_capacity",
            "provider_visible_in_current_proposals": True,
            "provider_family": "edge_trap",
            "source_stage": "stage4",
            "stage7_challenge_row": False,
        },
    ]

    summary = _module._summarize_coverage(rows)

    assert summary["positive_capacity_recall"] == 0.0
    assert summary["missing_positive_capacity_count"] == 1
    assert summary["stage7_row_count"] == 0


def test_strategy_sequence_candidate_frame_schema_is_non_causal():
    review = {
        "decision": {
            "future_runtime_sandbox_requires": [
                "candidate-generation candidate set exists",
            ]
        }
    }

    payload = _module.build_frame_schema_payload(review)

    assert payload["causal_status"] == "non_causal_schema_design"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_defaults_changed"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert "direct_provider_request" in payload["forbidden_causal_uses"]
    assert "capacity_evidence" in payload["required_fields"]


def test_strategy_sequence_capacity_frames_are_generation_not_selection_labels():
    frames = _populate.capacity_candidate_frames(
        [
            {
                "state_id": "state.a",
                "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                "source_stage": "stage5",
                "provider_id": "krk.fence_established",
                "provider_family": "fence_established",
                "capacity_label": "positive_capacity",
                "forced_result": "mate",
                "forced_first_move": "a1a2",
                "stage7_challenge_row": False,
            }
        ]
    )

    assert frames[0]["frame_type"] == "validated_provider_candidate"
    assert frames[0]["label_semantics"] == "capacity_evidence_not_ownership_label"
    assert frames[0]["usable_for_selector_training"] is False
    assert frames[0]["usable_for_candidate_generation_training"] is True
    assert frames[0]["causal_status"] == "non_causal"


def test_strategy_sequence_quality_blocks_stage7_training_rows():
    frames_payload = {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": {
            "readiness_training_stage7_row_count": 1,
        },
        "frames": [
            {
                "label_semantics": "capacity_evidence_not_ownership_label",
                "usable_for_selector_training": False,
                "stage7_challenge_row": True,
                "frame_type": "candidate_move_hypothesis",
                "sequence_evidence": {},
            }
        ],
    }

    quality = _populate.build_quality_payload(frames_payload)

    assert quality["quality_checks"]["stage7_excluded_from_training_readiness"] is False
    assert quality["decision"]["status"] == "frame_quality_blocked"


def test_progress_window_continuation_index_accepts_list_shape():
    indexed = _populate._continuation_index(
        [
            {
                "move": "a1a2",
                "continuation": {
                    "result": "max_plies",
                },
            }
        ]
    )

    assert indexed == {"a1a2": {"result": "max_plies"}}


def test_candidate_frame_source_benchmark_keeps_capacity_and_selection_separate():
    frames = [
        {
            "label_semantics": "capacity_evidence_not_ownership_label",
            "stage7_challenge_row": False,
            "state_id": "state.a",
            "candidate_strategy_family": "fence_established",
            "capacity_evidence": {"capacity_label": "positive_capacity"},
            "usable_for_candidate_generation_training": True,
            "usable_for_selector_training": False,
        },
        {
            "label_semantics": "capacity_evidence_not_ownership_label",
            "stage7_challenge_row": False,
            "state_id": "state.a",
            "candidate_strategy_family": "stage0_basin",
            "capacity_evidence": {"capacity_label": "negative_capacity"},
            "usable_for_candidate_generation_training": False,
            "usable_for_selector_training": False,
        },
    ]

    summary = _benchmark.benchmark_frames(frames)
    readiness = _benchmark.source_readiness(summary)

    assert summary["protected_forced_capacity"]["positive_capacity_ratio"] == 0.5
    assert summary["protected_forced_capacity"]["negative_capacity_ratio"] == 0.5
    assert readiness["protected_forced_capacity"]["selection_signal"] == (
        "blocked_capacity_not_ownership_label"
    )
    assert readiness["protected_forced_capacity"]["usable_next"] == (
        "candidate_generation_benchmark_only"
    )


def test_control_plane_decision_blocks_runtime_when_stage7_training_leaks():
    benchmark = {
        "channel_summaries": {
            "protected_forced_capacity": {
                "candidate_generation_training_row_count": 1,
                "negative_capacity_ratio": 0.0,
                "stage7_training_row_count": 1,
            }
        },
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }

    decision = _benchmark.build_decision_payload(benchmark)

    assert decision["decision"]["status"] == "blocked_stage7_leakage"
    assert decision["decision"]["runtime_sandbox_allowed_by_this_packet"] is False
    assert decision["evidence"]["stage7_training_row_count"] == 1


def test_candidate_generation_sandbox_review_is_observation_only():
    payload = _sandbox_review.build_review_payload()

    assert payload["decision"]["status"] == (
        "candidate_generation_observation_sandbox_review_ready"
    )
    assert payload["decision"]["implementation_authorized_by_this_packet"] is False
    assert payload["decision"]["runtime_sandbox_allowed_by_this_packet"] is False
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["score_changes_allowed"] is False
    assert payload["decision"]["routing_changes_allowed"] is False
    assert payload["runtime_candidate_generator_implemented"] is False
    assert payload["runtime_behavior_changed"] is False
    assert "selecting_a_provider" in payload["explicitly_forbidden"]
    assert "score_delta_zero" in payload["required_candidate_frame_fields"]


def test_candidate_generation_observation_frames_are_non_causal():
    suggestion = {
        "move": "a1a2",
        "score": 7.5,
        "meta": {"curriculum_label": "fence_established", "provider_version": "frozen"},
    }

    observation = _landmark._krk_candidate_generation_observation_for_suggestions(
        [suggestion],
        selected_suggestion=suggestion,
        active_landmark_label="fence_established",
        visible_terms={"fence_exists": True},
        board=None,
        blackboard={},
        limit=1,
    )

    assert observation["causal_status"] == "observation_only"
    assert observation["direct_request"] is False
    assert observation["score_delta"] == 0.0
    assert suggestion["score"] == 7.5
    assert observation["candidate_count"] == 1
    frame = observation["frames"][0]
    assert frame["candidate_source"] == "validated_provider_pack"
    assert frame["direct_request"] is False
    assert frame["score_delta"] == 0.0
    assert "selecting_a_provider" in frame["forbidden_actions"]


def test_candidate_generation_observation_smoke_decision_schema():
    payload = {
        "summary": {
            "generated_candidate_count": 1,
            "generated_candidate_count_by_source": {"validated_provider_pack": 1},
            "protected_candidate_count": 1,
            "stage7_heldout_candidate_count": 0,
            "capacity_evidence_counts": {"positive_capacity": 1},
            "selected_move_or_provider_changed": False,
            "playout_result_or_plies_changed": False,
        },
        "decision": {
            "status": "observation_sandbox_ready_for_non_causal_coverage_analysis",
            "default_off_equivalence_passed": True,
            "observation_frames_emitted": True,
            "frame_invariants_passed": True,
            "selector_allowed": False,
        },
        "cases": [],
    }

    assert _observation_smoke._same_decision(
        {"move": "a1a2", "selected_provider": "krk.fence", "confidence": 1.0},
        {"move": "a1a2", "selected_provider": "krk.fence", "confidence": 1.0},
    )
    assert payload["decision"]["selector_allowed"] is False


def test_candidate_generation_observation_runtime_flag_is_observation_only():
    case = _observation_smoke._load_cases()[0]

    flag_off = _observation_smoke._run_decision(case, enabled=False)
    enabled = _observation_smoke._run_decision(case, enabled=True)

    assert flag_off["observation_present"] is False
    assert enabled["observation_present"] is True
    assert _observation_smoke._same_decision(flag_off, enabled)
    observation = enabled["observation"]
    assert observation["direct_request"] is False
    assert observation["score_delta"] == 0.0
    assert observation["candidate_count"] > 0
    assert observation["sample_frames"][0]["causal_status"] == "observation_only"


def test_candidate_generation_observation_coverage_analysis_blocks_selector():
    payload = {
        "summary": {
            "generated_candidate_count": 1,
            "selected_move_or_provider_changed": False,
            "playout_result_or_plies_changed": False,
        },
        "cases": [
            {
                "case_id": "protected",
                "enabled_decision": {
                    "observation": {
                        "frames": [
                            {
                                "candidate_source": "validated_provider_pack",
                                "capacity_evidence_kind": "positive_capacity",
                                "protected_status": "protected_control",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            }
                        ]
                    }
                },
            }
        ],
    }

    analysis = _observation_analysis.analyze(payload)

    assert analysis["summary"]["invariant_failure_count"] == 0
    assert analysis["interpretation"]["candidate_generation_visible"] is True
    assert analysis["decision"]["selector_allowed"] is False
    assert analysis["decision"]["guardrails_allowed"] is False


def test_candidate_generation_broadened_sample_cases_keep_stage7_held_out():
    cases = _observation_broadened.load_broadened_cases(stage7_cap=2)

    assert cases
    assert any(case["source_stage"] in {"stage4", "stage5", "stage6"} for case in cases)
    assert sum(1 for case in cases if case["source_stage"] == "stage7") == 2
    assert all(case["held_out"] for case in cases if case["source_stage"] == "stage7")


def test_candidate_generation_broadened_aggregate_blocks_selector():
    rows = [
        {
            "case_id": "stage5_state",
            "source_stage": "stage5",
            "held_out": False,
            "source_artifact": "fixture",
            "flag_off_decision": {"observation_present": False},
            "enabled_decision": {
                "observation": {
                    "frames": [
                        {
                            "candidate_source": "validated_provider_pack",
                            "capacity_evidence_kind": "positive_capacity",
                            "protected_status": "protected_control",
                            "direct_request": False,
                            "score_delta": 0.0,
                            "causal_status": "observation_only",
                        }
                    ]
                }
            },
            "selected_move_provider_score_equivalent": True,
        },
        {
            "case_id": "stage7_state",
            "source_stage": "stage7",
            "held_out": True,
            "source_artifact": "fixture",
            "flag_off_decision": {"observation_present": False},
            "enabled_decision": {
                "observation": {
                    "frames": [
                        {
                            "candidate_source": "candidate_move_frame",
                            "capacity_evidence_kind": "held_out_challenge",
                            "protected_status": "held_out_stage7_challenge",
                            "direct_request": False,
                            "score_delta": 0.0,
                            "causal_status": "observation_only",
                        }
                    ]
                }
            },
            "selected_move_provider_score_equivalent": True,
        },
    ]

    summary = _observation_broadened._aggregate(rows)

    assert summary["stage7_heldout_case_count"] == 1
    assert summary["stage7_readiness_training_row_count"] == 0
    assert summary["selected_move_or_provider_delta_count"] == 0
    assert summary["default_off_observation_case_count"] == 0
    assert summary["invariant_failure_count"] == 0


def test_candidate_generation_observation_gap_review_blocks_selector_on_unknown_capacity():
    payload = {
        "cases": [
            {
                "case_id": "stage5_state",
                "source_stage": "stage5",
                "held_out": False,
                "enabled_decision": {
                    "observation": {
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "capacity_evidence_kind": "unknown_capacity",
                                "protected_status": "protected_or_unknown",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            },
                            {
                                "candidate_source": "candidate_move_frame",
                                "capacity_evidence_kind": "unknown_capacity",
                                "protected_status": "protected_or_unknown",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            },
                            {
                                "candidate_source": "validated_provider_pack",
                                "capacity_evidence_kind": "negative_capacity",
                                "protected_status": "protected_control",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            },
                        ]
                    }
                },
            }
        ]
    }

    review = _observation_gap_review.review(payload)

    assert review["decision"]["selector_allowed"] is False
    assert review["decision"]["guardrails_allowed"] is False
    assert "candidate_capacity_mostly_unknown" in review["selector_blockers"]
    assert "generated_set_contains_negative_capacity_candidates" in review["selector_blockers"]


def test_candidate_move_capacity_annotation_remains_offline_capacity_evidence():
    observation_payload = {
        "cases": [
            {
                "case_id": "stage5_state",
                "source_stage": "stage5",
                "held_out": False,
                "enabled_decision": {
                    "observation": {
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a2",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            },
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a3",
                                "direct_request": False,
                                "score_delta": 0.0,
                                "causal_status": "observation_only",
                            },
                        ]
                    }
                },
            }
        ]
    }
    capacity_payload = {
        "rows": [
            {
                "fen": "fen-a",
                "forced_first_move": "a1a2",
                "capacity_label": "positive_capacity",
                "provider_id": "krk.fence_established",
                "forced_result": "mate",
                "stage7_challenge_row": False,
            }
        ]
    }

    payload = _candidate_move_annotation.build_payload(
        observation_payload=observation_payload,
        capacity_payload=capacity_payload,
    )

    assert payload["summary"]["annotated_candidate_move_count"] == 1
    assert payload["summary"]["annotation_counts"]["positive_capacity"] == 1
    assert payload["summary"]["annotation_counts"]["unannotated"] == 1
    assert payload["interpretation"]["capacity_labels_are_not_ownership_labels"] is True
    assert payload["decision"]["selector_allowed"] is False


def test_candidate_move_capacity_manifest_is_bounded_and_protected_only():
    observation_payload = {
        "cases": [
            {
                "case_id": "stage5_state",
                "state_id": "state.a",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "held_out": False,
                "enabled_decision": {
                    "observation": {
                        "selected_move_before_observation": "a1a2",
                        "selected_provider_before_observation": "krk.fence_established",
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a3",
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": ["box_area_not_increased_after_move"],
                                "safety_terms": [],
                                "source_terms": [],
                            }
                        ],
                    }
                },
            },
            {
                "case_id": "stage7_state",
                "state_id": "state.b",
                "source_stage": "stage7",
                "active_landmark_label": "box_shrink",
                "held_out": True,
                "enabled_decision": {
                    "observation": {
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-b",
                                "move_uci": "b1b2",
                            }
                        ],
                    }
                },
            },
        ]
    }
    capacity_payload = {"rows": []}

    payload = _candidate_move_manifest.build_payload(
        observation_payload=observation_payload,
        capacity_payload=capacity_payload,
        cap=4,
    )

    assert payload["summary"]["job_count"] == 1
    assert payload["summary"]["stage7_job_count"] == 0
    assert payload["jobs"][0]["label_semantics"] == (
        "forced_first_move_capacity_not_runtime_ownership_label"
    )
    assert payload["decision"]["labels_run_by_this_artifact"] is False
    assert payload["decision"]["selector_allowed"] is False


def test_candidate_move_capacity_label_payload_validation_blocks_stage7():
    payload = {
        "schema_version": "krk_candidate_move_capacity_labels.v1",
        "causal_status": "non_causal_label_run",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": {
            "stage7_label_count": 0,
            "stage7_training_label_count": 0,
        },
        "labels": [
            {
                "causal_status": "non_causal_outcome_label",
                "label_semantics": "forced_first_move_capacity_not_runtime_ownership_label",
            }
        ],
    }

    _candidate_move_label.validate_payload(payload)


def test_candidate_move_capacity_merge_improves_annotation_but_keeps_selector_blocked():
    observation_payload = {
        "cases": [
            {
                "case_id": "stage5_state",
                "source_stage": "stage5",
                "held_out": False,
                "enabled_decision": {
                    "observation": {
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a2",
                            },
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a3",
                            },
                        ]
                    }
                },
            }
        ]
    }
    capacity_payload = {
        "rows": [
            {
                "fen": "fen-a",
                "forced_first_move": "a1a2",
                "capacity_label": "positive_capacity",
                "forced_result": "mate",
                "provider_id": "krk.fence_established",
            }
        ]
    }
    label_payload = {
        "labels": [
            {
                "fen": "fen-a",
                "forced_first_move": "a1a3",
                "capacity_label": "negative_capacity",
                "result": "max_plies",
                "source_stage": "stage5",
                "label_semantics": "forced_first_move_capacity_not_runtime_ownership_label",
            }
        ]
    }

    payload = _candidate_move_merge.build_payload(
        observation_payload=observation_payload,
        capacity_payload=capacity_payload,
        label_payload=label_payload,
    )

    assert payload["summary"]["annotated_candidate_move_count"] == 2
    assert payload["summary"]["annotation_counts"]["positive_capacity"] == 1
    assert payload["summary"]["annotation_counts"]["negative_capacity"] == 1
    assert payload["interpretation"]["capacity_labels_are_not_ownership_labels"] is True
    assert payload["decision"]["selector_allowed"] is False


def test_candidate_generation_label_blocker_review_rejects_blind_label_farming():
    gap_review = {
        "summary": {
            "frame_count": 100,
            "missing_expected_sources": ["plan_capsule_sequence_candidate"],
        },
        "selector_blockers": ["candidate_capacity_mostly_unknown"],
    }
    annotation_v2 = {
        "summary": {
            "candidate_move_frame_count": 80,
            "protected_candidate_move_count": 70,
            "protected_annotated_candidate_move_count": 5,
            "protected_annotation_recall": 5 / 70,
        }
    }
    labels_v1 = {
        "summary": {
            "label_count": 12,
            "capacity_label_counts": {"positive_capacity": 11, "negative_capacity": 1},
            "stage7_label_count": 0,
            "stage7_training_label_count": 0,
        }
    }
    manifest_v1 = {"summary": {"job_count": 12}}

    payload = _candidate_label_blocker.build_payload(
        gap_review=gap_review,
        annotation_v2=annotation_v2,
        labels_v1=labels_v1,
        manifest_v1=manifest_v1,
    )

    assert payload["decision"]["selector_allowed"] is False
    assert payload["interpretation"]["more_blind_label_farming_not_recommended"] is True
    assert "candidate_move_annotation_coverage_too_sparse" in payload["blockers"]


def test_candidate_proposal_quality_review_stays_non_causal():
    payload = _candidate_quality_review.build_payload(
        gap_review={
            "summary": {
                "frame_count": 10,
                "missing_expected_sources": ["plan_capsule_sequence_candidate"],
            }
        },
        annotation_v2={
            "summary": {
                "candidate_move_frame_count": 8,
                "protected_candidate_move_count": 8,
                "protected_annotated_candidate_move_count": 2,
                "protected_annotation_recall": 0.25,
            }
        },
        blocker_review={
            "evidence": {
                "bounded_label_count": 4,
                "bounded_label_positive_capacity_count": 3,
                "bounded_label_negative_capacity_count": 1,
            }
        },
    )

    assert payload["decision"]["status"] == "proposal_quality_prioritization_review_ready"
    assert payload["decision"]["selector_allowed"] is False
    assert payload["runtime_behavior_changed"] is False
    assert "runtime_selector" in payload["forbidden_next_steps"]
    assert payload["decision"]["recommended_next_step"] == (
        "build_non_causal_candidate_proposal_quality_dataset"
    )


def test_candidate_proposal_quality_dataset_keeps_capacity_not_selector_labels():
    observation_payload = {
        "cases": [
            {
                "case_id": "stage5_state",
                "state_id": "state.a",
                "source_stage": "stage5",
                "active_landmark_label": "fence_established",
                "held_out": False,
                "enabled_decision": {
                    "observation": {
                        "selected_move_before_observation": "a1a2",
                        "selected_provider_before_observation": "krk.stage0_basin",
                        "frames": [
                            {
                                "candidate_source": "candidate_move_frame",
                                "state_fen": "fen-a",
                                "move_uci": "a1a3",
                                "move_shape_terms": ["candidate_is_rook_move"],
                                "post_move_terms": ["box_area_not_increased_after_move"],
                                "safety_terms": [],
                                "source_terms": ["rook_safe"],
                                "direct_request": False,
                                "score_delta": 0.0,
                            }
                        ],
                    }
                },
            }
        ]
    }
    capacity_payload = {"rows": []}
    label_payload = {
        "labels": [
            {
                "fen": "fen-a",
                "forced_first_move": "a1a3",
                "capacity_label": "positive_capacity",
                "source_stage": "stage5",
            }
        ]
    }

    payload = _candidate_quality_dataset.build_payload(
        observation_payload=observation_payload,
        annotation_payload={"summary": {}},
        capacity_payload=capacity_payload,
        label_payload=label_payload,
    )

    assert payload["summary"]["quality_probe_row_count"] == 1
    assert payload["rows"][0]["capacity_evidence_kind"] == "positive_capacity"
    assert payload["rows"][0]["usable_for_selector_training"] is False
    assert payload["decision"]["selector_allowed"] is False


def test_candidate_proposal_quality_decision_blocks_selector_when_probe_weak():
    dataset = {
        "summary": {
            "row_count": 10,
            "quality_probe_row_count": 5,
            "stage7_challenge_row_count": 1,
            "stage7_readiness_training_row_count": 0,
        }
    }
    probe = {
        "summary": {
            "best_probe": "fixture",
            "best_probe_metrics": {
                "positive_precision": 0.8,
                "positive_recall": 0.6,
                "negative_suppression": 0.6,
                "balanced_score": 0.6,
            },
        }
    }

    payload = _candidate_quality_decision.build_payload(dataset=dataset, probe=probe)

    assert payload["decision"]["status"] == "candidate_proposal_quality_not_selector_ready"
    assert payload["decision"]["selector_allowed"] is False
    assert payload["decision"]["more_blind_label_farming_allowed"] is False
    assert payload["decision"]["recommended_next_step"] == (
        "design_broader_strategy_sequence_candidate_sources"
    )
