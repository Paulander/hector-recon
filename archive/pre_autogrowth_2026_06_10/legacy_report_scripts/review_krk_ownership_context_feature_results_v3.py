#!/usr/bin/env python3
"""Review targeted-negative-expanded ownership context probe."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import review_krk_ownership_context_feature_results_v0 as review_v0  # noqa: E402


CONTEXT_DATASET = Path("reports/krk_ownership_selection_context_dataset_v3.json")
CONTEXT_PROBE = Path("reports/krk_ownership_selection_context_feature_probe_v3.json")
BASE_PROBE = Path("reports/krk_ownership_selection_context_feature_probe_v2.json")
TARGETED_LABELS = Path("reports/krk_targeted_ownership_negative_labels_v0.json")
OUT_JSON = Path("reports/krk_ownership_context_feature_review_v3.json")
OUT_MD = Path("reports/krk_ownership_context_feature_review_v3.md")


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
    labels = _load(TARGETED_LABELS)
    payload["schema_version"] = "krk_ownership_context_feature_review.v3"
    payload["source_artifacts"] = [
        str(CONTEXT_DATASET),
        str(CONTEXT_PROBE),
        str(BASE_PROBE),
        str(TARGETED_LABELS),
    ]
    payload["summary"]["targeted_negative_label_count"] = (labels.get("summary") or {}).get(
        "label_count"
    )
    payload["summary"]["targeted_negative_failure_count"] = (labels.get("summary") or {}).get(
        "targeted_owner_failed_count"
    )
    if payload["summary"].get("context_best_balanced_negative_suppression", 0) >= 0.6:
        payload["interpretation"].append(
            "Targeted false-positive risk-cell labels improved balanced negative suppression "
            "to a reviewable level, but selector training remains blocked pending architecture review."
        )
    else:
        payload["interpretation"].append(
            "Targeted false-positive risk-cell labels added true negatives but did not clear "
            "the balanced runtime-review threshold."
        )
    payload["decision"]["recommended_next_step"] = (
        "architecture_review_before_any_selector_runtime_or_collect_more_targeted_negatives"
    )
    return payload


def render_markdown(payload: dict) -> str:
    return review_v0.render_markdown(payload).replace(
        "# KRK Ownership Context Feature Review v0",
        "# KRK Ownership Context Feature Review v3",
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
