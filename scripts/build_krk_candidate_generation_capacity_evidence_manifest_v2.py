#!/usr/bin/env python3
"""Build a bounded protected capacity-evidence manifest for candidate generation."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET = Path("reports/strategy_arbitration/krk_strategy_sequence_dataset_v2.json")
REFRESH_PROBE = Path("reports/strategy_arbitration/krk_candidate_generation_refresh_probe_v2.json")
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_capacity_evidence_manifest_v2.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_capacity_evidence_manifest_v2.md"
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
    digest = hashlib.sha1(f"{key}|candidate_generation_capacity_v2".encode()).hexdigest()[:12]
    return f"job.krk.cg_capacity_v2.{digest}"


def _known_capacity_pairs(rows: list[dict[str, Any]]) -> set[tuple[str, str]]:
    pairs = set()
    for row in rows:
        if row.get("evidence_channel") == "validated_provider_capacity":
            state_id = row.get("state_id")
            provider = row.get("candidate_provider_id")
            if state_id and provider:
                pairs.add((str(state_id), str(provider)))
    return pairs


def _candidate_rows(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(dataset.get("rows") or [])
    known_pairs = _known_capacity_pairs(rows)
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if row.get("stage7_challenge_row"):
            continue
        if row.get("evidence_channel") != "visible_provider_proposal":
            continue
        state_id = str(row.get("state_id") or "")
        provider = str(row.get("candidate_provider_id") or "")
        move = str(row.get("candidate_move_uci") or "")
        if not state_id or not provider:
            continue
        if (state_id, provider) in known_pairs:
            continue
        key = (state_id, provider, move)
        if key in seen:
            continue
        seen.add(key)
        candidates.append(row)
    return candidates


def _select_rows(candidates: list[dict[str, Any]], *, cap: int = 12) -> list[dict[str, Any]]:
    by_stage: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in candidates:
        by_stage[str(row.get("source_stage") or "unknown")].append(row)
    for stage_rows in by_stage.values():
        stage_rows.sort(
            key=lambda row: (
                str(row.get("candidate_strategy_family") or ""),
                str(row.get("state_id") or ""),
                str(row.get("candidate_provider_id") or ""),
            )
        )
    selected: list[dict[str, Any]] = []
    cursors = {stage: 0 for stage in ("stage4", "stage5", "stage6")}
    family_counts: Counter[str] = Counter()
    while len(selected) < cap:
        progressed = False
        for stage in ("stage4", "stage5", "stage6"):
            rows = by_stage.get(stage) or []
            cursor = cursors[stage]
            while cursor < len(rows):
                row = rows[cursor]
                cursors[stage] = cursor + 1
                family_key = f"{stage}:{row.get('candidate_strategy_family')}"
                if family_counts[family_key] >= 3:
                    cursor += 1
                    continue
                selected.append(row)
                family_counts[family_key] += 1
                progressed = True
                break
            if len(selected) >= cap:
                break
        if not progressed:
            break
    return selected


def build_payload(
    dataset: dict[str, Any] | None = None,
    refresh_probe: dict[str, Any] | None = None,
    *,
    cap: int = 12,
) -> dict[str, Any]:
    dataset = dataset or _load(DATASET)
    refresh_probe = refresh_probe or _load(REFRESH_PROBE)
    candidates = _candidate_rows(dataset)
    selected = _select_rows(candidates, cap=cap)
    jobs = []
    for row in selected:
        jobs.append(
            {
                "schema_version": "krk_candidate_generation_capacity_evidence_job.v2",
                "job_id": _job_id(row),
                "causal_status": "offline_label_manifest_only",
                "state_id": row.get("state_id"),
                "fen": row.get("fen"),
                "source_stage": row.get("source_stage"),
                "active_landmark_label": row.get("active_landmark_label"),
                "provider_id": row.get("candidate_provider_id"),
                "provider_family": row.get("candidate_strategy_family"),
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
    by_stage = Counter(str(job.get("source_stage") or "unknown") for job in jobs)
    by_family = Counter(str(job.get("provider_family") or "unknown") for job in jobs)
    status = (
        "candidate_generation_capacity_evidence_manifest_ready"
        if jobs and all(job.get("source_stage") != "stage7" for job in jobs)
        else "candidate_generation_capacity_evidence_manifest_blocked"
    )
    return {
        "schema_version": "krk_candidate_generation_capacity_evidence_manifest.v2",
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
        "source_artifacts": [str(DATASET), str(REFRESH_PROBE)],
        "input_decision": (refresh_probe.get("decision") or {}).get("status"),
        "summary": {
            "candidate_pool_count": len(candidates),
            "job_count": len(jobs),
            "job_cap": cap,
            "job_count_by_stage": dict(sorted(by_stage.items())),
            "job_count_by_provider_family": dict(sorted(by_family.items())),
            "stage7_job_count": sum(1 for job in jobs if job.get("source_stage") == "stage7"),
            "stage7_readiness_training_row_count": 0,
        },
        "jobs": jobs,
        "decision": {
            "status": status,
            "labels_run_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "review_or_run_bounded_offline_capacity_labels"
                if status == "candidate_generation_capacity_evidence_manifest_ready"
                else "review_manifest_blockers"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Candidate-Generation Capacity Evidence Manifest v2",
        "",
        "This manifest proposes a capped protected-only offline capacity-label slice for candidate generation. It does not run labels or authorize selector behavior.",
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
        f"- job_count_by_provider_family: `{summary['job_count_by_provider_family']}`",
        f"- stage7_job_count: {summary['stage7_job_count']}",
        "",
        "## Jobs",
        "",
    ]
    for job in payload["jobs"]:
        lines.append(
            f"- `{job['job_id']}` stage=`{job['source_stage']}` "
            f"provider=`{job['provider_id']}` family=`{job['provider_family']}` "
            f"move=`{job['observed_move_uci']}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Jobs are forced-provider capacity labels only. They are not ownership labels, runtime inputs, score updates, guardrails, or promotion evidence.",
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
