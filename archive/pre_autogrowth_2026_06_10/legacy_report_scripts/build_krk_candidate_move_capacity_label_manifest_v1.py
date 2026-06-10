#!/usr/bin/env python3
"""Build a bounded protected-only CandidateMoveFrame capacity label manifest."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OBSERVATION_SOURCE = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_observation_broadened_sample_v1.json"
)
CAPACITY_SOURCE = Path("reports/krk_protected_provider_coverage_frames_v0.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/krk_candidate_move_capacity_label_manifest_v1.json"
)
OUT_MD = Path("reports/strategy_arbitration/krk_candidate_move_capacity_label_manifest_v1.md")


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _known_capacity_keys(capacity_payload: dict[str, Any]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for row in capacity_payload.get("rows") or []:
        if not isinstance(row, dict) or row.get("stage7_challenge_row"):
            continue
        if row.get("fen") and row.get("forced_first_move"):
            keys.add((str(row["fen"]), str(row["forced_first_move"])))
    return keys


def _candidate_rows(
    observation_payload: dict[str, Any],
    known_capacity_keys: set[tuple[str, str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for case in observation_payload.get("cases") or []:
        if case.get("held_out") or case.get("source_stage") == "stage7":
            continue
        observation = ((case.get("enabled_decision") or {}).get("observation") or {})
        selected_move = observation.get("selected_move_before_observation")
        selected_provider = observation.get("selected_provider_before_observation")
        for frame in observation.get("frames") or []:
            if not isinstance(frame, dict) or frame.get("candidate_source") != "candidate_move_frame":
                continue
            fen = str(frame.get("state_fen") or "")
            move = str(frame.get("move_uci") or frame.get("move_id") or "")
            if not fen or not move:
                continue
            key = (fen, move)
            if key in seen or key in known_capacity_keys:
                continue
            seen.add(key)
            move_shape_terms = list(frame.get("move_shape_terms") or [])
            post_move_terms = list(frame.get("post_move_terms") or [])
            safety_terms = list(frame.get("safety_terms") or [])
            source_terms = list(frame.get("source_terms") or [])
            term_score = len(move_shape_terms) + len(post_move_terms) + len(safety_terms)
            rows.append(
                {
                    "state_fen": fen,
                    "source_stage": str(case.get("source_stage") or "unknown"),
                    "state_id": case.get("state_id"),
                    "case_id": case.get("case_id"),
                    "active_landmark_label": case.get("active_landmark_label"),
                    "candidate_move_uci": move,
                    "selected_move_before_observation": selected_move,
                    "selected_provider_before_observation": selected_provider,
                    "move_shape_terms": move_shape_terms,
                    "post_move_terms": post_move_terms,
                    "safety_terms": safety_terms,
                    "source_terms": source_terms[:30],
                    "term_score": term_score,
                    "is_selected_move": move == selected_move,
                    "protected_status": frame.get("protected_status"),
                }
            )
    return rows


def _select_manifest_rows(candidates: list[dict[str, Any]], *, cap: int = 12) -> list[dict[str, Any]]:
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_stage[str(row["source_stage"])].append(row)
    for stage_rows in by_stage.values():
        stage_rows.sort(
            key=lambda row: (
                row["is_selected_move"],
                -int(row["term_score"]),
                str(row["case_id"]),
                str(row["candidate_move_uci"]),
            )
        )

    selected: list[dict[str, Any]] = []
    stages = ["stage4", "stage5", "stage6"]
    cursors = {stage: 0 for stage in stages}
    while len(selected) < cap:
        progressed = False
        for stage in stages:
            rows = by_stage.get(stage) or []
            cursor = cursors[stage]
            if cursor >= len(rows):
                continue
            selected.append(rows[cursor])
            cursors[stage] += 1
            progressed = True
            if len(selected) >= cap:
                break
        if not progressed:
            break

    jobs: list[dict[str, Any]] = []
    for idx, row in enumerate(selected, start=1):
        jobs.append(
            {
                "job_id": f"cmcap.v1.{idx:03d}",
                "schema_version": "krk_candidate_move_capacity_label_job.v1",
                "causal_status": "offline_label_manifest_only",
                "source_observation_case_id": row["case_id"],
                "source_stage": row["source_stage"],
                "state_id": row["state_id"],
                "fen": row["state_fen"],
                "active_landmark_label": row["active_landmark_label"],
                "candidate_move_uci": row["candidate_move_uci"],
                "selected_move_before_observation": row["selected_move_before_observation"],
                "selected_provider_before_observation": row[
                    "selected_provider_before_observation"
                ],
                "label_request": "force_candidate_move_then_h40_continuation",
                "label_semantics": "forced_first_move_capacity_not_runtime_ownership_label",
                "horizon": 40,
                "stage7_training_row": False,
                "runtime_use_allowed": False,
                "selector_training_allowed": False,
                "move_shape_terms": row["move_shape_terms"],
                "post_move_terms": row["post_move_terms"],
                "safety_terms": row["safety_terms"],
                "source_terms": row["source_terms"],
            }
        )
    return jobs


def build_payload(
    observation_payload: dict[str, Any] | None = None,
    capacity_payload: dict[str, Any] | None = None,
    *,
    cap: int = 12,
) -> dict[str, Any]:
    observation_payload = observation_payload or _load(OBSERVATION_SOURCE)
    capacity_payload = capacity_payload or _load(CAPACITY_SOURCE)
    known_keys = _known_capacity_keys(capacity_payload)
    candidates = _candidate_rows(observation_payload, known_keys)
    jobs = _select_manifest_rows(candidates, cap=cap)
    by_stage: dict[str, int] = defaultdict(int)
    selected_moves = 0
    for job in jobs:
        by_stage[str(job["source_stage"])] += 1
        if job["candidate_move_uci"] == job["selected_move_before_observation"]:
            selected_moves += 1
    status = (
        "bounded_candidate_move_capacity_manifest_ready"
        if jobs and all(job["source_stage"] != "stage7" for job in jobs)
        else "bounded_candidate_move_capacity_manifest_blocked"
    )
    return {
        "schema_version": "krk_candidate_move_capacity_label_manifest.v1",
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
        "source_artifacts": {
            "observation_frames": str(OBSERVATION_SOURCE),
            "capacity_labels": str(CAPACITY_SOURCE),
        },
        "summary": {
            "candidate_pool_count": len(candidates),
            "job_count": len(jobs),
            "job_cap": cap,
            "job_count_by_stage": dict(sorted(by_stage.items())),
            "selected_move_job_count": selected_moves,
            "stage7_job_count": sum(1 for job in jobs if job["source_stage"] == "stage7"),
            "stage7_readiness_training_row_count": 0,
        },
        "jobs": jobs,
        "decision": {
            "status": status,
            "labels_run_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "run_bounded_offline_candidate_move_capacity_labels"
            if status == "bounded_candidate_move_capacity_manifest_ready"
            else "review_manifest_blocker",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK CandidateMoveFrame Capacity Label Manifest v1",
        "",
        "This manifest proposes a capped protected-only offline label slice. It does not run labels and does not authorize runtime selection.",
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
        f"- candidate_pool_count: {summary['candidate_pool_count']}",
        f"- job_count: {summary['job_count']}",
        f"- job_cap: {summary['job_cap']}",
        f"- job_count_by_stage: `{summary['job_count_by_stage']}`",
        f"- selected_move_job_count: {summary['selected_move_job_count']}",
        f"- stage7_job_count: {summary['stage7_job_count']}",
        "",
        "## Jobs",
        "",
    ]
    for job in payload["jobs"]:
        lines.extend(
            [
                f"### {job['job_id']}",
                "",
                f"- source_stage: `{job['source_stage']}`",
                f"- active_landmark_label: `{job['active_landmark_label']}`",
                f"- candidate_move_uci: `{job['candidate_move_uci']}`",
                f"- selected_move_before_observation: `{job['selected_move_before_observation']}`",
                f"- label_semantics: `{job['label_semantics']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Boundary",
            "",
            "These jobs are offline capacity-label requests only. They are not runtime inputs, selector labels, guardrails, or promotion evidence.",
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
