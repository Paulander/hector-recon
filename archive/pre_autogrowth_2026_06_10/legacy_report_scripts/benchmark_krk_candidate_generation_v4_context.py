#!/usr/bin/env python3
"""Benchmark dataset v4 candidate-generation context coverage non-causally."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v4.json")
QUALITY = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v4_quality_probe.json")
CONTEXT = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v4_context_review.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_generation_v4_context_benchmark.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_generation_v4_context_benchmark.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _key(row: dict[str, Any], *fields: str) -> tuple[str, ...]:
    return tuple(str(row.get(field) or "") for field in fields)


def build_payload(
    dataset: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    quality = quality or _load(QUALITY)
    context = context or _load(CONTEXT)
    rows = [row for row in dataset.get("rows") or [] if isinstance(row, dict)]
    capacity_rows = [
        row
        for row in rows
        if not row.get("stage7_challenge_row")
        and row.get("evidence_channel") == "validated_provider_capacity"
        and row.get("capacity_label") in {"positive_capacity", "negative_capacity"}
    ]
    positive_capacity = [
        row for row in capacity_rows if row.get("capacity_label") == "positive_capacity"
    ]
    negative_capacity = [
        row for row in capacity_rows if row.get("capacity_label") == "negative_capacity"
    ]
    trace_rows = [
        row
        for row in rows
        if row.get("evidence_channel") == "runtime_observation_trace_feature"
        and not row.get("stage7_challenge_row")
    ]
    refresh_trace_rows = [
        row
        for row in trace_rows
        if row.get("trace_feature_source") == "candidate_generation_refresh_sandbox"
    ]
    trace_by_source = Counter(str(row.get("trace_feature_source") or "unknown") for row in trace_rows)
    trace_exact_keys = {
        _key(row, "fen", "candidate_provider_id", "candidate_move_uci")
        for row in refresh_trace_rows
    }
    trace_state_provider_keys = {
        _key(row, "fen", "candidate_provider_id")
        for row in refresh_trace_rows
    }
    trace_stage_family_keys = {
        _key(row, "source_stage", "candidate_strategy_family")
        for row in refresh_trace_rows
    }
    trace_policy_cell_keys = {
        tuple(str(row.get("policy_cell") or "").split("|", 1))
        for row in refresh_trace_rows
        if "|" in str(row.get("policy_cell") or "")
    }
    exact_positive = [
        row
        for row in positive_capacity
        if _key(row, "fen", "candidate_provider_id", "candidate_move_uci") in trace_exact_keys
    ]
    state_provider_positive = [
        row
        for row in positive_capacity
        if _key(row, "fen", "candidate_provider_id") in trace_state_provider_keys
    ]
    stage_family_positive = [
        row
        for row in positive_capacity
        if _key(row, "source_stage", "candidate_strategy_family") in trace_stage_family_keys
    ]
    policy_cell_positive = [
        row
        for row in positive_capacity
        if _key(row, "source_stage", "candidate_strategy_family") in trace_policy_cell_keys
    ]
    exact_negative = [
        row
        for row in negative_capacity
        if _key(row, "fen", "candidate_provider_id", "candidate_move_uci") in trace_exact_keys
    ]
    stage_family_negative = [
        row
        for row in negative_capacity
        if _key(row, "source_stage", "candidate_strategy_family") in trace_stage_family_keys
    ]
    policy_cell_negative = [
        row
        for row in negative_capacity
        if _key(row, "source_stage", "candidate_strategy_family") in trace_policy_cell_keys
    ]
    positive_count = len(positive_capacity)
    negative_count = len(negative_capacity)
    exact_recall = len(exact_positive) / positive_count if positive_count else 0.0
    state_provider_recall = len(state_provider_positive) / positive_count if positive_count else 0.0
    stage_family_recall = len(stage_family_positive) / positive_count if positive_count else 0.0
    policy_cell_recall = len(policy_cell_positive) / positive_count if positive_count else 0.0
    exact_negative_exposure = len(exact_negative) / negative_count if negative_count else 0.0
    stage_family_negative_exposure = (
        len(stage_family_negative) / negative_count if negative_count else 0.0
    )
    policy_cell_negative_exposure = (
        len(policy_cell_negative) / negative_count if negative_count else 0.0
    )
    context_useful = (
        len(refresh_trace_rows) > 0
        and policy_cell_recall >= 0.5
        and policy_cell_negative_exposure == 0.0
        and (quality.get("decision") or {}).get("selector_allowed") is False
        and (context.get("decision") or {}).get("selector_allowed") is False
    )
    return {
        "schema_version": "krk_candidate_generation_v4_context_benchmark.v1",
        "causal_status": "non_causal_context_benchmark",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(QUALITY), str(CONTEXT)],
        "summary": {
            "capacity_row_count": len(capacity_rows),
            "positive_capacity_count": positive_count,
            "negative_capacity_count": negative_count,
            "runtime_trace_row_count": len(trace_rows),
            "refresh_trace_row_count": len(refresh_trace_rows),
            "runtime_trace_row_count_by_source": dict(sorted(trace_by_source.items())),
            "exact_positive_capacity_recall_from_refresh_trace": exact_recall,
            "state_provider_positive_capacity_recall_from_refresh_trace": state_provider_recall,
            "stage_family_positive_capacity_recall_from_refresh_trace": stage_family_recall,
            "policy_cell_positive_capacity_recall_from_refresh_trace": policy_cell_recall,
            "exact_negative_capacity_exposure_from_refresh_trace": exact_negative_exposure,
            "stage_family_negative_capacity_exposure_from_refresh_trace": (
                stage_family_negative_exposure
            ),
            "policy_cell_negative_capacity_exposure_from_refresh_trace": (
                policy_cell_negative_exposure
            ),
            "exact_positive_capacity_covered_count": len(exact_positive),
            "policy_cell_positive_capacity_covered_count": len(policy_cell_positive),
            "policy_cell_negative_capacity_exposed_count": len(policy_cell_negative),
            "selector_training_row_count": (dataset.get("summary") or {}).get(
                "selector_training_row_count"
            ),
            "stage7_readiness_training_row_count": (dataset.get("summary") or {}).get(
                "stage7_readiness_training_row_count"
            ),
        },
        "interpretation": {
            "context_useful_for_candidate_generation_analysis": context_useful,
            "selector_supported": False,
            "guardrails_supported": False,
            "capacity_labels_are_not_ownership_labels": True,
            "trace_rows_are_not_training_labels": True,
            "risk": (
                "Refresh trace context cleanly exposes reviewed candidate-generation "
                "cells, but it remains a candidate-generation signal, not an "
                "ownership selector or score calibration mechanism."
            ),
        },
        "decision": {
            "status": (
                "candidate_generation_v4_context_useful_selector_still_blocked"
                if context_useful
                else "candidate_generation_v4_context_underpowered"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "architecture_review_candidate_generation_context_to_next_runtime_boundary"
                if context_useful
                else "collect_more_protected_trace_context_non_causal"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation v4 Context Benchmark",
        "",
        "This replay-free benchmark compares protected capacity rows with candidate-generation refresh trace context in dataset v4. It does not authorize selection or runtime changes.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Interpretation", ""])
    lines.extend(f"- {key}: `{value}`" for key, value in payload["interpretation"].items())
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
