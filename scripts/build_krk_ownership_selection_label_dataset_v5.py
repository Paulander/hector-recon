#!/usr/bin/env python3
"""Merge targeted false-positive risk-cell labels into ownership v5."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP_V4 = Path("reports/krk_ownership_selection_label_dataset_v4.json")
TARGETED_NEGATIVE_LABELS = Path("reports/krk_targeted_ownership_negative_labels_v0.json")
OUT_JSON = Path("reports/krk_ownership_selection_label_dataset_v5.json")
OUT_MD = Path("reports/krk_ownership_selection_label_dataset_v5.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _provider_family(provider_id: str | None) -> str:
    text = str(provider_id or "")
    if text == "krk.stage0_basin":
        return "stage0_basin"
    if text == "krk.drive_to_edge":
        return "drive_to_edge"
    if text == "krk.fence_established":
        return "fence_established"
    if text.startswith("krk.edge_trap"):
        return "edge_trap"
    return "other"


def _row_from_label(label: dict[str, Any]) -> dict[str, Any]:
    provider_id = str(label.get("selected_provider") or "")
    result = (label.get("selected_playout_success") or {}).get("result")
    converted = result == "mate"
    return {
        "schema_version": "krk_ownership_selection_label.v5",
        "causal_status": "non_causal_ownership_label",
        "objective_id": "krk.selector.ownership_selection.v0",
        "objective_channel": "ownership_selection",
        "state_id": label.get("state_id"),
        "frame_id": label.get("frame_id"),
        "source_stage": label.get("source_stage"),
        "active_landmark_label": label.get("active_landmark_label"),
        "provider_id": provider_id,
        "provider_family": _provider_family(provider_id),
        "move_uci": label.get("selected_move"),
        "target_label": "selected_owner_converted" if converted else "selected_owner_failed",
        "owner_positive": converted,
        "selected_provider_before_observation": provider_id,
        "selected_provider_matches_target": True,
        "target_provider_best_rank": 1,
        "target_provider_best_raw_score": None,
        "target_provider_summary_count": None,
        "unique_provider_count": label.get("initial_provider_count"),
        "all_suggestion_count": None,
        "source_terms": [],
        "source_term_count": 0,
        "label_source": "targeted_false_positive_risk_cell_h40",
        "label_semantics": label.get("label_semantics"),
        "target_cell_id": label.get("target_cell_id"),
        "target_cell_reason": label.get("target_cell_reason"),
        "selected_playout_success": label.get("selected_playout_success"),
        "forced_provider_conversion_for_selected_provider": label.get(
            "forced_provider_conversion_for_selected_provider"
        ),
        "usable_for_offline_probe": True,
        "usable_for_selector_training": False,
        "training_block_reason": "ownership labels remain offline evidence pending readiness review",
        "stage7_training_row": False,
    }


def build_dataset() -> dict[str, Any]:
    base = _load(OWNERSHIP_V4)
    labels_payload = _load(TARGETED_NEGATIVE_LABELS)
    if base.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership v4 must remain non-causal")
    if labels_payload.get("causal_status") != "non_causal_label_run":
        raise ValueError("targeted labels must remain non-causal")

    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {
        (str(row.get("state_id")), str(row.get("provider_id"))): {
            **row,
            "schema_version": "krk_ownership_selection_label.v5",
            "usable_for_selector_training": False,
        }
        for row in base.get("rows") or []
        if row.get("source_stage") != "stage7"
    }
    added = []
    for label in labels_payload.get("labels") or []:
        if label.get("source_stage") == "stage7":
            continue
        row = _row_from_label(label)
        key = (str(row.get("state_id")), str(row.get("provider_id")))
        if key in rows_by_key:
            continue
        rows_by_key[key] = row
        added.append(row)

    rows = [rows_by_key[key] for key in sorted(rows_by_key)]
    summary = {
        "input_v4_row_count": len(base.get("rows") or []),
        "targeted_label_count": len(labels_payload.get("labels") or []),
        "targeted_added_row_count": len(added),
        "targeted_added_label_counts": dict(Counter(str(row.get("target_label")) for row in added)),
        "merged_row_count": len(rows),
        "target_label_counts": dict(Counter(str(row.get("target_label")) for row in rows)),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
        "label_source_counts": dict(Counter(str(row.get("label_source")) for row in rows)),
        "state_count": len({row.get("state_id") for row in rows}),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
    }
    payload = {
        "schema_version": "krk_ownership_selection_label_dataset.v5",
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
        "source_artifacts": [str(OWNERSHIP_V4), str(TARGETED_NEGATIVE_LABELS)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "ownership_selection_labels_expanded_with_targeted_false_positive_risk_cells",
            "recommended_next_step": "rerun_context_enriched_probe_with_targeted_negative_labels",
            "runtime_work_allowed": False,
            "selector_training_allowed": False,
            "stage7_promotion_allowed": False,
            "stage8_training_allowed": False,
        },
    }
    validate_dataset(payload)
    return payload


def validate_dataset(payload: dict[str, Any]) -> None:
    if payload.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("dataset must remain non-causal")
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


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Ownership Selection Label Dataset v5",
        "",
        "Adds targeted current-profile h40 labels from false-positive ownership risk cells. "
        "These remain non-causal offline evidence.",
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
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (ROOT / OUT_MD).write_text(render_markdown(payload), encoding="utf-8")
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
