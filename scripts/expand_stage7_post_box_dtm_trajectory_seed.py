#!/usr/bin/env python3
"""Expand Stage 7 post-box DTM trajectories from failed capsule rollouts.

This is DAgger-style offline supervision only: collect White-to-move states
visited by the current sandbox capsule, query the offline KRK DTM oracle, and
emit new shortest-DTM trajectories from those states. The output must not be
used as a runtime tablebase/controller.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_stage7_post_box_dtm_trajectory_seed import build_trajectory_seed
from probe_krk_dtm_oracle import _state_from_board, build_krk_dtm


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _dtm_for_fen(fen: str, index: dict[Any, int], dtm: list[int]) -> int:
    board = chess.Board(fen)
    state = _state_from_board(board)
    if state is None or state not in index:
        return -1
    return int(dtm[index[state]])


def _base_training_fens(seed: dict[str, Any]) -> set[str]:
    fens: set[str] = set()
    for trajectory in seed.get("trajectories") or []:
        if not isinstance(trajectory, dict):
            continue
        if trajectory.get("start_fen"):
            fens.add(str(trajectory["start_fen"]))
        for step in trajectory.get("white_training_steps") or []:
            if isinstance(step, dict) and step.get("fen"):
                fens.add(str(step["fen"]))
    return fens


def collect_rollout_fens(
    *,
    replay_payloads: list[dict[str, Any]],
    exclude_fens: set[str],
    max_new_starts: int,
    max_start_dtm: int,
) -> list[dict[str, Any]]:
    _, index, dtm = build_krk_dtm()
    records: list[dict[str, Any]] = []
    seen = set(exclude_fens)
    for replay_source_index, payload in enumerate(replay_payloads):
        source = str(payload.get("topology") or payload.get("schema_version") or replay_source_index)
        for record_index, record in enumerate(payload.get("records") or []):
            if not isinstance(record, dict) or record.get("result") == "mate":
                continue
            trace = record.get("trace") if isinstance(record.get("trace"), list) else []
            for event in trace:
                if not isinstance(event, dict) or event.get("turn") != "white" or not event.get("fen"):
                    continue
                fen = str(event["fen"])
                if fen in seen:
                    continue
                board = chess.Board(fen)
                if board.turn != chess.WHITE or board.is_checkmate() or board.is_stalemate():
                    continue
                state_dtm = _dtm_for_fen(fen, index, dtm)
                if state_dtm <= 0 or state_dtm > max_start_dtm:
                    continue
                seen.add(fen)
                records.append({
                    "fen": fen,
                    "state_dtm": state_dtm,
                    "source_replay": source,
                    "source_record_index": record_index,
                    "source_ply": event.get("ply"),
                    "selected_move_at_state": event.get("move"),
                    "source_result": record.get("result"),
                })
                if len(records) >= max_new_starts:
                    return records
    return records


def expand_seed(
    *,
    base_seed_path: Path,
    replay_paths: list[Path],
    max_new_starts: int = 24,
    max_start_dtm: int = 40,
    trajectory_max_plies: int = 40,
) -> dict[str, Any]:
    base_seed = _load_json(base_seed_path)
    replay_payloads = [_load_json(path) for path in replay_paths]
    expansion_records = collect_rollout_fens(
        replay_payloads=replay_payloads,
        exclude_fens=_base_training_fens(base_seed),
        max_new_starts=max_new_starts,
        max_start_dtm=max_start_dtm,
    )
    oracle_payload = {
        "schema_version": "stage7_post_box_dagger_expansion_oracle.v1",
        "causal_status": "non_causal_training_evidence",
        "records": expansion_records,
        "runtime_forbidden_terms": [
            "tablebase_lookup",
            "dtm_oracle_move_selection",
            "state_hash_exception",
        ],
    }
    tmp_oracle = Path("/tmp/stage7_post_box_dagger_expansion_oracle.json")
    tmp_oracle.write_text(json.dumps(oracle_payload, indent=2) + "\n", encoding="utf-8")
    expansion_seed = build_trajectory_seed(oracle_path=tmp_oracle, max_plies=trajectory_max_plies)
    trajectories = list(base_seed.get("trajectories") or []) + list(expansion_seed.get("trajectories") or [])
    return {
        "schema_version": "stage7_post_box_dtm_trajectory_seed.v1",
        "expansion_schema_version": "stage7_post_box_dagger_trajectory_seed_expansion.v1",
        "causal_status": "non_causal_training_evidence",
        "base_seed_source": str(base_seed_path),
        "replay_sources": [str(path) for path in replay_paths],
        "target_skill": "krk.post_box_shrink_continuation",
        "trajectory_count": len(trajectories),
        "base_trajectory_count": len(base_seed.get("trajectories") or []),
        "expanded_trajectory_count": len(expansion_seed.get("trajectories") or []),
        "white_training_step_count": sum(
            int(item.get("white_training_step_count", 0) or 0) for item in trajectories if isinstance(item, dict)
        ),
        "expansion_records": expansion_records,
        "trajectories": trajectories,
        "constraints": [
            "offline_training_seed_only",
            "do_not_use_dtm_or_tablebase_at_runtime",
            "do_not_use_state_hash_exception_at_runtime",
            "do_not_promote_without_guardrails",
            "replay_trace_states_are_evidence_not_runtime_control",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Expand Stage 7 post-box trajectory seed from failed rollouts")
    parser.add_argument("--base-seed", type=Path, required=True)
    parser.add_argument("--closed-loop-replay", type=Path, action="append", default=[])
    parser.add_argument("--max-new-starts", type=int, default=24)
    parser.add_argument("--max-start-dtm", type=int, default=40)
    parser.add_argument("--trajectory-max-plies", type=int, default=40)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--jsonl-output", type=Path, default=None)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = expand_seed(
        base_seed_path=args.base_seed,
        replay_paths=list(args.closed_loop_replay),
        max_new_starts=args.max_new_starts,
        max_start_dtm=args.max_start_dtm,
        trajectory_max_plies=args.trajectory_max_plies,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.jsonl_output:
        args.jsonl_output.parent.mkdir(parents=True, exist_ok=True)
        with args.jsonl_output.open("w", encoding="utf-8") as fh:
            for trajectory in payload.get("trajectories") or []:
                for step in trajectory.get("white_training_steps") or []:
                    fh.write(json.dumps(step, sort_keys=True) + "\n")
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
