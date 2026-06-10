#!/usr/bin/env python3
"""Targeted replay for the Stage 7 learnable Plan Capsule provider.

This starts from offline DTM-seeded post-box/post-reply states and runs the
compiled graph with the sandbox provider explicitly enabled. It is a diagnostic
Phase 1 artifact, not promotion and not runtime tablebase use.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter
from pathlib import Path
from typing import Any

import chess

import test_krk_landmark_progress as diag


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _seed_start_fens(seed: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for idx, trajectory in enumerate(seed.get("trajectories") or []):
        if not isinstance(trajectory, dict):
            continue
        steps = [step for step in trajectory.get("white_training_steps") or [] if isinstance(step, dict)]
        if not steps:
            continue
        fen = str(steps[0].get("fen") or "")
        if not fen or fen in seen:
            continue
        seen.add(fen)
        rows.append({
            "trajectory_index": idx,
            "fen": fen,
            "dtm_step_count": len(steps),
            "first_dtm_move": steps[0].get("move"),
            "first_child_dtm": steps[0].get("child_dtm"),
        })
    return rows


def replay(
    *,
    topology_path: Path,
    trajectory_seed_path: Path,
    max_plies: int = 40,
    max_ticks: int = 40,
    suggestion_limit: int = 5,
    learned_bonus: float = 0.01,
    seed: int = 7,
    trace: bool = True,
) -> dict[str, Any]:
    trajectory_seed = _load_json(trajectory_seed_path)
    targets = _seed_start_fens(trajectory_seed)
    graph = diag.build_graph_from_topology(topology_path)
    engine = diag.ReConEngine(graph)
    rng = random.Random(seed)

    records: list[dict[str, Any]] = []
    for row in targets:
        board = chess.Board(row["fen"])
        result = diag.play_to_mate(
            graph,
            engine,
            board,
            rng,
            label="box_shrink",
            stage_filter=None,
            max_plies=max_plies,
            black_policy="adversarial",
            trace=trace,
            trace_max_plies=max_plies,
            max_ticks=max_ticks,
            suggestion_limit=suggestion_limit,
            stage7_learned_post_box_continuation_enabled=True,
            stage7_learned_post_box_continuation_bonus=learned_bonus,
            plan_capsule_sandbox_enabled=True,
            stage7_plan_capsule_enabled=True,
            stage7_plan_capsule_ttl=4,
            stage7_plan_capsule_support_bonus=learned_bonus,
            stage7_plan_capsule_owned_arbitration_enabled=True,
            early_stop_stable_suggestions=2,
            enable_diagnostic_caches=True,
            initial_white_moves=1,
        )
        first_successor = result.get("first_successor") or {}
        first_engine = first_successor.get("engine") if isinstance(first_successor, dict) else {}
        if not isinstance(first_engine, dict):
            first_engine = {}
        selected_suggestion = first_engine.get("selected_suggestion")
        if not isinstance(selected_suggestion, dict):
            selected_suggestion = {}
        records.append({
            "trajectory_index": row["trajectory_index"],
            "start_fen": row["fen"],
            "dtm_step_count": row["dtm_step_count"],
            "first_dtm_move": row.get("first_dtm_move"),
            "first_child_dtm": row.get("first_child_dtm"),
            "result": result.get("result"),
            "plies": result.get("plies"),
            "first_successor": first_successor,
            "selected_skill": selected_suggestion.get("skill_id")
            or first_successor.get("selected_skill")
            or first_successor.get("successor_selected_skill"),
            "selected_move": selected_suggestion.get("move") or first_successor.get("move"),
            "selected_suggestion": selected_suggestion,
            "plan_capsule_supported_suggestion_count": int(
                first_engine.get("plan_capsule_supported_suggestion_count", 0) or 0
            ),
            "selected_by_stage7_plan_capsule_owned_arbitration": bool(
                first_engine.get("selected_by_stage7_plan_capsule_owned_arbitration", False)
            ),
            "stage7_plan_capsule_state": result.get("stage7_plan_capsule_state"),
            "final_mate_in_one_available": result.get("final_mate_in_one_available"),
            "stagnation_summary": result.get("stagnation_summary"),
            "trace": result.get("trace") if trace else None,
        })

    result_counts = Counter(str(record.get("result")) for record in records)
    selected_counts = Counter(str(record.get("selected_skill")) for record in records)
    owned_count = sum(
        1
        for record in records
        if (record.get("stage7_plan_capsule_state") or {}).get("selected_owned_provider")
    )
    provider_selected_count = selected_counts.get("krk.post_box_shrink_continuation", 0)
    if result_counts.get("mate", 0) == len(records) and records:
        promotion_status = "phase1_targeted_replay_improved"
        diagnosis = "learnable_capsule_provider_converts_seeded_families"
        next_action = "run_stage7_smoke_10_h40"
    elif provider_selected_count and owned_count:
        promotion_status = "phase1_targeted_replay_still_failing"
        diagnosis = "provider_selected_by_visible_plan_capsule_but_multistep_policy_still_fails"
        next_action = "refine_candidate_local_training_protocol_or_trajectory_targets"
    else:
        promotion_status = "phase1_targeted_replay_entry_or_arbitration_gap"
        diagnosis = "plan_capsule_did_not_select_owned_provider"
        next_action = "fix_default_off_safe_plan_entry_or_owned_arbitration_before_training"
    return {
        "schema_version": "stage7_learnable_capsule_provider_replay.v1",
        "causal_status": "sandbox_opt_in_diagnostic",
        "runtime_tablebase_lookup": False,
        "topology": str(topology_path),
        "trajectory_seed": str(trajectory_seed_path),
        "target_state_count": len(targets),
        "max_plies": int(max_plies),
        "max_ticks": int(max_ticks),
        "learned_bonus": float(learned_bonus),
        "plan_capsule_enabled": True,
        "plan_capsule_ttl": 4,
        "plan_capsule_support_bonus": float(learned_bonus),
        "plan_capsule_owned_arbitration_enabled": True,
        "result_counts": dict(result_counts),
        "selected_skill_counts": dict(selected_counts),
        "plan_owned_record_count": int(owned_count),
        "records": records,
        "candidate_status_update": {
            "candidate_id": "cand.krk.box_shrink.post_box_learnable_capsule_provider.v1",
            "causal_status": "non_causal",
            "credit": 0.0,
            "promotion_status": promotion_status,
            "diagnosis": diagnosis,
            "next_action": next_action,
        },
        "hard_constraints": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_use_dtm_or_tablebase_at_runtime",
            "do_not_mutate_topology_during_gameplay",
            "sandbox_provider_default_off_outside_this_probe",
        ],
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    lines = [
        "# Stage 7 Learnable Capsule Phase 1 Replay",
        "",
        f"- target_state_count: `{payload['target_state_count']}`",
        f"- max_plies: `{payload['max_plies']}`",
        f"- learned_bonus: `{payload['learned_bonus']}`",
        f"- result_counts: `{payload['result_counts']}`",
        f"- selected_skill_counts: `{payload['selected_skill_counts']}`",
        f"- plan_owned_record_count: `{payload['plan_owned_record_count']}`",
        f"- candidate_status: `{payload['candidate_status_update']['promotion_status']}`",
        f"- diagnosis: `{payload['candidate_status_update']['diagnosis']}`",
        "",
        "This is an opt-in diagnostic replay. DTM trajectory data provides the start states only; no DTM/tablebase lookup is used at runtime.",
        "",
        "## Records",
        "",
    ]
    for record in payload["records"]:
        lines.append(
            f"- `{record['start_fen']}` -> result `{record['result']}` in "
            f"`{record['plies']}` plies, selected `{record.get('selected_skill')}` "
            f"move `{record.get('selected_move')}`, plan-supported "
            f"`{record.get('plan_capsule_supported_suggestion_count')}`"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay Stage 7 learnable capsule provider on DTM-seeded states")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--trajectory-seed", type=Path, required=True)
    parser.add_argument("--max-plies", type=int, default=40)
    parser.add_argument("--max-ticks", type=int, default=40)
    parser.add_argument("--suggestion-limit", type=int, default=5)
    parser.add_argument("--learned-bonus", type=float, default=0.01)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = replay(
        topology_path=args.topology,
        trajectory_seed_path=args.trajectory_seed,
        max_plies=args.max_plies,
        max_ticks=args.max_ticks,
        suggestion_limit=args.suggestion_limit,
        learned_bonus=args.learned_bonus,
        seed=args.seed,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_markdown(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
