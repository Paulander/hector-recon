#!/usr/bin/env python3
"""Probe abstention v1 labels with selected-playout evidence included."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import probe_krk_abstention_training_dataset_v0 as probe_v0  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/krk_abstention_training_dataset_v1.json")
OUT_JSON = Path("reports/krk_abstention_training_probe_v1.json")
OUT_MD = Path("reports/krk_abstention_training_probe_v1.md")


def build_probe() -> dict:
    original = probe_v0.DATASET
    try:
        probe_v0.DATASET = DATASET
        payload = probe_v0.build_probe()
    finally:
        probe_v0.DATASET = original
    payload["schema_version"] = "krk_abstention_training_probe.v1"
    payload["source_artifact"] = str(DATASET)
    payload["decision"]["recommended_next_step"] = (
        "architecture_review_before_runtime_selector"
        if payload["decision"]["status"] == "abstention_signal_runtime_review_ready"
        else "collect_more_or_better_protected_negative_controls_before_runtime_review"
    )
    return payload


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(probe_v0.render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
