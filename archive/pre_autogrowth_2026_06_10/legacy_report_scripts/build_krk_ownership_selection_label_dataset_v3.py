#!/usr/bin/env python3
"""Recover supplemental ownership labels from selected-provider groups."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OWNERSHIP_V2 = Path("reports/krk_ownership_selection_label_dataset_v2.json")
SELECTOR_FEATURES = Path("reports/krk_selector_feature_dataset_v0.json")
OUT_JSON = Path("reports/krk_ownership_selection_label_dataset_v3.json")
OUT_MD = Path("reports/krk_ownership_selection_label_dataset_v3.md")


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


def _owner_label(label: str | None) -> str | None:
    if label == "positive":
        return "selected_owner_converted"
    if label == "negative":
        return "selected_owner_failed"
    return None


def _supplemental_rows(existing_keys: set[tuple[str, str]]) -> list[dict[str, Any]]:
    features = _load(SELECTOR_FEATURES)
    if features.get("causal_status") != "non_causal_feature_dataset":
        raise ValueError("selector feature dataset must remain non-causal")
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in features.get("rows") or []:
        selected_provider = str(row.get("selected_provider_before_observation") or "")
        key = (str(row.get("state_id") or ""), selected_provider)
        if (
            row.get("target_kind") == "selected_playout_success"
            and row.get("usable_for_training") is True
            and row.get("source_stage") != "stage7"
            and selected_provider
            and key not in existing_keys
            and _owner_label(row.get("label")) is not None
        ):
            grouped.setdefault(key, []).append(row)
    rows = []
    for (state_id, selected_provider), candidates in sorted(grouped.items()):
        labels = {_owner_label(row.get("label")) for row in candidates}
        if len(labels) != 1:
            continue
        first = sorted(
            candidates,
            key=lambda row: (
                str(row.get("provider_id") or ""),
                int(row.get("target_provider_best_rank") or 999),
            ),
        )[0]
        rows.append(
            {
                "schema_version": "krk_ownership_selection_label.v3",
                "causal_status": "non_causal_ownership_label",
                "objective_id": "krk.selector.ownership_selection.v0",
                "objective_channel": "ownership_selection",
                "state_id": state_id,
                "frame_id": first.get("frame_id"),
                "source_stage": first.get("source_stage"),
                "active_landmark_label": first.get("active_landmark_label"),
                "provider_id": selected_provider,
                "provider_family": _provider_family(selected_provider),
                "move_uci": first.get("move_uci"),
                "target_label": next(iter(labels)),
                "owner_positive": next(iter(labels)) == "selected_owner_converted",
                "selected_provider_before_observation": selected_provider,
                "selected_provider_matches_target": True,
                "target_provider_best_rank": None,
                "target_provider_best_raw_score": None,
                "target_provider_summary_count": (first.get("provider_summary") or {}).get(selected_provider),
                "unique_provider_count": first.get("unique_provider_count"),
                "all_suggestion_count": first.get("all_suggestion_count"),
                "source_terms": first.get("source_terms") or [],
                "source_term_count": first.get("source_term_count"),
                "label_source": "selected_provider_group_recovery",
                "label_semantics": "normal_selected_provider_outcome_recovered_from_group",
                "usable_for_offline_probe": True,
                "usable_for_selector_training": False,
                "training_block_reason": "supplemental ownership labels remain offline evidence pending readiness review",
                "stage7_training_row": False,
                "recovery_note": "selected provider was present in selected_playout_success group but absent as a target provider row",
            }
        )
    return rows


def build_dataset() -> dict[str, Any]:
    base = _load(OWNERSHIP_V2)
    if base.get("causal_status") != "non_causal_ownership_label_dataset":
        raise ValueError("ownership v2 must remain non-causal")
    rows_by_key: dict[tuple[str, str], dict[str, Any]] = {
        (str(row.get("state_id")), str(row.get("provider_id"))): {
            **row,
            "schema_version": "krk_ownership_selection_label.v3",
            "usable_for_selector_training": False,
        }
        for row in base.get("rows") or []
        if row.get("source_stage") != "stage7"
    }
    supplemental = _supplemental_rows(set(rows_by_key))
    for row in supplemental:
        rows_by_key.setdefault((str(row.get("state_id")), str(row.get("provider_id"))), row)
    rows = [rows_by_key[key] for key in sorted(rows_by_key)]
    summary = {
        "input_v2_row_count": len(base.get("rows") or []),
        "supplemental_row_count": len(supplemental),
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
        "schema_version": "krk_ownership_selection_label_dataset.v3",
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
        "source_artifacts": [str(OWNERSHIP_V2), str(SELECTOR_FEATURES)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "ownership_selection_labels_supplemented_from_selected_provider_groups",
            "recommended_next_step": "rerun_context_enriched_ownership_probe",
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
        "# KRK Ownership Selection Label Dataset v3",
        "",
        "Adds replay-free supplemental selected-owner labels from selected-playout groups where the actual selected provider was not present as a target row.",
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
