#!/usr/bin/env python3
"""Merge recovered and diversity-run ownership-selection labels."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP_V0 = Path("reports/krk_ownership_selection_label_dataset_v0.json")
DIVERSITY_LABELS = Path("reports/krk_selected_provider_diversity_ownership_labels_v0.json")
OUT_JSON = Path("reports/krk_ownership_selection_label_dataset_v1.json")
OUT_MD = Path("reports/krk_ownership_selection_label_dataset_v1.md")


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


def _best_initial_provider(label: dict[str, Any]) -> dict[str, Any]:
    providers = label.get("initial_same_move_providers") or []
    if not providers:
        return {}
    return sorted(
        providers,
        key=lambda item: (
            -float(item.get("score") if isinstance(item.get("score"), (int, float)) else -999999.0),
            str(item.get("provider_id") or ""),
        ),
    )[0]


def _row_from_diversity_label(label: dict[str, Any]) -> dict[str, Any]:
    selected = label.get("selected_playout_success") or {}
    provider_id = str(label.get("selected_provider") or "")
    best = _best_initial_provider(label)
    owner_positive = selected.get("result") == "mate"
    return {
        "schema_version": "krk_ownership_selection_label.v1",
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
        "target_label": "selected_owner_converted" if owner_positive else "selected_owner_failed",
        "owner_positive": owner_positive,
        "selected_provider_before_observation": provider_id,
        "selected_provider_matches_target": True,
        "target_provider_best_rank": 1 if best else None,
        "target_provider_best_raw_score": best.get("score"),
        "target_provider_summary_count": label.get("initial_provider_count"),
        "unique_provider_count": label.get("initial_provider_count"),
        "all_suggestion_count": len(label.get("initial_same_move_providers") or []),
        "source_terms": [
            "normal_routing_selected_provider",
            f"active_landmark:{label.get('active_landmark_label')}",
            f"selected_result:{selected.get('result')}",
        ],
        "source_term_count": 3,
        "label_source": "selected_provider_diversity_normal_routing_h40",
        "label_semantics": "normal_selected_provider_outcome",
        "selected_playout_result": selected.get("result"),
        "selected_playout_plies": selected.get("plies"),
        "usable_for_offline_probe": True,
        "usable_for_selector_training": False,
        "training_block_reason": "ownership labels expanded for offline review; selector training requires readiness review",
        "stage7_training_row": False,
    }


def _normalize_v0_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "schema_version": "krk_ownership_selection_label.v1",
        "usable_for_selector_training": False,
        "training_block_reason": row.get("training_block_reason")
        or "ownership labels remain offline evidence pending readiness review",
        "stage7_training_row": False,
    }


def build_dataset() -> dict[str, Any]:
    v0 = _load(OWNERSHIP_V0)
    diversity = _load(DIVERSITY_LABELS)
    if v0.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership v0 must remain non-causal")
    if diversity.get("causal_status") != "non_causal_label_run":
        raise ValueError("diversity labels must remain non-causal")

    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []
    for row in [_normalize_v0_row(row) for row in v0.get("rows") or []] + [
        _row_from_diversity_label(label) for label in diversity.get("labels") or []
    ]:
        if row.get("source_stage") == "stage7":
            continue
        key = (str(row.get("state_id")), str(row.get("provider_id")))
        existing = rows_by_key.get(key)
        if existing and existing.get("target_label") != row.get("target_label"):
            conflicts.append({"key": list(key), "existing": existing.get("target_label"), "new": row.get("target_label")})
            continue
        rows_by_key.setdefault(key, row)

    rows = [rows_by_key[key] for key in sorted(rows_by_key)]
    summary = {
        "input_v0_row_count": len(v0.get("rows") or []),
        "input_diversity_label_count": len(diversity.get("labels") or []),
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
        "schema_version": "krk_ownership_selection_label_dataset.v1",
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
        "source_artifacts": [str(OWNERSHIP_V0), str(DIVERSITY_LABELS)],
        "summary": summary,
        "conflicts": conflicts,
        "rows": rows,
        "decision": {
            "status": "ownership_selection_labels_expanded_with_diversity_negatives",
            "recommended_next_step": "rerun_ownership_selection_feature_probe",
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


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Ownership Selection Label Dataset v1",
        "",
        "Merges recovered ownership labels with bounded selected-provider diversity h40 labels.",
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
