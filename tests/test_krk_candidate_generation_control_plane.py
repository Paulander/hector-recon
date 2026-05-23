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
