from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "audit_krk_selector_negative_suppression_evidence_v0.py"
)
SPEC = importlib.util.spec_from_file_location("audit_krk_selector_negative_suppression_evidence_v0", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_selector_negative_suppression_audit_stays_non_causal(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(module, "ROOT", root)
    _write_json(
        root,
        module.CONTRAST,
        {
            "causal_status": "non_causal_state_local_contrast_dataset",
            "rows": [
                {
                    "state_id": "s1",
                    "source_stage": "stage5",
                    "provider_id": "krk.stage0_basin",
                    "provider_family": "stage0_basin",
                    "provider_maturity": "foundation_frozen",
                    "global_raw_score_rank": 1,
                    "provider_local_rank": 1,
                    "normalized_score": 1.0,
                    "contrast_label": "positive",
                    "forced_result": "mate",
                    "forced_plies": 3,
                    "usable_for_training": True,
                    "stage7_challenge_row": False,
                },
                {
                    "state_id": "s2",
                    "source_stage": "stage6",
                    "provider_id": "krk.edge_trap_close",
                    "provider_family": "edge_trap",
                    "provider_maturity": "validated_low_plasticity",
                    "global_raw_score_rank": 1,
                    "provider_local_rank": 1,
                    "normalized_score": 1.0,
                    "contrast_label": "negative",
                    "forced_result": "max_plies",
                    "forced_plies": 40,
                    "usable_for_training": True,
                    "stage7_challenge_row": False,
                },
            ],
        },
    )
    _write_json(root, module.PROBE, {"causal_status": "non_causal_offline_probe"})
    _write_json(
        root,
        module.CAPACITY_FRAMES,
        {
            "causal_status": "non_causal_capacity_frame_dataset",
            "rows": [
                {
                    "state_id": "s3",
                    "source_stage": "stage4",
                    "provider_id": "krk.edge_trap_close",
                    "provider_family": "edge_trap",
                    "capacity_label": "negative_capacity",
                    "forced_first_move": "a1a2",
                    "forced_plies": 40,
                    "existing_frame_providers": ["krk.stage0_basin"],
                }
            ],
        },
    )
    _write_json(root, module.TWO_STAGE, {"causal_status": "non_causal_benchmark"})

    audit = module.build_audit()

    assert audit["schema_version"] == "krk_selector_negative_suppression_evidence.v0"
    assert audit["causal_status"] == "non_causal_evidence_audit"
    assert audit["runtime_behavior_changed"] is False
    assert audit["runtime_selector_implemented"] is False
    assert audit["runtime_candidate_generator_implemented"] is False
    assert audit["stage7_promotion_allowed"] is False
    assert audit["stage8_training_allowed"] is False
    assert audit["label_balance"]["training_negative_count"] == 1
    assert audit["label_balance"]["capacity_negative_count"] == 1
    assert audit["decision"]["selector_training_allowed"] is False
