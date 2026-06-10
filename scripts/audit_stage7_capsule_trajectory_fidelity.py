#!/usr/bin/env python3
"""Audit trajectory fidelity for the Stage 7 learnable Plan Capsule provider.

This is non-causal analysis. It compares the sandbox provider's teacher-forced
choices against the offline DTM trajectory seed, then classifies existing
closed-loop replay artifacts. It does not use DTM/tablebase at runtime and does
not mutate topology.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any

import chess

import test_krk_landmark_progress as diag


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return payload


def _training_steps(seed: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for trajectory_index, trajectory in enumerate(seed.get("trajectories") or []):
        if not isinstance(trajectory, dict):
            continue
        for step_index, step in enumerate(trajectory.get("white_training_steps") or []):
            if not isinstance(step, dict) or not step.get("fen"):
                continue
            labels = [item for item in step.get("legal_move_labels") or [] if isinstance(item, dict)]
            label_by_move = {str(item.get("move")): item for item in labels if item.get("move")}
            positive_moves = sorted(
                str(item.get("move"))
                for item in labels
                if item.get("move") and int(item.get("label", 0) or 0) == 1
            )
            optimal_moves = sorted(
                str(item.get("move"))
                for item in labels
                if item.get("move") and str(item.get("target_class") or "") == "optimal_dtm_move"
            )
            rows.append({
                "trajectory_index": trajectory_index,
                "step_index": step_index,
                "fen": str(step["fen"]),
                "teacher_move": str(step.get("move") or ""),
                "teacher_child_dtm": step.get("child_dtm"),
                "positive_moves": positive_moves,
                "optimal_moves": optimal_moves or positive_moves,
                "label_by_move": label_by_move,
            })
    return rows


def _ranked_unique_moves(suggestions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for suggestion in suggestions:
        move = str(suggestion.get("move") or "")
        if not move:
            continue
        current = best.get(move)
        score = float(suggestion.get("score", 0.0) or 0.0)
        if current is None or score > float(current.get("score", 0.0) or 0.0):
            best[move] = suggestion
    return sorted(best.values(), key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)


def _move_rank(ranked: list[dict[str, Any]], moves: set[str]) -> int | None:
    for idx, item in enumerate(ranked, start=1):
        if str(item.get("move") or "") in moves:
            return idx
    return None


def _score_for_moves(ranked: list[dict[str, Any]], moves: set[str]) -> float | None:
    for item in ranked:
        if str(item.get("move") or "") in moves:
            return float(item.get("score", 0.0) or 0.0)
    return None


def _term_payload(label: dict[str, Any]) -> dict[str, Any]:
    return {
        "move_shape_terms": list(label.get("move_shape_terms") or []),
        "post_move_terms": list(label.get("post_move_terms") or []),
        "worst_reply_terms": list(label.get("worst_reply_terms") or []),
        "safety_terms": list(label.get("safety_terms") or []),
        "target_class": label.get("target_class"),
        "label": label.get("label"),
        "child_dtm": label.get("child_dtm"),
    }


def _teacher_forced_records(
    *,
    topology_path: Path,
    steps: list[dict[str, Any]],
    learned_bonus: float,
    max_ticks: int,
    top_k: int,
) -> list[dict[str, Any]]:
    graph = diag.build_graph_from_topology(topology_path)
    engine = diag.ReConEngine(graph)
    records: list[dict[str, Any]] = []
    for row in steps:
        board = chess.Board(row["fen"])
        state = diag._stage7_plan_capsule_default_state(ttl=4)
        move_details = diag.choose_move_details(
            graph,
            engine,
            board,
            max_ticks=max_ticks,
            stage_filter=None,
            suggestion_limit=128,
            stage7_learned_post_box_continuation_enabled=True,
            stage7_learned_post_box_continuation_bonus=learned_bonus,
            plan_capsule_sandbox_enabled=True,
            stage7_plan_capsule_enabled=True,
            stage7_plan_capsule_ttl=4,
            stage7_plan_capsule_support_bonus=learned_bonus,
            stage7_plan_capsule_owned_arbitration_enabled=True,
            stage7_plan_capsule_state=state,
            active_landmark_label="box_shrink",
            stage7_post_box_post_reply_context=True,
            early_stop_stable_suggestions=2,
            enable_diagnostic_caches=True,
        )
        suggestions = _ranked_unique_moves(list(move_details.get("suggestions") or []))
        selected = move_details.get("selected_suggestion") or {}
        selected_move = str(selected.get("move") or move_details.get("move") or "")
        teacher_move = row["teacher_move"]
        positive_moves = set(row["positive_moves"])
        optimal_moves = set(row["optimal_moves"])
        teacher_label = row["label_by_move"].get(selected_move, {})
        teacher_move_score = _score_for_moves(suggestions, {teacher_move})
        positive_move_score = _score_for_moves(suggestions, positive_moves)
        optimal_move_score = _score_for_moves(suggestions, optimal_moves)
        selected_score = float(selected.get("score", 0.0) or 0.0) if selected else None
        records.append({
            "trajectory_index": row["trajectory_index"],
            "step_index": row["step_index"],
            "fen": row["fen"],
            "teacher_move": teacher_move,
            "teacher_child_dtm": row.get("teacher_child_dtm"),
            "positive_moves": sorted(positive_moves),
            "optimal_moves": sorted(optimal_moves),
            "selected_move": selected_move,
            "selected_score": selected_score,
            "selected_skill": selected.get("skill_id"),
            "selected_target_class": teacher_label.get("target_class"),
            "selected_child_dtm": teacher_label.get("child_dtm"),
            "selected_label": teacher_label.get("label"),
            "teacher_move_rank": _move_rank(suggestions, {teacher_move}),
            "positive_move_rank": _move_rank(suggestions, positive_moves),
            "optimal_move_rank": _move_rank(suggestions, optimal_moves),
            "teacher_move_score": teacher_move_score,
            "positive_move_score": positive_move_score,
            "optimal_move_score": optimal_move_score,
            "selected_minus_teacher_score": (
                selected_score - teacher_move_score if selected_score is not None and teacher_move_score is not None else None
            ),
            "selected_minus_positive_score": (
                selected_score - positive_move_score if selected_score is not None and positive_move_score is not None else None
            ),
            "selected_minus_optimal_score": (
                selected_score - optimal_move_score if selected_score is not None and optimal_move_score is not None else None
            ),
            "selected_visible_terms": _term_payload(teacher_label),
            "teacher_visible_terms": _term_payload(row["label_by_move"].get(teacher_move, {})),
            "teacher_in_top_k": teacher_move in {str(item.get("move")) for item in suggestions[:top_k]},
            "positive_in_top_k": bool(positive_moves & {str(item.get("move")) for item in suggestions[:top_k]}),
            "optimal_in_top_k": bool(optimal_moves & {str(item.get("move")) for item in suggestions[:top_k]}),
            "top_moves": [
                {
                    "move": item.get("move"),
                    "score": item.get("score"),
                    "skill_id": item.get("skill_id"),
                    "target_class": row["label_by_move"].get(str(item.get("move") or ""), {}).get("target_class"),
                    "label": row["label_by_move"].get(str(item.get("move") or ""), {}).get("label"),
                    "child_dtm": row["label_by_move"].get(str(item.get("move") or ""), {}).get("child_dtm"),
                }
                for item in suggestions[:top_k]
            ],
            "plan_capsule_supported_suggestion_count": int(
                move_details.get("plan_capsule_supported_suggestion_count", 0) or 0
            ),
            "selected_by_stage7_plan_capsule_owned_arbitration": bool(
                move_details.get("selected_by_stage7_plan_capsule_owned_arbitration", False)
            ),
        })
    return records


def _first_miss(records: list[dict[str, Any]], key: str) -> dict[str, Any] | None:
    for record in records:
        if not record.get(key):
            return {
                "trajectory_index": record["trajectory_index"],
                "step_index": record["step_index"],
                "fen": record["fen"],
                "selected_move": record["selected_move"],
                "teacher_move": record["teacher_move"],
                "positive_moves": record["positive_moves"],
                "optimal_moves": record["optimal_moves"],
            }
    return None


def _accuracy(records: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(records)
    selected_teacher = sum(1 for r in records if r.get("selected_move") == r.get("teacher_move"))
    selected_positive = sum(1 for r in records if r.get("selected_move") in set(r.get("positive_moves") or []))
    selected_optimal = sum(1 for r in records if r.get("selected_move") in set(r.get("optimal_moves") or []))
    teacher_top3 = sum(1 for r in records if r.get("teacher_move_rank") and int(r["teacher_move_rank"]) <= 3)
    positive_top3 = sum(1 for r in records if r.get("positive_move_rank") and int(r["positive_move_rank"]) <= 3)
    optimal_top3 = sum(1 for r in records if r.get("optimal_move_rank") and int(r["optimal_move_rank"]) <= 3)
    positive_ranks = [int(r["positive_move_rank"]) for r in records if r.get("positive_move_rank")]
    optimal_ranks = [int(r["optimal_move_rank"]) for r in records if r.get("optimal_move_rank")]
    selected_non_positive = sum(
        1 for r in records if r.get("selected_move") not in set(r.get("positive_moves") or [])
    )
    return {
        "total_teacher_forced_states": total,
        "teacher_move_top1_rate": selected_teacher / total if total else 0.0,
        "dtm_positive_top1_rate": selected_positive / total if total else 0.0,
        "dtm_optimal_top1_rate": selected_optimal / total if total else 0.0,
        "teacher_move_top3_rate": teacher_top3 / total if total else 0.0,
        "dtm_positive_top3_rate": positive_top3 / total if total else 0.0,
        "dtm_optimal_top3_rate": optimal_top3 / total if total else 0.0,
        "positive_rank_mean": mean(positive_ranks) if positive_ranks else None,
        "optimal_rank_mean": mean(optimal_ranks) if optimal_ranks else None,
        "positive_rank_distribution": dict(Counter(str(r) for r in positive_ranks)),
        "optimal_rank_distribution": dict(Counter(str(r) for r in optimal_ranks)),
        "selected_non_positive_count": selected_non_positive,
        "selected_non_positive_rate": selected_non_positive / total if total else 0.0,
        "first_teacher_miss": _first_miss(records, "teacher_in_top_k"),
        "first_positive_miss": _first_miss(records, "positive_in_top_k"),
        "first_optimal_miss": _first_miss(records, "optimal_in_top_k"),
    }


def _closed_loop_records(
    *,
    replay_payloads: list[dict[str, Any]],
    step_by_fen: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for payload in replay_payloads:
        source = payload.get("topology") or payload.get("schema_version")
        for replay in payload.get("records") or []:
            if not isinstance(replay, dict):
                continue
            fen = str(replay.get("start_fen") or "")
            step = step_by_fen.get(fen, {})
            selected_move = str(replay.get("selected_move") or "")
            label = (step.get("label_by_move") or {}).get(selected_move, {})
            positive_moves = set(step.get("positive_moves") or [])
            optimal_moves = set(step.get("optimal_moves") or [])
            trace = replay.get("trace") if isinstance(replay.get("trace"), list) else []
            first_divergence = None
            for event in trace:
                if not isinstance(event, dict) or event.get("turn") != "white":
                    continue
                event_fen = str(event.get("fen") or "")
                event_step = step_by_fen.get(event_fen)
                if not event_step:
                    continue
                event_move = str(event.get("move") or "")
                if event_move not in set(event_step.get("positive_moves") or []):
                    first_divergence = {
                        "ply": event.get("ply"),
                        "fen": event_fen,
                        "selected_move": event_move,
                        "positive_moves": event_step.get("positive_moves"),
                        "optimal_moves": event_step.get("optimal_moves"),
                    }
                    break
            records.append({
                "source": source,
                "start_fen": fen,
                "result": replay.get("result"),
                "plies": replay.get("plies"),
                "selected_skill": replay.get("selected_skill"),
                "selected_move": selected_move,
                "selected_target_class": label.get("target_class"),
                "selected_label": label.get("label"),
                "selected_child_dtm": label.get("child_dtm"),
                "selected_is_dtm_positive": selected_move in positive_moves,
                "selected_is_dtm_optimal": selected_move in optimal_moves,
                "teacher_move": step.get("teacher_move"),
                "positive_moves": sorted(positive_moves),
                "optimal_moves": sorted(optimal_moves),
                "first_divergence": first_divergence,
                "plan_owned_record": bool((replay.get("stage7_plan_capsule_state") or {}).get("selected_owned_provider")),
                "plan_progress_terms": list((replay.get("stage7_plan_capsule_state") or {}).get("progress_terms_confirmed") or []),
            })
    return records


def _diagnosis_by_family(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result = []
    for record in records:
        if not record.get("selected_is_dtm_positive"):
            diagnosis = "teacher_fidelity_ranking_gap"
        elif record.get("result") != "mate":
            diagnosis = "closed_loop_compounding_or_followup_policy_gap"
        else:
            diagnosis = "closed_loop_success"
        result.append({
            "start_fen": record.get("start_fen"),
            "selected_move": record.get("selected_move"),
            "selected_target_class": record.get("selected_target_class"),
            "result": record.get("result"),
            "diagnosis": diagnosis,
        })
    return result


def _top_level_diagnosis(
    *,
    accuracy: dict[str, Any],
    closed_loop: list[dict[str, Any]],
) -> tuple[str, str]:
    closed_loop_failures = [item for item in closed_loop if item.get("result") != "mate"]
    closed_loop_ranking_gaps = [item for item in closed_loop_failures if not item.get("selected_is_dtm_positive")]
    if float(accuracy.get("dtm_positive_top1_rate", 0.0) or 0.0) < 0.5 or closed_loop_ranking_gaps:
        return (
            "trajectory_ranking_and_closed_loop_gap",
            "expand_offline_dtm_seed_and_train_ranked_imitation_before_more_runtime_repair",
        )
    if float(accuracy.get("dtm_positive_top3_rate", 0.0) or 0.0) < 0.8:
        return (
            "model_expression_gap",
            "improve_provider_representation_or_ranking_objective_before_more_runtime_repair",
        )
    if closed_loop_failures:
        return (
            "closed_loop_compounding_error",
            "offline_dagger_style_seed_expansion_from_failed_rollouts",
        )
    return (
        "trajectory_fidelity_sufficient_for_targeted_families",
        "run_small_stage7_h40_smoke_before_guardrails",
    )


def audit(
    *,
    topology_path: Path,
    trajectory_seed_path: Path,
    replay_paths: list[Path],
    learned_bonus: float = 0.01,
    max_ticks: int = 40,
    top_k: int = 3,
) -> dict[str, Any]:
    seed = _load_json(trajectory_seed_path)
    steps = _training_steps(seed)
    teacher_forced = _teacher_forced_records(
        topology_path=topology_path,
        steps=steps,
        learned_bonus=learned_bonus,
        max_ticks=max_ticks,
        top_k=max(3, top_k),
    )
    step_by_fen = {step["fen"]: step for step in steps}
    replay_payloads = [_load_json(path) for path in replay_paths if path.exists()]
    closed_loop = _closed_loop_records(replay_payloads=replay_payloads, step_by_fen=step_by_fen)
    accuracy = _accuracy(teacher_forced)
    top_diagnosis, next_action = _top_level_diagnosis(accuracy=accuracy, closed_loop=closed_loop)
    return {
        "schema_version": "stage7_capsule_trajectory_fidelity_audit.v1",
        "causal_status": "non_causal",
        "runtime_behavior_changed": False,
        "topology": str(topology_path),
        "trajectory_seed": str(trajectory_seed_path),
        "replay_sources": [str(path) for path in replay_paths],
        "learned_bonus": float(learned_bonus),
        "teacher_forced_accuracy": accuracy,
        "teacher_forced_records": teacher_forced,
        "closed_loop_records": closed_loop,
        "diagnosis_by_family": _diagnosis_by_family(closed_loop),
        "top_level_diagnosis": top_diagnosis,
        "recommended_next_action": next_action,
        "candidate_status_update": {
            "candidate_id": "cand.krk.box_shrink.post_box_continuation_capsule.v1",
            "status": "selected_but_closed_loop_fails",
            "diagnosis": "trajectory_target_or_model_expression_gap",
            "next_action": "trajectory_fidelity_audit_complete",
            "causal_status": "non_causal",
            "credit": 0.0,
        },
        "hard_constraints": [
            "do_not_train_stage8",
            "do_not_promote_stage7",
            "do_not_use_dtm_or_tablebase_at_runtime",
            "do_not_add_hidden_python_routing",
            "do_not_mutate_topology_during_gameplay",
            "keep_plan_capsule_sandbox_default_off",
        ],
    }


def _write_markdown(payload: dict[str, Any], path: Path) -> None:
    acc = payload["teacher_forced_accuracy"]
    lines = [
        "# Stage 7 Capsule Trajectory Fidelity Audit",
        "",
        "This is non-causal analysis. DTM labels are used only as offline supervision evidence.",
        "",
        "## Summary",
        "",
        f"- teacher states: `{acc['total_teacher_forced_states']}`",
        f"- teacher top-1: `{acc['teacher_move_top1_rate']:.3f}`",
        f"- DTM-positive top-1: `{acc['dtm_positive_top1_rate']:.3f}`",
        f"- DTM-positive top-3: `{acc['dtm_positive_top3_rate']:.3f}`",
        f"- DTM-optimal top-1: `{acc['dtm_optimal_top1_rate']:.3f}`",
        f"- DTM-optimal top-3: `{acc['dtm_optimal_top3_rate']:.3f}`",
        f"- diagnosis: `{payload['top_level_diagnosis']}`",
        f"- next_action: `{payload['recommended_next_action']}`",
        "",
        "## Closed-Loop Families",
        "",
    ]
    for item in payload["diagnosis_by_family"]:
        lines.append(
            f"- `{item['start_fen']}` selected `{item['selected_move']}` "
            f"({item.get('selected_target_class')}) -> `{item['result']}`: `{item['diagnosis']}`"
        )
    lines.extend(["", "## First Misses", ""])
    for key in ("first_teacher_miss", "first_positive_miss", "first_optimal_miss"):
        lines.append(f"- {key}: `{acc.get(key)}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Stage 7 capsule trajectory fidelity")
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--trajectory-seed", type=Path, required=True)
    parser.add_argument("--closed-loop-replay", type=Path, action="append", default=[])
    parser.add_argument("--learned-bonus", type=float, default=0.01)
    parser.add_argument("--max-ticks", type=int, default=40)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--no-json-stdout", action="store_true")
    args = parser.parse_args()

    payload = audit(
        topology_path=args.topology,
        trajectory_seed_path=args.trajectory_seed,
        replay_paths=list(args.closed_loop_replay),
        learned_bonus=args.learned_bonus,
        max_ticks=args.max_ticks,
        top_k=args.top_k,
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    _write_markdown(payload, args.markdown_output)
    if not args.no_json_stdout:
        print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
