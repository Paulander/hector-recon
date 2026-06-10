#!/usr/bin/env python3
"""Build a targeted cross-stage capacity manifest for candidate generation."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MERGED_DATASET = Path(
    "reports/strategy_arbitration/krk_strategy_sequence_dataset_v2_capacity_merged.json"
)
CROSS_STAGE_REVIEW = Path(
    "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_review_v2.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_manifest_v3.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_candidate_generation_cross_stage_capacity_manifest_v3.md"
)


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _job_id(row: dict[str, Any]) -> str:
    key = "|".join(
        str(row.get(part) or "")
        for part in ("state_id", "candidate_provider_id", "candidate_move_uci")
    )
    digest = hashlib.sha1(f"{key}|cross_stage_capacity_v3".encode()).hexdigest()[:12]
    return f"job.krk.cg_cross_stage_v3.{digest}"


def _known_capacity_pairs(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    known = set()
    for row in rows:
        if row.get("evidence_channel") != "validated_provider_capacity":
            continue
        state_id = row.get("state_id")
        provider = row.get("candidate_provider_id")
        if state_id and provider:
            known.add((str(state_id), str(provider)))
    return known


def _target_cells(review: dict[str, Any]) -> dict[str, str]:
    findings = review.get("findings") or {}
    priority: dict[str, str] = {}
    for key in findings.get("underpowered_cells") or []:
        priority[str(key)] = "underpowered_cell"
    for key in findings.get("positive_only_cells") or []:
        priority[str(key)] = "positive_only_cell"
    for key in findings.get("negative_only_cells") or []:
        priority[str(key)] = "negative_only_cell"
    for key in findings.get("mixed_capacity_cells") or []:
        priority[str(key)] = "mixed_capacity_cell"
    return priority


def _candidate_rows(dataset: dict[str, Any], target_cells: dict[str, str]) -> list[dict[str, Any]]:
    rows = list(dataset.get("rows") or [])
    known = _known_capacity_pairs(rows)
    candidates = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if row.get("stage7_challenge_row"):
            continue
        if row.get("evidence_channel") != "visible_provider_proposal":
            continue
        state_id = str(row.get("state_id") or "")
        provider = str(row.get("candidate_provider_id") or "")
        move = str(row.get("candidate_move_uci") or "")
        stage = str(row.get("source_stage") or "unknown")
        family = str(row.get("candidate_strategy_family") or "unknown")
        cell = f"{stage}|{family}"
        if cell not in target_cells:
            continue
        if not state_id or not provider:
            continue
        if (state_id, provider) in known:
            continue
        key = (state_id, provider, move)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(row)
    return candidates


def _select_rows(
    candidates: list[dict[str, Any]], target_cells: dict[str, str], *, cap: int
) -> list[dict[str, Any]]:
    rank = {
        "underpowered_cell": 0,
        "positive_only_cell": 1,
        "negative_only_cell": 1,
        "mixed_capacity_cell": 2,
    }
    by_cell: Counter[str] = Counter()

    def sort_key(row: dict[str, Any]) -> tuple[int, int, str, str, str]:
        cell = f"{row.get('source_stage')}|{row.get('candidate_strategy_family')}"
        return (
            rank.get(target_cells.get(cell, "mixed_capacity_cell"), 9),
            by_cell[cell],
            cell,
            str(row.get("state_id") or ""),
            str(row.get("candidate_provider_id") or ""),
        )

    selected: list[dict[str, Any]] = []
    pool = list(candidates)
    while pool and len(selected) < cap:
        pool.sort(key=sort_key)
        row = pool.pop(0)
        cell = f"{row.get('source_stage')}|{row.get('candidate_strategy_family')}"
        if by_cell[cell] >= 3:
            continue
        selected.append(row)
        by_cell[cell] += 1
    return selected


def build_payload(
    dataset: dict[str, Any] | None = None,
    review: dict[str, Any] | None = None,
    *,
    cap: int = 12,
) -> dict[str, Any]:
    dataset = dataset or _load(MERGED_DATASET)
    review = review or _load(CROSS_STAGE_REVIEW)
    targets = _target_cells(review)
    candidates = _candidate_rows(dataset, targets)
    selected = _select_rows(candidates, targets, cap=cap)
    candidate_cells = {f"{row.get('source_stage')}|{row.get('candidate_strategy_family')}" for row in candidates}
    unavailable_targets = sorted(set(targets) - candidate_cells)
    jobs = []
    for row in selected:
        cell = f"{row.get('source_stage')}|{row.get('candidate_strategy_family')}"
        jobs.append(
            {
                "schema_version": "krk_candidate_generation_cross_stage_capacity_job.v3",
                "job_id": _job_id(row),
                "causal_status": "offline_label_manifest_only",
                "state_id": row.get("state_id"),
                "fen": row.get("fen"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "provider_id": row.get("candidate_provider_id"),
                "provider_family": row.get("candidate_strategy_family"),
                "stage_family_cell": cell,
                "target_cell_maturity": targets.get(cell),
                "observed_move_uci": row.get("candidate_move_uci"),
                "horizon": 40,
                "label_request": "force_provider_then_h40_continuation",
                "label_semantics": "forced_provider_capacity_not_runtime_ownership",
                "stage7_training_row": False,
                "runtime_use_allowed": False,
                "selector_training_allowed": False,
                "candidate_generation_training_use": (
                    "allowed_only_after_merge_review_if_positive_capacity"
                ),
                "source_terms": list(row.get("source_terms") or []),
                "move_shape_terms": list(row.get("move_shape_terms") or []),
                "post_move_terms": list(row.get("post_move_terms") or []),
                "safety_terms": list(row.get("safety_terms") or []),
            }
        )
    status = (
        "cross_stage_capacity_manifest_ready_partial_target_coverage"
        if jobs
        else "cross_stage_capacity_manifest_blocked_no_candidates"
    )
    return {
        "schema_version": "krk_candidate_generation_cross_stage_capacity_manifest.v3",
        "causal_status": "offline_label_manifest_only",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifacts": [str(MERGED_DATASET), str(CROSS_STAGE_REVIEW)],
        "summary": {
            "target_cell_count": len(targets),
            "candidate_pool_count": len(candidates),
            "job_count": len(jobs),
            "job_cap": cap,
            "job_count_by_stage": dict(
                sorted(Counter(str(job.get("source_stage") or "unknown") for job in jobs).items())
            ),
            "job_count_by_provider_family": dict(
                sorted(
                    Counter(str(job.get("provider_family") or "unknown") for job in jobs).items()
                )
            ),
            "job_count_by_target_cell_maturity": dict(
                sorted(
                    Counter(str(job.get("target_cell_maturity") or "unknown") for job in jobs).items()
                )
            ),
            "unavailable_target_cells": unavailable_targets,
            "stage7_job_count": sum(1 for job in jobs if job.get("source_stage") == "stage7"),
            "stage7_readiness_training_row_count": 0,
        },
        "target_cells": targets,
        "jobs": jobs,
        "decision": {
            "status": status,
            "labels_run_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "review_or_run_bounded_cross_stage_capacity_labels"
                if jobs
                else "review_candidate_source_coverage_for_missing_target_cells"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation Cross-Stage Capacity Manifest v3",
        "",
        "This manifest proposes a capped protected-only offline label slice targeted at stage-family capacity cells that block cross-stage candidate-generation refresh.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- labels_run_by_this_artifact: `{payload['decision']['labels_run_by_this_artifact']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- target_cell_count: {summary['target_cell_count']}",
        f"- candidate_pool_count: {summary['candidate_pool_count']}",
        f"- job_count: {summary['job_count']}",
        f"- job_cap: {summary['job_cap']}",
        f"- job_count_by_stage: `{summary['job_count_by_stage']}`",
        f"- job_count_by_provider_family: `{summary['job_count_by_provider_family']}`",
        f"- job_count_by_target_cell_maturity: `{summary['job_count_by_target_cell_maturity']}`",
        f"- unavailable_target_cells: `{summary['unavailable_target_cells']}`",
        f"- stage7_job_count: {summary['stage7_job_count']}",
        "",
        "## Jobs",
        "",
    ]
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['job_id']}` cell=`{job['stage_family_cell']}` "
            f"maturity=`{job['target_cell_maturity']}` provider=`{job['provider_id']}` "
            f"move=`{job['observed_move_uci']}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "This artifact does not run labels. Jobs are offline forced-provider capacity checks only; they are not selector labels, runtime inputs, score updates, guardrails, or promotion evidence.",
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
