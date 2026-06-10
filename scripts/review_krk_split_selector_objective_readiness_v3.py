#!/usr/bin/env python3
"""Review split selector readiness with twice-expanded ownership labels."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import review_krk_split_selector_objective_readiness_v1 as readiness_v1  # noqa: E402


SPLIT = Path("reports/krk_split_selector_objective_dataset_v3.json")
OWNERSHIP_PROBE = Path("reports/krk_ownership_selection_feature_probe_v2.json")
OUT_JSON = Path("reports/krk_split_selector_objective_readiness_v3.json")
OUT_MD = Path("reports/krk_split_selector_objective_readiness_v3.md")


def build_review() -> dict:
    readiness_v1.ROOT = ROOT
    readiness_v1.SPLIT = SPLIT
    readiness_v1.OWNERSHIP_PROBE = OWNERSHIP_PROBE
    payload = readiness_v1.build_review()
    payload["schema_version"] = "krk_split_selector_objective_readiness.v3"
    payload["source_artifacts"] = [
        str(SPLIT),
        str(OWNERSHIP_PROBE),
        str(readiness_v1.CAPACITY_FEATURE_REVIEW),
    ]
    return payload


def render_markdown(payload: dict) -> str:
    return readiness_v1.render_markdown(payload).replace(
        "# KRK Split Selector Objective Readiness v1",
        "# KRK Split Selector Objective Readiness v3",
        1,
    )


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
