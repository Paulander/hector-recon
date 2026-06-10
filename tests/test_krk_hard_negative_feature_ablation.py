from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "run_krk_hard_negative_selector_feature_ablation_v0.py"
)
SPEC = importlib.util.spec_from_file_location("run_krk_hard_negative_selector_feature_ablation_v0", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_hard_negative_feature_ablation_is_offline_only(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(module, "ROOT", root)
    _write_json(
        root,
        module.TARGETS,
        {
            "causal_status": "non_causal_target_dataset",
            "rows": [
                {
                    "state_id": "s1",
                    "source_stage": "stage4",
                    "provider_id": "krk.edge_trap_close",
                    "provider_family": "edge_trap",
                    "target_kind": "positive_capacity_context",
                    "forced_piece_type": "king",
                    "white_king_distance_delta": -1,
                    "rook_distance_delta": 0,
                    "king_moves_toward_black": True,
                    "rook_moves_toward_black": False,
                },
                {
                    "state_id": "s2",
                    "source_stage": "stage4",
                    "provider_id": "krk.edge_trap_close",
                    "provider_family": "edge_trap",
                    "target_kind": "hard_negative_capacity",
                    "forced_piece_type": "rook",
                    "white_king_distance_delta": 0,
                    "rook_distance_delta": 1,
                    "king_moves_toward_black": False,
                    "rook_moves_toward_black": False,
                },
            ],
        },
    )
    _write_json(
        root,
        module.SEMANTICS,
        {
            "causal_status": "non_causal_semantics_review",
            "decision": {"offline_benchmark_allowed": True},
        },
    )

    ablation = module.build_ablation()

    assert ablation["schema_version"] == "krk_hard_negative_selector_feature_ablation.v0"
    assert ablation["causal_status"] == "non_causal_feature_ablation"
    assert ablation["runtime_behavior_changed"] is False
    assert ablation["runtime_selector_implemented"] is False
    assert ablation["stage7_promotion_allowed"] is False
    assert ablation["stage8_training_allowed"] is False
    assert ablation["summary"]["row_count"] == 2
    assert ablation["decision"]["selector_training_allowed"] is False
