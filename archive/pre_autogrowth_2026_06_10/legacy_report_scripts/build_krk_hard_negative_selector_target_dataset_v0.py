#!/usr/bin/env python3
"""Build non-causal hard-negative selector target candidates."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DIRECTED_REVIEW = Path("reports/krk_selector_directed_fix_review_v0.json")
GEOMETRY = Path("reports/krk_capacity_geometry_feature_audit_v0.json")
OUT_JSON = Path("reports/krk_hard_negative_selector_target_dataset_v0.json")
OUT_MD = Path("reports/krk_hard_negative_selector_target_dataset_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _target_kind(capacity_label: str | None) -> str | None:
    if capacity_label == "negative_capacity":
        return "hard_negative_capacity"
    if capacity_label == "positive_capacity":
        return "positive_capacity_context"
    return None


def build_dataset() -> dict[str, Any]:
    review = _load(DIRECTED_REVIEW)
    geometry = _load(GEOMETRY)
    if review.get("causal_status") != "non_causal_architecture_review":
        raise ValueError("directed fix review must remain non-causal")
    if geometry.get("causal_status") != "non_causal_feature_audit":
        raise ValueError("geometry audit must remain non-causal")
    rows = []
    for row in geometry.get("rows") or []:
        target = _target_kind(row.get("capacity_label"))
        if target is None:
            continue
        rows.append({
            "schema_version": "krk_hard_negative_selector_target_candidate.v0",
            "causal_status": "non_causal_target_candidate",
            "target_kind": target,
            "label_semantics": "forced_provider_capacity_label_not_runtime_ownership",
            "state_id": row.get("state_id"),
            "source_stage": row.get("source_stage"),
            "provider_id": row.get("provider_id"),
            "provider_family": row.get("provider_family"),
            "capacity_label": row.get("capacity_label"),
            "forced_first_move": row.get("forced_first_move"),
            "forced_plies": row.get("forced_plies"),
            "forced_piece_type": row.get("forced_piece_type"),
            "black_king_edge_distance": row.get("black_king_edge_distance"),
            "black_king_corner_distance": row.get("black_king_corner_distance"),
            "white_king_distance_delta": row.get("white_king_distance_delta"),
            "rook_distance_delta": row.get("rook_distance_delta"),
            "king_moves_toward_black": row.get("king_moves_toward_black"),
            "rook_moves_toward_black": row.get("rook_moves_toward_black"),
            "rook_same_file_as_black_after": row.get("rook_same_file_as_black_after"),
            "rook_same_rank_as_black_after": row.get("rook_same_rank_as_black_after"),
            "usable_for_training": False,
            "training_block_reason": "requires selector-label semantics review before training use",
            "stage7_challenge_row": False,
        })
    summary = {
        "row_count": len(rows),
        "target_kind_counts": dict(Counter(str(row.get("target_kind")) for row in rows)),
        "source_stage_counts": dict(Counter(str(row.get("source_stage")) for row in rows)),
        "provider_family_counts": dict(Counter(str(row.get("provider_family")) for row in rows)),
        "stage7_row_count": sum(1 for row in rows if row.get("source_stage") == "stage7"),
        "training_row_count": sum(1 for row in rows if row.get("usable_for_training")),
        "state_count": len({row.get("state_id") for row in rows}),
    }
    payload = {
        "schema_version": "krk_hard_negative_selector_target_dataset.v0",
        "causal_status": "non_causal_target_dataset",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_candidate_generator_implemented": False,
        "runtime_terminals_added": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DIRECTED_REVIEW), str(GEOMETRY)],
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "hard_negative_selector_target_candidates_built",
            "recommended_next_step": "review_hard_negative_target_training_semantics",
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
    if payload["summary"]["training_row_count"] != 0:
        raise ValueError("hard-negative target candidates are not training rows yet")
    if payload["decision"]["selector_training_allowed"] is not False:
        raise ValueError("selector training remains blocked")
    for row in payload.get("rows") or []:
        if row.get("causal_status") != "non_causal_target_candidate":
            raise ValueError("target rows must remain non-causal")
        if row.get("usable_for_training"):
            raise ValueError("target rows require review before training use")


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# KRK Hard-Negative Selector Target Dataset v0",
        "",
        "This dataset packages protected capacity labels and geometry features as non-causal selector target candidates. It does not authorize selector training.",
        "",
        "## Summary",
        "",
    ]
    for key, value in payload["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Rows", ""])
    for row in payload["rows"]:
        lines.append(
            f"- state=`{row['state_id']}` target=`{row['target_kind']}` provider=`{row['provider_id']}` "
            f"move=`{row['forced_first_move']}` piece=`{row['forced_piece_type']}` "
            f"king_delta=`{row['white_king_distance_delta']}` rook_delta=`{row['rook_distance_delta']}`"
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
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
