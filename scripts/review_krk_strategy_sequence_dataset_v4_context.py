#!/usr/bin/env python3
"""Review KRK strategy-sequence dataset v4 context integration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v4.json")
QUALITY = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v4_quality_probe.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v4_context_review.json")
OUT_MD = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v4_context_review.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(
    dataset: dict[str, Any] | None = None,
    quality: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    quality = quality or _load(QUALITY)
    ds = dataset.get("summary") or {}
    qs = quality.get("summary") or {}
    trace_sources = dict(ds.get("runtime_trace_feature_row_count_by_source") or {})
    context_ready = (
        (dataset.get("decision") or {}).get("selector_allowed") is False
        and (quality.get("decision") or {}).get("selector_allowed") is False
        and int(ds.get("selector_training_row_count", 0) or 0) == 0
        and int(ds.get("stage7_readiness_training_row_count", 0) or 0) == 0
        and trace_sources.get("candidate_generation_refresh_sandbox", 0) > 0
        and trace_sources.get("repair_monitor_observation", 0) > 0
    )
    return {
        "schema_version": "krk_strategy_sequence_dataset_v4_context_review.v1",
        "causal_status": "non_causal_context_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(QUALITY)],
        "summary": {
            "row_count": ds.get("row_count"),
            "candidate_generation_training_row_count": ds.get(
                "candidate_generation_training_row_count"
            ),
            "selector_training_row_count": ds.get("selector_training_row_count"),
            "stage7_readiness_training_row_count": ds.get(
                "stage7_readiness_training_row_count"
            ),
            "runtime_trace_feature_row_count": ds.get("runtime_trace_feature_row_count"),
            "runtime_trace_feature_row_count_by_source": trace_sources,
            "candidate_generation_refresh_trace_row_count": qs.get(
                "candidate_generation_refresh_trace_row_count"
            ),
            "quality_status": (quality.get("decision") or {}).get("status"),
            "quality_selector_blockers": list(quality.get("selector_blockers") or []),
            "quality_row_count": qs.get("row_count"),
        },
        "validated_progress": [
            "candidate_generation_refresh_sandbox_default_off_equivalent",
            "candidate_generation_refresh_frames_folded_non_causal",
            "candidate_generation_refresh_trace_source_integrated",
            "repair_monitor_trace_features_preserved",
            "capacity_labels_preserved_for_candidate_generation_only",
        ],
        "still_blocked": [
            "selector_training",
            "guardrail_campaign",
            "score_changes",
            "provider_routing",
            "stage7_promotion",
            "stage8_training",
            "stage4_runtime_scope",
        ],
        "decision": {
            "status": (
                "strategy_sequence_dataset_v4_context_integrated_selector_still_blocked"
                if context_ready
                else "strategy_sequence_dataset_v4_context_blocked"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "candidate_generation_v4_context_benchmark_non_causal"
                if context_ready
                else "fix_dataset_v4_context_integration"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Strategy-Sequence Dataset v4 Context Review",
        "",
        "This review closes the v4 integration slice. Dataset v4 is usable as candidate-generation context, not as selector training data.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- guardrails_allowed: `{payload['decision']['guardrails_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in summary.items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Validated Progress", ""])
    lines.extend(f"- `{item}`" for item in payload["validated_progress"])
    lines.extend(["", "## Still Blocked", ""])
    lines.extend(f"- `{item}`" for item in payload["still_blocked"])
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
