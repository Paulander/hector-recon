#!/usr/bin/env python3
"""Align CandidateMoveFrame records with DTM/reference trajectory labels.

This is a non-causal diagnosis step. It decides whether a residual family
looks like a visible single-move role candidate or a multi-step continuation
gap. It must not select moves, train providers, or mutate topology.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _terms(frame: dict[str, Any], key: str) -> set[str]:
    values = frame.get(key)
    if not isinstance(values, list):
        return set()
    return {str(item) for item in values}


def _common(frames: list[dict[str, Any]], key: str) -> set[str]:
    sets = [_terms(frame, key) for frame in frames]
    if not sets:
        return set()
    acc = set(sets[0])
    for item in sets[1:]:
        acc &= item
    return acc


def _counts(frames: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for frame in frames:
        counter.update(_terms(frame, key))
    return dict(sorted(counter.items()))


def _record_for_fen(payload: dict[str, Any], fen: str) -> dict[str, Any] | None:
    for record in payload.get("records") or []:
        if isinstance(record, dict) and str(record.get("fen") or "") == fen:
            return record
    return None


def _trajectory_for_fen(payload: dict[str, Any], fen: str) -> dict[str, Any] | None:
    for trajectory in payload.get("trajectories") or []:
        if isinstance(trajectory, dict) and str(trajectory.get("start_fen") or "") == fen:
            return trajectory
    return None


def _legal_first_summary(payload: dict[str, Any], fen: str) -> dict[str, Any]:
    outcomes: Counter[str] = Counter()
    mating_moves: list[dict[str, Any]] = []
    probe_count = 0
    for record in payload.get("records") or []:
        if not isinstance(record, dict) or str(record.get("post_reply_fen") or "") != fen:
            continue
        for probe in record.get("legal_first_probes") or []:
            if not isinstance(probe, dict):
                continue
            probe_count += 1
            horizon = int(probe.get("horizon") or 0)
            result = str(probe.get("result") or "unknown")
            outcomes[f"h{horizon}:{result}"] += 1
            if result == "mate":
                mating_moves.append(
                    {
                        "move": probe.get("move"),
                        "horizon": horizon,
                        "plies": probe.get("plies"),
                    }
                )
    return {
        "probe_count": probe_count,
        "outcome_counts": dict(sorted(outcomes.items())),
        "mating_moves": mating_moves,
    }


def diagnose_alignment(
    *,
    candidate_frames_path: Path,
    dtm_oracle_path: Path,
    trajectory_path: Path | None = None,
    legal_first_path: Path | None = None,
    fen: str | None = None,
) -> dict[str, Any]:
    frame_payload = _load_json(candidate_frames_path)
    dtm_payload = _load_json(dtm_oracle_path)
    frame_records = [
        record
        for record in (frame_payload.get("records") or [])
        if isinstance(record, dict)
    ]
    if not frame_records:
        raise ValueError("candidate frame audit contains no records")
    target_fen = fen or str(frame_records[0].get("fen") or "")
    frame_record = next(
        (record for record in frame_records if str(record.get("fen") or "") == target_fen),
        None,
    )
    if frame_record is None:
        raise ValueError(f"candidate frame audit missing FEN: {target_fen}")
    dtm_record = _record_for_fen(dtm_payload, target_fen)
    if dtm_record is None:
        raise ValueError(f"DTM oracle missing FEN: {target_fen}")

    frames_by_move = {
        str(frame.get("move_uci")): frame
        for frame in frame_record.get("candidate_move_frames") or []
        if isinstance(frame, dict)
    }
    legal_by_move = {
        str(item.get("move")): item
        for item in dtm_record.get("legal_moves") or []
        if isinstance(item, dict)
    }
    best_moves = [str(item.get("move")) for item in dtm_record.get("best_winning_moves") or []]
    child_dtms = [
        int(item.get("child_dtm"))
        for item in legal_by_move.values()
        if item.get("child_dtm") is not None and int(item.get("child_dtm")) >= 0
    ]
    best_child_dtm = min(child_dtms) if child_dtms else None

    labeled_frames: list[dict[str, Any]] = []
    optimal_frames: list[dict[str, Any]] = []
    winning_frames: list[dict[str, Any]] = []
    nonoptimal_winning_frames: list[dict[str, Any]] = []
    for move, frame in sorted(frames_by_move.items()):
        legal = legal_by_move.get(move, {})
        child_dtm = legal.get("child_dtm")
        forces_mate = bool(legal.get("forces_mate", False))
        is_optimal = (
            best_child_dtm is not None
            and child_dtm is not None
            and int(child_dtm) == int(best_child_dtm)
        )
        row = {
            "move": move,
            "forces_mate": forces_mate,
            "child_dtm": child_dtm,
            "optimal_dtm_move": bool(is_optimal),
            "candidate_frame": frame,
        }
        labeled_frames.append(row)
        if forces_mate:
            winning_frames.append(frame)
        if is_optimal:
            optimal_frames.append(frame)
        elif forces_mate:
            nonoptimal_winning_frames.append(frame)

    separating_terms: dict[str, list[str]] = {}
    term_splits: dict[str, Any] = {}
    for key in ("current_terms", "move_shape_terms", "post_move_terms"):
        optimal_common = _common(optimal_frames, key)
        nonoptimal_counts = _counts(nonoptimal_winning_frames, key)
        split = sorted(term for term in optimal_common if nonoptimal_counts.get(term, 0) == 0)
        term_splits[key] = {
            "optimal_common": sorted(optimal_common),
            "winning_counts": _counts(winning_frames, key),
            "nonoptimal_winning_counts": nonoptimal_counts,
            "optimal_common_absent_from_nonoptimal_winning": split,
        }
        if split:
            separating_terms[key] = split

    trajectory_summary: dict[str, Any] = {}
    if trajectory_path is not None:
        trajectory_payload = _load_json(trajectory_path)
        trajectory = _trajectory_for_fen(trajectory_payload, target_fen)
        if trajectory is not None:
            first_steps = []
            for step in trajectory.get("white_training_steps") or []:
                if not isinstance(step, dict):
                    continue
                first_steps.append(
                    {
                        "ply_index": step.get("ply_index"),
                        "move": step.get("move"),
                        "child_dtm": step.get("child_dtm"),
                        "move_shape_terms": step.get("move_shape_terms") or [],
                        "post_move_terms": step.get("post_move_terms") or [],
                    }
                )
            trajectory_summary = {
                "start_dtm": trajectory.get("start_dtm"),
                "ended_in_checkmate": bool(trajectory.get("ended_in_checkmate", False)),
                "white_training_step_count": trajectory.get("white_training_step_count"),
                "first_white_steps": first_steps[:5],
            }

    legal_first = (
        _legal_first_summary(_load_json(legal_first_path), target_fen)
        if legal_first_path is not None
        else {"probe_count": 0, "outcome_counts": {}, "mating_moves": []}
    )

    legal_move_count = int(dtm_record.get("legal_move_count", 0) or 0)
    winning_move_count = int(dtm_record.get("winning_move_count", 0) or 0)
    all_legal_winning = legal_move_count > 0 and winning_move_count == legal_move_count
    legal_first_has_mate = bool(legal_first.get("mating_moves"))
    strong_single_move_boundary = bool(
        separating_terms.get("move_shape_terms") or separating_terms.get("post_move_terms")
    ) and len(optimal_frames) <= max(1, legal_move_count // 3)

    if all_legal_winning and not legal_first_has_mate:
        diagnosis = "multi_step_continuation_policy_gap_not_single_move_gap"
        status = "narrow_plan_capsule_or_overlay_training_protocol_ready"
        candidate_type = "post_box_continuation_overlay_protocol"
    elif strong_single_move_boundary:
        diagnosis = "visible_single_move_role_candidate_possible"
        status = "move_shape_role_sandbox_ready"
        candidate_type = "move_shape_role_refinement"
    else:
        diagnosis = "candidate_move_boundary_underseparated"
        status = "needs_more_reference_or_progress_terms"
        candidate_type = "continuation_diagnosis"

    suffix = "2cc0b3e1033a" if "R7/8/2k5" in target_fen else "unknown"
    return {
        "schema_version": "candidate_move_frame_dtm_alignment.v1",
        "causal_status": "non_causal",
        "target_fen": target_fen,
        "sources": {
            "candidate_frames": str(candidate_frames_path),
            "dtm_oracle": str(dtm_oracle_path),
            "trajectory": str(trajectory_path) if trajectory_path else None,
            "legal_first": str(legal_first_path) if legal_first_path else None,
        },
        "dtm": {
            "state_dtm": dtm_record.get("state_dtm"),
            "legal_move_count": legal_move_count,
            "winning_move_count": winning_move_count,
            "all_legal_moves_win": all_legal_winning,
            "best_child_dtm": best_child_dtm,
            "best_moves": best_moves[:10],
            "optimal_move_count": len(optimal_frames),
        },
        "legal_first_current_graph": legal_first,
        "trajectory_summary": trajectory_summary,
        "term_splits": term_splits,
        "labeled_candidate_frames": labeled_frames,
        "candidate_update": {
            "schema_version": "structural_candidate.v1",
            "candidate_id": (
                f"cand.krk.box_shrink.family_{suffix}.{candidate_type}.v1"
            ),
            "candidate_type": candidate_type,
            "source_monitor_script": "growth.monitor.candidate_move_dtm_alignment",
            "source_terms": [
                "candidate_move_frames_available",
                "dtm_won_within_h40",
                "all_legal_first_moves_tablebase_winning" if all_legal_winning else "some_legal_first_moves_tablebase_losing",
                "current_graph_legal_first_fails" if not legal_first_has_mate else "current_graph_legal_first_has_mate",
            ],
            "trigger_failure_classes": [
                "provider_capacity_missing",
                "continuation_topology_underexpressive",
                "multi_step_policy_gap",
            ],
            "target_skill": "krk.box_shrink",
            "parent_skill": "krk.post_box_shrink_continuation",
            "post_reply_fen": target_fen,
            "diagnosis": diagnosis,
            "proposed_change": {
                "kind": (
                    "narrow_post_box_continuation_capsule_or_overlay_protocol"
                    if candidate_type == "post_box_continuation_overlay_protocol"
                    else "visible_move_shape_role_or_more_terms"
                ),
                "dtm_reference_first_steps": trajectory_summary.get("first_white_steps", [])[:3],
                "visible_progress_terms_to_consider": sorted(
                    set(term_splits.get("post_move_terms", {}).get("optimal_common", []))
                    | set(term_splits.get("move_shape_terms", {}).get("optimal_common", []))
                ),
                "do_not_use_tablebase_at_runtime": True,
                "do_not_use_state_hash_exception": True,
            },
            "promotion_status": status,
            "causal_status": "non_causal",
            "credit": 0.0,
        },
    }


def _write_md(payload: dict[str, Any], path: Path) -> None:
    update = payload["candidate_update"]
    dtm = payload["dtm"]
    legal = payload["legal_first_current_graph"]
    lines = [
        "# CandidateMoveFrame DTM Alignment",
        "",
        f"Schema: `{payload['schema_version']}`",
        f"Causal status: `{payload['causal_status']}`",
        f"FEN: `{payload['target_fen']}`",
        "",
        "## Diagnosis",
        "",
        f"- Candidate: `{update['candidate_id']}`",
        f"- Diagnosis: `{update['diagnosis']}`",
        f"- Status: `{update['promotion_status']}`",
        "",
        "## DTM",
        "",
        f"- State DTM: {dtm.get('state_dtm')}",
        f"- Legal moves: {dtm.get('legal_move_count')}",
        f"- Winning moves: {dtm.get('winning_move_count')}",
        f"- All legal moves win: `{dtm.get('all_legal_moves_win')}`",
        f"- Best child DTM: {dtm.get('best_child_dtm')}",
        f"- Best moves: {', '.join(f'`{move}`' for move in dtm.get('best_moves', [])[:5])}",
        "",
        "## Current Graph Legal-First",
        "",
        f"- Probe count: {legal.get('probe_count')}",
        f"- Outcomes: `{legal.get('outcome_counts')}`",
        "",
        "## Interpretation",
        "",
    ]
    if update["diagnosis"] == "multi_step_continuation_policy_gap_not_single_move_gap":
        lines.extend(
            [
                "All legal first moves are tablebase-winning, but current graph legal-first probes do not convert.",
                "This supports a multi-step continuation/capsule diagnosis rather than another single legal-move role.",
            ]
        )
    else:
        lines.append("The candidate-frame boundary requires further visible-term refinement.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-frames", type=Path, required=True)
    parser.add_argument("--dtm-oracle", type=Path, required=True)
    parser.add_argument("--trajectory", type=Path, default=None)
    parser.add_argument("--legal-first", type=Path, default=None)
    parser.add_argument("--fen", type=str, default=None)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = diagnose_alignment(
        candidate_frames_path=args.candidate_frames,
        dtm_oracle_path=args.dtm_oracle,
        trajectory_path=args.trajectory,
        legal_first_path=args.legal_first,
        fen=args.fen,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.markdown_output is not None:
        _write_md(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
