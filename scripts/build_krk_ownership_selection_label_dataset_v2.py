#!/usr/bin/env python3
"""Merge all recovered and diversity-run ownership-selection labels."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_krk_ownership_selection_label_dataset_v1 as ownership_v1  # noqa: E402


OWNERSHIP_V1 = Path("reports/krk_ownership_selection_label_dataset_v1.json")
DIVERSITY_LABELS_V1 = Path("reports/krk_selected_provider_diversity_ownership_labels_v1.json")
OUT_JSON = Path("reports/krk_ownership_selection_label_dataset_v2.json")
OUT_MD = Path("reports/krk_ownership_selection_label_dataset_v2.md")


def build_dataset() -> dict[str, Any]:
    base = json.loads((ROOT / OWNERSHIP_V1).read_text(encoding="utf-8"))
    diversity = json.loads((ROOT / DIVERSITY_LABELS_V1).read_text(encoding="utf-8"))
    if base.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership v1 must remain non-causal")
    if diversity.get("causal_status") != "non_causal_label_run":
        raise ValueError("diversity labels v1 must remain non-causal")

    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    input_rows = list(base.get("rows") or []) + [
        ownership_v1._row_from_diversity_label(label) | {"label_source": "selected_provider_diversity_fresh_seed_normal_routing_h40"}
        for label in diversity.get("labels") or []
    ]
    for row in input_rows:
        if row.get("source_stage") == "stage7":
            continue
        row = {**row, "schema_version": "krk_ownership_selection_label.v2", "usable_for_selector_training": False}
        key = (str(row.get("state_id")), str(row.get("provider_id")))
        existing = rows_by_key.get(key)
        if existing and existing.get("target_label") != row.get("target_label"):
            conflicts.append({"key": list(key), "existing": existing.get("target_label"), "new": row.get("target_label")})
            continue
        rows_by_key.setdefault(key, row)

    rows = [rows_by_key[key] for key in sorted(rows_by_key)]
    summary = {
        "input_v1_row_count": len(base.get("rows") or []),
        "input_fresh_seed_label_count": len(diversity.get("labels") or []),
        "merged_row_count": len(rows),
        "conflict_count": len(conflicts),
        "target_label_counts": dict(Counter(str(row.get("target_label")) for row in rows)),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
        "label_source_counts": dict(Counter(str(row.get("label_source")) for row in rows)),
        "state_count": len({row.get("state_id") for row in rows}),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
    }
    payload = {
        "schema_version": "krk_ownership_selection_label_dataset.v2",
        "causal_status": "non_causal_ownership_label_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(OWNERSHIP_V1), str(DIVERSITY_LABELS_V1)],
        "summary": summary,
        "conflicts": conflicts,
        "rows": rows,
        "decision": {
            "status": "ownership_selection_labels_expanded_with_second_diversity_slice",
            "recommended_next_step": "rerun_ownership_selection_feature_probe",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    ownership_v1.validate_dataset(payload)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Ownership Selection Label Dataset v2",
        "",
        "Merges recovered ownership labels with two bounded selected-provider diversity h40 label slices.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    if payload["conflicts"]:
        lines.extend(["", "## Conflicts", ""])
        for conflict in payload["conflicts"]:
            lines.append(f"- `{conflict}`")
    lines.extend(["", "## Decision", ""])
    for key, value in payload["decision"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    payload = build_dataset()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
