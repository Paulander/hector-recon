#!/usr/bin/env python3
"""Build context dataset from supplemented ownership labels."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_krk_ownership_selection_context_dataset_v0 as context_v0  # noqa: E402


OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v3.json")
OUT_JSON = Path("reports/krk_ownership_selection_context_dataset_v1.json")
OUT_MD = Path("reports/krk_ownership_selection_context_dataset_v1.md")


def build_dataset() -> dict:
    context_v0.ROOT = ROOT
    context_v0.OWNERSHIP = OWNERSHIP
    payload = context_v0.build_dataset()
    payload["schema_version"] = "krk_ownership_selection_context_dataset.v1"
    payload["source_artifacts"][0] = str(OWNERSHIP)
    payload["decision"]["recommended_next_step"] = "probe_supplemented_context_enriched_ownership_selection_features"
    return payload


def render_markdown(payload: dict) -> str:
    return context_v0.render_markdown(payload).replace(
        "# KRK Ownership Selection Context Dataset v0",
        "# KRK Ownership Selection Context Dataset v1",
        1,
    )


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
