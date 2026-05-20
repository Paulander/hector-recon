#!/usr/bin/env python3
"""Recover non-causal ownership-selection labels from normal selected-playout evidence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SELECTOR_FEATURES = Path("reports/krk_selector_feature_dataset_v0.json")
SPLIT_READINESS = Path("reports/krk_split_selector_objective_readiness_v0.json")
OUT_JSON = Path("reports/krk_ownership_selection_label_dataset_v0.json")
OUT_MD = Path("reports/krk_ownership_selection_label_dataset_v0.md")


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
    if text.startswith("krk.box_shrink"):
        return "box_shrink"
    return "other"


def _owner_label(row: dict[str, Any]) -> str | None:
    if row.get("label") == "positive":
        return "selected_owner_converted"
    if row.get("label") == "negative":
        return "selected_owner_failed"
    return None


def _best_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row.get("state_id")), str(row.get("provider_id")))
        grouped.setdefault(key, []).append(row)
    out = []
    for (_state_id, _provider), candidates in sorted(grouped.items()):
        labels = {row.get("label") for row in candidates}
        if len(labels) > 1:
            # Do not invent a target if artifacts disagree.
            continue
        out.append(
            sorted(
                candidates,
                key=lambda item: (
                    int(item.get("target_provider_best_rank") or 999),
                    -float(item.get("target_provider_best_raw_score") or 0.0),
                    str(item.get("move_uci") or ""),
                ),
            )[0]
        )
    return out


def build_dataset() -> dict[str, Any]:
    features = _load(SELECTOR_FEATURES)
    readiness = _load(SPLIT_READINESS)
    if features.get("causal_status") != "non_causal_feature_dataset":
        raise ValueError("selector feature dataset must remain non-causal")
    if readiness.get("causal_status") != "non_causal_readiness_review":
        raise ValueError("split readiness must remain non-causal")
    candidates = [
        row
        for row in features.get("rows") or []
        if row.get("target_kind") == "selected_playout_success"
        and row.get("usable_for_training") is True
        and row.get("source_stage") != "stage7"
        and row.get("selected_provider_matches_target") is True
        and _owner_label(row) is not None
    ]
    rows = []
    for row in _best_rows(candidates):
        provider_id = str(row.get("provider_id") or "")
        rows.append(
            {
                "schema_version": "krk_ownership_selection_label.v0",
                "causal_status": "non_causal_ownership_label",
                "objective_id": "krk.selector.ownership_selection.v0",
                "objective_channel": "ownership_selection",
                "state_id": row.get("state_id"),
                "frame_id": row.get("frame_id"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "provider_id": provider_id,
                "provider_family": _provider_family(provider_id),
                "move_uci": row.get("move_uci"),
                "target_label": _owner_label(row),
                "owner_positive": row.get("label") == "positive",
                "selected_provider_before_observation": row.get("selected_provider_before_observation"),
                "selected_provider_matches_target": row.get("selected_provider_matches_target"),
                "target_provider_best_rank": row.get("target_provider_best_rank"),
                "target_provider_best_raw_score": row.get("target_provider_best_raw_score"),
                "target_provider_summary_count": row.get("target_provider_summary_count"),
                "unique_provider_count": row.get("unique_provider_count"),
                "all_suggestion_count": row.get("all_suggestion_count"),
                "source_terms": row.get("source_terms") or [],
                "source_term_count": row.get("source_term_count"),
                "label_source": "normal_selected_playout",
                "label_semantics": "normal_selected_provider_outcome",
                "usable_for_offline_probe": True,
                "usable_for_selector_training": False,
                "training_block_reason": "ownership labels recovered for offline review; selector training requires readiness review",
                "stage7_training_row": False,
            }
        )
    summary = {
        "candidate_row_count": len(candidates),
        "deduplicated_row_count": len(rows),
        "target_label_counts": dict(Counter(str(row.get("target_label")) for row in rows)),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
        "state_count": len({row.get("state_id") for row in rows}),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "selector_training_row_count": sum(1 for row in rows if row.get("usable_for_selector_training")),
    }
    payload = {
        "schema_version": "krk_ownership_selection_label_dataset.v0",
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
        "source_artifacts": [str(SELECTOR_FEATURES), str(SPLIT_READINESS)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "ownership_selection_labels_recovered",
            "recommended_next_step": "merge_ownership_labels_into_split_objective_dataset",
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
        raise ValueError("ownership labels are not training rows yet")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Ownership Selection Label Dataset v0",
        "",
        "Recovered non-causal ownership-selection labels from normal selected-playout evidence.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            f"- state=`{row['state_id']}` stage=`{row['source_stage']}` provider=`{row['provider_id']}` "
            f"label=`{row['target_label']}` move=`{row['move_uci']}`"
        )
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
