#!/usr/bin/env python3
"""Targeted Stage 7 role-owned arbitration runtime probe.

This is a sandbox diagnostic. It starts from post-box-shrink family states and
runs normal playout with role-owned score normalization enabled. It does not
force a provider and does not mutate topology.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import Any

import chess

sys.path.insert(0, str(Path(__file__).resolve().parent))

from recon_lite.engine import ReConEngine

from test_krk_landmark_progress import (
    build_graph_from_topology,
    play_to_mate,
    stable_record_id,
)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _families(diagnosis: dict[str, Any], state_ids: tuple[str, ...]) -> list[dict[str, Any]]:
    allowed = set(state_ids)
    records = list(diagnosis.get("families") or diagnosis.get("unique_failed_post_reply_states") or [])
    out: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or not record.get("post_reply_fen"):
            continue
        try:
            board = chess.Board(str(record["post_reply_fen"]))
            state_id = str(record.get("state_id") or stable_record_id("state", board.board_fen(), chess.WHITE))
        except Exception:
            continue
        if allowed and state_id not in allowed:
            continue
        out.append({**record, "state_id": state_id})
    return out


def _first_white_event(result: dict[str, Any]) -> dict[str, Any]:
    for event in result.get("trace") or []:
        if isinstance(event, dict) and event.get("turn") == "white":
            return event
    return {}


def _event_summary(event: dict[str, Any]) -> dict[str, Any]:
    engine = event.get("engine") if isinstance(event.get("engine"), dict) else {}
    selected = engine.get("selected_suggestion") if isinstance(engine.get("selected_suggestion"), dict) else {}
    evidence = engine.get("selected_successor_summary") if isinstance(
        engine.get("selected_successor_summary"), dict
    ) else {}
    return {
        "move": event.get("move"),
        "selected_skill": evidence.get("successor_selected_skill")
        or selected.get("skill_id")
        or selected.get("curriculum_label"),
        "selected_score": selected.get("score"),
        "selected_by_role_owned_score_normalization": bool(
            engine.get("selected_by_role_owned_score_normalization", False)
        ),
        "visible_role_owned_score_normalization": dict(
            engine.get("visible_role_owned_score_normalization", {}) or {}
        ),
        "visible_role_provider_support_adapter": dict(
            evidence.get("visible_role_provider_support_adapter", {})
            or selected.get("visible_role_provider_support_adapter", {})
            or {}
        ),
        "role_owned_raw_selected": dict(engine.get("role_owned_raw_selected", {}) or {}),
    }


def run_probe(args: argparse.Namespace) -> dict[str, Any]:
    diagnosis = _load_json(args.family_diagnosis)
    graph = build_graph_from_topology(args.topology)
    engine = ReConEngine(graph)
    rng = random.Random(args.seed)
    records: list[dict[str, Any]] = []
    for family in _families(diagnosis, _parse_csv(args.state_ids)):
        board = chess.Board(str(family["post_reply_fen"]))
        result = play_to_mate(
            graph,
            engine,
            board,
            random.Random(rng.randrange(2**32)),
            args.label,
            None,
            args.horizon,
            args.black_policy,
            trace=True,
            trace_max_plies=args.trace_max_plies,
            max_ticks=args.max_ticks,
            suggestion_limit=args.suggestion_limit,
            successor_affordance_layer_enabled=True,
            successor_role_license_enabled=True,
            explicit_role_provider_support_enabled=args.enable_explicit_role_provider_support,
            role_owned_score_normalization_enabled=args.enable_role_owned_score_normalization,
            successor_role_scoped_move_shape_enabled=True,
            stage7_king_tempo_enabled=args.enable_stage7_king_tempo,
            stage7_king_tempo_score=args.stage7_king_tempo_score,
            stage7_drive_repair_enabled=args.enable_stage7_drive_repair,
            stage7_drive_repair_score=args.stage7_drive_repair_score,
            stage7_post_king_tempo_enabled=args.enable_stage7_post_king_tempo,
            stage7_post_king_tempo_score=args.stage7_post_king_tempo_score,
            early_stop_stable_suggestions=args.early_stop_stable_suggestions,
            enable_diagnostic_caches=True,
        )
        first_event = _first_white_event(result)
        records.append({
            "state_id": family.get("state_id"),
            "family_id": family.get("family_id"),
            "post_reply_fen": family.get("post_reply_fen"),
            "source_selected_successor": family.get("selected_successor"),
            "source_conversion_result": family.get("conversion_result"),
            "result": result.get("result"),
            "plies": result.get("plies"),
            "first_white_event": _event_summary(first_event),
            "trace": result.get("trace"),
            "stagnation_summary": result.get("stagnation_summary"),
        })
    counts: dict[str, int] = {}
    for record in records:
        first = record.get("first_white_event") or {}
        key = (
            f"{first.get('selected_skill', 'unknown')}:"
            f"{'role_owned' if first.get('selected_by_role_owned_score_normalization') else 'raw'}:"
            f"{record.get('result')}"
        )
        counts[key] = counts.get(key, 0) + 1
    return {
        "schema_version": "stage7_role_owned_runtime_probe.v1",
        "causal_status": "sandbox_opt_in",
        "family_diagnosis_source": str(args.family_diagnosis),
        "topology": str(args.topology),
        "state_ids": list(_parse_csv(args.state_ids)),
        "config": {
            "horizon": args.horizon,
            "black_policy": args.black_policy,
            "explicit_role_provider_support_enabled": args.enable_explicit_role_provider_support,
            "role_owned_score_normalization_enabled": args.enable_role_owned_score_normalization,
            "stage7_king_tempo_enabled": args.enable_stage7_king_tempo,
            "stage7_king_tempo_score": args.stage7_king_tempo_score,
            "stage7_drive_repair_enabled": args.enable_stage7_drive_repair,
            "stage7_drive_repair_score": args.stage7_drive_repair_score,
            "stage7_post_king_tempo_enabled": args.enable_stage7_post_king_tempo,
            "stage7_post_king_tempo_score": args.stage7_post_king_tempo_score,
            "max_ticks": args.max_ticks,
            "suggestion_limit": args.suggestion_limit,
        },
        "record_count": len(records),
        "choice_result_counts": counts,
        "records": records,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Stage 7 role-owned runtime arbitration")
    parser.add_argument("--family-diagnosis", type=Path, required=True)
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--state-ids", required=True)
    parser.add_argument("--label", default="box_shrink")
    parser.add_argument("--horizon", type=int, default=80)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--black-policy", choices=["random", "adversarial"], default="adversarial")
    parser.add_argument("--max-ticks", type=int, default=40)
    parser.add_argument("--suggestion-limit", type=int, default=5)
    parser.add_argument("--early-stop-stable-suggestions", type=int, default=2)
    parser.add_argument("--trace-max-plies", type=int, default=12)
    parser.add_argument("--enable-explicit-role-provider-support", action="store_true")
    parser.add_argument("--enable-role-owned-score-normalization", action="store_true")
    parser.add_argument("--enable-stage7-king-tempo", action="store_true")
    parser.add_argument("--stage7-king-tempo-score", type=float, default=25.0)
    parser.add_argument("--enable-stage7-drive-repair", action="store_true")
    parser.add_argument("--stage7-drive-repair-score", type=float, default=28.0)
    parser.add_argument("--enable-stage7-post-king-tempo", action="store_true")
    parser.add_argument("--stage7-post-king-tempo-score", type=float, default=30.0)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = run_probe(args)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if not args.no_json_stdout:
        print(json.dumps({
            "record_count": payload["record_count"],
            "choice_result_counts": payload["choice_result_counts"],
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
