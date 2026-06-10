from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load_module(name: str, script: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / script)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


plan_module = _load_module(
    "plan_krk_balanced_hard_negative_provider_labels_v0",
    "plan_krk_balanced_hard_negative_provider_labels_v0.py",
)
manifest_module = _load_module(
    "build_krk_balanced_hard_negative_execution_manifest_v0",
    "build_krk_balanced_hard_negative_execution_manifest_v0.py",
)
review_module = _load_module(
    "review_krk_balanced_hard_negative_execution_manifest_v0",
    "review_krk_balanced_hard_negative_execution_manifest_v0.py",
)
runner_module = _load_module(
    "run_krk_balanced_hard_negative_labels_v0",
    "run_krk_balanced_hard_negative_labels_v0.py",
)
dataset_module = _load_module(
    "build_krk_hard_negative_selector_target_dataset_v1",
    "build_krk_hard_negative_selector_target_dataset_v1.py",
)
ablation_module = _load_module(
    "run_krk_hard_negative_selector_feature_ablation_v1",
    "run_krk_hard_negative_selector_feature_ablation_v1.py",
)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_balanced_hard_negative_plan_excludes_stage7(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(plan_module, "ROOT", root)
    _write_json(
        root,
        plan_module.RANKED_FRAMES,
        {
            "causal_status": "non_causal_ranked_frame_dataset",
            "rows": [
                {
                    "frame_id": "f5",
                    "state_id": "s5",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "fen": "5k2/7R/1K6/8/8/8/8/8 w - - 2 2",
                    "provider_id": "krk.stage0_basin",
                    "frame_outcome": "max_plies",
                },
                {
                    "frame_id": "f7",
                    "state_id": "s7",
                    "source_stage": "stage7",
                    "active_landmark_label": "box_shrink",
                    "fen": "8/8/8/R7/4k3/8/3K4/8 w - - 2 2",
                    "provider_id": "krk.stage0_basin",
                },
            ],
        },
    )
    _write_json(root, plan_module.CAPACITY_FRAMES, {"causal_status": "non_causal_capacity_frame_dataset", "rows": []})
    _write_json(root, plan_module.HARD_NEGATIVE_ABLATION, {"causal_status": "non_causal_feature_ablation"})
    _write_json(root, plan_module.STATE_LOCAL_CONTRAST, {"rows": []})
    _write_json(root, plan_module.MISSING_PROVIDER_LABELS, {"labels": []})

    plan = plan_module.build_plan()

    assert plan["causal_status"] == "non_causal_label_plan"
    assert plan["summary"]["stage7_jobs"] == 0
    assert plan["runtime_selector_implemented"] is False
    assert plan["decision"]["selector_training_allowed"] is False
    assert all(job["source_stage"] != "stage7" for job in plan["jobs"])


def test_balanced_manifest_review_blocks_stage7_jobs(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(review_module, "ROOT", root)
    _write_json(
        root,
        review_module.MANIFEST,
        {
            "binding_summary": {"all_bindings_valid": True},
            "jobs": [
                {
                    "job_id": "j1",
                    "source_stage": "stage7",
                    "horizon": 40,
                    "execution_binding": {
                        "execution_mode": "force_provider_first_white_move_then_release",
                        "enable_diagnostic_caches": True,
                        "trace_mode": "failures_only",
                        "plasticity_scope": "protected_frozen",
                    },
                }
            ],
        },
    )

    review = review_module.build_review()

    assert review["decision"]["labels_allowed"] is False
    assert review["runtime_selector_implemented"] is False
    assert any(v["violation"] == "stage7_job_not_allowed" for v in review["review_summary"]["violations"])


def test_balanced_label_runner_is_non_causal_with_mocked_harness(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(runner_module, "ROOT", root)
    _write_json(
        root,
        runner_module.MANIFEST,
        {
            "causal_status": "non_causal_execution_manifest",
            "binding_summary": {"all_bindings_valid": True},
            "jobs": [
                {
                    "job_id": "j1",
                    "frame_id": "f1",
                    "state_id": "s1",
                    "source_stage": "stage5",
                    "active_landmark_label": "fence_established",
                    "provider_id": "krk.drive_to_edge",
                    "provider_family": "drive_to_edge",
                    "fen": "5k2/7R/1K6/8/8/8/8/8 w - - 2 2",
                    "execution_binding": {"provider_version": "stage6_overlay_v1"},
                }
            ],
        },
    )
    _write_json(
        root,
        runner_module.REVIEW,
        {
            "causal_status": "non_causal_manifest_review",
            "decision": {"labels_allowed": True},
        },
    )

    def fake_run_job(_root: Path, job: dict, _cache: dict):
        return {
            "causal_status": "non_causal_outcome_label",
            "job_id": job["job_id"],
            "frame_id": job["frame_id"],
            "state_id": job["state_id"],
            "source_stage": job["source_stage"],
            "provider_id": job["provider_id"],
            "forced_first_move": "h7h8",
            "forced_successor_available": True,
            "result": "max_plies",
            "plies": 40,
        }

    monkeypatch.setattr(runner_module.forced_labels, "_run_job", fake_run_job)

    payload = runner_module.run_labels()

    assert payload["causal_status"] == "non_causal_label_run"
    assert payload["summary"]["negative_capacity_count"] == 1
    assert payload["summary"]["stage7_labels"] == 0
    assert payload["runtime_behavior_changed"] is False
    assert payload["decision"]["selector_training_allowed"] is False


def test_expanded_target_dataset_and_ablation_remain_offline(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(dataset_module, "ROOT", root)
    monkeypatch.setattr(ablation_module, "ROOT", root)
    fen = "5k2/7R/1K6/8/8/8/8/8 w - - 2 2"
    _write_json(
        root,
        dataset_module.TARGETS_V0,
        {
            "causal_status": "non_causal_target_dataset",
            "rows": [
                {
                    "causal_status": "non_causal_target_candidate",
                    "target_kind": "positive_capacity_context",
                    "state_id": "s1",
                    "source_stage": "stage5",
                    "provider_id": "krk.stage0_basin",
                    "provider_family": "stage0_basin",
                    "forced_first_move": "b6c7",
                    "forced_piece_type": "king",
                    "white_king_distance_delta": -1,
                    "rook_distance_delta": 0,
                }
            ],
        },
    )
    _write_json(
        root,
        dataset_module.BALANCED_LABELS,
        {
            "causal_status": "non_causal_label_run",
            "labels": [
                {
                    "causal_status": "non_causal_outcome_label",
                    "result": "max_plies",
                    "state_id": "s2",
                    "frame_id": "f2",
                    "source_stage": "stage5",
                    "source_active_landmark_label": "fence_established",
                    "provider_id": "krk.drive_to_edge",
                    "provider_family": "drive_to_edge",
                    "forced_first_move": "h7h8",
                    "forced_successor_available": True,
                    "provider_version": "stage6_overlay_v1",
                    "fen": fen,
                    "plies": 40,
                }
            ],
        },
    )
    _write_json(root, dataset_module.SEMANTICS, {"causal_status": "non_causal_semantics_review"})

    dataset = dataset_module.build_dataset()
    _write_json(root, ablation_module.TARGETS, dataset)
    ablation = ablation_module.build_ablation()

    assert dataset["schema_version"] == "krk_hard_negative_selector_target_dataset.v1"
    assert dataset["summary"]["stage7_row_count"] == 0
    assert dataset["summary"]["training_row_count"] == 0
    assert dataset["decision"]["selector_training_allowed"] is False
    assert ablation["schema_version"] == "krk_hard_negative_selector_feature_ablation.v1"
    assert ablation["runtime_selector_implemented"] is False
    assert ablation["decision"]["selector_training_allowed"] is False
