#!/usr/bin/env python3
"""Run a broadened protected sample for Stage 5/6 refresh observation frames."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_krk_stage5_6_candidate_generation_refresh_smoke_v0 import (
    OUT_JSON as SMOKE_JSON,
    _frames,
    _refresh_frames,
    _run_decision,
    load_cases,
)
from scripts.run_krk_candidate_generation_observation_sandbox_v0 import _same_decision


OUT_JSON = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_broadened_v0.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/krk_stage5_6_candidate_generation_refresh_broadened_v0.md"
)


def build_payload(stage_cap: int = 4) -> dict[str, Any]:
    rows = []
    for case in load_cases(stage_cap=stage_cap):
        baseline = _run_decision(case, refresh_enabled=False)
        enabled = _run_decision(case, refresh_enabled=True)
        rows.append(
            {
                **case,
                "baseline_decision": baseline,
                "enabled_decision": enabled,
                "selected_move_provider_score_equivalent": _same_decision(baseline, enabled),
                "baseline_refresh_frame_count": len(_refresh_frames(baseline)),
                "enabled_refresh_frame_count": len(_refresh_frames(enabled)),
                "enabled_refresh_sample_frames": _refresh_frames(enabled)[:5],
            }
        )

    source_counts: Counter[str] = Counter()
    capacity_counts: Counter[str] = Counter()
    stage_counts: Counter[str] = Counter()
    provider_counts: Counter[str] = Counter()
    invariant_failures: list[dict[str, Any]] = []
    refresh_frame_count = 0
    for row in rows:
        stage_counts[str(row.get("source_stage") or "unknown")] += 1
        for frame in _frames(row["enabled_decision"]):
            source_counts[str(frame.get("candidate_source") or "unknown")] += 1
            capacity_counts[str(frame.get("capacity_evidence_kind") or "unknown")] += 1
            if frame.get("candidate_source") != "stage_conditioned_candidate_generation_refresh":
                continue
            refresh_frame_count += 1
            provider_counts[str(frame.get("provider_id") or "unknown")] += 1
            if (
                frame.get("direct_request") is not False
                or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
                or frame.get("causal_status") != "observation_only"
                or frame.get("protected_status") != "protected_control"
            ):
                invariant_failures.append(frame)

    selected_delta_count = sum(
        1 for row in rows if not row["selected_move_provider_score_equivalent"]
    )
    baseline_leak_count = sum(int(row["baseline_refresh_frame_count"]) for row in rows)
    stage7_case_count = sum(1 for row in rows if row.get("source_stage") == "stage7")
    status = (
        "stage5_6_candidate_generation_refresh_broadened_default_off_equivalent"
        if rows
        and refresh_frame_count > 0
        and selected_delta_count == 0
        and baseline_leak_count == 0
        and stage7_case_count == 0
        and not invariant_failures
        else "stage5_6_candidate_generation_refresh_broadened_blocked"
    )
    return {
        "schema_version": "krk_stage5_6_candidate_generation_refresh_broadened.v0",
        "sandbox_id": "sandbox.krk.stage5_6_candidate_generation_refresh_v0",
        "causal_status": "runtime_observation_only_source_broadened_sample",
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_provider_suppression": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(SMOKE_JSON),
        "summary": {
            "case_count": len(rows),
            "case_count_by_stage": dict(sorted(stage_counts.items())),
            "refresh_frame_count": refresh_frame_count,
            "candidate_count_by_source": dict(sorted(source_counts.items())),
            "capacity_evidence_counts": dict(sorted(capacity_counts.items())),
            "refresh_provider_counts": dict(sorted(provider_counts.items())),
            "selected_move_provider_delta_count": selected_delta_count,
            "baseline_refresh_frame_count": baseline_leak_count,
            "invariant_failure_count": len(invariant_failures),
            "stage7_case_count": stage7_case_count,
        },
        "cases": rows,
        "invariant_failures": invariant_failures[:10],
        "decision": {
            "status": status,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": (
                "stage5_6_candidate_generation_refresh_quality_review"
                if status == "stage5_6_candidate_generation_refresh_broadened_default_off_equivalent"
                else "quarantine_stage5_6_candidate_generation_refresh_source"
            ),
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Stage 5/6 Candidate-Generation Refresh Broadened v0",
        "",
        "This broadens the protected Stage 5/6 observation-only refresh sample. It does not authorize selection, scoring, guardrails, or promotion.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- case_count: {summary['case_count']}",
        f"- case_count_by_stage: `{summary['case_count_by_stage']}`",
        f"- refresh_frame_count: {summary['refresh_frame_count']}",
        f"- candidate_count_by_source: `{summary['candidate_count_by_source']}`",
        f"- capacity_evidence_counts: `{summary['capacity_evidence_counts']}`",
        f"- refresh_provider_counts: `{summary['refresh_provider_counts']}`",
        f"- selected_move_provider_delta_count: {summary['selected_move_provider_delta_count']}",
        f"- baseline_refresh_frame_count: {summary['baseline_refresh_frame_count']}",
        f"- invariant_failure_count: {summary['invariant_failure_count']}",
        f"- stage7_case_count: {summary['stage7_case_count']}",
    ]
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
