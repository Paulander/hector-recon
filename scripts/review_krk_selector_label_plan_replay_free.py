#!/usr/bin/env python3
"""Check whether planned selector labels can be filled replay-free."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PLAN = Path("reports/krk_selector_stratified_label_plan_v1.json")
TARGETS = Path("reports/krk_selector_target_dataset_v0.json")
FRAMES = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
OUT_JSON = Path("reports/krk_selector_label_plan_replay_free_review_v1.json")
OUT_MD = Path("reports/krk_selector_label_plan_replay_free_review_v1.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _target_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str | None], list[dict[str, Any]]]:
    index: dict[tuple[str, str | None], list[dict[str, Any]]] = {}
    for row in rows:
        key = (str(row.get("state_id") or ""), row.get("provider_id"))
        index.setdefault(key, []).append(row)
    return index


def _proposal_index(frames: list[dict[str, Any]]) -> dict[tuple[str, str | None], list[dict[str, Any]]]:
    index: dict[tuple[str, str | None], list[dict[str, Any]]] = {}
    for frame in frames:
        state_id = str(frame.get("state_id") or "")
        for proposal in frame.get("strategy_proposal_frames", []) or []:
            key = (state_id, proposal.get("provider_id"))
            index.setdefault(key, []).append(proposal)
    return index


def _proposal_result(proposal: dict[str, Any]) -> str | None:
    label = proposal.get("known_outcome_label") or {}
    return label.get("result") or label.get("playout_result") or label.get("label")


def build_review() -> dict[str, Any]:
    plan = _load_json(PLAN)
    targets = _load_json(TARGETS).get("rows", []) or []
    frames = _load_json(FRAMES).get("frames", []) or []
    targets_by_key = _target_index(targets)
    proposals_by_key = _proposal_index(frames)
    reviews = []
    status_counts = Counter()
    for job in plan.get("jobs", []) or []:
        key = (str(job.get("state_id") or ""), job.get("provider_id"))
        target_matches = targets_by_key.get(key, [])
        proposal_matches = proposals_by_key.get(key, [])
        target_labels = [
            {
                "target_kind": row.get("target_kind"),
                "label": row.get("label"),
                "label_source": row.get("label_source"),
                "usable_for_training": row.get("usable_for_training"),
            }
            for row in target_matches
            if row.get("label") in {"positive", "negative"}
        ]
        proposal_labels = [
            {
                "result": _proposal_result(proposal),
                "label": (proposal.get("known_outcome_label") or {}),
                "move_uci": proposal.get("move_uci"),
            }
            for proposal in proposal_matches
            if _proposal_result(proposal)
        ]
        if target_labels:
            fill_status = "compatible_target_label_available"
        elif proposal_labels:
            fill_status = "compatible_proposal_label_available"
        else:
            fill_status = "missing_replay_free_label"
        status_counts[fill_status] += 1
        reviews.append({
            "job_id": job.get("job_id"),
            "target_kind": job.get("target_kind"),
            "source_stage": job.get("source_stage"),
            "state_id": job.get("state_id"),
            "provider_id": job.get("provider_id"),
            "fill_status": fill_status,
            "target_labels": target_labels,
            "proposal_labels": proposal_labels,
            "execute_playout_needed": fill_status == "missing_replay_free_label",
        })
    missing = status_counts.get("missing_replay_free_label", 0)
    return {
        "schema_version": "krk_selector_label_plan_replay_free_review.v1",
        "causal_status": "non_causal_replay_free_review",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifacts": [str(PLAN), str(TARGETS), str(FRAMES)],
        "planned_job_count": len(reviews),
        "fill_status_counts": dict(sorted(status_counts.items())),
        "missing_replay_free_label_count": missing,
        "reviews": reviews,
        "decision": {
            "status": (
                "planned_labels_replay_free_fillable"
                if missing == 0
                else "planned_labels_partly_require_execution"
            ),
            "execute_labels_now": False,
            "runtime_arbiter_allowed": False,
            "selector_sandbox_ready": False,
            "recommended_next_step": (
                "build_replay_free_stratified_selector_label_dataset"
                if missing == 0
                else "review_missing_label_jobs_before_execution"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    lines = [
        "# KRK Selector Label Plan Replay-Free Review v1",
        "",
        "This review checks whether the bounded stratified label plan can be filled from existing artifacts before running any new playouts.",
        "",
        "## Summary",
        "",
        f"- Planned jobs: `{payload['planned_job_count']}`",
        f"- Fill status counts: `{payload['fill_status_counts']}`",
        f"- Missing replay-free labels: `{payload['missing_replay_free_label_count']}`",
        f"- Execute labels now: `{payload['decision']['execute_labels_now']}`",
        f"- Decision: `{payload['decision']['status']}`",
        "",
        "## Job Review",
        "",
    ]
    for review in payload["reviews"]:
        lines.append(
            f"- `{review['job_id']}` status=`{review['fill_status']}` "
            f"target_labels=`{len(review['target_labels'])}` proposal_labels=`{len(review['proposal_labels'])}`"
        )
    lines.extend([
        "",
        "## Recommended Next Step",
        "",
        f"`{payload['decision']['recommended_next_step']}`",
    ])
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_review()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload)


if __name__ == "__main__":
    main()
