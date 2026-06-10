#!/usr/bin/env python3
"""Build split non-causal selector objective channels from capacity evidence."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGETS = Path("reports/krk_hard_negative_selector_target_dataset_v2.json")
SEMANTICS = Path("reports/krk_hard_negative_label_semantics_review_v1.json")
FEATURE_REVIEW = Path("reports/krk_stronger_selector_feature_review_v0.json")
OUT_JSON = Path("reports/krk_split_selector_objective_dataset_v0.json")
OUT_MD = Path("reports/krk_split_selector_objective_dataset_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _capacity_label(row: dict[str, Any]) -> str | None:
    if row.get("target_kind") == "positive_capacity_context":
        return "capacity_positive"
    if row.get("target_kind") == "hard_negative_capacity":
        return "capacity_negative"
    return None


def _base(row: dict[str, Any], objective_id: str, objective_channel: str) -> dict[str, Any]:
    keys = (
        "state_id",
        "frame_id",
        "source_stage",
        "active_landmark_label",
        "provider_id",
        "provider_family",
        "forced_first_move",
        "forced_piece_type",
        "forced_plies",
        "white_king_distance_delta",
        "rook_distance_delta",
        "king_moves_toward_black",
        "rook_moves_toward_black",
        "rook_same_file_as_black_after",
        "rook_same_rank_as_black_after",
        "black_king_edge_distance",
        "black_king_corner_distance",
        "black_king_legal_reply_count_after",
        "source_artifact_channel",
    )
    return {
        "schema_version": "krk_split_selector_objective_row.v0",
        "causal_status": "non_causal_objective_row",
        "objective_id": objective_id,
        "objective_channel": objective_channel,
        **{key: row.get(key) for key in keys if key in row},
        "source_target_kind": row.get("target_kind"),
        "source_label_semantics": row.get("label_semantics"),
        "stage7_training_row": False,
    }


def _capacity_recall_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        label = _capacity_label(row)
        if label != "capacity_positive":
            continue
        item = _base(row, "krk.selector.capacity_recall.v0", "capacity_recall")
        item.update(
            {
                "target_label": "include_validated_provider_candidate",
                "usable_for_offline_probe": True,
                "usable_for_selector_training": False,
                "training_block_reason": (
                    "capacity recall only says provider should be represented in a candidate set; "
                    "it does not say provider should own runtime selection"
                ),
            }
        )
        out.append(item)
    return out


def _capacity_risk_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        label = _capacity_label(row)
        if label is None:
            continue
        item = _base(row, "krk.selector.capacity_risk.v0", "capacity_risk")
        item.update(
            {
                "target_label": "risk_path_failed_h40" if label == "capacity_negative" else "risk_path_converted_h40",
                "risk_positive": label == "capacity_negative",
                "usable_for_offline_probe": True,
                "usable_for_selector_training": False,
                "training_block_reason": (
                    "capacity risk is a diagnostic/hard-negative channel; it must be combined with "
                    "safe-preservation and ownership labels before selector training"
                ),
            }
        )
        out.append(item)
    return out


def _safe_preservation_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        label = _capacity_label(row)
        if label != "capacity_positive":
            continue
        item = _base(row, "krk.selector.safe_preservation.v0", "safe_preservation")
        item.update(
            {
                "target_label": "preserve_validated_conversion_capacity",
                "safe_positive": True,
                "usable_for_offline_probe": True,
                "usable_for_selector_training": False,
                "training_block_reason": (
                    "safe preservation can protect known converting capacity, but it is not a positive "
                    "runtime ownership label by itself"
                ),
            }
        )
        out.append(item)
    return out


def _ownership_selection_stub() -> list[dict[str, Any]]:
    return [
        {
            "schema_version": "krk_split_selector_objective_row.v0",
            "causal_status": "non_causal_objective_row",
            "objective_id": "krk.selector.ownership_selection.v0",
            "objective_channel": "ownership_selection",
            "target_label": "missing_runtime_ownership_label",
            "usable_for_offline_probe": False,
            "usable_for_selector_training": False,
            "training_block_reason": (
                "Forced-provider capacity labels do not identify which provider should own normal runtime selection. "
                "This channel requires selected-playout/paired-normal-routing evidence with safe-owner preservation."
            ),
            "stage7_training_row": False,
        }
    ]


def build_dataset() -> dict[str, Any]:
    targets = _load(TARGETS)
    semantics = _load(SEMANTICS)
    feature_review = _load(FEATURE_REVIEW)
    if targets.get("causal_status") != "non_causal_target_dataset":
        raise ValueError("targets must remain non-causal")
    if semantics.get("causal_status") != "non_causal_semantics_review":
        raise ValueError("semantics review must remain non-causal")
    if feature_review.get("causal_status") != "non_causal_feature_review":
        raise ValueError("feature review must remain non-causal")
    source_rows = [row for row in targets.get("rows") or [] if row.get("source_stage") != "stage7"]
    objective_rows = (
        _capacity_recall_rows(source_rows)
        + _capacity_risk_rows(source_rows)
        + _safe_preservation_rows(source_rows)
        + _ownership_selection_stub()
    )
    summary = {
        "source_row_count": len(source_rows),
        "objective_row_count": len(objective_rows),
        "objective_channel_counts": dict(Counter(str(row.get("objective_channel")) for row in objective_rows)),
        "target_label_counts": dict(Counter(str(row.get("target_label")) for row in objective_rows)),
        "offline_probe_row_count": sum(1 for row in objective_rows if row.get("usable_for_offline_probe")),
        "selector_training_row_count": sum(1 for row in objective_rows if row.get("usable_for_selector_training")),
        "stage7_row_count": sum(1 for row in objective_rows if row.get("source_stage") == "stage7"),
        "ownership_selection_available": any(
            row.get("objective_channel") == "ownership_selection" and row.get("usable_for_offline_probe")
            for row in objective_rows
        ),
    }
    payload = {
        "schema_version": "krk_split_selector_objective_dataset.v0",
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
        "source_artifacts": [str(TARGETS), str(SEMANTICS), str(FEATURE_REVIEW)],
        "objective_definitions": {
            "capacity_recall": {
                "meaning": "validated provider has conversion capacity and should be present in candidate set",
                "not_meaning": "provider should own runtime decision",
            },
            "capacity_risk": {
                "meaning": "forced provider path failed or converted under h40, useful as risk evidence",
                "not_meaning": "global provider suppression rule",
            },
            "safe_preservation": {
                "meaning": "known converting capacity that future suppressors must preserve",
                "not_meaning": "positive ownership selection",
            },
            "ownership_selection": {
                "meaning": "which provider should own normal runtime selection",
                "not_meaning": "derivable from forced-provider labels alone",
                "current_status": "missing_required_label_channel",
            },
        },
        "summary": summary,
        "rows": objective_rows,
        "decision": {
            "status": "split_selector_objective_channels_built",
            "recommended_next_step": "review_split_objective_readiness_before_any_selector_training",
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
        raise ValueError("split objective rows must not authorize selector training")
    if payload["summary"]["ownership_selection_available"]:
        raise ValueError("ownership selection cannot be supplied by forced-provider capacity labels")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Split Selector Objective Dataset v0",
        "",
        "This artifact fixes the hard-negative label semantics issue by separating capacity recall, capacity risk, safe preservation, and ownership selection.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Objective Definitions", ""])
    for key, value in payload["objective_definitions"].items():
        lines.append(f"- `{key}`: means `{value['meaning']}`; does not mean `{value['not_meaning']}`")
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
