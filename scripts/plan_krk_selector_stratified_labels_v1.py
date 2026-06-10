#!/usr/bin/env python3
"""Plan bounded stratified selector labels without executing playouts."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
TARGETS = Path("reports/krk_selector_target_dataset_v0.json")
FRAMES = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
OBJECTIVE_REVIEW = Path("reports/krk_selector_objective_architecture_review_v1.json")
OUT_JSON = Path("reports/krk_selector_stratified_label_plan_v1.json")
OUT_MD = Path("reports/krk_selector_stratified_label_plan_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _target_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind_stage: dict[str, Counter[str]] = defaultdict(Counter)
    by_kind_label: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        kind = str(row.get("target_kind") or "unknown")
        by_kind_stage[kind][str(row.get("source_stage") or "unknown")] += 1
        by_kind_label[kind][str(row.get("label") or "none")] += 1
    return {
        "by_kind_stage": {kind: dict(sorted(counts.items())) for kind, counts in sorted(by_kind_stage.items())},
        "by_kind_label": {kind: dict(sorted(counts.items())) for kind, counts in sorted(by_kind_label.items())},
    }


def _proposal_label_counts(frames: list[dict[str, Any]]) -> dict[str, Any]:
    by_stage_result: dict[str, Counter[str]] = defaultdict(Counter)
    by_stage_label_source: dict[str, Counter[str]] = defaultdict(Counter)
    unlabeled_by_stage = Counter()
    for frame in frames:
        stage = str(frame.get("source_stage") or "unknown")
        for proposal in frame.get("strategy_proposal_frames", []) or []:
            label = proposal.get("known_outcome_label") or {}
            result = label.get("result") or label.get("playout_result") or label.get("label")
            if result:
                by_stage_result[stage][str(result)] += 1
                by_stage_label_source[stage][str(label.get("label_source") or label.get("source") or label.get("label_type") or "unknown")] += 1
            else:
                unlabeled_by_stage[stage] += 1
    return {
        "by_stage_result": {stage: dict(sorted(counts.items())) for stage, counts in sorted(by_stage_result.items())},
        "by_stage_label_source": {stage: dict(sorted(counts.items())) for stage, counts in sorted(by_stage_label_source.items())},
        "unlabeled_by_stage": dict(sorted(unlabeled_by_stage.items())),
    }


def _selected_provider(frame: dict[str, Any]) -> str | None:
    for proposal in frame.get("strategy_proposal_frames", []) or []:
        if proposal.get("provider_local_rank") == 1:
            return proposal.get("provider_id")
    return None


def _candidate_alternative_provider(frame: dict[str, Any]) -> str | None:
    selected = _selected_provider(frame)
    for proposal in frame.get("strategy_proposal_frames", []) or []:
        provider = proposal.get("provider_id")
        if provider and provider != selected:
            return provider
    return None


def _make_jobs(frames: list[dict[str, Any]], max_jobs: int = 12) -> list[dict[str, Any]]:
    jobs: list[dict[str, Any]] = []
    seen_job_keys: set[tuple[str, str, str | None]] = set()
    protected = [
        frame for frame in frames
        if frame.get("source_stage") in {"stage4", "stage5", "stage6"}
        and not (frame.get("filter_metadata") or {}).get("context_only")
    ]
    stages = ["stage4", "stage5", "stage6"]
    per_stage = max_jobs // len(stages)
    for stage in stages:
        stage_frames = [frame for frame in protected if frame.get("source_stage") == stage]
        for frame in stage_frames[:per_stage]:
            selected = _selected_provider(frame)
            alt = _candidate_alternative_provider(frame)
            selected_key = (str(frame.get("state_id")), "guardrail_safe_selected_playout", selected)
            if selected_key in seen_job_keys:
                continue
            seen_job_keys.add(selected_key)
            jobs.append({
                "job_id": f"selector_label.{stage}.{frame.get('state_id')}.selected_guardrail",
                "target_kind": "guardrail_safe_selected_playout",
                "source_stage": stage,
                "state_id": frame.get("state_id"),
                "frame_id": frame.get("frame_id"),
                "fen": frame.get("fen"),
                "provider_id": selected,
                "horizon": 40,
                "trace_mode": "failures_only",
                "diagnostic_caches": True,
                "stage7_training_row": False,
                "causal_status": "non_causal_label_job_plan",
            })
            if len(jobs) >= max_jobs:
                return jobs
            if alt:
                alt_key = (
                    str(frame.get("state_id")),
                    "same_move_provider_compatibility_or_forced_alternative",
                    alt,
                )
                if alt_key in seen_job_keys:
                    continue
                seen_job_keys.add(alt_key)
                jobs.append({
                    "job_id": f"selector_label.{stage}.{frame.get('state_id')}.same_move_or_alt_provider",
                    "target_kind": "same_move_provider_compatibility_or_forced_alternative",
                    "source_stage": stage,
                    "state_id": frame.get("state_id"),
                    "frame_id": frame.get("frame_id"),
                    "fen": frame.get("fen"),
                    "provider_id": alt,
                    "horizon": 40,
                    "trace_mode": "failures_only",
                    "diagnostic_caches": True,
                    "stage7_training_row": False,
                    "causal_status": "non_causal_label_job_plan",
                })
            if len(jobs) >= max_jobs:
                return jobs
    return jobs[:max_jobs]


def build_plan() -> dict[str, Any]:
    targets = _load_json(TARGETS)
    frames_payload = _load_json(FRAMES)
    review = _load_json(OBJECTIVE_REVIEW)
    rows = targets.get("rows", []) or []
    frames = frames_payload.get("frames", []) or []
    jobs = _make_jobs(frames)
    return {
        "schema_version": "krk_selector_stratified_label_plan.v1",
        "causal_status": "non_causal_label_plan",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifacts": [str(TARGETS), str(FRAMES), str(OBJECTIVE_REVIEW)],
        "objective_review_status": review.get("decision", {}).get("status"),
        "existing_target_counts": _target_counts(rows),
        "existing_proposal_label_counts": _proposal_label_counts(frames),
        "planned_job_count": len(jobs),
        "max_new_states": 12,
        "horizon": 40,
        "jobs": jobs,
        "stage7_training_rows": 0,
        "decision": {
            "status": "bounded_selector_stratified_label_plan_ready",
            "execute_labels_now": False,
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": "review_label_plan_before_execution_or_replay_free_extraction",
        },
        "blocked_next_work": [
            "runtime_arbiter",
            "selector_sandbox",
            "stage7_repair",
            "stage7_promotion",
            "stage8_training",
            "runtime_dtm_or_tablebase",
            "gameplay_topology_mutation",
        ],
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Stratified Label Plan v1",
        "",
        "This is a bounded non-causal plan for improving selector objective evidence. It does not execute labels.",
        "",
        "## Summary",
        "",
        f"- Objective review status: `{payload['objective_review_status']}`",
        f"- Planned jobs: `{payload['planned_job_count']}`",
        f"- Horizon: `h{payload['horizon']}`",
        f"- Stage7 training rows: `{payload['stage7_training_rows']}`",
        f"- Execute labels now: `{payload['decision']['execute_labels_now']}`",
        f"- Runtime arbiter allowed: `{payload['decision']['runtime_arbiter_allowed']}`",
        "",
        "## Existing Target Counts",
        "",
        f"- By kind/stage: `{payload['existing_target_counts']['by_kind_stage']}`",
        f"- By kind/label: `{payload['existing_target_counts']['by_kind_label']}`",
        "",
        "## Existing Proposal Label Counts",
        "",
        f"- By stage/result: `{payload['existing_proposal_label_counts']['by_stage_result']}`",
        f"- Unlabeled by stage: `{payload['existing_proposal_label_counts']['unlabeled_by_stage']}`",
        "",
        "## Planned Jobs",
        "",
    ]
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['job_id']}` target=`{job['target_kind']}` "
            f"stage=`{job['source_stage']}` provider=`{job.get('provider_id')}`"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        f"Recommended next step: `{payload['decision']['recommended_next_step']}`",
        "",
        "The plan should be reviewed before execution. If replay-free extraction can fill the same cells, prefer that over new playouts.",
    ])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_plan()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
