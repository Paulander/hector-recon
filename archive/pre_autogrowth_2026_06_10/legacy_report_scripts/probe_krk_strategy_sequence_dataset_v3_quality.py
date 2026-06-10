#!/usr/bin/env python3
"""Probe KRK strategy-sequence dataset v3 quality without enabling selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v3.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v3_quality_probe.json")
OUT_MD = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v3_quality_probe.md")


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
        row for row in rows if row.get("usable_for_candidate_generation_training_v3")
    ]
    selector_rows = [row for row in rows if row.get("usable_for_selector_training_v3")]
    trace_rows = [
        row for row in rows if row.get("evidence_channel") == "runtime_observation_trace_feature"
    ]
    stage7_readiness_count = int(summary.get("stage7_readiness_training_row_count", 0) or 0)
    quality_checks = {
        "stage7_excluded_from_readiness": stage7_readiness_count == 0,
        "selector_rows_absent_without_ownership_labels": len(selector_rows) == 0,
        "candidate_generation_rows_preserved": len(generator_rows) > 0,
        "stage5_6_refresh_trace_source_present": (
            trace_by_source.get("stage5_6_candidate_generation_refresh", 0) > 0
        ),
        "repair_monitor_trace_source_preserved": (
            trace_by_source.get("repair_monitor_observation", 0) > 0
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
    selector_blockers = ["no_explicit_ownership_selector_rows"]
    if trace_rows:
        selector_blockers.append("runtime_trace_features_are_context_not_selector_labels")
    if generator_rows:
        selector_blockers.append("capacity_rows_are_candidate_generation_not_ownership_labels")
    status = (
        "strategy_sequence_dataset_v3_quality_candidate_generation_context_ready_selector_blocked"
        if all(quality_checks.values())
        else "strategy_sequence_dataset_v3_quality_blocked"
    )
    return {
        "schema_version": "krk_strategy_sequence_dataset_v3_quality_probe.v1",
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
            "stage7_readiness_training_row_count": stage7_readiness_count,
        },
        "quality_checks": quality_checks,
        "selector_blockers": selector_blockers,
        "interpretation": {
            "candidate_generation_context_usable": len(generator_rows) > 0 and len(trace_rows) > 0,
            "selector_dataset_usable": False,
            "reason": (
                "V3 integrates Stage 5/6 refresh traces as observation context and "
                "preserves positive capacity rows for candidate-generation recall, "
                "but still has no explicit ownership selector labels."
            ),
        },
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "candidate_generation_v3_context_review_or_bounded_non_causal_probe"
                if status.endswith("selector_blocked")
                else "fix_dataset_v3_channel_semantics"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy-Sequence Dataset v3 Quality Probe",
        "",
        "This probe validates dataset v3 channel semantics. It does not train a selector or authorize runtime changes.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- row_count: {summary['row_count']}",
        f"- row_count_by_channel: `{summary['row_count_by_channel']}`",
        f"- runtime_trace_feature_row_count_by_source: `{summary['runtime_trace_feature_row_count_by_source']}`",
        f"- candidate_generation_training_row_count: {summary['candidate_generation_training_row_count']}",
        f"- selector_training_row_count: {summary['selector_training_row_count']}",
        f"- runtime_trace_feature_row_count: {summary['runtime_trace_feature_row_count']}",
        f"- stage7_readiness_training_row_count: {summary['stage7_readiness_training_row_count']}",
        "",
        "## Selector Blockers",
        "",
    ]
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
