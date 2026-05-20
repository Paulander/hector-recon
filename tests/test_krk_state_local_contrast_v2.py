from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_krk_state_local_contrast_labels_v2.py"
SPEC = importlib.util.spec_from_file_location("build_krk_state_local_contrast_labels_v2", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

REVIEW_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_protected_missing_provider_label_merge_review.py"
)
REVIEW_SPEC = importlib.util.spec_from_file_location(
    "summarize_krk_protected_missing_provider_label_merge_review",
    REVIEW_SCRIPT,
)
assert REVIEW_SPEC is not None
assert REVIEW_SPEC.loader is not None
review_module = importlib.util.module_from_spec(REVIEW_SPEC)
REVIEW_SPEC.loader.exec_module(review_module)

COVERAGE_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_ranked_proposal_frame_coverage_for_protected_missing_provider.py"
)
COVERAGE_SPEC = importlib.util.spec_from_file_location(
    "summarize_krk_ranked_proposal_frame_coverage_for_protected_missing_provider",
    COVERAGE_SCRIPT,
)
assert COVERAGE_SPEC is not None
assert COVERAGE_SPEC.loader is not None
coverage_module = importlib.util.module_from_spec(COVERAGE_SPEC)
COVERAGE_SPEC.loader.exec_module(coverage_module)

EXPANSION_PLAN_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "summarize_krk_protected_proposal_coverage_expansion_plan.py"
)
EXPANSION_PLAN_SPEC = importlib.util.spec_from_file_location(
    "summarize_krk_protected_proposal_coverage_expansion_plan",
    EXPANSION_PLAN_SCRIPT,
)
assert EXPANSION_PLAN_SPEC is not None
assert EXPANSION_PLAN_SPEC.loader is not None
expansion_plan_module = importlib.util.module_from_spec(EXPANSION_PLAN_SPEC)
EXPANSION_PLAN_SPEC.loader.exec_module(expansion_plan_module)

COVERAGE_FRAMES_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "build_krk_protected_provider_coverage_frames_v0.py"
)
COVERAGE_FRAMES_SPEC = importlib.util.spec_from_file_location(
    "build_krk_protected_provider_coverage_frames_v0",
    COVERAGE_FRAMES_SCRIPT,
)
assert COVERAGE_FRAMES_SPEC is not None
assert COVERAGE_FRAMES_SPEC.loader is not None
coverage_frames_module = importlib.util.module_from_spec(COVERAGE_FRAMES_SPEC)
COVERAGE_FRAMES_SPEC.loader.exec_module(coverage_frames_module)

CAPACITY_SEMANTICS_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_protected_provider_capacity_frame_training_semantics.py"
)
CAPACITY_SEMANTICS_SPEC = importlib.util.spec_from_file_location(
    "review_krk_protected_provider_capacity_frame_training_semantics",
    CAPACITY_SEMANTICS_SCRIPT,
)
assert CAPACITY_SEMANTICS_SPEC is not None
assert CAPACITY_SEMANTICS_SPEC.loader is not None
capacity_semantics_module = importlib.util.module_from_spec(CAPACITY_SEMANTICS_SPEC)
CAPACITY_SEMANTICS_SPEC.loader.exec_module(capacity_semantics_module)

CANDIDATE_COVERAGE_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "audit_krk_candidate_generator_coverage_v0.py"
)
CANDIDATE_COVERAGE_SPEC = importlib.util.spec_from_file_location(
    "audit_krk_candidate_generator_coverage_v0",
    CANDIDATE_COVERAGE_SCRIPT,
)
assert CANDIDATE_COVERAGE_SPEC is not None
assert CANDIDATE_COVERAGE_SPEC.loader is not None
candidate_coverage_module = importlib.util.module_from_spec(CANDIDATE_COVERAGE_SPEC)
CANDIDATE_COVERAGE_SPEC.loader.exec_module(candidate_coverage_module)

VALIDATED_CANDIDATE_SET_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "audit_krk_validated_provider_candidate_set_v0.py"
)
VALIDATED_CANDIDATE_SET_SPEC = importlib.util.spec_from_file_location(
    "audit_krk_validated_provider_candidate_set_v0",
    VALIDATED_CANDIDATE_SET_SCRIPT,
)
assert VALIDATED_CANDIDATE_SET_SPEC is not None
assert VALIDATED_CANDIDATE_SET_SPEC.loader is not None
validated_candidate_set_module = importlib.util.module_from_spec(VALIDATED_CANDIDATE_SET_SPEC)
VALIDATED_CANDIDATE_SET_SPEC.loader.exec_module(validated_candidate_set_module)

TWO_STAGE_REVIEW_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_two_stage_candidate_selection_review_v0.py"
)
TWO_STAGE_REVIEW_SPEC = importlib.util.spec_from_file_location(
    "summarize_krk_two_stage_candidate_selection_review_v0",
    TWO_STAGE_REVIEW_SCRIPT,
)
assert TWO_STAGE_REVIEW_SPEC is not None
assert TWO_STAGE_REVIEW_SPEC.loader is not None
two_stage_review_module = importlib.util.module_from_spec(TWO_STAGE_REVIEW_SPEC)
TWO_STAGE_REVIEW_SPEC.loader.exec_module(two_stage_review_module)

TWO_STAGE_BENCHMARK_PLAN_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "plan_krk_two_stage_candidate_selection_benchmark_v0.py"
)
TWO_STAGE_BENCHMARK_PLAN_SPEC = importlib.util.spec_from_file_location(
    "plan_krk_two_stage_candidate_selection_benchmark_v0",
    TWO_STAGE_BENCHMARK_PLAN_SCRIPT,
)
assert TWO_STAGE_BENCHMARK_PLAN_SPEC is not None
assert TWO_STAGE_BENCHMARK_PLAN_SPEC.loader is not None
two_stage_benchmark_plan_module = importlib.util.module_from_spec(TWO_STAGE_BENCHMARK_PLAN_SPEC)
TWO_STAGE_BENCHMARK_PLAN_SPEC.loader.exec_module(two_stage_benchmark_plan_module)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_state_local_contrast_v2_includes_protected_missing_provider_labels(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(module, "ROOT", root)

    _write_json(
        root,
        module.RANKED_FRAMES,
        {
            "causal_status": "non_causal_ranked_frame_dataset",
            "rows": [
                {
                    "frame_id": "cp.protected",
                    "state_id": "state.protected",
                    "source_stage": "stage6",
                    "active_landmark_label": "drive_to_edge",
                    "provider_id": "krk.drive_to_edge",
                    "provider_family": "drive",
                    "provider_maturity": "validated_low_plasticity",
                    "move_uci": "a1a2",
                    "global_raw_score_rank": 1,
                    "provider_local_rank": 1,
                    "normalized_score": 1.0,
                    "stage7_challenge_row": False,
                }
            ],
        },
    )
    for path in module.FORCED_LABELS[:-1]:
        _write_json(root, path, {"causal_status": "non_causal_label_run", "labels": []})
    _write_json(
        root,
        module.FORCED_LABELS[-1],
        {
            "causal_status": "non_causal_label_run",
            "labels": [
                {
                    "causal_status": "non_causal_outcome_label",
                    "job_id": "job.protected",
                    "state_id": "state.protected",
                    "source_stage": "stage6",
                    "provider_id": "krk.drive_to_edge",
                    "provider_family": "drive",
                    "result": "mate",
                    "plies": 11,
                    "forced_first_move": "a1a2",
                    "stage7_challenge_row": False,
                }
            ],
        },
    )

    dataset = module.build_dataset()

    assert str(module.FORCED_LABELS[-1]) in dataset["source_artifacts"]
    assert dataset["schema_version"] == "krk_state_local_contrast_labels.v2"
    assert dataset["causal_status"] == "non_causal_state_local_contrast_dataset"
    assert dataset["runtime_behavior_changed"] is False
    assert dataset["stage7_promotion_allowed"] is False
    assert dataset["stage8_training_allowed"] is False
    assert dataset["summary"]["row_count"] == 1
    assert dataset["summary"]["usable_training_row_count"] == 1
    assert dataset["rows"][0]["source_label_job_id"] == "job.protected"
    assert dataset["rows"][0]["contrast_label"] == "positive"


def test_protected_missing_provider_label_merge_review_blocks_unmatched_runtime_work(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(review_module, "ROOT", root)
    _write_json(
        root,
        review_module.LABELS,
        {
            "causal_status": "non_causal_label_run",
            "labels": [
                {
                    "causal_status": "non_causal_outcome_label",
                    "job_id": "job.krk.protected_missing_provider.a",
                    "state_id": "state.a",
                    "source_stage": "stage6",
                    "provider_id": "krk.drive_to_edge",
                    "result": "mate",
                    "plies": 9,
                }
            ],
        },
    )
    _write_json(
        root,
        review_module.CONTRAST,
        {
            "causal_status": "non_causal_state_local_contrast_dataset",
            "rows": [
                {
                    "source_label_job_id": "job.other",
                    "source_stage": "stage6",
                }
            ],
        },
    )

    review = review_module.build_review()

    assert review["schema_version"] == "krk_protected_missing_provider_label_merge_review.v0"
    assert review["causal_status"] == "non_causal_merge_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_selector_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["summary"]["matched_protected_label_count"] == 0
    assert review["summary"]["unmatched_protected_label_count"] == 1
    assert review["decision"]["status"] == "protected_missing_provider_labels_unmatched_by_current_proposal_frames"
    assert review["decision"]["runtime_work_allowed"] is False


def test_ranked_proposal_frame_coverage_review_detects_missing_provider_rows(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(coverage_module, "ROOT", root)
    _write_json(
        root,
        coverage_module.RANKED_FRAMES,
        {
            "causal_status": "non_causal_ranked_frame_dataset",
            "rows": [
                {
                    "frame_id": "cp.a",
                    "state_id": "state.a",
                    "provider_id": "krk.stage0_basin",
                }
            ],
        },
    )
    _write_json(
        root,
        coverage_module.LABELS,
        {
            "causal_status": "non_causal_label_run",
            "labels": [
                {
                    "causal_status": "non_causal_outcome_label",
                    "job_id": "job.krk.protected_missing_provider.a",
                    "frame_id": "cp.a",
                    "state_id": "state.a",
                    "source_stage": "stage6",
                    "provider_id": "krk.drive_to_edge",
                    "result": "mate",
                    "plies": 9,
                }
            ],
        },
    )

    review = coverage_module.build_review()

    assert review["schema_version"] == "krk_ranked_proposal_frame_protected_provider_coverage_review.v0"
    assert review["causal_status"] == "non_causal_coverage_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_selector_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["summary"]["frames_present_count"] == 1
    assert review["summary"]["provider_present_in_frame_count"] == 0
    assert review["summary"]["missing_provider_mate_label_count"] == 1
    assert review["decision"]["status"] == "proposal_provider_coverage_gap_blocks_selector_training"
    assert review["decision"]["runtime_work_allowed"] is False


def test_protected_proposal_coverage_expansion_plan_keeps_rows_non_training(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(expansion_plan_module, "ROOT", root)
    _write_json(
        root,
        expansion_plan_module.COVERAGE_REVIEW,
        {
            "causal_status": "non_causal_coverage_review",
            "records": [
                {
                    "provider_present_in_frame": False,
                    "source_stage": "stage6",
                    "provider_id": "krk.drive_to_edge",
                },
                {
                    "provider_present_in_frame": True,
                    "source_stage": "stage6",
                    "provider_id": "krk.stage0_basin",
                },
            ],
        },
    )

    plan = expansion_plan_module.build_plan()

    assert plan["schema_version"] == "krk_protected_proposal_coverage_expansion_plan.v0"
    assert plan["causal_status"] == "non_causal_design_plan"
    assert plan["runtime_behavior_changed"] is False
    assert plan["runtime_selector_implemented"] is False
    assert plan["stage7_promotion_allowed"] is False
    assert plan["stage8_training_allowed"] is False
    assert plan["expansion_design"]["rows_to_create"] == 1
    assert plan["acceptance_for_next_slice"]["stage7_rows_allowed"] == 0
    assert plan["acceptance_for_next_slice"]["training_allowed_initially"] is False
    assert plan["decision"]["recommended_next_step"] == "build_non_causal_protected_provider_coverage_frames_v0"


def test_protected_provider_coverage_frames_are_capacity_evidence_not_training(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(coverage_frames_module, "ROOT", root)
    _write_json(root, coverage_frames_module.PLAN, {"causal_status": "non_causal_design_plan"})
    _write_json(
        root,
        coverage_frames_module.RANKED_FRAMES,
        {
            "causal_status": "non_causal_ranked_frame_dataset",
            "rows": [
                {
                    "frame_id": "cp.a",
                    "state_id": "state.a",
                    "fen": "8/8/8/8/8/8/8/8 w - - 0 1",
                    "active_landmark_label": "drive_to_edge",
                    "provider_id": "krk.stage0_basin",
                }
            ],
        },
    )
    _write_json(
        root,
        coverage_frames_module.LABELS,
        {
            "causal_status": "non_causal_label_run",
            "labels": [
                {
                    "causal_status": "non_causal_outcome_label",
                    "job_id": "job.krk.protected_missing_provider.a",
                    "frame_id": "cp.a",
                    "state_id": "state.a",
                    "source_stage": "stage6",
                    "source_active_landmark_label": "drive_to_edge",
                    "provider_id": "krk.drive_to_edge",
                    "provider_version": "stage6_overlay_v1",
                    "result": "mate",
                    "plies": 9,
                    "forced_first_move": "a1a2",
                    "forced_successor_available": True,
                }
            ],
        },
    )

    payload = coverage_frames_module.build_frames()

    assert payload["schema_version"] == "krk_protected_provider_coverage_frames.v0"
    assert payload["causal_status"] == "non_causal_capacity_frame_dataset"
    assert payload["runtime_behavior_changed"] is False
    assert payload["runtime_selector_implemented"] is False
    assert payload["stage7_promotion_allowed"] is False
    assert payload["stage8_training_allowed"] is False
    assert payload["summary"]["row_count"] == 1
    assert payload["summary"]["training_row_count"] == 0
    assert payload["summary"]["runtime_proposal_row_count"] == 0
    row = payload["rows"][0]
    assert row["capacity_label"] == "positive_capacity"
    assert row["proposal_source"] == "offline_forced_provider_label_not_runtime_proposal"
    assert row["usable_for_training"] is False
    assert row["has_runtime_proposal_frame"] is False


def test_capacity_frame_training_semantics_review_blocks_selector_training(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(capacity_semantics_module, "ROOT", root)
    _write_json(
        root,
        capacity_semantics_module.COVERAGE_FRAMES,
        {
            "causal_status": "non_causal_capacity_frame_dataset",
            "rows": [
                {
                    "source_stage": "stage6",
                    "provider_family": "drive_to_edge",
                    "capacity_label": "positive_capacity",
                    "usable_for_training": False,
                    "has_runtime_proposal_frame": False,
                },
                {
                    "source_stage": "stage5",
                    "provider_family": "edge_trap",
                    "capacity_label": "negative_capacity",
                    "usable_for_training": False,
                    "has_runtime_proposal_frame": False,
                },
            ],
        },
    )

    review = capacity_semantics_module.build_review()

    assert review["schema_version"] == "krk_protected_provider_capacity_frame_training_semantics_review.v0"
    assert review["causal_status"] == "non_causal_semantics_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_selector_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["summary"]["positive_capacity_count"] == 1
    assert review["summary"]["negative_capacity_count"] == 1
    assert "direct_selector_training_positive" in review["blocked_uses"]
    assert review["decision"]["selector_training_allowed"] is False
    assert review["decision"]["status"] == "capacity_frames_diagnostic_not_selector_training_ready"


def test_candidate_generator_coverage_audit_confirms_zero_positive_recall(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(candidate_coverage_module, "ROOT", root)
    _write_json(
        root,
        candidate_coverage_module.CAPACITY_FRAMES,
        {
            "causal_status": "non_causal_capacity_frame_dataset",
            "rows": [
                {
                    "source_stage": "stage6",
                    "state_id": "state.a",
                    "provider_id": "krk.drive_to_edge",
                    "provider_family": "drive_to_edge",
                    "capacity_label": "positive_capacity",
                    "has_runtime_proposal_frame": False,
                    "existing_frame_providers": ["krk.stage0_basin"],
                }
            ],
        },
    )
    _write_json(
        root,
        candidate_coverage_module.SEMANTICS_REVIEW,
        {"causal_status": "non_causal_semantics_review"},
    )

    audit = candidate_coverage_module.build_audit()

    assert audit["schema_version"] == "krk_candidate_generator_coverage_audit.v0"
    assert audit["causal_status"] == "non_causal_candidate_generator_audit"
    assert audit["runtime_behavior_changed"] is False
    assert audit["runtime_candidate_generator_implemented"] is False
    assert audit["stage7_promotion_allowed"] is False
    assert audit["stage8_training_allowed"] is False
    assert audit["summary"]["positive_capacity_count"] == 1
    assert audit["summary"]["runtime_proposal_positive_recall_rate"] == 0.0
    assert audit["decision"]["status"] == "candidate_generator_recall_gap_confirmed"
    assert audit["decision"]["selector_training_allowed"] is False


def test_validated_provider_candidate_set_audit_keeps_runtime_blocked(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(validated_candidate_set_module, "ROOT", root)
    _write_json(
        root,
        validated_candidate_set_module.CANDIDATE_COVERAGE,
        {"causal_status": "non_causal_candidate_generator_audit"},
    )
    _write_json(
        root,
        validated_candidate_set_module.CAPACITY_FRAMES,
        {
            "causal_status": "non_causal_capacity_frame_dataset",
            "rows": [
                {
                    "source_stage": "stage6",
                    "state_id": "state.a",
                    "provider_id": "krk.drive_to_edge",
                    "provider_family": "drive_to_edge",
                    "capacity_label": "positive_capacity",
                    "existing_frame_providers": ["krk.stage0_basin"],
                },
                {
                    "source_stage": "stage6",
                    "state_id": "state.a",
                    "provider_id": "krk.fence_established",
                    "provider_family": "fence_established",
                    "capacity_label": "negative_capacity",
                    "existing_frame_providers": ["krk.stage0_basin"],
                },
            ],
        },
    )

    audit = validated_candidate_set_module.build_audit()

    assert audit["schema_version"] == "krk_validated_provider_candidate_set_audit.v0"
    assert audit["causal_status"] == "non_causal_candidate_set_audit"
    assert audit["runtime_candidate_generator_implemented"] is False
    assert audit["runtime_selector_implemented"] is False
    assert audit["stage7_promotion_allowed"] is False
    assert audit["stage8_training_allowed"] is False
    assert audit["summary"]["added_positive_capacity_count"] == 1
    assert audit["summary"]["added_negative_capacity_count"] == 1
    assert audit["decision"]["candidate_generator_runtime_allowed"] is False
    assert audit["decision"]["selector_training_allowed"] is False


def test_two_stage_candidate_selection_review_blocks_runtime_and_training(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(two_stage_review_module, "ROOT", root)
    _write_json(
        root,
        two_stage_review_module.CANDIDATE_SET_AUDIT,
        {
            "causal_status": "non_causal_candidate_set_audit",
            "summary": {
                "added_positive_capacity_count": 2,
                "added_negative_capacity_count": 1,
            },
        },
    )
    _write_json(
        root,
        two_stage_review_module.CAPACITY_SEMANTICS,
        {"causal_status": "non_causal_semantics_review"},
    )

    review = two_stage_review_module.build_review()

    assert review["schema_version"] == "krk_two_stage_candidate_selection_review.v0"
    assert review["causal_status"] == "non_causal_architecture_review"
    assert review["runtime_candidate_generator_implemented"] is False
    assert review["runtime_selector_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["current_evidence"]["positive_capacity_recovered_by_validated_provider_set"] == 2
    assert review["current_evidence"]["negative_capacity_also_included"] == 1
    assert review["decision"]["candidate_generator_runtime_allowed"] is False
    assert review["decision"]["selector_training_allowed"] is False
    assert review["decision"]["status"] == "two_stage_non_causal_benchmark_design_needed"


def test_two_stage_candidate_selection_benchmark_plan_is_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(two_stage_benchmark_plan_module, "ROOT", root)
    _write_json(
        root,
        two_stage_benchmark_plan_module.TWO_STAGE_REVIEW,
        {"causal_status": "non_causal_architecture_review"},
    )

    plan = two_stage_benchmark_plan_module.build_plan()

    assert plan["schema_version"] == "krk_two_stage_candidate_selection_benchmark_plan.v0"
    assert plan["causal_status"] == "non_causal_benchmark_plan"
    assert plan["runtime_behavior_changed"] is False
    assert plan["runtime_candidate_generator_implemented"] is False
    assert plan["runtime_selector_implemented"] is False
    assert plan["stage7_promotion_allowed"] is False
    assert plan["stage8_training_allowed"] is False
    assert plan["acceptance"]["stage7_training_rows"] == 0
    assert plan["acceptance"]["reports_candidate_generation_and_selection_separately"] is True
    assert plan["decision"]["candidate_generator_runtime_allowed"] is False
    assert plan["decision"]["selector_training_allowed"] is False
