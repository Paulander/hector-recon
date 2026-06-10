#!/usr/bin/env python3
"""Run second expanded offline hard-negative selector feature ablation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_krk_hard_negative_selector_feature_ablation_v1.py"
SPEC = importlib.util.spec_from_file_location("_ablation_v1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

module.TARGETS = Path("reports/krk_hard_negative_selector_target_dataset_v2.json")
module.OUT_JSON = Path("reports/krk_hard_negative_selector_feature_ablation_v2.json")
module.OUT_MD = Path("reports/krk_hard_negative_selector_feature_ablation_v2.md")


def main() -> None:
    payload = module.build_ablation()
    payload["schema_version"] = "krk_hard_negative_selector_feature_ablation.v2"
    if payload["decision"]["status"] == "hard_negative_feature_ablation_still_not_runtime_ready":
        payload["decision"]["recommended_next_step"] = (
            "review_label_semantics_or_design_stronger_selector_features_before_more_label_jobs"
        )
    (ROOT / module.OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / module.OUT_MD).write_text(module.render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
