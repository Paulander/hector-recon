#!/usr/bin/env python3
"""Build a replay-free balanced selector label dataset from controls."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
POSITIVES = Path("reports/krk_selector_stratified_label_dataset_v1.json")
NEGATIVES = Path("reports/krk_selector_negative_control_manifest_v1.json")
PROVENANCE = Path("reports/krk_selector_provenance_feature_dataset_v0.json")
OUT_JSON = Path("reports/krk_selector_balanced_label_dataset_v1.json")
OUT_MD = Path("reports/krk_selector_balanced_label_dataset_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _provenance_index() -> dict[tuple[str, str | None], dict[str, Any]]:
    rows = _load_json(PROVENANCE).get("rows", []) or []
    result: dict[tuple[str, str | None], dict[str, Any]] = {}
    for row in rows:
        if row.get("provider_id"):
            result.setdefault((str(row.get("state_id")), row.get("provider_id")), row)
    return result


def build_dataset() -> dict[str, Any]:
    positives = [
        row for row in _load_json(POSITIVES).get("rows", []) or []
        if row.get("label") == "positive"
    ]
    negatives = _load_json(NEGATIVES).get("controls", []) or []
    provenance = _provenance_index()
    target_count = min(len(positives), len(negatives))
    rows = []
    for source, label_rows in [("positive_guardrail_controls", positives[:target_count]), ("negative_selected_controls", negatives[:target_count])]:
        for row in label_rows:
            context = provenance.get((str(row.get("state_id")), row.get("provider_id")), {})
            rows.append({
                "schema_version": "krk_selector_balanced_label_example.v1",
                "causal_status": "non_causal_balanced_label_example",
                "state_id": row.get("state_id"),
                "frame_id": row.get("frame_id") or context.get("frame_id"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label") or context.get("active_landmark_label"),
                "provider_id": row.get("provider_id"),
                "provider_family": row.get("provider_family") or context.get("provider_family"),
                "provider_maturity": row.get("provider_maturity") or context.get("provider_maturity"),
                "provider_source_stage": context.get("provider_source_stage"),
                "provider_validated_role": context.get("provider_validated_role"),
                "move_uci": row.get("move_uci") or context.get("move_uci"),
                "target_kind": row.get("target_kind"),
                "label": row.get("label"),
                "label_source": row.get("label_source"),
                "source_bucket": source,
                "stage7_training_row": False,
            })
    label_counts = Counter(str(row.get("label") or "none") for row in rows)
    stage_counts = Counter(str(row.get("source_stage") or "unknown") for row in rows)
    return {
        "schema_version": "krk_selector_balanced_label_dataset.v1",
        "causal_status": "non_causal_balanced_label_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifacts": [str(POSITIVES), str(NEGATIVES), str(PROVENANCE)],
        "row_count": len(rows),
        "label_counts": dict(sorted(label_counts.items())),
        "stage_counts": dict(sorted(stage_counts.items())),
        "stage7_training_rows": 0,
        "rows": rows,
        "decision": {
            "status": "balanced_selector_label_dataset_built_replay_free",
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": "probe_balanced_selector_labels_non_causal",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Balanced Label Dataset v1",
        "",
        "This replay-free dataset balances guardrail-positive protected controls with negative selected-playout controls.",
        "",
        "## Summary",
        "",
        f"- Rows: `{payload['row_count']}`",
        f"- Label counts: `{payload['label_counts']}`",
        f"- Stage counts: `{payload['stage_counts']}`",
        f"- Stage7 training rows: `{payload['stage7_training_rows']}`",
        f"- Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        f"- Selector sandbox ready: `{payload['decision']['selector_sandbox_ready']}`",
    ]
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
