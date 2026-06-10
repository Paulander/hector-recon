#!/usr/bin/env python3
"""Analyze the approved KRK candidate-generation refresh sandbox frames.

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
SANDBOX = Path("reports/strategy_arbitration/krk_candidate_generation_refresh_sandbox_v0.json")
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v3.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_coverage_analysis_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_refresh_coverage_analysis_v0.md"
)

APPROVED_CELLS = {
    ("stage5", "edge_trap"),
    ("stage5", "fence_established"),
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
    return (
        str(frame.get("stage") or ""),
        str(frame.get("provider_family") or ""),
    )


def _cell_from_row(row: dict[str, Any]) -> tuple[str, str]:
    return (
        str(row.get("source_stage") or ""),
        str(row.get("candidate_strategy_family") or ""),
    )


def _iter_refresh_frames(sandbox: dict[str, Any]) -> list[dict[str, Any]]:
    frames: list[dict[str, Any]] = []
    for case in sandbox.get("cases") or []:
        if not isinstance(case, dict):
            continue
        for frame in case.get("enabled_refresh_frames") or []:
            if not isinstance(frame, dict):
                continue
            if frame.get("candidate_source") != "stage_conditioned_candidate_generation_refresh":
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


def _capacity_rows_for_sample(dataset: dict[str, Any], fens: set[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in dataset.get("rows") or []:
        if not isinstance(row, dict):
            continue
        if row.get("stage7_challenge_row"):
            continue
        if row.get("evidence_channel") != "validated_provider_capacity":
            continue
        if row.get("capacity_label") not in {"positive_capacity", "negative_capacity"}:
            continue
        if str(row.get("fen") or "") not in fens:
            continue
        rows.append(row)
    return rows


def analyze(
    sandbox: dict[str, Any] | None = None,
    dataset: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sandbox = sandbox or _load(SANDBOX)
    dataset = dataset or _load(DATASET)
    frames = _iter_refresh_frames(sandbox)
    fens = {str(case.get("fen") or "") for case in sandbox.get("cases") or [] if case.get("fen")}
    capacity_rows = _capacity_rows_for_sample(dataset, fens)
    approved_positive_rows = [
        row
        for row in capacity_rows
        if row.get("capacity_label") == "positive_capacity"
        and _cell_from_row(row) in APPROVED_CELLS
    ]
    negative_rows = [
        row for row in capacity_rows if row.get("capacity_label") == "negative_capacity"
    ]
    emitted_keys = {_frame_key(frame) for frame in frames}
    emitted_cells = {_cell_from_frame(frame) for frame in frames}
    emitted_positive_capacity_keys = {
        _frame_key(frame)
        for frame in frames
        if frame.get("capacity_evidence_kind") == "positive_capacity"
    }
    exact_positive_hits = [
        row for row in approved_positive_rows if _row_key(row) in emitted_keys
    ]
    exact_negative_exposures = [
        row for row in negative_rows if _row_key(row) in emitted_keys
    ]
    stage_family_positive_hits = [
        row for row in approved_positive_rows if _cell_from_row(row) in emitted_cells
    ]
    stage_family_negative_exposures = [
        row for row in negative_rows if _cell_from_row(row) in emitted_cells
    ]
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
    evidence_counts = Counter(str(frame.get("capacity_evidence_kind") or "unknown") for frame in frames)
    policy_cell_counts = Counter(
        f"{stage}|{family}" for stage, family in (_cell_from_frame(frame) for frame in frames)
    )
    source_summary = sandbox.get("summary") or {}
    exact_recall = (
        len(exact_positive_hits) / len(approved_positive_rows)
        if approved_positive_rows
        else 0.0
    )
    stage_family_recall = (
        len(stage_family_positive_hits) / len(approved_positive_rows)
        if approved_positive_rows
        else 0.0
    )
    exact_negative_exposure = (
        len(exact_negative_exposures) / len(negative_rows) if negative_rows else 0.0
    )
    stage_family_negative_exposure = (
        len(stage_family_negative_exposures) / len(negative_rows) if negative_rows else 0.0
    )
    ready = (
        (sandbox.get("decision") or {}).get("status")
        == "candidate_generation_refresh_sandbox_ready_for_non_causal_coverage_analysis"
        and bool(frames)
        and not invalid_frames
        and source_summary.get("selected_move_delta_count") == 0
        and source_summary.get("selected_provider_delta_count") == 0
        and source_summary.get("score_delta_count") == 0
        and stage_counts.get("stage4", 0) == 0
        and stage_counts.get("stage7", 0) == 0
    )
    return {
        "schema_version": "krk_candidate_generation_refresh_coverage_analysis.v0",
        "causal_status": "non_causal_candidate_generation_frame_coverage_analysis",
        **_runtime_false_block(),
        "source_artifacts": [str(SANDBOX), str(DATASET)],
        "summary": {
            "case_count": len(sandbox.get("cases") or []),
            "emitted_refresh_frame_count": len(frames),
            "emitted_frame_count_by_stage": dict(sorted(stage_counts.items())),
            "emitted_frame_count_by_provider_family": dict(sorted(family_counts.items())),
            "emitted_frame_count_by_policy_cell": dict(sorted(policy_cell_counts.items())),
            "capacity_evidence_counts": dict(sorted(evidence_counts.items())),
            "approved_positive_capacity_rows_in_sample": len(approved_positive_rows),
            "negative_capacity_rows_in_sample": len(negative_rows),
            "exact_positive_capacity_hits": len(exact_positive_hits),
            "exact_positive_capacity_recall": exact_recall,
            "stage_family_positive_capacity_hits": len(stage_family_positive_hits),
            "stage_family_positive_capacity_recall": stage_family_recall,
            "exact_negative_capacity_exposures": len(exact_negative_exposures),
            "exact_negative_capacity_exposure_rate": exact_negative_exposure,
            "stage_family_negative_capacity_exposures": len(stage_family_negative_exposures),
            "stage_family_negative_capacity_exposure_rate": stage_family_negative_exposure,
            "positive_capacity_frame_count": len(emitted_positive_capacity_keys),
            "positive_capacity_scope_frame_count": evidence_counts.get(
                "positive_capacity_scope",
                0,
            ),
            "truncation_count": int(source_summary.get("truncation_count", 0) or 0),
            "truncated_frame_count": int(source_summary.get("truncated_frame_count", 0) or 0),
            "invalid_frame_count": len(invalid_frames),
            "selected_move_delta_count": int(source_summary.get("selected_move_delta_count", 0) or 0),
            "selected_provider_delta_count": int(
                source_summary.get("selected_provider_delta_count", 0) or 0
            ),
            "score_delta_count": int(source_summary.get("score_delta_count", 0) or 0),
            "stage4_frame_count": stage_counts.get("stage4", 0),
            "stage7_frame_count": stage_counts.get("stage7", 0),
        },
        "interpretation": {
            "approved_cells_only": not invalid_frames,
            "exact_capacity_recall_is_sample_limited": exact_recall < stage_family_recall,
            "stage_family_context_visible": stage_family_recall > 0,
            "negative_capacity_suppression_preserved_in_sample": (
                stage_family_negative_exposure == 0.0
            ),
            "candidate_volume_bound_exercised": int(source_summary.get("truncation_count", 0) or 0) > 0,
            "selector_supported": False,
            "guardrails_supported": False,
            "capacity_labels_are_not_ownership_labels": True,
        },
        "missed_approved_positive_capacity_rows": [
            {
                "state_id": row.get("state_id"),
                "source_stage": row.get("source_stage"),
                "candidate_strategy_family": row.get("candidate_strategy_family"),
                "candidate_provider_id": row.get("candidate_provider_id"),
                "candidate_move_uci": row.get("candidate_move_uci"),
            }
            for row in approved_positive_rows
            if _row_key(row) not in emitted_keys
        ],
        "invalid_frames": invalid_frames[:10],
        "decision": {
            "status": (
                "candidate_generation_refresh_coverage_ready_for_trace_dataset_refresh"
                if ready
                else "candidate_generation_refresh_coverage_blocked"
            ),
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": (
                "fold_refresh_sandbox_frames_into_non_causal_strategy_sequence_trace_dataset"
                if ready
                else "quarantine_or_fix_candidate_generation_refresh_frame_emission"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    interpretation = payload["interpretation"]
    lines = [
        "# KRK Candidate-Generation Refresh Coverage Analysis v0",
        "",
        "This replay-free analysis evaluates emitted candidate-generation-only refresh frames from the approved default-off sandbox. It does not authorize selection, scoring, routing, guardrails, promotion, or Stage 8 training.",
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
            "The emitted frames expand visible candidate-generation context only. Capacity labels remain capacity evidence, not selector or ownership labels.",
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
