#!/usr/bin/env python3
"""Build KRK strategy-sequence dataset v5 with exact trace enrichment context."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BASE_DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v4.json")
EXACT_TRACE = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_exact_trace_enrichment_trace_features_v1.json"
)
DESIGN = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_design_v3.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5.json")
OUT_MD = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v5.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _runtime_false_block() -> dict[str, bool]:
    return {
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
    }


def _normalize_existing_row(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized["schema_version"] = "krk_strategy_sequence_dataset_row.v5"
    normalized["usable_for_selector_training_v5"] = False
    normalized["usable_for_candidate_generation_training_v5"] = bool(
        row.get("usable_for_candidate_generation_training_v4")
    )
    normalized["causal_status"] = "non_causal_dataset_row"
    return normalized


def _row_from_exact_trace_frame(frame: dict[str, Any]) -> dict[str, Any]:
    capacity = frame.get("capacity_evidence") or {}
    ownership = frame.get("ownership_evidence") or {}
    sequence = frame.get("sequence_evidence") or {}
    return {
        "schema_version": "krk_strategy_sequence_dataset_row.v5",
        "row_id": frame.get("frame_id"),
        "state_id": frame.get("state_id"),
        "fen": frame.get("fen"),
        "source_stage": frame.get("source_stage"),
        "active_landmark_label": frame.get("active_landmark_label"),
        "evidence_channel": "runtime_observation_trace_feature",
        "trace_feature_source": "exact_trace_enrichment_sandbox",
        "frame_type": frame.get("frame_type"),
        "candidate_strategy_family": frame.get("candidate_strategy_family"),
        "candidate_provider_id": frame.get("candidate_provider_id"),
        "candidate_move_uci": frame.get("candidate_move_uci"),
        "label_semantics": frame.get("label_semantics"),
        "stage7_challenge_row": False,
        "legacy_usable_for_selector_training": bool(frame.get("usable_for_selector_training")),
        "usable_for_selector_training_v5": False,
        "usable_for_candidate_generation_training_v5": False,
        "capacity_label": capacity.get("capacity_label"),
        "capacity_label_semantics": capacity.get("label_semantics"),
        "ownership_label_semantics": ownership.get("label_semantics"),
        "selected_provider_before_observation": ownership.get(
            "selected_provider_before_observation"
        ),
        "selected_move_before_observation": ownership.get("selected_move_before_observation"),
        "source_terms": list(frame.get("source_terms") or []),
        "move_shape_terms": list(frame.get("move_shape_terms") or []),
        "post_move_terms": list(frame.get("post_move_terms") or []),
        "safety_terms": list(frame.get("safety_terms") or []),
        "internal_monitor_terms": list(frame.get("internal_monitor_terms") or []),
        "sequence_evidence_keys": sorted(sequence.keys()),
        "policy": sequence.get("policy"),
        "policy_cell": sequence.get("policy_cell"),
        "exact_enrichment_reason": sequence.get("exact_enrichment_reason"),
        "source_artifact": str(EXACT_TRACE),
        "causal_status": "non_causal_dataset_row",
    }


def _summarize(rows: list[dict[str, Any]], added_rows: list[dict[str, Any]]) -> dict[str, Any]:
    channel_counts = Counter(row.get("evidence_channel") for row in rows)
    trace_source_counts = Counter(
        str(row.get("trace_feature_source") or "none")
        for row in rows
        if row.get("evidence_channel") == "runtime_observation_trace_feature"
    )
    stage_counts = Counter(str(row.get("source_stage") or "unknown") for row in rows)
    generator_counts = Counter(
        row.get("evidence_channel")
        for row in rows
        if row.get("usable_for_candidate_generation_training_v5")
    )
    return {
        "row_count": len(rows),
        "added_exact_trace_enrichment_row_count": len(added_rows),
        "row_count_by_channel": dict(sorted(channel_counts.items())),
        "runtime_trace_feature_row_count_by_source": dict(sorted(trace_source_counts.items())),
        "source_stage_counts": dict(sorted(stage_counts.items())),
        "candidate_generation_training_row_count": sum(
            1 for row in rows if row.get("usable_for_candidate_generation_training_v5")
        ),
        "candidate_generation_training_row_count_by_channel": dict(
            sorted(generator_counts.items())
        ),
        "selector_training_row_count": sum(
            1 for row in rows if row.get("usable_for_selector_training_v5")
        ),
        "stage7_challenge_row_count": sum(1 for row in rows if row.get("stage7_challenge_row")),
        "stage7_readiness_training_row_count": sum(
            1
            for row in rows
            if row.get("stage7_challenge_row")
            and (
                row.get("usable_for_selector_training_v5")
                or row.get("usable_for_candidate_generation_training_v5")
            )
        ),
        "runtime_trace_feature_row_count": channel_counts.get(
            "runtime_observation_trace_feature",
            0,
        ),
    }


def build_payload(
    *,
    base_dataset: dict[str, Any] | None = None,
    exact_trace: dict[str, Any] | None = None,
    design: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_dataset = base_dataset or _load(BASE_DATASET)
    exact_trace = exact_trace or _load(EXACT_TRACE)
    design = design or _load(DESIGN)
    if (exact_trace.get("decision") or {}).get("selector_allowed") is not False:
        raise ValueError("exact trace source must not authorize selector use")
    rows = [
        _normalize_existing_row(row)
        for row in base_dataset.get("rows") or []
        if isinstance(row, dict)
    ]
    added_rows = [
        _row_from_exact_trace_frame(frame)
        for frame in exact_trace.get("trace_only_frames") or []
        if isinstance(frame, dict)
    ]
    rows.extend(added_rows)
    summary = _summarize(rows, added_rows)
    return {
        "schema_version": "krk_strategy_sequence_dataset.v5",
        "causal_status": "non_causal_dataset_refresh",
        **_runtime_false_block(),
        "source_artifacts": [str(BASE_DATASET), str(EXACT_TRACE), str(DESIGN)],
        "design_version": design.get("schema_version"),
        "summary": summary,
        "rows": rows,
        "decision": {
            "status": "strategy_sequence_dataset_v5_refreshed_non_causal_selector_blocked",
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "probe_strategy_sequence_dataset_v5_quality_non_causal",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy-Sequence Dataset v5",
        "",
        "This non-causal dataset refresh appends approved exact trace enrichment sandbox trace features to dataset v4. It does not authorize selector behavior.",
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
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "V5 keeps all selector-training rows false. Exact trace enrichment rows are runtime-observation context only, not capacity labels, ownership labels, routing requests, or score changes.",
        ]
    )
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
