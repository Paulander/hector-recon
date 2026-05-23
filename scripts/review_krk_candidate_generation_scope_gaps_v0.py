#!/usr/bin/env python3
"""Review scope gaps before another KRK candidate-generation runtime boundary."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v4.json")
BENCHMARK = Path("reports/strategy_arbitration/krk_candidate_generation_v4_context_benchmark.json")
BOUNDARY = Path(
    "reports/strategy_arbitration/krk_candidate_generation_v4_next_runtime_boundary_review_v0.json"
)
OUT_JSON = Path("reports/strategy_arbitration/krk_candidate_generation_scope_gap_review_v0.json")
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_generation_scope_gap_review_v0.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _num(value: Any) -> float:
    return float(value or 0.0)


def build_payload(
    dataset: dict[str, Any] | None = None,
    benchmark: dict[str, Any] | None = None,
    boundary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    benchmark = benchmark or _load(BENCHMARK)
    boundary = boundary or _load(BOUNDARY)
    rows = [row for row in dataset.get("rows") or [] if isinstance(row, dict)]
    capacity_rows = [
        row
        for row in rows
        if row.get("evidence_channel") == "validated_provider_capacity"
        and not row.get("stage7_challenge_row")
    ]
    trace_rows = [
        row
        for row in rows
        if row.get("evidence_channel") == "runtime_observation_trace_feature"
        and not row.get("stage7_challenge_row")
    ]
    capacity_by_stage = Counter(str(row.get("source_stage") or "unknown") for row in capacity_rows)
    trace_by_stage = Counter(str(row.get("source_stage") or "unknown") for row in trace_rows)
    capacity_by_family = Counter(
        str(row.get("candidate_strategy_family") or "unknown") for row in capacity_rows
    )
    trace_by_family = Counter(
        str(row.get("candidate_strategy_family") or "unknown") for row in trace_rows
    )
    bsummary = benchmark.get("summary") or {}
    exact_recall = _num(bsummary.get("exact_positive_capacity_recall_from_refresh_trace"))
    policy_cell_recall = _num(
        bsummary.get("policy_cell_positive_capacity_recall_from_refresh_trace")
    )
    negative_exposure = _num(
        bsummary.get("policy_cell_negative_capacity_exposure_from_refresh_trace")
    )
    selector_rows = int(bsummary.get("selector_training_row_count", 0) or 0)
    stage7_rows = int(bsummary.get("stage7_readiness_training_row_count", 0) or 0)
    gaps = []
    if exact_recall < 0.5:
        gaps.append("exact_move_provider_coverage_partial")
    if selector_rows == 0:
        gaps.append("ownership_selector_labels_absent")
    if "stage4" not in trace_by_stage:
        gaps.append("stage4_runtime_scope_unreviewed")
    if not any("plan" in family for family in trace_by_family):
        gaps.append("plan_sequence_candidate_trace_missing")
    if stage7_rows == 0:
        gaps.append("stage7_held_out_only")
    if negative_exposure > 0.0:
        gaps.append("negative_capacity_exposure_requires_filtering")
    new_runtime_blocked = (
        (boundary.get("decision") or {}).get("runtime_changes_allowed") is False
        and ("exact_move_provider_coverage_partial" in gaps or selector_rows == 0)
    )
    return {
        "schema_version": "krk_candidate_generation_scope_gap_review.v1",
        "causal_status": "non_causal_scope_gap_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(DATASET), str(BENCHMARK), str(BOUNDARY)],
        "summary": {
            "capacity_row_count": len(capacity_rows),
            "trace_row_count": len(trace_rows),
            "capacity_by_stage": dict(sorted(capacity_by_stage.items())),
            "trace_by_stage": dict(sorted(trace_by_stage.items())),
            "capacity_by_family": dict(sorted(capacity_by_family.items())),
            "trace_by_family": dict(sorted(trace_by_family.items())),
            "exact_positive_capacity_recall_from_refresh_trace": exact_recall,
            "policy_cell_positive_capacity_recall_from_refresh_trace": policy_cell_recall,
            "policy_cell_negative_capacity_exposure_from_refresh_trace": negative_exposure,
            "selector_training_row_count": selector_rows,
            "stage7_readiness_training_row_count": stage7_rows,
        },
        "scope_gaps": gaps,
        "gap_interpretation": {
            "candidate_generation_context_promising": policy_cell_recall >= 0.7,
            "new_runtime_boundary_blocked": new_runtime_blocked,
            "selection_blocked_by_label_semantics": selector_rows == 0,
            "stage4_requires_separate_review": "stage4_runtime_scope_unreviewed" in gaps,
            "stage7_remains_challenge_only": stage7_rows == 0,
        },
        "candidate_next_non_causal_slices": [
            {
                "slice": "candidate_source_gap_manifest",
                "purpose": "Identify which positive-capacity stage/family cells lack exact runtime-observation trace coverage.",
                "runtime_allowed": False,
            },
            {
                "slice": "protected_stage4_scope_review",
                "purpose": "Decide whether Stage 4 can be added to candidate-generation observation scope without changing behavior.",
                "runtime_allowed": False,
            },
            {
                "slice": "plan_sequence_candidate_trace_review",
                "purpose": "Review whether PlanCapsule/sequence candidates need observation frames distinct from provider-pack candidates.",
                "runtime_allowed": False,
            },
        ],
        "still_forbidden": [
            "selector_training",
            "score_changes",
            "provider_routing",
            "new_runtime_sandbox_without_review_packet",
            "guardrail_campaign_from_context_only",
            "stage7_promotion",
            "stage8_training",
        ],
        "decision": {
            "status": (
                "candidate_generation_scope_gap_review_blocks_new_runtime_boundary"
                if new_runtime_blocked
                else "candidate_generation_scope_gap_review_ready_for_runtime_packet"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "candidate_source_gap_manifest_non_causal"
                if "exact_move_provider_coverage_partial" in gaps
                else "protected_stage4_scope_review_non_causal"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation Scope Gap Review v0",
        "",
        "This non-causal review identifies what is still missing before any new candidate-generation runtime boundary can be considered.",
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
    lines.extend(["", "## Scope Gaps", ""])
    lines.extend(f"- `{gap}`" for gap in payload["scope_gaps"])
    lines.extend(["", "## Candidate Next Non-Causal Slices", ""])
    for item in payload["candidate_next_non_causal_slices"]:
        lines.append(
            f"- `{item['slice']}`: {item['purpose']} runtime_allowed=`{item['runtime_allowed']}`"
        )
    lines.extend(["", "## Still Forbidden", ""])
    lines.extend(f"- `{item}`" for item in payload["still_forbidden"])
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
