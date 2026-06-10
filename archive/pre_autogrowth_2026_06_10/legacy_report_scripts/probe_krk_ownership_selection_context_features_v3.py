#!/usr/bin/env python3
"""Probe targeted-negative-expanded context ownership labels."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import probe_krk_ownership_selection_context_features_v0 as probe_v0  # noqa: E402


DATASET = Path("reports/krk_ownership_selection_context_dataset_v3.json")
OUT_JSON = Path("reports/krk_ownership_selection_context_feature_probe_v3.json")
OUT_MD = Path("reports/krk_ownership_selection_context_feature_probe_v3.md")


def build_probe() -> dict:
    probe_v0.ROOT = ROOT
    probe_v0.DATASET = DATASET
    payload = probe_v0.build_probe()
    payload["schema_version"] = "krk_ownership_selection_context_feature_probe.v3"
    payload["source_artifacts"] = [str(DATASET)]
    return payload


def render_markdown(payload: dict) -> str:
    return probe_v0.render_markdown(payload).replace(
        "# KRK Ownership Selection Context Feature Probe v0",
        "# KRK Ownership Selection Context Feature Probe v3",
        1,
    )


def main() -> None:
    payload = build_probe()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
