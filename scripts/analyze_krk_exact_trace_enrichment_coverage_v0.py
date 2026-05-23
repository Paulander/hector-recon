#!/usr/bin/env python3
"""Analyze KRK exact trace enrichment sandbox frames.

This is a replay-free coverage analysis over emitted candidate-generation-only
frames. It does not authorize selector behavior, score changes, routing, or
guardrails.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SANDBOX = Path("reports/strategy_arbitration/krk_exact_trace_enrichment_sandbox_v0.json")
GAPS = Path("reports/strategy_arbitration/krk_candidate_source_gap_manifest_v0.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_exact_trace_enrichment_coverage_analysis_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_exact_trace_enrichment_coverage_analysis_v0.md"
)

APPROVED_CELLS = {
    ("stage5", "edge_trap"),
    ("stage5", "stage0_basin"),
    ("stage6", "stage0_basin"),
}


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


def _frame_key(frame: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(frame.get("state_fen") or ""),
        str(frame.get("provider_id") or ""),
        str(frame.get("move_id") or ""),
    )


def _row_key(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(row.get("fen") or ""),
        str(row.get("candidate_provider_id") or ""),
        str(row.get("candidate_move_uci") or ""),
    )


def _cell_from_frame(frame: dict[str, Any]) -> tuple[str, str]:
    return (str(frame.get("stage") or ""), str(frame.get("provider_family") or ""))


def _cell_from_row(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("source_stage") or ""),
        str(row.get("candidate_strategy_family") or ""),
    )


def _iter_exact_frames(sandbox: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for case in sandbox.get("cases") or []:
        if not isinstance(case, dict):
            continue
        for frame in case.get("enabled_exact_frames") or []:
            if not isinstance(frame, dict):
                continue
            if frame.get("candidate_source") != "exact_trace_enrichment":
                continue
            frames.append(
                {
                    **frame,
                    "_case_id": case.get("case_id"),
                    "_case_stage": case.get("source_stage"),
                    "_case_fen": case.get("fen"),
                }
            )
    return frames


def _target_gap_rows(gaps: dict[str, Any], fens: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in gaps.get("gap_records") or []:
        if not isinstance(row, dict):
            continue
        if row.get("gap_type") != "policy_cell_covered_exact_missing":
            continue
        if row.get("stage7_challenge_row"):
            continue
        if _cell_from_row(row) not in APPROVED_CELLS:
            continue
        if str(row.get("fen") or "") not in fens:
            continue
        rows.append(row)
    return rows


def analyze(
    sandbox: dict[str, Any] | None = None,
    gaps: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sandbox = sandbox or _load(SANDBOX)
    gaps = gaps or _load(GAPS)
    frames = _iter_exact_frames(sandbox)
    fens = {str(case.get("fen") or "") for case in sandbox.get("cases") or [] if case.get("fen")}
    target_rows = _target_gap_rows(gaps, fens)
    emitted_keys = {_frame_key(frame) for frame in frames}
    emitted_cells = {_cell_from_frame(frame) for frame in frames}
    exact_hits = [row for row in target_rows if _row_key(row) in emitted_keys]
    cell_hits = [row for row in target_rows if _cell_from_row(row) in emitted_cells]
    invalid_frames = [
        frame
        for frame in frames
        if _cell_from_frame(frame) not in APPROVED_CELLS
        or frame.get("policy") != "trace_stage_family_context"
        or frame.get("direct_request") is not False
        or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
        or frame.get("causal_status") != "candidate_generation_only"
        or frame.get("protected_status") != "protected_control"
    ]
    stage_counts = Counter(str(frame.get("stage") or "unknown") for frame in frames)
    family_counts = Counter(str(frame.get("provider_family") or "unknown") for frame in frames)
    policy_cell_counts = Counter(
        f"{stage}|{family}" for stage, family in (_cell_from_frame(frame) for frame in frames)
    )
    source_summary = sandbox.get("summary") or {}
    exact_recall = len(exact_hits) / len(target_rows) if target_rows else 0.0
    cell_recall = len(cell_hits) / len(target_rows) if target_rows else 0.0
    ready = (
        (sandbox.get("decision") or {}).get("status")
        == "exact_trace_enrichment_sandbox_ready_for_non_causal_coverage_analysis"
        and bool(frames)
        and not invalid_frames
        and source_summary.get("selected_move_delta_count") == 0
        and source_summary.get("selected_provider_delta_count") == 0
        and source_summary.get("score_delta_count") == 0
        and stage_counts.get("stage4", 0) == 0
        and stage_counts.get("stage7", 0) == 0
    )
    return {
        "schema_version": "krk_exact_trace_enrichment_coverage_analysis.v0",
        "causal_status": "non_causal_candidate_generation_frame_coverage_analysis",
        **_runtime_false_block(),
        "source_artifacts": [str(SANDBOX), str(GAPS)],
        "summary": {
            "case_count": len(sandbox.get("cases") or []),
            "emitted_exact_frame_count": len(frames),
            "emitted_frame_count_by_stage": dict(sorted(stage_counts.items())),
            "emitted_frame_count_by_provider_family": dict(sorted(family_counts.items())),
            "emitted_frame_count_by_policy_cell": dict(sorted(policy_cell_counts.items())),
            "target_gap_rows_in_sample": len(target_rows),
            "exact_gap_hits": len(exact_hits),
            "exact_gap_recall": exact_recall,
            "policy_cell_gap_hits": len(cell_hits),
            "policy_cell_gap_recall": cell_recall,
            "truncation_count": int(source_summary.get("truncation_count", 0) or 0),
            "truncated_frame_count": int(source_summary.get("truncated_frame_count", 0) or 0),
            "invalid_frame_count": len(invalid_frames),
            "selected_move_delta_count": int(source_summary.get("selected_move_delta_count", 0) or 0),
            "selected_provider_delta_count": int(source_summary.get("selected_provider_delta_count", 0) or 0),
            "score_delta_count": int(source_summary.get("score_delta_count", 0) or 0),
            "stage4_frame_count": stage_counts.get("stage4", 0),
            "stage7_frame_count": stage_counts.get("stage7", 0),
        },
        "interpretation": {
            "approved_cells_only": not invalid_frames,
            "exact_gap_coverage_visible": exact_recall > 0,
            "negative_or_selector_evidence_added": False,
            "selector_supported": False,
            "guardrails_supported": False,
            "capacity_gap_labels_are_not_ownership_labels": True,
        },
        "missed_target_gap_rows": [
            {
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "candidate_strategy_family": row.get("candidate_strategy_family"),
                "candidate_provider_id": row.get("candidate_provider_id"),
                "candidate_move_uci": row.get("candidate_move_uci"),
            }
            for row in target_rows
            if _row_key(row) not in emitted_keys
        ],
        "invalid_frames": invalid_frames[:10],
        "decision": {
            "status": (
                "exact_trace_enrichment_coverage_ready_for_trace_dataset_refresh"
                if ready
                else "exact_trace_enrichment_coverage_blocked"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "fold_exact_trace_enrichment_frames_into_non_causal_strategy_sequence_trace_dataset"
                if ready
                else "quarantine_or_fix_exact_trace_enrichment_frame_emission"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    interpretation = payload["interpretation"]
    lines = [
        "# KRK Exact Trace Enrichment Coverage Analysis v0",
        "",
        "This replay-free analysis evaluates emitted candidate-generation-only exact trace enrichment frames. It does not authorize selection, scoring, routing, guardrails, promotion, or Stage 8 training.",
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
    lines.extend(f"- {key}: `{value}`" for key, value in interpretation.items())
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "The emitted frames expand visible candidate-generation context only. Capacity gap labels remain capacity evidence, not selector or ownership labels.",
        ]
    )
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = analyze()
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
