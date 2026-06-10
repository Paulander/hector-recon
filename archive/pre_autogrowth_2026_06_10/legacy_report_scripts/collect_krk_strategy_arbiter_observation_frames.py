#!/usr/bin/env python3
"""Collect default-off KRK strategy-arbiter observation frames.

This script is diagnostic-only. It replays existing control-plane FENs through
the normal one-ply suggestion path with trace-only observability enabled, then
serializes the resulting non-causal observation metadata. It does not run
conversion playouts, train, mutate topology, or change runtime defaults.
"""

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

from scripts.test_krk_landmark_progress import (  # noqa: E402
    COMPOSITION_PROFILE_HANDOFF_V1,
    _composition_profile_metadata,
    _skill_id_for_suggestion,
    build_graph_from_topology,
    choose_move_details,
)
from recon_lite.engine import ReConEngine  # noqa: E402


FRAMES = Path("reports/krk_control_plane_filtered_frames_with_forced_controls_v0.json")
TOPOLOGY = Path(
    "snapshots/krk_triplet_pipeline/adaptive_krk_stage6_drive_overlay_composed/topology/krk_entry_topology.json"
)
OUT_JSON = Path("reports/krk_strategy_arbiter_observation_frames_v0.json")
OUT_MD = Path("reports/krk_strategy_arbiter_observation_frames_v0.md")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _profile_kwargs() -> dict[str, Any]:
    profile = _composition_profile_metadata(COMPOSITION_PROFILE_HANDOFF_V1) or {}
    settings = dict(profile.get("settings", {}) or {})
    return {
        "successor_affordance_layer_enabled": bool(
            settings.get("successor_affordance_layer_enabled", False)
        ),
        "successor_role_license_enabled": bool(
            settings.get("successor_role_license_enabled", False)
        ),
        "successor_role_scoped_move_shape_enabled": bool(
            settings.get("successor_role_scoped_move_shape_enabled", False)
        ),
        "successor_role_scoped_move_shape_bonus": float(
            settings.get("successor_role_scoped_move_shape_bonus", 0.0)
        ),
        "stagnation_breaker_enabled": bool(settings.get("stagnation_breaker_enabled", False)),
        "stagnation_breaker_bonus": float(settings.get("stagnation_breaker_bonus", 0.0)),
        "post_break_continuation_enabled": bool(
            settings.get("post_break_continuation_enabled", False)
        ),
        "post_break_continuation_bonus": float(
            settings.get("post_break_continuation_bonus", 0.0)
        ),
        "successor_stage0_drift_penalty": float(
            settings.get("successor_stage0_drift_penalty", 0.0)
        ),
    }


def _frame_rows(payload: dict[str, Any], *, max_frames: int) -> list[dict[str, Any]]:
    frames = list(payload.get("frames", []) or [])
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    # Keep a small stratified order: Stage7 challenge rows first, then protected controls.
    frames.sort(key=lambda item: (str(item.get("source_stage") or "") != "stage7", str(item.get("state_id") or "")))
    for frame in frames:
        fen = frame.get("fen")
        state_id = str(frame.get("state_id") or frame.get("frame_id") or "")
        if not fen or state_id in seen:
            continue
        seen.add(state_id)
        selected.append(frame)
        if len(selected) >= max_frames:
            break
    return selected


def build_observation_export(root: Path = ROOT, *, max_frames: int = 12) -> dict[str, Any]:
    frames_payload = _load_json(FRAMES)
    graph = build_graph_from_topology(root / TOPOLOGY)
    engine = ReConEngine(graph)
    records: list[dict[str, Any]] = []
    kwargs = _profile_kwargs()
    for frame in _frame_rows(frames_payload, max_frames=max_frames):
        fen = str(frame.get("fen"))
        board = chess.Board(fen)
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
        observation = dict(move_details.get("krk_strategy_arbiter_observation", {}) or {})
        records.append({
            "schema_version": "krk_strategy_arbiter_observation_record.v0",
            "causal_status": "non_causal_observation_record",
            "frame_id": frame.get("frame_id"),
            "state_id": frame.get("state_id"),
            "source_stage": frame.get("source_stage"),
            "active_landmark_label": active_label,
            "fen": fen,
            "selected_move": move_details.get("move"),
            "selected_provider": _skill_id_for_suggestion(selected) if selected else None,
            "selected_score": move_details.get("confidence"),
            "observation": observation,
        })
    stage_counts = Counter(str(record.get("source_stage") or "unknown") for record in records)
    selected_provider_counts = Counter(
        str(record.get("selected_provider") or "unknown") for record in records
    )
    proposal_counts = [
        int((record.get("observation") or {}).get("proposal_count", 0) or 0)
        for record in records
    ]
    return {
        "schema_version": "krk_strategy_arbiter_observation_frames.v0",
        "causal_status": "non_causal_observation_export",
        "runtime_behavior_changed": False,
        "runtime_defaults_changed": False,
        "runtime_arbiter_implemented": False,
        "runtime_dtm_or_tablebase_lookup": False,
        "gameplay_topology_mutation": False,
        "source_artifacts": [str(FRAMES), str(TOPOLOGY)],
        "composition_profile": COMPOSITION_PROFILE_HANDOFF_V1,
        "max_frames": max_frames,
        "record_count": len(records),
        "stage_counts": dict(sorted(stage_counts.items())),
        "selected_provider_counts": dict(sorted(selected_provider_counts.items())),
        "proposal_count_min": min(proposal_counts) if proposal_counts else 0,
        "proposal_count_max": max(proposal_counts) if proposal_counts else 0,
        "records": records,
        "decision": {
            "status": "observation_frames_collected",
            "runtime_arbiter_allowed": False,
            "recommended_next_step": "review_observation_frame_separability_before_any_sandbox"
        },
    }


def write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# KRK Strategy Arbiter Observation Frames v0",
        "",
        "This is a non-causal one-ply observation export over existing control-plane FENs.",
        "It does not run conversion playouts, train, mutate topology, or change runtime defaults.",
        "",
        "## Summary",
        "",
        f"- Records: `{payload['record_count']}`",
        f"- Composition profile: `{payload['composition_profile']}`",
        f"- Stage counts: `{payload['stage_counts']}`",
        f"- Selected provider counts: `{payload['selected_provider_counts']}`",
        f"- Proposal count range: `{payload['proposal_count_min']}` to `{payload['proposal_count_max']}`",
        "",
        "## Records",
        "",
    ]
    for record in payload["records"]:
        observation = record.get("observation") or {}
        lines.extend([
            f"- `{record.get('state_id')}` stage=`{record.get('source_stage')}` "
            f"label=`{record.get('active_landmark_label')}` "
            f"selected=`{record.get('selected_provider')}` move=`{record.get('selected_move')}` "
            f"proposals=`{observation.get('proposal_count')}`",
        ])
    lines.extend([
        "",
        "## Decision",
        "",
        f"Status: `{payload['decision']['status']}`",
        "",
        "Runtime arbitration remains blocked. Review observation-frame separability before any sandbox.",
    ])
    (ROOT / path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    payload = build_observation_export()
    (ROOT / OUT_JSON).write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(payload, OUT_MD)


if __name__ == "__main__":
    main()
