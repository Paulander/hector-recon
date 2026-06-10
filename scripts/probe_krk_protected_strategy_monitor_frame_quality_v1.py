#!/usr/bin/env python3
"""Probe protected strategy-monitor frame quality non-causally."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FRAMES = Path("reports/strategy_arbitration/krk_protected_strategy_monitor_frame_expansion_v1.json")
OUT_JSON = Path("reports/strategy_arbitration/krk_protected_strategy_monitor_frame_quality_v1.json")
OUT_MD = Path("reports/strategy_arbitration/krk_protected_strategy_monitor_frame_quality_v1.md")


def _load(path: Path = FRAMES) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _family_stats(frames: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for frame in frames:
        by_family[str(frame.get("candidate_strategy_family") or "unknown")].append(frame)
    stats: dict[str, dict[str, Any]] = {}
    for family, rows in by_family.items():
        outcomes = Counter(str(row.get("associated_outcome") or "unknown") for row in rows)
        total = len(rows)
        mate = outcomes.get("mate", 0)
        max_plies = outcomes.get("max_plies", 0)
        stats[family] = {
            "frame_count": total,
            "mate_count": mate,
            "max_plies_count": max_plies,
            "success_precision": mate / total if total else 0.0,
            "failure_precision": max_plies / total if total else 0.0,
            "outcome_counts": dict(sorted(outcomes.items())),
        }
    return dict(sorted(stats.items()))


def build_payload(frames_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    frames_payload = frames_payload or _load()
    frames = [frame for frame in frames_payload.get("frames") or [] if isinstance(frame, dict)]
    stats = _family_stats(frames)
    strong_failure_families = [
        family
        for family, row in stats.items()
        if row["frame_count"] >= 5 and row["failure_precision"] >= 0.7
    ]
    strong_success_families = [
        family
        for family, row in stats.items()
        if row["frame_count"] >= 5 and row["success_precision"] >= 0.7
    ]
    ambiguous_families = [
        family
        for family, row in stats.items()
        if row["frame_count"] >= 5 and row["success_precision"] < 0.7 and row["failure_precision"] < 0.7
    ]
    status = (
        "protected_strategy_monitor_frames_have_monitor_signal"
        if strong_failure_families or strong_success_families
        else "protected_strategy_monitor_frames_ambiguous"
    )
    return {
        "schema_version": "krk_protected_strategy_monitor_frame_quality.v1",
        "causal_status": "non_causal_source_quality_probe",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_candidate_generator_changes_implemented": False,
        "runtime_selector_implemented": False,
        "runtime_score_changes": False,
        "runtime_direct_routing": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "stage7_promotion_allowed": False,
        "stage8_training_allowed": False,
        "source_artifact": str(FRAMES),
        "summary": {
            "frame_count": len(frames),
            "stage7_challenge_row_count": sum(1 for frame in frames if frame.get("stage7_challenge_row")),
            "stage7_readiness_training_row_count": 0,
            "strong_failure_family_count": len(strong_failure_families),
            "strong_success_family_count": len(strong_success_families),
            "ambiguous_family_count": len(ambiguous_families),
        },
        "family_stats": stats,
        "interpretation": {
            "strong_failure_families": strong_failure_families,
            "strong_success_families": strong_success_families,
            "ambiguous_families": ambiguous_families,
            "monitor_frames_are_candidates_not_actions": True,
            "runtime_observation_source_review_possible": bool(
                strong_failure_families or strong_success_families
            ),
        },
        "decision": {
            "status": status,
            "implementation_allowed_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "protected_strategy_monitor_observation_source_review_packet"
            if status == "protected_strategy_monitor_frames_have_monitor_signal"
            else "refine_strategy_monitor_companion_terms",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Protected Strategy Monitor Frame Quality v1",
        "",
        "This probe summarizes protected broader-strategy monitor frames. It does not authorize runtime source expansion.",
        "",
        "## Decision",
        "",
        f"- status: `{payload['decision']['status']}`",
        f"- selector_allowed: `{payload['decision']['selector_allowed']}`",
        f"- recommended_next_step: `{payload['decision']['recommended_next_step']}`",
        "",
        "## Summary",
        "",
        f"- frame_count: {summary['frame_count']}",
        f"- strong_failure_family_count: {summary['strong_failure_family_count']}",
        f"- strong_success_family_count: {summary['strong_success_family_count']}",
        f"- ambiguous_family_count: {summary['ambiguous_family_count']}",
        "",
        "## Family Stats",
        "",
    ]
    for family, stats in payload["family_stats"].items():
        lines.append(
            f"- `{family}`: count={stats['frame_count']} success_precision=`{stats['success_precision']:.3f}` "
            f"failure_precision=`{stats['failure_precision']:.3f}` outcomes=`{stats['outcome_counts']}`"
        )
    lines.extend(
        [
            "",
            "## Boundary",
            "",
            "Monitor frames are candidates, not actions. Runtime observation expansion still requires a separate review packet.",
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
