#!/usr/bin/env python3
"""Benchmark dataset v5 candidate-generation context coverage non-causally."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5.json")
QUALITY = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5_quality_probe.json")
CONTEXT = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5_context_review.json")
V4_BENCHMARK = Path("reports/strategy_arbitration/krk_candidate_generation_v4_context_benchmark.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_generation_v5_context_benchmark.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_generation_v5_context_benchmark.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _load_optional(path: Path) -> dict[str, Any]:
    full_path = ROOT / path
    if not full_path.exists():
        return {}
    return _load(path)


def _key(row: dict[str, Any], *fields: str) -> tuple[str, ...]:
    return tuple(str(row.get(field) or "") for field in fields)


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def build_payload(
    dataset: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    v4_benchmark: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    quality = quality or _load(QUALITY)
    context = context or _load(CONTEXT)
    v4_benchmark = v4_benchmark if v4_benchmark is not None else _load_optional(V4_BENCHMARK)
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
    exact_trace_rows = [
        row
        for row in trace_rows
        if row.get("trace_feature_source") == "exact_trace_enrichment_sandbox"
    ]
    candidate_generation_trace_rows = refresh_trace_rows + exact_trace_rows
    trace_by_source = Counter(str(row.get("trace_feature_source") or "unknown") for row in trace_rows)

    def exact_keys(source_rows: list[dict[str, Any]]) -> set[tuple[str, ...]]:
        return {_key(row, "fen", "candidate_provider_id", "candidate_move_uci") for row in source_rows}

    def state_provider_keys(source_rows: list[dict[str, Any]]) -> set[tuple[str, ...]]:
        return {_key(row, "fen", "candidate_provider_id") for row in source_rows}

    def stage_family_keys(source_rows: list[dict[str, Any]]) -> set[tuple[str, ...]]:
        return {_key(row, "source_stage", "candidate_strategy_family") for row in source_rows}

    def policy_cell_keys(source_rows: list[dict[str, Any]]) -> set[tuple[str, ...]]:
        return {
            tuple(str(row.get("policy_cell") or "").split("|", 1))
            for row in source_rows
            if "|" in str(row.get("policy_cell") or "")
        }

    refresh_exact_keys = exact_keys(refresh_trace_rows)
    exact_enrichment_keys = exact_keys(exact_trace_rows)
    combined_exact_keys = exact_keys(candidate_generation_trace_rows)
    combined_state_provider_keys = state_provider_keys(candidate_generation_trace_rows)
    combined_stage_family_keys = stage_family_keys(candidate_generation_trace_rows)
    combined_policy_cell_keys = policy_cell_keys(candidate_generation_trace_rows)

    refresh_exact_positive = [
        row
        for row in positive_capacity
        if _key(row, "fen", "candidate_provider_id", "candidate_move_uci")
        in refresh_exact_keys
    ]
    exact_enrichment_positive = [
        row
        for row in positive_capacity
        if _key(row, "fen", "candidate_provider_id", "candidate_move_uci")
        in exact_enrichment_keys
    ]
    combined_exact_positive = [
        row
        for row in positive_capacity
        if _key(row, "fen", "candidate_provider_id", "candidate_move_uci")
        in combined_exact_keys
    ]
    combined_state_provider_positive = [
        row
        for row in positive_capacity
        if _key(row, "fen", "candidate_provider_id") in combined_state_provider_keys
    ]
    combined_stage_family_positive = [
        row
        for row in positive_capacity
        if _key(row, "source_stage", "candidate_strategy_family")
        in combined_stage_family_keys
    ]
    combined_policy_cell_positive = [
        row
        for row in positive_capacity
        if _key(row, "source_stage", "candidate_strategy_family")
        in combined_policy_cell_keys
    ]
    combined_exact_negative = [
        row
        for row in negative_capacity
        if _key(row, "fen", "candidate_provider_id", "candidate_move_uci")
        in combined_exact_keys
    ]
    combined_stage_family_negative = [
        row
        for row in negative_capacity
        if _key(row, "source_stage", "candidate_strategy_family")
        in combined_stage_family_keys
    ]
    combined_policy_cell_negative = [
        row
        for row in negative_capacity
        if _key(row, "source_stage", "candidate_strategy_family")
        in combined_policy_cell_keys
    ]
    positive_count = len(positive_capacity)
    negative_count = len(negative_capacity)
    v4_summary = v4_benchmark.get("summary") or {}
    v4_exact_recall = v4_summary.get("exact_positive_capacity_recall_from_refresh_trace")
    v4_exact_recall_value = float(v4_exact_recall) if v4_exact_recall is not None else None
    combined_exact_recall = _ratio(len(combined_exact_positive), positive_count)
    exact_recall_delta = (
        combined_exact_recall - v4_exact_recall_value
        if v4_exact_recall_value is not None
        else None
    )
    policy_cell_recall = _ratio(len(combined_policy_cell_positive), positive_count)
    policy_cell_negative_exposure = _ratio(len(combined_policy_cell_negative), negative_count)
    context_useful = (
        len(exact_trace_rows) > 0
        and combined_exact_recall >= (v4_exact_recall_value or 0.0)
        and policy_cell_recall >= 0.5
        and policy_cell_negative_exposure == 0.0
        and (quality.get("decision") or {}).get("selector_allowed") is False
        and (context.get("decision") or {}).get("selector_allowed") is False
    )
    return {
        "schema_version": "krk_candidate_generation_v5_context_benchmark.v1",
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
        "source_artifacts": [str(DATASET), str(QUALITY), str(CONTEXT), str(V4_BENCHMARK)],
        "summary": {
            "capacity_row_count": len(capacity_rows),
            "positive_capacity_count": positive_count,
            "negative_capacity_count": negative_count,
            "runtime_trace_row_count": len(trace_rows),
            "refresh_trace_row_count": len(refresh_trace_rows),
            "exact_trace_enrichment_trace_row_count": len(exact_trace_rows),
            "candidate_generation_trace_row_count": len(candidate_generation_trace_rows),
            "runtime_trace_row_count_by_source": dict(sorted(trace_by_source.items())),
            "exact_positive_capacity_recall_from_refresh_trace": _ratio(
                len(refresh_exact_positive), positive_count
            ),
            "exact_positive_capacity_recall_from_exact_trace_enrichment": _ratio(
                len(exact_enrichment_positive), positive_count
            ),
            "exact_positive_capacity_recall_from_candidate_generation_trace": (
                combined_exact_recall
            ),
            "state_provider_positive_capacity_recall_from_candidate_generation_trace": _ratio(
                len(combined_state_provider_positive), positive_count
            ),
            "stage_family_positive_capacity_recall_from_candidate_generation_trace": _ratio(
                len(combined_stage_family_positive), positive_count
            ),
            "policy_cell_positive_capacity_recall_from_candidate_generation_trace": (
                policy_cell_recall
            ),
            "exact_negative_capacity_exposure_from_candidate_generation_trace": _ratio(
                len(combined_exact_negative), negative_count
            ),
            "stage_family_negative_capacity_exposure_from_candidate_generation_trace": _ratio(
                len(combined_stage_family_negative), negative_count
            ),
            "policy_cell_negative_capacity_exposure_from_candidate_generation_trace": (
                policy_cell_negative_exposure
            ),
            "exact_positive_capacity_covered_count": len(combined_exact_positive),
            "exact_trace_enrichment_positive_capacity_covered_count": len(
                exact_enrichment_positive
            ),
            "policy_cell_positive_capacity_covered_count": len(combined_policy_cell_positive),
            "policy_cell_negative_capacity_exposed_count": len(combined_policy_cell_negative),
            "v4_exact_positive_capacity_recall_from_refresh_trace": v4_exact_recall,
            "exact_positive_capacity_recall_delta_vs_v4": exact_recall_delta,
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
            "exact_trace_enrichment_improved_exact_coverage": bool(
                exact_recall_delta is not None and exact_recall_delta > 0.0
            ),
            "risk": (
                "V5 exact trace enrichment improves exact candidate visibility for "
                "reviewed policy-cell-covered gaps, but these rows remain trace "
                "context and do not provide ownership selector labels."
            ),
        },
        "decision": {
            "status": (
                "candidate_generation_v5_context_useful_selector_still_blocked"
                if context_useful
                else "candidate_generation_v5_context_underpowered"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "candidate_generation_v5_boundary_review_or_ownership_label_recovery"
                if context_useful
                else "collect_more_protected_trace_context_non_causal"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation v5 Context Benchmark",
        "",
        "This replay-free benchmark compares protected capacity rows with refresh plus exact-trace enrichment context in dataset v5. It does not authorize selection or runtime changes.",
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
