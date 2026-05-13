#!/usr/bin/env python3
"""Replay failed KRK handoff states with forced successor skills.

This is an offline audit tool. It reads diagnostic JSON emitted by
``test_krk_landmark_progress.py`` and replays only failed post-reply states,
forcing one candidate successor skill for the first White continuation move.
It does not change topology or runtime routing.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

import chess

from recon_lite.engine import ReConEngine

from test_krk_landmark_progress import (
    build_graph_from_topology,
    run_counterfactual_successor_sweep,
    stable_record_id,
    summarize_counterfactual_successor_sweeps,
)


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def _route_scores(evidence: dict[str, Any]) -> dict[str, float]:
    skills = evidence.get("successor_skills")
    if not isinstance(skills, dict):
        return {}
    scores: dict[str, float] = {}
    for skill_id, payload in skills.items():
        if isinstance(payload, dict):
            scores[str(skill_id)] = float(payload.get("score", 0.0) or 0.0)
    return scores


def failed_post_reply_states(
    diagnostic: dict[str, Any],
    *,
    dedupe_state_signatures: bool = True,
) -> list[dict[str, Any]]:
    """Extract failed post-opponent-reply states from a diagnostic payload."""
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    for packet in diagnostic.get("handoff_packets") or []:
        if not isinstance(packet, dict):
            continue
        if packet.get("phase") != "post_opponent_reply":
            continue
        evidence = packet.get("evidence_terms")
        if not isinstance(evidence, dict):
            continue
        result = str(evidence.get("playout_result") or packet.get("observed_outcome") or "unknown")
        if result == "mate":
            continue
        post_reply_fen = evidence.get("post_reply_fen")
        if not post_reply_fen:
            continue
        try:
            state_signature = stable_record_id("state", chess.Board(post_reply_fen).board_fen(), chess.WHITE)
        except Exception:
            state_signature = "state.invalid"
        if dedupe_state_signatures and state_signature in seen:
            continue
        seen.add(state_signature)
        records.append({
            "packet_id": packet.get("packet_id"),
            "state_signature": state_signature,
            "start_fen": evidence.get("fen"),
            "post_reply_fen": post_reply_fen,
            "actual_selected_successor": evidence.get("successor_selected_skill"),
            "actual_result": result,
            "actual_route_scores": _route_scores(evidence),
            "failure_classes": list(evidence.get("failure_classes") or []),
        })
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Replay failed KRK handoff states with forced successors")
    parser.add_argument("--diagnostic", type=Path, required=True)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--successors", type=str, required=True,
                        help="Comma-separated canonical successor skill IDs")
    parser.add_argument("--label", default="fence_established")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--max-states", type=int, default=0,
                        help="If >0, limit replay to this many failed post-reply states")
    parser.add_argument("--include-duplicate-states", action="store_true",
                        help="Replay duplicate failed post-reply state signatures instead of one representative each")
    parser.add_argument("--playout-max-plies", type=int, default=80)
    parser.add_argument("--black-policy", choices=["random", "adversarial"], default="adversarial")
    parser.add_argument("--max-ticks", type=int, default=200)
    parser.add_argument("--suggestion-limit", type=int, default=5)
    parser.add_argument("--enable-successor-affordance-layer", action="store_true")
    parser.add_argument("--steps-output", type=Path, default=None,
                        help="Optional JSONL path for per-forced-successor records")
    parser.add_argument("--sweeps-output", type=Path, default=None,
                        help="Optional JSONL path for per-state sweep records")
    parser.add_argument("--json-output", type=Path, default=None)
    args = parser.parse_args()

    diagnostic = json.loads(args.diagnostic.read_text(encoding="utf-8"))
    all_states = failed_post_reply_states(diagnostic, dedupe_state_signatures=False)
    states = failed_post_reply_states(
        diagnostic,
        dedupe_state_signatures=not args.include_duplicate_states,
    )
    if args.max_states > 0:
        states = states[:args.max_states]
    successors = tuple(item.strip() for item in args.successors.split(",") if item.strip())

    graph = build_graph_from_topology(args.topology)
    engine = ReConEngine(graph)
    rng = random.Random(args.seed)

    sweeps: list[dict[str, Any]] = []
    for index, state in enumerate(states, start=1):
        print(
            f"{index:4d}/{len(states)} state={state['state_signature']} "
            f"actual={state.get('actual_selected_successor')} result={state.get('actual_result')}",
            flush=True,
        )
        step_context = {
            "source_diagnostic": str(args.diagnostic),
            "state_index": index - 1,
            **state,
        }
        results = run_counterfactual_successor_sweep(
            graph,
            engine,
            post_reply_fen=str(state["post_reply_fen"]),
            successors=successors,
            rng=rng,
            label=args.label,
            max_plies=args.playout_max_plies,
            black_policy=args.black_policy,
            max_ticks=args.max_ticks,
            suggestion_limit=args.suggestion_limit,
            successor_affordance_layer_enabled=args.enable_successor_affordance_layer,
            step_output=args.steps_output,
            step_context=step_context,
        )
        sweep = {
            **state,
            "counterfactual_results": results,
        }
        sweeps.append(sweep)
        if args.sweeps_output is not None:
            _append_jsonl(args.sweeps_output, sweep)

    summary = {
        "schema_version": "krk_counterfactual_successor_sweep.v1",
        "source_diagnostic": str(args.diagnostic),
        "topology": str(args.topology),
        "successors": list(successors),
        "source_failed_state_count": len(all_states),
        "failed_state_count": len(states),
        "dedupe_state_signatures": not args.include_duplicate_states,
        "counterfactual_successor_sweeps": sweeps,
        "counterfactual_successor_summary": summarize_counterfactual_successor_sweeps(sweeps),
    }
    if args.json_output is not None:
        args.json_output.parent.mkdir(parents=True, exist_ok=True)
        args.json_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary["counterfactual_successor_summary"], indent=2))


if __name__ == "__main__":
    main()
