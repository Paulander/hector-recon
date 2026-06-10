from __future__ import annotations

import importlib.util
import json
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "review_krk_hard_negative_selector_target_training_semantics_v0.py"
)
SPEC = importlib.util.spec_from_file_location(
    "review_krk_hard_negative_selector_target_training_semantics_v0",
    SCRIPT,
)
assert SPEC is not None
assert SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _write_json(root: Path, relative: Path, payload: dict) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_hard_negative_training_semantics_only_allows_offline_benchmark(tmp_path, monkeypatch):
    root = tmp_path
    monkeypatch.setattr(module, "ROOT", root)
    _write_json(
        root,
        module.TARGETS,
        {
            "causal_status": "non_causal_target_dataset",
            "summary": {
                "row_count": 2,
                "target_kind_counts": {
                    "hard_negative_capacity": 1,
                    "positive_capacity_context": 1,
                },
                "stage7_row_count": 0,
                "training_row_count": 0,
            },
        },
    )
    _write_json(root, module.DIRECTED_REVIEW, {"causal_status": "non_causal_architecture_review"})

    review = module.build_review()

    assert review["schema_version"] == "krk_hard_negative_selector_target_training_semantics_review.v0"
    assert review["causal_status"] == "non_causal_semantics_review"
    assert review["runtime_selector_implemented"] is False
    assert review["runtime_behavior_changed"] is False
    assert review["stage7_promotion_allowed"] is False
    assert review["stage8_training_allowed"] is False
    assert review["decision"]["offline_benchmark_allowed"] is True
    assert review["decision"]["selector_training_allowed"] is False
    assert review["decision"]["runtime_work_allowed"] is False
