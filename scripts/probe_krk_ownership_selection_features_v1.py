#!/usr/bin/env python3
"""Probe expanded ownership-selection labels non-causally."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import probe_krk_ownership_selection_features_v0 as probe_v0  # noqa: E402


OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v1.json")
OUT_JSON = Path("reports/krk_ownership_selection_feature_probe_v1.json")
OUT_MD = Path("reports/krk_ownership_selection_feature_probe_v1.md")


def build_probe() -> dict:
    probe_v0.ROOT = ROOT
    probe_v0.OWNERSHIP = OWNERSHIP
    payload = probe_v0.build_probe()
    payload["schema_version"] = "krk_ownership_selection_feature_probe.v1"
    payload["source_artifacts"] = [str(OWNERSHIP)]
    payload["decision"]["recommended_next_step"] = "review_split_objective_readiness_with_expanded_ownership_labels"
    return payload


def render_markdown(payload: dict) -> str:
    text = probe_v0.render_markdown(payload)
    return text.replace(
        "# KRK Ownership Selection Feature Probe v0",
        "# KRK Ownership Selection Feature Probe v1",
        1,
    ).replace(
        "recovered normal-routing ownership-selection labels",
        "expanded normal-routing ownership-selection labels",
        1,
    )


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
