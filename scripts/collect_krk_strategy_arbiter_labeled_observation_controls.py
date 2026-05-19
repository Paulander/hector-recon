#!/usr/bin/env python3
"""Collect stratified labeled KRK strategy-arbiter observation controls."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import chess

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.collect_krk_strategy_arbiter_observation_frames import (  # noqa: E402
    FRAMES,
    TOPOLOGY,
    _load_json,
    _profile_kwargs,
)
from scripts.test_krk_landmark_progress import (  # noqa: E402
    COMPOSITION_PROFILE_HANDOFF_V1,
    _skill_id_for_suggestion,
    build_graph_from_topology,
    choose_move_details,
)
from recon_lite.engine import ReConEngine  # noqa: E402


OUT_JSON = Path("reports/krk_strategy_arbiter_labeled_observation_controls_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_labeled_observation_controls_v0.md")


def _proposal_label_sets(frame: dict[str, Any]) -> dict[str, Any]:
    positives: set[str] = set()
    negatives: set[str] = set()
    unknowns: set[str] = set()
    for proposal in frame.get("strategy_proposal_frames", []) or []:
        if not isinstance(proposal, dict):
            continue
        provider = str(proposal.get("provider_id") or proposal.get("skill_id") or "")
        if not provider:
            continue
        forced = proposal.get("forced_control_outcome_label")
        known = proposal.get("known_outcome_label")
        result = None
        if isinstance(forced, dict):
            result = forced.get("result")
        if not result and isinstance(known, dict):
            result = known.get("playout_result")
        if result == "mate":
            positives.add(provider)
        elif result in {"max_plies", "draw", "no_move", "illegal_move"}:
            negatives.add(provider)
        else:
            unknowns.add(provider)
    return {
        "positive_providers": sorted(positives),
        "negative_providers": sorted(negatives),
        "unknown_providers": sorted(unknowns),
        "known_label_count": len(positives) + len(negatives),
    }


def _select_frames(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    # Include all labeled protected controls, then a bounded Stage7 holdout slice.
    for stage in ("stage5", "stage6", "stage4"):
        for frame in frames:
            if str(frame.get("source_stage") or "") != stage:
                continue
            labels = _proposal_label_sets(frame)
            if labels["known_label_count"] <= 0:
                continue
            key = (str(frame.get("state_id") or ""), stage)
            if key in seen:
                continue
            seen.add(key)
            selected.append(frame)
    stage7_added = 0
    for frame in frames:
        if str(frame.get("source_stage") or "") != "stage7":
            continue
        key = (str(frame.get("state_id") or ""), "stage7")
        if key in seen:
            continue
        seen.add(key)
        selected.append(frame)
        stage7_added += 1
        if stage7_added >= 6:
            break
    return selected


def build_export(root: Path = ROOT) -> dict[str, Any]:
    frames_payload = _load_json(FRAMES)
    graph = build_graph_from_topology(root / TOPOLOGY)
    engine = ReConEngine(graph)
    records: list[dict[str, Any]] = []
    kwargs = _profile_kwargs()
    for frame in _select_frames(list(frames_payload.get("frames", []) or [])):
        board = chess.Board(str(frame.get("fen")))
        active_label = str(frame.get("active_landmark_label") or "")
        move_details = choose_move_details(
            graph,
            engine,
            board,
            max_ticks=200,
            suggestion_limit=10,
            active_landmark_label=active_label,
            krk_strategy_arbiter_observability_enabled=True,
            enable_diagnostic_caches=True,
            **kwargs,
        )
        selected = dict(move_details.get("selected_suggestion", {}) or {})
        labels = _proposal_label_sets(frame)
        selected_provider = _skill_id_for_suggestion(selected) if selected else None
        selected_label = "unknown"
        if selected_provider in labels["positive_providers"]:
            selected_label = "positive"
        elif selected_provider in labels["negative_providers"]:
            selected_label = "negative"
        records.append({
            "schema_version": "krk_strategy_arbiter_labeled_observation_control.v0",
            "causal_status": "non_causal_labeled_observation_control",
            "frame_id": frame.get("frame_id"),
            "state_id": frame.get("state_id"),
            "source_stage": frame.get("source_stage"),
            "active_landmark_label": active_label,
            "fen": frame.get("fen"),
            "selected_move": move_details.get("move"),
            "selected_provider": selected_provider,
            "selected_label": selected_label,
            "positive_providers": labels["positive_providers"],
            "negative_providers": labels["negative_providers"],
            "known_label_count": labels["known_label_count"],
            "observation": dict(move_details.get("krk_strategy_arbiter_observation", {}) or {}),
        })
    stage_counts = Counter(str(record.get("source_stage") or "unknown") for record in records)
    selected_label_counts = Counter(str(record.get("selected_label") or "unknown") for record in records)
    return {
        "schema_version": "krk_strategy_arbiter_labeled_observation_controls.v0",
        "causal_status": "non_causal_labeled_observation_controls",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "source_artifacts": [str(FRAMES), str(TOPOLOGY)],
        "composition_profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "record_count": len(records),
        "stage_counts": dict(sorted(stage_counts.items())),
        "selected_label_counts": dict(sorted(selected_label_counts.items())),
        "records": records,
        "decision": {
            "status": "labeled_observation_controls_collected",
            "runtime_arbiter_allowed": False,
            "recommended_next_step": "probe_labeled_observation_controls_replay_free",
        },
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# KRK Strategy Arbiter Labeled Observation Controls v0",
        "",
        "This export collects trace-only observations for labeled protected controls plus a bounded Stage7 holdout slice.",
        "",
        "## Summary",
        "",
        f"- Records: `{payload['record_count']}`",
        f"- Stage counts: `{payload['stage_counts']}`",
        f"- Selected label counts: `{payload['selected_label_counts']}`",
        "",
        "## Records",
        "",
    ]
    for record in payload["records"]:
        lines.append(
            f"- `{record['state_id']}` stage=`{record['source_stage']}` "
            f"selected=`{record['selected_provider']}` label=`{record['selected_label']}` "
            f"positives=`{record['positive_providers']}` negatives=`{record['negative_providers']}`"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        "Runtime arbiter remains blocked.",
    ])
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_export()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, OUT_MD)


if __name__ == "__main__":
    main()
