from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_krk_capacity_geometry_features_v0.py"
SPEC = importlib.util.spec_from_file_location("audit_krk_capacity_geometry_features_v0", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_capacity_geometry_feature_audit_extracts_non_causal_terms(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(module, "ROOT", root)
    _write_json(
        root,
        module.CAPACITY_FRAMES,
        {
            "causal_status": "non_causal_capacity_frame_dataset",
            "rows": [
                {
                    "state_id": "state.a",
                    "source_stage": "stage5",
                    "provider_id": "krk.stage0_basin",
                    "provider_family": "stage0_basin",
                    "capacity_label": "positive_capacity",
                    "forced_first_move": "b6c7",
                    "forced_plies": 27,
                    "fen": "5k2/7R/1K6/8/8/8/8/8 w - - 2 2",
                }
            ],
        },
    )
    _write_json(root, module.NEGATIVE_EVIDENCE, {"causal_status": "non_causal_evidence_audit"})

    audit = module.build_audit()

    assert audit["schema_version"] == "krk_capacity_geometry_feature_audit.v0"
    assert audit["causal_status"] == "non_causal_feature_audit"
    assert audit["runtime_behavior_changed"] is False
    assert audit["runtime_selector_implemented"] is False
    assert audit["stage7_promotion_allowed"] is False
    assert audit["stage8_training_allowed"] is False
    assert audit["summary"]["row_count"] == 1
    row = audit["rows"][0]
    assert row["causal_status"] == "non_causal_feature_evidence"
    assert row["forced_piece_type"] == "king"
    assert row["king_moves_toward_black"] is True
    assert audit["decision"]["selector_training_allowed"] is False
