#!/usr/bin/env python3
"""Add explicit non-causal provider provenance features to selector rows."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FEATURE_DATASET = Path("reports/krk_selector_feature_dataset_v0.json")
PROVIDER_REVIEW = Path("reports/krk_provider_identity_maturity_review_v0.json")
OUT_JSON = Path("reports/krk_selector_provenance_feature_dataset_v0.json")
OUT_MD = Path("reports/krk_selector_provenance_feature_dataset_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _provider_metadata(review: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for item in review.get("provider_summary", []) or []:
        provider_id = str(item.get("provider_id") or "")
        if provider_id:
            result[provider_id] = dict(item.get("metadata", {}) or {})
    return result


def build_dataset() -> dict[str, Any]:
    base = _load_json(FEATURE_DATASET)
    metadata_by_provider = _provider_metadata(_load_json(PROVIDER_REVIEW))
    rows = []
    for row in base.get("rows", []) or []:
        provider_id = str(row.get("provider_id") or "")
        metadata = metadata_by_provider.get(provider_id, {})
        enriched = dict(row)
        enriched.update({
            "schema_version": "krk_selector_provenance_feature_example.v0",
            "causal_status": "non_causal_provenance_feature_example",
            "provider_family": metadata.get("provider_family"),
            "provider_source_stage": metadata.get("source_stage"),
            "provider_maturity": metadata.get("provider_maturity"),
            "provider_validated_role": metadata.get("validated_role"),
            "protected_provider": metadata.get("protected_provider"),
            "overlay_provider": metadata.get("overlay_provider"),
            "provider_provenance_available": bool(metadata),
        })
        rows.append(enriched)
    training_rows = [row for row in rows if row.get("usable_for_training")]
    return {
        "schema_version": "krk_selector_provenance_feature_dataset.v0",
        "causal_status": "non_causal_provenance_feature_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifacts": [str(FEATURE_DATASET), str(PROVIDER_REVIEW)],
        "row_count": len(rows),
        "training_row_count": len(training_rows),
        "rows_with_provider_provenance": sum(
            1 for row in rows if row.get("provider_provenance_available")
        ),
        "stage7_training_rows": sum(
            1 for row in training_rows if row.get("source_stage") == "stage7"
        ),
        "label_counts": dict(sorted(Counter(str(row.get("label") or "none") for row in rows).items())),
        "provider_maturity_counts": dict(sorted(Counter(
            str(row.get("provider_maturity") or "unknown") for row in rows
        ).items())),
        "provider_family_counts": dict(sorted(Counter(
            str(row.get("provider_family") or "unknown") for row in rows
        ).items())),
        "rows": rows,
        "decision": {
            "status": "selector_provenance_feature_dataset_built",
            "runtime_arbiter_allowed": False,
            "sandbox_ready": False,
            "recommended_next_step": "probe_selector_provenance_features_non_causal",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Provenance Feature Dataset v0",
        "",
        "This replay-free dataset decomposes provider identity into explicit non-causal provenance and maturity fields.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Training rows: `{payload['training_row_count']}`",
        f"- Rows with provider provenance: `{payload['rows_with_provider_provenance']}`",
        f"- Stage7 training rows: `{payload['stage7_training_rows']}`",
        f"- Label counts: `{payload['label_counts']}`",
        f"- Provider maturity counts: `{payload['provider_maturity_counts']}`",
        f"- Provider family counts: `{payload['provider_family_counts']}`",
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        f"Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"Sandbox ready: `{payload['decision']['sandbox_ready']}`",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
    ]
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
