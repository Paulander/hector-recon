#!/usr/bin/env python3
"""Build a non-causal manifest of candidate source coverage gaps in dataset v4."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v4.json")
SCOPE_REVIEW = Path("reports/strategy_arbitration/krk_candidate_generation_scope_gap_review_v0.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_source_gap_manifest_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_source_gap_manifest_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _key(row: dict[str, Any], *fields: str) -> tuple[str, ...]:
    return tuple(str(row.get(field) or "") for field in fields)


def _gap_record(row: dict[str, Any], gap_type: str) -> dict[str, Any]:
    return {
        "gap_type": gap_type,
        "state_id": row.get("state_id"),
        "fen": row.get("fen"),
        "source_stage": row.get("source_stage"),
        "active_landmark_label": row.get("active_landmark_label"),
        "candidate_strategy_family": row.get("candidate_strategy_family"),
        "candidate_provider_id": row.get("candidate_provider_id"),
        "candidate_move_uci": row.get("candidate_move_uci"),
        "capacity_label": row.get("capacity_label"),
        "label_semantics": row.get("label_semantics"),
        "stage7_challenge_row": bool(row.get("stage7_challenge_row")),
        "runtime_allowed": False,
    }


def build_payload(
    dataset: dict[str, Any] | None = None,
    scope_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    scope_review = scope_review or _load(SCOPE_REVIEW)
    rows = [row for row in dataset.get("rows") or [] if isinstance(row, dict)]
    positive_capacity = [
        row
        for row in rows
        if row.get("evidence_channel") == "validated_provider_capacity"
        and row.get("capacity_label") == "positive_capacity"
        and not row.get("stage7_challenge_row")
    ]
    refresh_trace = [
        row
        for row in rows
        if row.get("evidence_channel") == "runtime_observation_trace_feature"
        and row.get("trace_feature_source") == "candidate_generation_refresh_sandbox"
        and not row.get("stage7_challenge_row")
    ]
    exact_trace_keys = {
        _key(row, "fen", "candidate_provider_id", "candidate_move_uci") for row in refresh_trace
    }
    policy_cell_trace_keys = {
        tuple(str(row.get("policy_cell") or "").split("|", 1))
        for row in refresh_trace
        if "|" in str(row.get("policy_cell") or "")
    }
    exact_covered = [
        row
        for row in positive_capacity
        if _key(row, "fen", "candidate_provider_id", "candidate_move_uci") in exact_trace_keys
    ]
    exact_missing = [
        row
        for row in positive_capacity
        if _key(row, "fen", "candidate_provider_id", "candidate_move_uci") not in exact_trace_keys
    ]
    policy_cell_covered_exact_missing = [
        row
        for row in exact_missing
        if _key(row, "source_stage", "candidate_strategy_family") in policy_cell_trace_keys
    ]
    policy_cell_missing = [
        row
        for row in exact_missing
        if _key(row, "source_stage", "candidate_strategy_family") not in policy_cell_trace_keys
    ]
    gap_records = [
        _gap_record(row, "policy_cell_covered_exact_missing")
        for row in policy_cell_covered_exact_missing
    ] + [_gap_record(row, "policy_cell_missing") for row in policy_cell_missing]
    gap_by_stage = Counter(str(record["source_stage"] or "unknown") for record in gap_records)
    gap_by_family = Counter(
        str(record["candidate_strategy_family"] or "unknown") for record in gap_records
    )
    return {
        "schema_version": "krk_candidate_source_gap_manifest.v1",
        "causal_status": "non_causal_gap_manifest",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(SCOPE_REVIEW)],
        "summary": {
            "positive_capacity_count": len(positive_capacity),
            "refresh_trace_count": len(refresh_trace),
            "exact_covered_positive_capacity_count": len(exact_covered),
            "exact_missing_positive_capacity_count": len(exact_missing),
            "policy_cell_covered_exact_missing_count": len(
                policy_cell_covered_exact_missing
            ),
            "policy_cell_missing_count": len(policy_cell_missing),
            "gap_count_by_stage": dict(sorted(gap_by_stage.items())),
            "gap_count_by_family": dict(sorted(gap_by_family.items())),
        },
        "gap_records": gap_records,
        "interpretation": {
            "exact_candidate_source_coverage_incomplete": len(exact_missing) > 0,
            "policy_cell_context_covers_most_missing_exact_candidates": (
                len(policy_cell_covered_exact_missing) >= len(policy_cell_missing)
            ),
            "capacity_rows_remain_non_causal": True,
            "not_selector_training_data": True,
            "scope_review_status": (scope_review.get("decision") or {}).get("status"),
        },
        "decision": {
            "status": (
                "candidate_source_gap_manifest_ready_non_causal"
                if exact_missing
                else "candidate_source_gap_manifest_no_exact_gaps"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "review_candidate_source_expansion_options_non_causal"
                if exact_missing
                else "architecture_review_before_any_runtime_boundary"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate Source Gap Manifest v0",
        "",
        "This manifest lists positive-capacity candidate rows that are not exactly covered by candidate-generation refresh runtime-observation traces. It is non-causal and does not authorize selection or runtime changes.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- runtime_changes_allowed: `{payload['decision']['runtime_changes_allowed']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## First Gap Records", ""])
    for record in payload["gap_records"][:20]:
        lines.append(
            "- "
            f"`{record['gap_type']}` "
            f"stage=`{record['source_stage']}` "
            f"family=`{record['candidate_strategy_family']}` "
            f"provider=`{record['candidate_provider_id']}` "
            f"move=`{record['candidate_move_uci']}`"
        )
    if len(payload["gap_records"]) > 20:
        lines.append(f"- ... {len(payload['gap_records']) - 20} additional gaps omitted")
    lines.extend(["", "## Interpretation", ""])
    for key, value in payload["interpretation"].items():
        lines.append(f"- {key}: `{value}`")
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
