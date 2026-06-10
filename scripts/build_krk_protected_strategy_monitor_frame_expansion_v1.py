#!/usr/bin/env python3
"""Expand protected KRK StrategyMonitor records into non-causal strategy frames."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MONITOR_RECORDS = Path("reports/strategy_arbitration/krk_strategy_monitor_records_v0.json")
SOURCE_REVIEW = Path(
    "reports/strategy_arbitration/krk_broader_strategy_sequence_candidate_source_review_v1.json"
)
OUT_JSON = Path(
    "reports/strategy_arbitration/"
    "krk_protected_strategy_monitor_frame_expansion_v1.json"
)
OUT_MD = Path(
    "reports/strategy_arbitration/"
    "krk_protected_strategy_monitor_frame_expansion_v1.md"
)

LANDMARK_STAGE = {
    "wrong_tempo_control": "stage4",
    "fence_established": "stage5",
    "drive_to_edge": "stage6",
}
MONITOR_TO_STRATEGY = {
    "OwnerExitMonitor": "terminal.krk.owner_exit_monitor",
    "PhaseBoundaryMonitor": "terminal.krk.phase_boundary_monitor",
    "RepairNeededMonitor": "terminal.krk.repair_needed_monitor",
    "PlanSelectionNeededMonitor": "terminal.krk.plan_selection_needed",
}


def _load(path: Path) -> dict[str, Any]:
    payload = json.loads((ROOT / path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _frame_from_record(record: dict[str, Any], index: int) -> dict[str, Any] | None:
    label = str(record.get("active_landmark_label") or "")
    stage = LANDMARK_STAGE.get(label)
    if not stage:
        return None
    monitor_type = str(record.get("monitor_type") or "unknown")
    strategy_family = MONITOR_TO_STRATEGY.get(monitor_type, f"terminal.krk.{monitor_type}")
    return {
        "schema_version": "strategy_sequence_candidate_frame.v1",
        "frame_id": f"protected_strategy_monitor.{stage}.{index:04d}",
        "frame_type": "broader_krk_strategy_candidate",
        "causal_status": "non_causal",
        "state_id": record.get("state_id"),
        "fen": record.get("fen"),
        "source_stage": stage,
        "active_landmark_label": label,
        "stage7_challenge_row": False,
        "candidate_id": f"candidate.strategy_monitor.{strategy_family}",
        "candidate_strategy_family": strategy_family,
        "candidate_provider_id": None,
        "candidate_move_uci": None,
        "candidate_plan_id": None,
        "source_terms": list(record.get("source_terms") or []),
        "internal_monitor_terms": [str(record.get("monitor_id") or strategy_family)],
        "monitor_type": monitor_type,
        "associated_outcome": record.get("associated_outcome"),
        "suggested_action_class": record.get("suggested_action_class"),
        "confidence": record.get("confidence"),
        "missing_terms": list(record.get("missing_terms") or []),
        "capacity_evidence": {},
        "ownership_evidence": {},
        "sequence_evidence": {},
        "move_shape_terms": [],
        "post_move_terms": [],
        "safety_terms": [],
        "label_semantics": "monitor_strategy_candidate_not_ownership_label",
        "usable_for_candidate_generation_training": False,
        "usable_for_selector_training": False,
        "usable_for_source_review": True,
    }


def build_payload(
    monitor_payload: dict[str, Any] | None = None,
    source_review: dict[str, Any] | None = None,
) -> dict[str, Any]:
    monitor_payload = monitor_payload or _load(MONITOR_RECORDS)
    source_review = source_review or _load(SOURCE_REVIEW)
    frames: list[dict[str, Any]] = []
    for index, record in enumerate(monitor_payload.get("records") or [], start=1):
        if not isinstance(record, dict):
            continue
        frame = _frame_from_record(record, index)
        if frame:
            frames.append(frame)
    by_stage = Counter(str(frame.get("source_stage")) for frame in frames)
    by_family = Counter(str(frame.get("candidate_strategy_family")) for frame in frames)
    by_outcome = Counter(str(frame.get("associated_outcome") or "unknown") for frame in frames)
    status = (
        "protected_strategy_monitor_frames_expanded_non_causal"
        if frames and by_stage
        else "protected_strategy_monitor_frame_expansion_empty"
    )
    return {
        "schema_version": "krk_protected_strategy_monitor_frame_expansion.v1",
        "causal_status": "non_causal_frame_expansion",
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
        "source_artifacts": [str(MONITOR_RECORDS), str(SOURCE_REVIEW)],
        "source_review_status": (source_review.get("decision") or {}).get("status"),
        "summary": {
            "frame_count": len(frames),
            "frame_count_by_stage": dict(sorted(by_stage.items())),
            "frame_count_by_strategy_family": dict(sorted(by_family.items())),
            "frame_count_by_associated_outcome": dict(sorted(by_outcome.items())),
            "stage7_challenge_row_count": sum(1 for frame in frames if frame["stage7_challenge_row"]),
            "stage7_readiness_training_row_count": 0,
        },
        "frames": frames,
        "decision": {
            "status": status,
            "implementation_allowed_by_this_artifact": False,
            "selector_allowed": False,
            "guardrails_allowed": False,
            "runtime_changes_allowed": False,
            "recommended_next_step": "probe_protected_strategy_monitor_frame_source_quality",
        },
    }


def write_markdown(payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "# KRK Protected Strategy Monitor Frame Expansion v1",
        "",
        "This replay-free expansion converts protected Stage 4/5/6 StrategyMonitor records into broader-strategy candidate frames. It is non-causal.",
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
        f"- frame_count_by_stage: `{summary['frame_count_by_stage']}`",
        f"- frame_count_by_strategy_family: `{summary['frame_count_by_strategy_family']}`",
        f"- frame_count_by_associated_outcome: `{summary['frame_count_by_associated_outcome']}`",
        f"- stage7_challenge_row_count: {summary['stage7_challenge_row_count']}",
        "",
        "## Boundary",
        "",
        "These frames are source-review evidence only. They do not authorize runtime source expansion, selector training, score changes, guardrails, Stage 7 promotion, or Stage 8 training.",
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
