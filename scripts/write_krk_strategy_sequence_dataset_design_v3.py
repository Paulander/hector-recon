#!/usr/bin/env python3
"""Write KRK strategy-sequence dataset design v3 with Stage 5/6 refresh traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STAGE5_6_TRACE = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_stage5_6_refresh_trace_features_v0.json"
)
OUT_JSON = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_design_v3.json")
OUT_MD = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_design_v3.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def build_payload(stage5_6_trace: dict[str, Any] | None = None) -> dict[str, Any]:
    stage5_6_trace = stage5_6_trace or _load(STAGE5_6_TRACE)
    trace_summary = stage5_6_trace.get("summary") or {}
    return {
        "schema_version": "krk_strategy_sequence_dataset_design.v3",
        "causal_status": "non_causal_design",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(STAGE5_6_TRACE)],
        "design_goal": (
            "Integrate the approved Stage 5/6 candidate-generation refresh observation "
            "frames into the strategy-sequence dataset as trace-only context, while "
            "preserving the split between candidate-generation capacity evidence and "
            "runtime ownership/selector labels."
        ),
        "inherits_from": "krk_strategy_sequence_dataset_design.v2",
        "new_trace_feature_sources": [
            {
                "source": "stage5_6_candidate_generation_refresh",
                "source_artifact": str(STAGE5_6_TRACE),
                "allowed_use": "candidate_generation_context_and_proposal_coverage_analysis",
                "forbidden_use": "selector_training_or_guardrail_trigger",
                "trace_frame_count": trace_summary.get("trace_frame_count"),
                "stage7_trace_frame_count": trace_summary.get("stage7_trace_frame_count"),
                "selector_training_row_count": trace_summary.get("selector_training_row_count"),
                "candidate_generation_training_row_count": trace_summary.get(
                    "candidate_generation_training_row_count"
                ),
            }
        ],
        "integration_rules": [
            "append trace-only rows without rewriting existing capacity labels",
            "set usable_for_selector_training_v3=false for all rows",
            "carry candidate-generation training rows only from protected positive capacity evidence",
            "preserve Stage 7 as held-out challenge evidence",
            "report runtime trace rows by source artifact",
            "block selector review unless explicit ownership labels exist",
        ],
        "decision": {
            "status": "strategy_sequence_dataset_design_v3_ready",
            "implementation_allowed_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "recommended_next_step": "implement_strategy_sequence_dataset_v3_non_causal",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Strategy-Sequence Dataset Design v3",
        "",
        payload["design_goal"],
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- implementation_allowed_by_this_artifact: `{payload['decision']['implementation_allowed_by_this_artifact']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## New Trace Feature Sources",
        "",
    ]
    for source in payload["new_trace_feature_sources"]:
        lines.extend(
            [
                f"### {source['source']}",
                "",
                f"- source_artifact: `{source['source_artifact']}`",
                f"- allowed_use: `{source['allowed_use']}`",
                f"- forbidden_use: `{source['forbidden_use']}`",
                f"- trace_frame_count: {source['trace_frame_count']}",
                f"- stage7_trace_frame_count: {source['stage7_trace_frame_count']}",
                f"- selector_training_row_count: {source['selector_training_row_count']}",
                f"- candidate_generation_training_row_count: {source['candidate_generation_training_row_count']}",
                "",
            ]
        )
    lines.extend(["## Integration Rules", ""])
    lines.extend(f"- `{item}`" for item in payload["integration_rules"])
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
