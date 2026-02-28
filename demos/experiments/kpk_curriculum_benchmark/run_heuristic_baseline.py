#!/usr/bin/env python3
from __future__ import annotations

import argparse
import platform
import random
import sys
from pathlib import Path
from typing import Any, Dict, List

import chess

from benchmark_common import (
    DEFAULT_STAGES,
    REPO_ROOT,
    ensure_eval_fens,
    load_fens,
    parse_stage_list,
    timestamp_utc,
    write_json,
)
from kpk_stage_env import KPKStageEnv
from recon_lite_chess.sensors import structure as struct_sensors
from recon_lite_chess.sensors import tactics as tactic_sensors


def _promotion_square(pawn_sq: int, color: chess.Color) -> int:
    direction = 8 if color == chess.WHITE else -8
    return pawn_sq + direction


def choose_move_heuristic(board: chess.Board, legal_moves: List[chess.Move], rng: random.Random) -> chess.Move:
    # 1) Immediate promotion is always best.
    for mv in legal_moves:
        if mv.promotion:
            return mv

    summary = struct_sensors.summarize_kpk_material(board)
    is_kpk = bool(summary.get("is_kpk"))
    attacker_color = summary.get("attacker_color")
    pawn_sq = summary.get("pawn_square")
    attacker_king = summary.get("attacker_king")
    defender_king = summary.get("defender_king")

    # 2) Safe pawn push.
    if is_kpk and attacker_color == board.turn and pawn_sq is not None:
        push_sq = _promotion_square(pawn_sq, attacker_color)
        push = chess.Move(pawn_sq, push_sq)
        if push in legal_moves and tactic_sensors.can_push_pawn_safely(board, attacker_color=attacker_color):
            return push

    # 3) King move scoring.
    king_moves = []
    for mv in legal_moves:
        piece = board.piece_at(mv.from_square)
        if piece and piece.piece_type == chess.KING and piece.color == board.turn:
            king_moves.append(mv)

    if king_moves:
        scored = []
        for mv in king_moves:
            trial = board.copy(stack=False)
            trial.push(mv)
            score = 0.0

            trial_summary = struct_sensors.summarize_kpk_material(trial)
            trial_attacker_king = trial_summary.get("attacker_king")
            trial_defender_king = trial_summary.get("defender_king")

            if pawn_sq is not None and trial_attacker_king is not None:
                # Escort/support the pawn.
                if chess.square_distance(trial_attacker_king, pawn_sq) <= 1:
                    score += 1.0
                pf = chess.square_file(pawn_sq)
                pr = chess.square_rank(pawn_sq)
                kf = chess.square_file(trial_attacker_king)
                kr = chess.square_rank(trial_attacker_king)
                if abs(kf - pf) <= 1 and kr >= pr:
                    score += 0.8

                # Push black king away from promotion square.
                if defender_king is not None and trial_defender_king is not None and attacker_color is not None:
                    promo_sq = _promotion_square(pawn_sq, attacker_color)
                    old_dist = chess.square_distance(defender_king, promo_sq)
                    new_dist = chess.square_distance(trial_defender_king, promo_sq)
                    if new_dist > old_dist:
                        score += 0.4

            if trial.is_check():
                score += 0.25
            if attacker_color is not None and tactic_sensors.has_opposition_alignment(
                trial, attacker_color=attacker_color
            ):
                score += 0.3

            scored.append((score, mv))

        scored.sort(key=lambda item: item[0], reverse=True)
        best_score = scored[0][0]
        best_moves = [mv for score, mv in scored if score == best_score]
        return rng.choice(best_moves)

    # 4) Fallback.
    return rng.choice(legal_moves)


def evaluate_stage(stage: int, fens: List[str], max_moves: int, seed: int) -> Dict[str, Any]:
    env = KPKStageEnv(stage=stage, max_moves=max_moves)
    rng = random.Random(seed + stage * 9973)

    outcomes = {
        "checkmate": 0,
        "promotion": 0,
        "loss": 0,
        "draw": 0,
        "timeout": 0,
        "unknown": 0,
    }
    total_moves = 0

    for fen in fens:
        _obs, _info = env.reset(options={"fen": fen})
        done = False
        info: Dict[str, Any] = {}
        while not done:
            legal = list(env.legal_moves_list)
            if not legal:
                action = 0
            else:
                move = choose_move_heuristic(env.board, legal, rng)  # type: ignore[arg-type]
                try:
                    action = legal.index(move)
                except ValueError:
                    action = 0
            _obs, _reward, terminated, truncated, info = env.step(action)
            done = bool(terminated or truncated)

        outcome = str(info.get("outcome", "unknown"))
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
        total_moves += int(info.get("move_count", 0))

    episodes = len(fens)
    success = outcomes["checkmate"] + outcomes["promotion"]
    return {
        "stage": stage,
        "episodes": episodes,
        "success_rate": success / episodes if episodes else 0.0,
        "win_rate": outcomes["checkmate"] / episodes if episodes else 0.0,
        "promotion_rate": outcomes["promotion"] / episodes if episodes else 0.0,
        "avg_moves": total_moves / episodes if episodes else 0.0,
        "outcomes": outcomes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Heuristic KPK baseline evaluation")
    parser.add_argument(
        "--stages",
        type=str,
        default=",".join(str(s) for s in DEFAULT_STAGES),
        help="Comma-separated stage list",
    )
    parser.add_argument("--eval-per-stage", type=int, default=100, help="Eval episodes per stage")
    parser.add_argument("--max-moves", type=int, default=100, help="Max plies per episode")
    parser.add_argument("--seed", type=int, default=2026, help="Base random seed")
    parser.add_argument(
        "--eval-dir",
        type=Path,
        default=Path("demos/experiments/kpk_curriculum_benchmark/data/eval_fens"),
        help="Eval FEN directory",
    )
    parser.add_argument("--regen-eval-fens", action="store_true", help="Regenerate eval FEN sets")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Run output directory. Defaults to _private/heuristic/<timestamp>",
    )
    args = parser.parse_args()

    stages = parse_stage_list(args.stages)
    if args.output_dir is None:
        run_dir = (
            REPO_ROOT
            / "demos/experiments/kpk_curriculum_benchmark/_private/heuristic"
            / timestamp_utc()
        )
    else:
        run_dir = args.output_dir
    run_dir.mkdir(parents=True, exist_ok=True)

    ensure_eval_fens(
        eval_dir=args.eval_dir,
        stages=stages,
        per_stage=args.eval_per_stage,
        seed=args.seed,
        force=args.regen_eval_fens,
    )

    rows: List[Dict[str, Any]] = []
    for stage in stages:
        fens = load_fens(args.eval_dir / f"stage_{stage:02d}.fens")[: args.eval_per_stage]
        row = evaluate_stage(stage=stage, fens=fens, max_moves=args.max_moves, seed=args.seed)
        rows.append(row)
        write_json(run_dir / f"stage_{stage:02d}_results.json", row)
        print(
            f"stage {stage:02d}: success={row['success_rate']:.3f} "
            f"(win={row['win_rate']:.3f}, promo={row['promotion_rate']:.3f})"
        )

    payload = {
        "run_type": "heuristic_baseline",
        "created_utc": timestamp_utc(),
        "repo_root": str(REPO_ROOT),
        "python": sys.version,
        "platform": platform.platform(),
        "config": {
            "stages": stages,
            "eval_per_stage": args.eval_per_stage,
            "max_moves": args.max_moves,
            "seed": args.seed,
            "eval_dir": str(args.eval_dir),
        },
        "stage_results": rows,
    }
    write_json(run_dir / "heuristic_results.json", payload)
    print(f"Saved: {run_dir / 'heuristic_results.json'}")


if __name__ == "__main__":
    main()
