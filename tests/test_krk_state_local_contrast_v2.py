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
