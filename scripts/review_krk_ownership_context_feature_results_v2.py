#!/usr/bin/env python3
"""Review targeted-refreshed context-enriched ownership probe results."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import review_krk_ownership_context_feature_results_v0 as review_v0  # noqa: E402


CONTEXT_DATASET = Path("reports/krk_ownership_selection_context_dataset_v2.json")
CONTEXT_PROBE = Path("reports/krk_ownership_selection_context_feature_probe_v2.json")
BASE_PROBE = Path("reports/krk_ownership_selection_context_feature_probe_v1.json")
TARGETED_REVIEW = Path("reports/krk_targeted_non_stage0_ownership_review_v0.json")
OUT_JSON = Path("reports/krk_ownership_context_feature_review_v2.json")
OUT_MD = Path("reports/krk_ownership_context_feature_review_v2.md")


def _load(path: Path) -> dict:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_review() -> dict:
    review_v0.ROOT = ROOT
    review_v0.CONTEXT_DATASET = CONTEXT_DATASET
    review_v0.CONTEXT_PROBE = CONTEXT_PROBE
    review_v0.BASE_PROBE = BASE_PROBE
    payload = review_v0.build_review()
    targeted = _load(TARGETED_REVIEW)
    payload["schema_version"] = "krk_ownership_context_feature_review.v2"
    payload["source_artifacts"] = [
        str(CONTEXT_DATASET),
        str(CONTEXT_PROBE),
        str(BASE_PROBE),
        str(TARGETED_REVIEW),
    ]
    payload["summary"]["targeted_non_stage0_status"] = targeted.get("decision", {}).get("status")
    payload["summary"]["targeted_preserved_count"] = (
        targeted.get("summary") or {}
    ).get("preserved_historical_non_stage0_count")
    payload["interpretation"].append(
        "Targeted current-profile replay preserved four historical non-stage0 owners, "
        "so source diversity is recoverable. However, the refreshed labels reduce "
        "unsafe-owner examples, keeping selector training blocked until more true "
        "ownership negatives are recovered."
    )
    payload["decision"]["recommended_next_step"] = (
        "recover_more_true_ownership_negative_labels_or_review_profile_dominance_before_runtime"
    )
    return payload


def render_markdown(payload: dict) -> str:
    return review_v0.render_markdown(payload).replace(
        "# KRK Ownership Context Feature Review v0",
        "# KRK Ownership Context Feature Review v2",
        1,
    )


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
