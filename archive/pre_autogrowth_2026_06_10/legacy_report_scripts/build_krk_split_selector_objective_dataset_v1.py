#!/usr/bin/env python3
"""Build split selector objective dataset with recovered ownership labels."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SPLIT_V0 = Path("reports/krk_split_selector_objective_dataset_v0.json")
OWNERSHIP = Path("reports/krk_ownership_selection_label_dataset_v0.json")
OUT_JSON = Path("reports/krk_split_selector_objective_dataset_v1.json")
OUT_MD = Path("reports/krk_split_selector_objective_dataset_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _ownership_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in payload.get("rows") or []:
        rows.append(
            {
                **row,
                "schema_version": "krk_split_selector_objective_row.v1",
                "causal_status": "non_causal_objective_row",
                "objective_id": "krk.selector.ownership_selection.v0",
                "objective_channel": "ownership_selection",
                "source_target_kind": "selected_playout_success",
                "usable_for_offline_probe": True,
                "usable_for_selector_training": False,
                "training_block_reason": "ownership labels are now available for offline probe; training still requires readiness review",
            }
        )
    return rows


def build_dataset() -> dict[str, Any]:
    split_v0 = _load(SPLIT_V0)
    ownership = _load(OWNERSHIP)
    if split_v0.get("causal_status") != "non_causal_split_objective_dataset":
        raise ValueError("split v0 must remain non-causal")
    if ownership.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership labels must remain non-causal")
    base_rows = [
        {**row, "schema_version": "krk_split_selector_objective_row.v1"}
        for row in split_v0.get("rows") or []
        if row.get("objective_channel") != "ownership_selection"
    ]
    rows = base_rows + _ownership_rows(ownership)
    summary = {
        "objective_row_count": len(rows),
        "objective_channel_counts": dict(Counter(str(row.get("objective_channel")) for row in rows)),
        "target_label_counts": dict(Counter(str(row.get("target_label")) for row in rows)),
        "offline_probe_row_count": sum(1 for row in rows if row.get("usable_for_offline_probe")),
        "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "ownership_selection_available": any(
            row.get("objective_channel") == "ownership_selection" and row.get("usable_for_offline_probe")
            for row in rows
        ),
        "ownership_selection_row_count": sum(1 for row in rows if row.get("objective_channel") == "ownership_selection"),
    }
    payload = {
        "schema_version": "krk_split_selector_objective_dataset.v1",
        "causal_status": "non_causal_split_objective_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(SPLIT_V0), str(OWNERSHIP)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "split_selector_objective_channels_with_ownership_labels",
            "recommended_next_step": "probe_ownership_selection_features_non_causal",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_dataset(payload)
    return payload


def validate_dataset(payload: dict[str, Any]) -> None:
    for key in (
        "runtime_behavior_changed",
        "runtime_defaults_changed",
        "runtime_selector_implemented",
        "runtime_candidate_generator_implemented",
        "runtime_terminals_added",
        "runtime_dtm_or_tablebase_lookup",
        "gameplay_topology_mutation",
        "stage7_promotion_allowed",
        "stage8_training_allowed",
    ):
        if payload.get(key) is not False:
            raise ValueError(f"{key} must be false")
    if payload["summary"]["stage7_row_count"] != 0:
        raise ValueError("Stage 7 rows must remain excluded")
    if payload["summary"]["selector_training_row_count"] != 0:
        raise ValueError("selector training remains blocked")
    if not payload["summary"]["ownership_selection_available"]:
        raise ValueError("ownership selection labels should be present in v1")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Split Selector Objective Dataset v1",
        "",
        "Adds recovered normal-routing ownership-selection labels to the split objective channels.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
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
