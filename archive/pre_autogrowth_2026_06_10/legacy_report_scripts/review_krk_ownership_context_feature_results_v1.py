#!/usr/bin/env python3
"""Review supplemented context-enriched ownership-selection probe results."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import review_krk_ownership_context_feature_results_v0 as review_v0  # noqa: E402


CONTEXT_DATASET = Path("reports/krk_ownership_selection_context_dataset_v1.json")
CONTEXT_PROBE = Path("reports/krk_ownership_selection_context_feature_probe_v1.json")
BASE_PROBE = Path("reports/krk_ownership_selection_feature_probe_v2.json")
OUT_JSON = Path("reports/krk_ownership_context_feature_review_v1.json")
OUT_MD = Path("reports/krk_ownership_context_feature_review_v1.md")


def build_review() -> dict:
    review_v0.ROOT = ROOT
    review_v0.CONTEXT_DATASET = CONTEXT_DATASET
    review_v0.CONTEXT_PROBE = CONTEXT_PROBE
    review_v0.BASE_PROBE = BASE_PROBE
    payload = review_v0.build_review()
    payload["schema_version"] = "krk_ownership_context_feature_review.v1"
    payload["source_artifacts"] = [str(CONTEXT_DATASET), str(CONTEXT_PROBE), str(BASE_PROBE)]
    if payload["summary"]["context_best_balanced_negative_suppression"] >= 0.5:
        payload["interpretation"].append(
            "Supplemental selected-provider-group recovery improved balanced negative suppression to 0.5, but the result is still below the 0.6 runtime-review threshold."
        )
    return payload


def render_markdown(payload: dict) -> str:
    return review_v0.render_markdown(payload).replace(
        "# KRK Ownership Context Feature Review v0",
        "# KRK Ownership Context Feature Review v1",
        1,
    )


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
