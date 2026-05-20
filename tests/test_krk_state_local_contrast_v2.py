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
