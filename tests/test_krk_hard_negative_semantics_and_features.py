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


semantics_module = _load_module(
    "summarize_krk_hard_negative_label_semantics_review_v1",
    "summarize_krk_hard_negative_label_semantics_review_v1.py",
)
features_module = _load_module(
    "review_krk_stronger_selector_features_v0",
    "review_krk_stronger_selector_features_v0.py",
)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _target_rows() -> list[dict]:
    base = {
        "causal_status": "non_causal_target_candidate",
        "source_stage": "stage5",
        "stage7_challenge_row": False,
        "source_artifact_channel": "fixture",
        "active_landmark_label": "fence_established",
        "black_king_legal_reply_count_after": 4,
        "black_king_edge_distance": 0,
    }
    return [
        {
            **base,
            "state_id": "s1",
            "provider_id": "krk.stage0_basin",
            "provider_family": "stage0_basin",
            "target_kind": "positive_capacity_context",
            "forced_piece_type": "king",
            "white_king_distance_delta": -1,
            "rook_distance_delta": 0,
            "rook_same_file_as_black_after": False,
            "rook_same_rank_as_black_after": False,
        },
        {
            **base,
            "state_id": "s2",
            "provider_id": "krk.drive_to_edge",
            "provider_family": "drive_to_edge",
            "target_kind": "hard_negative_capacity",
            "forced_piece_type": "rook",
            "white_king_distance_delta": 0,
            "rook_distance_delta": 1,
            "rook_same_file_as_black_after": False,
            "rook_same_rank_as_black_after": False,
        },
        {
            **base,
            "state_id": "s3",
            "provider_id": "krk.edge_trap_close",
            "provider_family": "edge_trap",
            "target_kind": "positive_capacity_context",
            "forced_piece_type": "rook",
            "white_king_distance_delta": 0,
            "rook_distance_delta": -1,
            "rook_same_file_as_black_after": True,
            "rook_same_rank_as_black_after": False,
        },
    ]


def test_hard_negative_semantics_blocks_direct_selector_training(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(semantics_module, "ROOT", root)
    _write_json(
        root,
        semantics_module.TARGETS,
        {
            "causal_status": "non_causal_target_dataset",
            "rows": _target_rows(),
        },
    )
    _write_json(
        root,
        semantics_module.ABLATION,
        {
            "causal_status": "non_causal_feature_ablation",
            "best_result": {"negative_suppression": 0.25, "positive_recall": 1.0},
        },
    )
    _write_json(root, semantics_module.EVIDENCE_REVIEW, {"causal_status": "non_causal_evidence_review"})

    review = semantics_module.build_review()

    assert review["causal_status"] == "non_causal_semantics_review"
    assert review["runtime_selector_implemented"] is False
    assert review["decision"]["selector_training_allowed"] is False
    assert review["decision"]["status"] == "capacity_labels_not_direct_selector_targets"
    assert review["summary"]["stage7_row_count"] == 0
    assert "ownership_selection_objective" in review["recommended_objective_split"]


def test_stronger_selector_feature_review_is_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(features_module, "ROOT", root)
    _write_json(
        root,
        features_module.TARGETS,
        {
            "causal_status": "non_causal_target_dataset",
            "rows": _target_rows(),
        },
    )
    _write_json(
        root,
        features_module.SEMANTICS,
        {
            "causal_status": "non_causal_semantics_review",
            "decision": {"selector_training_allowed": False},
        },
    )
    _write_json(
        root,
        features_module.ABLATION,
        {
            "causal_status": "non_causal_feature_ablation",
            "best_result": {"negative_suppression": 0.0, "positive_recall": 1.0},
        },
    )

    review = features_module.build_review()

    assert review["causal_status"] == "non_causal_feature_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_selector_implemented"] is False
    assert review["decision"]["selector_training_allowed"] is False
    assert review["decision"]["runtime_work_allowed"] is False
    assert review["summary"]["stage7_row_count"] == 0
    assert "piece_motion@0.5" in review["results"]
