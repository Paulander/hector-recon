"""M8 multi-candidate growth trainer for KRK autogrowth."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

import chess

from .evaluate import (
    choose_black_reply,
    classify_terminal_outcome,
    _position_repetition_key,
)
from .features import validate_learner_record
from .positions import KRKPositionSet, generate_position_sets
from .sandbox import (
    _action_schema_matches,
    _after_condition_matches,
    _before_condition_matches,
    _learning_decision,
    _paired_delta,
    _sandbox_result,
    _safety_counts,
    evaluate_sandbox_arm,
)
from .evaluate import evaluate_arm


@dataclass(frozen=True)
class GrowthTrainingConfig:
    seed: int = 20260610
    train_count: int = 200
    heldout_weakness_count: int = 100
    heldout_broader_count: int = 100
    candidate_path: str = "reports/autogrowth/krk_autogrowth_m4_candidates.json"
    candidate_count: int = 8
    cycles: int = 4
    train_horizon: int = 40
    eval_horizon: int = 40
    activation_max_distance: float = 1.5
    eta_m3_initial: float = 0.08
    eta_m3_final: float = 0.03
    mature_experience: int = 8
    mature_min_mean_credit: float = 0.0
    prune_min_experience: int = 3
    prune_max_rook_losses: int = 1
    prune_max_stalemates: int = 0
    prune_min_fast_weight: float = -0.25


@dataclass
class CandidateLifecycle:
    candidate_key: str
    rank: int
    lifecycle_state: str = "young"
    experience_count: int = 0
    activation_count: int = 0
    action_count: int = 0
    changed_action_count: int = 0
    positive_credit_count: int = 0
    negative_credit_count: int = 0
    rook_loss_count: int = 0
    stalemate_count: int = 0
    illegal_count: int = 0
    fast_weight: float = 0.0
    credit_sum: float = 0.0

    @property
    def mean_credit(self) -> float:
        return 0.0 if self.experience_count == 0 else self.credit_sum / self.experience_count

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mean_credit"] = self.mean_credit
        return payload


@dataclass(frozen=True)
class GrowthTrainingResult:
    config: GrowthTrainingConfig
    positions: KRKPositionSet
    candidates: list[dict[str, Any]]
    lifecycle: dict[str, CandidateLifecycle]
    cycle_summaries: list[dict[str, Any]]
    heldout: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        validate_learner_record(self.candidates)
        lifecycle_payload = {
            key: state.to_dict()
            for key, state in sorted(self.lifecycle.items())
        }
        return {
            "schema_version": "krk_autogrowth_m8_training.v0",
            "config": asdict(self.config),
            "dataset": {
                "seed": self.positions.seed,
                "digest": self.positions.digest(),
                "train_count": len(self.positions.train),
                "heldout_count": len(self.positions.heldout),
                "heldout_weakness_count": len(self.positions.heldout_weakness),
                "heldout_broader_count": len(self.positions.heldout_broader),
            },
            "summary": _training_summary(lifecycle_payload, self.heldout),
            "candidates": self.candidates,
            "candidate_lifecycle": lifecycle_payload,
            "cycle_summaries": self.cycle_summaries,
            "heldout": self.heldout,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def load_candidate_pool(path: str | Path, *, candidate_count: int) -> list[dict[str, Any]]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    candidates = list(payload["candidates"])[: int(candidate_count)]
    if not candidates:
        raise ValueError("candidate artifact has no candidates")
    validate_learner_record(candidates)
    return candidates


def train_growth_candidates(
    *,
    config: GrowthTrainingConfig,
    positions: KRKPositionSet | None = None,
    candidates: list[dict[str, Any]] | None = None,
) -> GrowthTrainingResult:
    positions = positions or generate_position_sets(
        seed=config.seed,
        train_count=config.train_count,
        heldout_weakness_count=config.heldout_weakness_count,
        heldout_broader_count=config.heldout_broader_count,
    )
    candidates = candidates or load_candidate_pool(config.candidate_path, candidate_count=config.candidate_count)
    lifecycle = {
        candidate["candidate_key"]: CandidateLifecycle(
            candidate_key=candidate["candidate_key"],
            rank=int(candidate["rank"]),
        )
        for candidate in candidates
    }
    cycle_summaries: list[dict[str, Any]] = []

    for cycle in range(int(config.cycles)):
        eta = _annealed_eta(config, cycle)
        before_rook_losses = sum(state.rook_loss_count for state in lifecycle.values())
        before_updates = sum(state.experience_count for state in lifecycle.values())
        for fen in positions.train:
            _training_playout(
                fen,
                candidates=candidates,
                lifecycle=lifecycle,
                config=config,
                eta_m3=eta,
            )
        _update_lifecycle_states(lifecycle, config)
        cycle_summaries.append(
            {
                "cycle": cycle,
                "eta_m3": eta,
                "active_candidate_count": sum(1 for state in lifecycle.values() if state.lifecycle_state != "quarantined"),
                "mature_candidate_count": sum(1 for state in lifecycle.values() if state.lifecycle_state == "mature"),
                "quarantined_candidate_count": sum(1 for state in lifecycle.values() if state.lifecycle_state == "quarantined"),
                "m3_update_count": sum(state.experience_count for state in lifecycle.values()) - before_updates,
                "new_rook_loss_count": sum(state.rook_loss_count for state in lifecycle.values()) - before_rook_losses,
                "mean_fast_weight": _mean([state.fast_weight for state in lifecycle.values()]),
            }
        )

    heldout = _evaluate_trained_pool(
        positions=positions,
        candidates=candidates,
        lifecycle=lifecycle,
        config=config,
    )
    return GrowthTrainingResult(
        config=config,
        positions=positions,
        candidates=candidates,
        lifecycle=lifecycle,
        cycle_summaries=cycle_summaries,
        heldout=heldout,
    )


def _training_playout(
    fen: str,
    *,
    candidates: list[dict[str, Any]],
    lifecycle: dict[str, CandidateLifecycle],
    config: GrowthTrainingConfig,
    eta_m3: float,
) -> None:
    board = chess.Board(fen)
    pending_key: str | None = None

    for _ply in range(int(config.train_horizon)):
        terminal = classify_terminal_outcome(board)
        if terminal is not None:
            if pending_key is not None and terminal in {"rook_loss", "stalemate", "illegal_move"}:
                _apply_candidate_credit(
                    lifecycle[pending_key],
                    credit=-1.0,
                    eta_m3=eta_m3,
                    terminal=terminal,
                )
            return

        if board.turn == chess.BLACK:
            move = choose_black_reply(board)
            if move is None or move not in board.legal_moves:
                if pending_key is not None:
                    _apply_candidate_credit(
                        lifecycle[pending_key],
                        credit=-1.0,
                        eta_m3=eta_m3,
                        terminal="illegal_move",
                    )
                return
            board.push(move)
            continue

        decision = _choose_candidate_action(
            board,
            candidates=candidates,
            lifecycle=lifecycle,
            activation_max_distance=config.activation_max_distance,
        )
        if decision is None:
            return

        candidate = decision["candidate"]
        move = decision["move"]
        state = lifecycle[candidate["candidate_key"]]
        before = board.copy(stack=False)
        state.activation_count += int(decision["terminal_activated"])
        state.action_count += 1
        state.changed_action_count += 1
        board.push(move)
        pending_key = candidate["candidate_key"]

        if _after_condition_matches(before, board, candidate):
            _apply_candidate_credit(state, credit=0.2, eta_m3=eta_m3, terminal=None)
            pending_key = None
        else:
            _apply_candidate_credit(state, credit=-0.1, eta_m3=eta_m3, terminal=None)


def _choose_candidate_action(
    board: chess.Board,
    *,
    candidates: list[dict[str, Any]],
    lifecycle: dict[str, CandidateLifecycle],
    activation_max_distance: float,
) -> dict[str, Any] | None:
    options: list[tuple[float, str, dict[str, Any], chess.Move]] = []
    for candidate in candidates:
        state = lifecycle[candidate["candidate_key"]]
        if state.lifecycle_state == "quarantined":
            continue
        if not _before_condition_matches(board, candidate, activation_max_distance):
            continue
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            if _action_schema_matches(board, move, candidate["action_schema"]):
                score = state.fast_weight + 0.01 * max(0, 100 - state.experience_count)
                options.append((score, candidate["candidate_key"], candidate, move))
    if not options:
        return None
    options.sort(key=lambda item: (item[0], item[1], item[3].uci()), reverse=True)
    _score, _key, candidate, move = options[0]
    return {
        "candidate": candidate,
        "move": move,
        "terminal_activated": True,
    }


def _apply_candidate_credit(
    state: CandidateLifecycle,
    *,
    credit: float,
    eta_m3: float,
    terminal: str | None,
) -> None:
    state.experience_count += 1
    state.credit_sum += credit
    state.fast_weight += eta_m3 * credit
    if credit >= 0.0:
        state.positive_credit_count += 1
    else:
        state.negative_credit_count += 1
    if terminal == "rook_loss":
        state.rook_loss_count += 1
    elif terminal == "stalemate":
        state.stalemate_count += 1
    elif terminal == "illegal_move":
        state.illegal_count += 1


def _update_lifecycle_states(
    lifecycle: dict[str, CandidateLifecycle],
    config: GrowthTrainingConfig,
) -> None:
    for state in lifecycle.values():
        if state.lifecycle_state == "quarantined":
            continue
        unsafe = (
            state.experience_count >= config.prune_min_experience
            and (
                state.rook_loss_count > config.prune_max_rook_losses
                or state.stalemate_count > config.prune_max_stalemates
                or state.illegal_count > 0
                or state.fast_weight < config.prune_min_fast_weight
            )
        )
        if unsafe:
            state.lifecycle_state = "quarantined"
            continue
        mature = (
            state.experience_count >= config.mature_experience
            and state.mean_credit >= config.mature_min_mean_credit
            and state.rook_loss_count == 0
            and state.stalemate_count == 0
            and state.illegal_count == 0
        )
        if mature:
            state.lifecycle_state = "mature"
        elif state.experience_count > 0:
            state.lifecycle_state = "trial"


def _evaluate_trained_pool(
    *,
    positions: KRKPositionSet,
    candidates: list[dict[str, Any]],
    lifecycle: dict[str, CandidateLifecycle],
    config: GrowthTrainingConfig,
) -> dict[str, Any]:
    selected = _select_heldout_candidate(candidates, lifecycle)
    baseline_metrics, baseline_outcomes = evaluate_arm(
        positions.heldout,
        arm="baseline",
        horizon=config.eval_horizon,
    )
    if selected is None:
        return {
            "selected_candidate_key": None,
            "baseline": baseline_metrics.to_dict(),
            "trained_candidate": None,
            "paired_delta": {},
            "safety": {},
            "learning_decision": {
                "decision": "quarantine",
                "reasons": ["no_active_candidate"],
                "m3_update_count": sum(state.experience_count for state in lifecycle.values()),
                "m4_consolidation_event_count": 0,
            },
        }
    sandbox_metrics, sandbox_outcomes = evaluate_sandbox_arm(
        positions.heldout,
        candidate=selected,
        horizon=config.eval_horizon,
        activation_max_distance=config.activation_max_distance,
    )
    paired = _paired_delta(baseline_outcomes, sandbox_outcomes)
    safety = _safety_counts(baseline_outcomes, sandbox_outcomes)
    learning = _learning_decision(
        sandbox_metric=sandbox_metrics,
        paired_delta=paired,
        safety=safety,
    )
    return {
        "selected_candidate_key": selected["candidate_key"],
        "baseline": baseline_metrics.to_dict(),
        "trained_candidate": sandbox_metrics.to_dict(),
        "paired_delta": paired,
        "safety": safety,
        "learning_decision": learning,
    }


def _select_heldout_candidate(
    candidates: list[dict[str, Any]],
    lifecycle: dict[str, CandidateLifecycle],
) -> dict[str, Any] | None:
    active = [
        (lifecycle[candidate["candidate_key"]], candidate)
        for candidate in candidates
        if lifecycle[candidate["candidate_key"]].lifecycle_state != "quarantined"
    ]
    if not active:
        return None
    active.sort(
        key=lambda item: (
            item[0].lifecycle_state == "mature",
            item[0].fast_weight,
            item[0].experience_count,
            -item[0].rank,
        ),
        reverse=True,
    )
    return active[0][1]


def _training_summary(
    lifecycle: dict[str, dict[str, Any]],
    heldout: dict[str, Any],
) -> dict[str, Any]:
    promoted = heldout.get("learning_decision", {}).get("decision") == "promote"
    return {
        "candidate_nodes_spawned": len(lifecycle),
        "mature_candidate_count": sum(1 for item in lifecycle.values() if item["lifecycle_state"] == "mature"),
        "quarantined_candidate_count": sum(1 for item in lifecycle.values() if item["lifecycle_state"] == "quarantined"),
        "trial_candidate_count": sum(1 for item in lifecycle.values() if item["lifecycle_state"] == "trial"),
        "m3_update_count": sum(int(item["experience_count"]) for item in lifecycle.values()),
        "candidate_nodes_promoted": 1 if promoted else 0,
        "m4_consolidation_event_count": 1 if promoted else 0,
        "deleted_candidate_count": 0 if promoted else sum(1 for item in lifecycle.values() if item["lifecycle_state"] == "quarantined"),
        "heldout_selected_candidate_key": heldout.get("selected_candidate_key"),
        "heldout_decision": heldout.get("learning_decision", {}).get("decision"),
    }


def _annealed_eta(config: GrowthTrainingConfig, cycle: int) -> float:
    if config.cycles <= 1:
        return float(config.eta_m3_final)
    t = cycle / max(1, config.cycles - 1)
    return float(config.eta_m3_initial * (1.0 - t) + config.eta_m3_final * t)


def _mean(values: list[float]) -> float:
    return 0.0 if not values else sum(values) / len(values)
