#!/usr/bin/env python3
"""Probe KRK strategy-sequence dataset v5 quality without enabling selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5_quality_probe.json")
OUT_MD = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5_quality_probe.md")


def _load(path: Path = DATASET) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(dataset: dict[str, Any] | None = None) -> dict[str, Any]:
    dataset = dataset or _load()
    summary = dataset.get("summary") or {}
    rows = list(dataset.get("rows") or [])
    channel_counts = dict(summary.get("row_count_by_channel") or {})
    trace_by_source = dict(summary.get("runtime_trace_feature_row_count_by_source") or {})
    generator_rows = [
        row for row in rows if row.get("usable_for_candidate_generation_training_v5")
    ]
    selector_rows = [row for row in rows if row.get("usable_for_selector_training_v5")]
    trace_rows = [
        row for row in rows if row.get("evidence_channel") == "runtime_observation_trace_feature"
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
    stage7_readiness_count = int(summary.get("stage7_readiness_training_row_count", 0) or 0)
    quality_checks = {
        "stage7_excluded_from_readiness": stage7_readiness_count == 0,
        "selector_rows_absent_without_ownership_labels": len(selector_rows) == 0,
        "candidate_generation_rows_preserved": len(generator_rows) > 0,
        "candidate_generation_refresh_trace_source_present": (
            trace_by_source.get("candidate_generation_refresh_sandbox", 0) > 0
        ),
        "exact_trace_enrichment_source_present": (
            trace_by_source.get("exact_trace_enrichment_sandbox", 0) > 0
        ),
        "repair_monitor_trace_source_preserved": (
            trace_by_source.get("repair_monitor_observation", 0) > 0
        ),
        "refresh_trace_rows_are_context_only": all(
            not row.get("usable_for_selector_training_v5")
            and not row.get("usable_for_candidate_generation_training_v5")
            and row.get("causal_status") == "non_causal_dataset_row"
            for row in refresh_trace_rows
        ),
        "exact_trace_rows_are_context_only": all(
            not row.get("usable_for_selector_training_v5")
            and not row.get("usable_for_candidate_generation_training_v5")
            and row.get("causal_status") == "non_causal_dataset_row"
            for row in exact_trace_rows
        ),
        "multiple_evidence_channels_present": len(channel_counts) >= 4,
        "runtime_flags_false": all(
            dataset.get(key) is False
            for key in (
                "runtime_behavior_changed",
                "runtime_defaults_changed",
                "runtime_selector_implemented",
                "runtime_score_changes",
                "runtime_direct_routing",
                "runtime_dtm_or_tablebase_lookup",
                "gameplay_topology_mutation",
                "stage7_promotion_allowed",
                "stage8_training_allowed",
            )
        ),
    }
    selector_blockers = [
        "no_explicit_ownership_selector_rows",
        "runtime_trace_features_are_context_not_selector_labels",
        "capacity_rows_are_candidate_generation_not_ownership_labels",
        "exact_trace_enrichment_rows_are_context_not_selector_labels",
    ]
    status = (
        "strategy_sequence_dataset_v5_quality_candidate_generation_context_ready_selector_blocked"
        if all(quality_checks.values())
        else "strategy_sequence_dataset_v5_quality_blocked"
    )
    return {
        "schema_version": "krk_strategy_sequence_dataset_v5_quality_probe.v1",
        "causal_status": "non_causal_dataset_quality_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET)],
        "summary": {
            "row_count": len(rows),
            "evidence_channel_count": len(channel_counts),
            "row_count_by_channel": channel_counts,
            "runtime_trace_feature_row_count_by_source": trace_by_source,
            "candidate_generation_training_row_count": len(generator_rows),
            "selector_training_row_count": len(selector_rows),
            "runtime_trace_feature_row_count": len(trace_rows),
            "candidate_generation_refresh_trace_row_count": len(refresh_trace_rows),
            "exact_trace_enrichment_trace_row_count": len(exact_trace_rows),
            "stage7_readiness_training_row_count": stage7_readiness_count,
        },
        "quality_checks": quality_checks,
        "selector_blockers": selector_blockers,
        "interpretation": {
            "candidate_generation_context_usable": len(generator_rows) > 0 and len(trace_rows) > 0,
            "selector_dataset_usable": False,
            "reason": (
                "V5 integrates exact trace enrichment sandbox traces as observation "
                "context and preserves candidate-generation capacity rows, but still "
                "has no explicit ownership selector labels."
            ),
        },
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "candidate_generation_v5_context_review_or_bounded_non_causal_probe"
                if status.endswith("selector_blocked")
                else "fix_dataset_v5_channel_semantics"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy-Sequence Dataset v5 Quality Probe",
        "",
        "This probe validates dataset v5 channel semantics. It does not train a selector or authorize runtime changes.",
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
    lines.extend(["", "## Selector Blockers", ""])
    lines.extend(f"- `{item}`" for item in payload["selector_blockers"])
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
