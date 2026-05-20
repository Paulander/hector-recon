from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "summarize_krk_selector_directed_fix_review_v0.py"
SPEC = importlib.util.spec_from_file_location("summarize_krk_selector_directed_fix_review_v0", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_selector_directed_fix_review_blocks_runtime_paths(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(module, "ROOT", root)
    _write_json(
        root,
        module.TWO_STAGE,
        {
            "causal_status": "non_causal_benchmark",
            "candidate_generation_track": {
                "current_runtime_proposal_frames": {"positive_capacity_recall_rate": 0.0},
                "validated_provider_candidate_set_expansion": {
                    "positive_capacity_recall_rate": 1.0,
                    "negative_capacity_inclusion_rate": 1.0,
                },
            },
        },
    )
    _write_json(
        root,
        module.NEGATIVE,
        {
            "causal_status": "non_causal_evidence_audit",
            "label_balance": {
                "training_positive_count": 2,
                "training_negative_count": 1,
                "training_negative_state_count": 1,
            },
            "leave_state_out_best_objective_replay": {"negative_suppression": 0.0},
        },
    )
    _write_json(
        root,
        module.GEOMETRY,
        {
            "causal_status": "non_causal_feature_probe",
            "summary": {"underpowered": True},
            "best_result": {"objective": "provider_family", "negative_suppression": 0.0},
        },
    )
    _write_json(root, module.CANDIDATE_SET, {"causal_status": "non_causal_candidate_set_audit"})
    _write_json(root, module.CAPACITY_SEMANTICS, {"causal_status": "non_causal_semantics_review"})

    review = module.build_review()

    assert review["schema_version"] == "krk_selector_directed_fix_review.v0"
    assert review["causal_status"] == "non_causal_architecture_review"
    assert review["runtime_behavior_changed"] is False
    assert review["runtime_selector_implemented"] is False
    assert review["runtime_candidate_generator_implemented"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert "runtime_selector_now" in {item["fix"] for item in review["rejected_fixes"]}
    assert review["recommended_fix_class"]["name"] == "non_causal_hard_negative_selector_target_design"
    assert review["decision"]["selector_training_allowed"] is False
