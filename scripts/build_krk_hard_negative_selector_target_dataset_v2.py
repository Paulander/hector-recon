#!/usr/bin/env python3
"""Build second expanded non-causal hard-negative selector targets."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_krk_hard_negative_selector_target_dataset_v1.py"
SPEC = importlib.util.spec_from_file_location("_target_dataset_v1", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

module.TARGETS_V0 = Path("reports/krk_hard_negative_selector_target_dataset_v1.json")
module.BALANCED_LABELS = Path("reports/krk_balanced_hard_negative_labels_v1.json")
module.OUT_JSON = Path("reports/krk_hard_negative_selector_target_dataset_v2.json")
module.OUT_MD = Path("reports/krk_hard_negative_selector_target_dataset_v2.md")


def main() -> None:
    payload = module.build_dataset()
    payload["schema_version"] = "krk_hard_negative_selector_target_dataset.v2"
    payload["decision"]["status"] = "hard_negative_selector_target_dataset_expanded_v2"
    payload["decision"]["recommended_next_step"] = "run_hard_negative_selector_feature_ablation_v2"
    (ROOT / module.OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / module.OUT_MD).write_text(module.render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
