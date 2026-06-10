from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "probe_krk_geometry_augmented_selector_features_v0.py"
)
SPEC = importlib.util.spec_from_file_location("probe_krk_geometry_augmented_selector_features_v0", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_geometry_augmented_selector_probe_stays_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(module, "ROOT", root)
    _write_json(
        root,
        module.GEOMETRY,
        {
            "causal_status": "non_causal_feature_audit",
            "rows": [
                {
                    "state_id": "s1",
                    "source_stage": "stage5",
                    "provider_family": "stage0_basin",
                    "provider_id": "krk.stage0_basin",
                    "capacity_label": "positive_capacity",
                    "forced_piece_type": "king",
                    "white_king_distance_delta": -1,
                    "rook_distance_delta": 0,
                    "black_king_edge_distance": 0,
                },
                {
                    "state_id": "s2",
                    "source_stage": "stage5",
                    "provider_family": "edge_trap",
                    "provider_id": "krk.edge_trap_close",
                    "capacity_label": "negative_capacity",
                    "forced_piece_type": "rook",
                    "white_king_distance_delta": 0,
                    "rook_distance_delta": 1,
                    "black_king_edge_distance": 0,
                },
            ],
        },
    )
    _write_json(root, module.NEGATIVE_EVIDENCE, {"causal_status": "non_causal_evidence_audit"})

    probe = module.build_probe()

    assert probe["schema_version"] == "krk_geometry_augmented_selector_feature_probe.v0"
    assert probe["causal_status"] == "non_causal_feature_probe"
    assert probe["runtime_behavior_changed"] is False
    assert probe["runtime_selector_implemented"] is False
    assert probe["stage7_promotion_allowed"] is False
    assert probe["stage8_training_allowed"] is False
    assert probe["summary"]["row_count"] == 2
    assert probe["summary"]["stage7_row_count"] == 0
    assert probe["decision"]["selector_training_allowed"] is False
