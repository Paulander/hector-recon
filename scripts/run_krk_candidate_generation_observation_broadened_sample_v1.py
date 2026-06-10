#!/usr/bin/env python3
"""Run a broadened observation-only KRK candidate-generation sample.

This script intentionally stays narrower than a guardrail campaign: it checks
one-ply default-off equivalence and emitted observation-frame coverage across a
larger protected/held-out sample. It does not select from generated frames.
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_krk_candidate_generation_observation_sandbox_v0 import (  # noqa: E402
    CAPACITY_FRAMES,
    RANKED_FRAMES,
    _run_decision,
    _same_decision,
)


OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_observation_broadened_sample_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_candidate_generation_observation_broadened_sample_v1.md"
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _row_key(row: dict[str, Any]) -> str:
    return str(row.get("state_id") or row.get("frame_id") or row.get("fen"))


def _case_from_row(row: dict[str, Any], *, source_artifact: str) -> dict[str, Any]:
    stage = str(row.get("source_stage") or "unknown")
    state_id = _row_key(row)
    return {
        "case_id": f"{stage}_{state_id}",
        "state_id": state_id,
        "fen": row["fen"],
        "active_landmark_label": row.get("active_landmark_label") or row.get("provider_family"),
        "source_stage": stage,
        "held_out": stage == "stage7" or bool(row.get("stage7_challenge_row")),
        "source_artifact": source_artifact,
    }


def load_broadened_cases(*, stage7_cap: int = 4) -> list[dict[str, Any]]:
    """Build a small stratified set from existing artifacts.

    Protected Stage 4/5/6 unique states are included when available. Stage 7 is
    capped and marked held-out challenge only.
    """

    capacity = _load_json(CAPACITY_FRAMES)
    ranked = _load_json(RANKED_FRAMES)
    cases_by_key: dict[str, dict[str, Any]] = {}

    # Prefer capacity rows for protected stages because they have capacity labels
    # and provider-family context. Add ranked rows to broaden state coverage.
    for source_artifact, rows in [
        (str(CAPACITY_FRAMES), capacity.get("rows") or []),
        (str(RANKED_FRAMES), ranked.get("rows") or []),
    ]:
        for row in rows:
            if not isinstance(row, dict) or not row.get("fen"):
                continue
            stage = str(row.get("source_stage") or "")
            if stage not in {"stage4", "stage5", "stage6", "stage7"}:
                continue
            if stage == "stage7":
                continue
            key = f"{stage}:{_row_key(row)}"
            cases_by_key.setdefault(key, _case_from_row(row, source_artifact=source_artifact))

    stage7_cases: dict[str, dict[str, Any]] = {}
    for row in ranked.get("rows") or []:
        if not isinstance(row, dict) or not row.get("fen"):
            continue
        if not row.get("stage7_challenge_row") and row.get("source_stage") != "stage7":
            continue
        key = f"stage7:{_row_key(row)}"
        stage7_cases.setdefault(key, _case_from_row(row, source_artifact=str(RANKED_FRAMES)))
        if len(stage7_cases) >= stage7_cap:
            break

    return sorted(cases_by_key.values(), key=lambda c: (c["source_stage"], c["case_id"])) + list(
        stage7_cases.values()
    )


def _frames_from_decision(decision: dict[str, Any]) -> list[dict[str, Any]]:
    observation = decision.get("observation") or {}
    frames = observation.get("frames") or observation.get("sample_frames") or []
    return [frame for frame in frames if isinstance(frame, dict)]


def _aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_stage: Counter[str] = Counter()
    by_case_source: Counter[str] = Counter()
    by_candidate_source: Counter[str] = Counter()
    by_capacity: Counter[str] = Counter()
    by_protected_status: Counter[str] = Counter()
    by_stage_and_candidate_source: dict[str, Counter[str]] = defaultdict(Counter)
    invariant_failures: list[dict[str, Any]] = []
    selected_delta_cases: list[str] = []
    default_off_observation_cases: list[str] = []
    total_frames = 0
    stage7_rows = 0

    for row in rows:
        stage = str(row["source_stage"])
        by_stage[stage] += 1
        by_case_source[str(row.get("source_artifact") or "unknown")] += 1
        if row.get("held_out"):
            stage7_rows += 1
        if not row.get("selected_move_provider_score_equivalent"):
            selected_delta_cases.append(str(row["case_id"]))
        if row["flag_off_decision"].get("observation_present"):
            default_off_observation_cases.append(str(row["case_id"]))

        frames = _frames_from_decision(row["enabled_decision"])
        total_frames += len(frames)
        for frame in frames:
            source = str(frame.get("candidate_source") or "unknown")
            by_candidate_source[source] += 1
            by_stage_and_candidate_source[stage][source] += 1
            by_capacity[str(frame.get("capacity_evidence_kind") or "unknown_capacity")] += 1
            by_protected_status[str(frame.get("protected_status") or "unknown")] += 1
            if (
                frame.get("direct_request") is not False
                or float(frame.get("score_delta", 1.0) or 0.0) != 0.0
                or frame.get("causal_status") != "observation_only"
            ):
                invariant_failures.append(
                    {
                        "case_id": row["case_id"],
                        "candidate_source": frame.get("candidate_source"),
                        "provider_id": frame.get("provider_id"),
                        "move_uci": frame.get("move_uci"),
                        "direct_request": frame.get("direct_request"),
                        "score_delta": frame.get("score_delta"),
                        "causal_status": frame.get("causal_status"),
                    }
                )

    return {
        "case_count": len(rows),
        "case_count_by_stage": dict(sorted(by_stage.items())),
        "case_count_by_source_artifact": dict(sorted(by_case_source.items())),
        "emitted_frame_count": total_frames,
        "frame_count_by_candidate_source": dict(sorted(by_candidate_source.items())),
        "frame_count_by_stage_and_candidate_source": {
            stage: dict(sorted(counter.items()))
            for stage, counter in sorted(by_stage_and_candidate_source.items())
        },
        "capacity_evidence_counts": dict(sorted(by_capacity.items())),
        "protected_status_counts": dict(sorted(by_protected_status.items())),
        "stage7_heldout_case_count": stage7_rows,
        "stage7_readiness_training_row_count": 0,
        "selected_move_or_provider_delta_count": len(selected_delta_cases),
        "selected_move_or_provider_delta_cases": selected_delta_cases,
        "default_off_observation_case_count": len(default_off_observation_cases),
        "default_off_observation_cases": default_off_observation_cases,
        "invariant_failure_count": len(invariant_failures),
        "invariant_failures": invariant_failures[:10],
    }


def build_payload() -> dict[str, Any]:
    cases = load_broadened_cases()
    rows = []
    for case in cases:
        flag_off_decision = _run_decision(case, enabled=False)
        enabled_decision = _run_decision(case, enabled=True)
        rows.append(
            {
                **case,
                "flag_off_decision": flag_off_decision,
                "enabled_decision": enabled_decision,
                "selected_move_provider_score_equivalent": _same_decision(
                    flag_off_decision,
                    enabled_decision,
                ),
            }
        )

    summary = _aggregate(rows)
    pass_invariants = (
        summary["case_count"] > 0
        and summary["emitted_frame_count"] > 0
        and summary["selected_move_or_provider_delta_count"] == 0
        and summary["default_off_observation_case_count"] == 0
        and summary["invariant_failure_count"] == 0
    )
    status = (
        "broadened_observation_sample_supports_coverage_analysis"
        if pass_invariants
        else "broadened_observation_sample_blocked"
    )
    return {
        "schema_version": "krk_candidate_generation_observation_broadened_sample.v1",
        "sandbox_id": "sandbox.krk.candidate_generation_observation_v0",
        "causal_status": "runtime_observation_only_broadened_sample",
        "runtime_defaults_changed": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_provider_suppression": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "summary": summary,
        "cases": rows,
        "decision": {
            "status": status,
            "default_off_equivalence_passed": (
                summary["selected_move_or_provider_delta_count"] == 0
                and summary["default_off_observation_case_count"] == 0
            ),
            "observation_frames_emitted": summary["emitted_frame_count"] > 0,
            "frame_invariants_passed": summary["invariant_failure_count"] == 0,
            "stage7_readiness_training_row_count": 0,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "promotion_allowed": False,
            "recommended_next_step": "non_causal_candidate_coverage_gap_review",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    decision = payload["decision"]
    lines = [
        "# KRK Candidate-Generation Observation Broadened Sample v1",
        "",
        "This is a bounded observation-only runtime sample. Generated frames remain non-causal and are not used for selection.",
        "",
        "## Decision",
        "",
        f"- status: `{decision['status']}`",
        f"- default_off_equivalence_passed: `{decision['default_off_equivalence_passed']}`",
        f"- observation_frames_emitted: `{decision['observation_frames_emitted']}`",
        f"- frame_invariants_passed: `{decision['frame_invariants_passed']}`",
        f"- selector_allowed: `{decision['selector_allowed']}`",
        f"- guardrails_allowed: `{decision['guardrails_allowed']}`",
        "",
        "## Summary",
        "",
        f"- case_count: {summary['case_count']}",
        f"- case_count_by_stage: `{summary['case_count_by_stage']}`",
        f"- emitted_frame_count: {summary['emitted_frame_count']}",
        f"- frame_count_by_candidate_source: `{summary['frame_count_by_candidate_source']}`",
        f"- capacity_evidence_counts: `{summary['capacity_evidence_counts']}`",
        f"- protected_status_counts: `{summary['protected_status_counts']}`",
        f"- stage7_heldout_case_count: {summary['stage7_heldout_case_count']}",
        f"- stage7_readiness_training_row_count: {summary['stage7_readiness_training_row_count']}",
        f"- selected_move_or_provider_delta_count: {summary['selected_move_or_provider_delta_count']}",
        f"- default_off_observation_case_count: {summary['default_off_observation_case_count']}",
        f"- invariant_failure_count: {summary['invariant_failure_count']}",
        "",
        "## Stage / Source Coverage",
        "",
        f"- frame_count_by_stage_and_candidate_source: `{summary['frame_count_by_stage_and_candidate_source']}`",
        f"- case_count_by_source_artifact: `{summary['case_count_by_source_artifact']}`",
        "",
        "## Boundary",
        "",
        "This artifact does not authorize selector implementation, score changes, guardrails, promotion, or Stage 8 training.",
    ]
    (ROOT / OUT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_payload()
    (ROOT / OUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    (ROOT / OUT_JSON).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    write_markdown(payload)
    print(json.dumps(payload["decision"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
