from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "build_krk_hard_negative_selector_target_dataset_v0.py"
)
SPEC = importlib.util.spec_from_file_location("build_krk_hard_negative_selector_target_dataset_v0", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_hard_negative_selector_target_candidates_are_not_training_rows(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(module, "ROOT", root)
    _write_json(root, module.DIRECTED_REVIEW, {"causal_status": "non_causal_architecture_review"})
    _write_json(
        root,
        module.GEOMETRY,
        {
            "causal_status": "non_causal_feature_audit",
            "rows": [
                {
                    "state_id": "s1",
                    "source_stage": "stage4",
                    "provider_id": "krk.edge_trap_close",
                    "provider_family": "edge_trap",
                    "capacity_label": "negative_capacity",
                    "forced_first_move": "a1a2",
                    "forced_plies": 40,
                    "forced_piece_type": "king",
                    "black_king_edge_distance": 0,
                    "white_king_distance_delta": -1,
                    "rook_distance_delta": 0,
                }
            ],
        },
    )

    dataset = module.build_dataset()

    assert dataset["schema_version"] == "krk_hard_negative_selector_target_dataset.v0"
    assert dataset["causal_status"] == "non_causal_target_dataset"
    assert dataset["runtime_behavior_changed"] is False
    assert dataset["runtime_selector_implemented"] is False
    assert dataset["stage7_promotion_allowed"] is False
    assert dataset["stage8_training_allowed"] is False
    assert dataset["summary"]["target_kind_counts"] == {"hard_negative_capacity": 1}
    assert dataset["summary"]["training_row_count"] == 0
    assert dataset["rows"][0]["usable_for_training"] is False
    assert dataset["decision"]["selector_training_allowed"] is False
