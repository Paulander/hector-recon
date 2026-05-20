#!/usr/bin/env python3
"""Build split selector objective dataset with twice-expanded ownership labels."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_krk_split_selector_objective_dataset_v1 as split_v1  # noqa: E402


OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v2.json")
OUT_JSON = Path("reports/krk_split_selector_objective_dataset_v3.json")
OUT_MD = Path("reports/krk_split_selector_objective_dataset_v3.md")


def build_dataset() -> dict:
    split_v1.ROOT = ROOT
    split_v1.OWNERSHIP = OWNERSHIP
    payload = split_v1.build_dataset()
    payload["schema_version"] = "krk_split_selector_objective_dataset.v3"
    payload["source_artifacts"] = [str(split_v1.SPLIT_V0), str(OWNERSHIP)]
    payload["decision"]["recommended_next_step"] = "probe_twice_expanded_ownership_selection_features_non_causal"
    return payload


def render_markdown(payload: dict) -> str:
    return split_v1.render_markdown(payload).replace(
        "# KRK Split Selector Objective Dataset v1",
        "# KRK Split Selector Objective Dataset v3",
        1,
    )


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
