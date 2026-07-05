"""TG26n single-graph KRK curriculum chain.

This checkpoint removes the special "call the Mate_In_1 helper" handoff used
by earlier Mate_In_2 validators. One persistent graph is trained through the
curriculum and the same graph chooses every white move.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState, StemCellTerminal

from .curated_replay_curriculum import _mate2_buckets
from .curated_terminal_curriculum import curated_stage_entries
from .features import validate_learner_record, validate_learner_visible_keys
from .foundation_curriculum import (
    _forced_mate_in_two_first_moves,
    _mate_moves,
    _move_reward,
)
from .terminal_substrate import (
    TerminalAffordanceLearner,
    _bucket,
    _delta_bucket,
    extract_terminal_feature_vector,
    terminal_action_feature_keys,
)


@dataclass(frozen=True)
class SingleGraphCurriculumConfig:
    include_symmetries: bool = True
    train_repetitions: int = 5
    continuation_repetitions: int = 2
    eta_m3: float = 0.10
    rich_feature_credit_scale: float = 0.25
    normalize_terminal_activation: bool = True
    terminal_score_scale: float = 1.0
    score_context_free_action_terminals: bool = False
    triplet_credit_scale: float = 0.35
    max_abs_local_weight: float = 1.0
    triplet_mature_min_abs_weight: float = 0.20
    mate1_threshold: float = 0.98
    mate2_threshold: float = 0.95
    max_samples: int = 32


@dataclass
class SingleGraphTriplet:
    triplet_id: str
    before_keys: tuple[str, ...]
    action_delta_keys: tuple[str, ...]
    after_keys: tuple[str, ...]
    cell: StemCellTerminal
    local_weight: float = 0.0
    positive_credit: int = 0
    negative_credit: int = 0
    neutral_credit: int = 0
    request_exposures: int = 0
    activation_count: int = 0
    confirm_count: int = 0
    last_stage: str = ""

    def update(self, *, reward: float, eta: float, cycle: int, stage: str) -> None:
        self.request_exposures += 1
        self.activation_count += 1
        self.local_weight += eta * reward
        self.cell.xp += 1
        self.cell.total_exposures += 1
        self.cell.candidate_stats.record_request(parent_id="single_graph_triplet_parent")
        self.cell.candidate_stats.record_activation(parent_id="single_graph_triplet_parent")
        self.last_stage = stage
        if reward > 0.0:
            self.positive_credit += 1
            self.confirm_count += 1
            self.cell.xp_successes += 1
            self.cell.candidate_stats.record_confirm(cycle, parent_id="single_graph_triplet_parent")
            self.cell.candidate_stats.record_intervention("positive")
        elif reward < 0.0:
            self.negative_credit += 1
            self.cell.xp_failures += 1
            self.cell.candidate_stats.record_intervention("negative")
        else:
            self.neutral_credit += 1
            self.cell.candidate_stats.record_intervention("neutral")
        self.cell.candidate_stats.recompute_survival(
            xp=self.cell.xp,
            solidify_xp=self.cell.XP_SOLIDIFY,
        )

    def mature(self) -> None:
        self.cell.state = StemCellState.MATURE
        self.cell.metadata["tier"] = "mature"
        self.cell.metadata["mature_reason"] = "single_graph_curriculum_stage_completion"

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "triplet_id": self.triplet_id,
            "node_type": "TRIAL/MATURE triplet",
            "represented_as": "before_terminal -> action_delta -> after_terminal",
            "stem_cell_state": self.cell.state.name,
            "before_key_count": len(self.before_keys),
            "action_delta_key_count": len(self.action_delta_keys),
            "after_key_count": len(self.after_keys),
            "local_weight": round(self.local_weight, 6),
            "positive_credit": self.positive_credit,
            "negative_credit": self.negative_credit,
            "neutral_credit": self.neutral_credit,
            "request_exposures": self.request_exposures,
            "activation_count": self.activation_count,
            "confirm_count": self.confirm_count,
            "last_stage": self.last_stage,
            "chooses_move_directly": False,
        }
        validate_learner_record(payload)
        return payload


@dataclass
class SingleGraphKRKNetwork:
    learner: TerminalAffordanceLearner
    triplets: dict[str, SingleGraphTriplet]
    cycle: int = 0
    triplet_key_cache: dict[
        tuple[str, str],
        tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]],
    ] = field(default_factory=dict)

    @classmethod
    def create(cls, *, config: SingleGraphCurriculumConfig) -> "SingleGraphKRKNetwork":
        return cls(
            learner=TerminalAffordanceLearner.create(
                eta_m3=config.eta_m3,
                rich_feature_credit_scale=config.rich_feature_credit_scale,
            ),
            triplets={},
        )

    def choose(self, board: chess.Board, *, config: SingleGraphCurriculumConfig) -> chess.Move | None:
        options: list[tuple[float, str, chess.Move]] = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            score = self.score_move(board, move, config=config)
            options.append((score, move.uci(), move))
        if not options:
            return None
        options.sort(reverse=True)
        return options[0][-1]

    def score_move(self, board: chess.Board, move: chess.Move, *, config: SingleGraphCurriculumConfig) -> float:
        terminal_score, active_terminal_count = self._terminal_score_for_move(
            board,
            move,
            include_context_free_action_terminals=config.score_context_free_action_terminals,
        )
        if config.normalize_terminal_activation:
            terminal_score /= max(1, active_terminal_count)
        terminal_score *= config.terminal_score_scale
        before_keys, action_delta_keys, after_keys = self._cached_triplet_keys(board, move)
        triplet = self.triplets.get(_triplet_id(before_keys, action_delta_keys, after_keys))
        triplet_score = 0.0 if triplet is None else triplet.local_weight
        return terminal_score + config.triplet_credit_scale * triplet_score

    def _terminal_score_for_move(
        self,
        board: chess.Board,
        move: chess.Move,
        *,
        include_context_free_action_terminals: bool,
    ) -> tuple[float, int]:
        terminal_score = 0.0
        active_terminal_count = 0
        for terminal_key, _scale in terminal_action_feature_keys(
            board,
            move,
            hub=self.learner.hub,
            feature_cache=self.learner.feature_cache,
        ):
            if not include_context_free_action_terminals and terminal_key.startswith("action_pattern:"):
                continue
            terminal = self.learner.terminals.get(terminal_key)
            if terminal is None:
                continue
            terminal_score += terminal.local_weight
            active_terminal_count += 1
        return terminal_score, active_terminal_count

    def train_action_rewards(
        self,
        board: chess.Board,
        *,
        rewards: Mapping[str, float],
        stage: str,
        config: SingleGraphCurriculumConfig,
    ) -> dict[str, int]:
        updates = self.learner.train_position_rewards(board, move_rewards=rewards)
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            reward = float(rewards.get(move.uci(), 0.0))
            triplet = self.get_triplet(board, move)
            self.cycle += 1
            triplet.update(reward=reward, eta=config.eta_m3, cycle=self.cycle, stage=stage)
        self._clip_local_weights(config=config)
        return updates

    def get_triplet(self, board: chess.Board, move: chess.Move) -> SingleGraphTriplet:
        before_keys, action_delta_keys, after_keys = self._cached_triplet_keys(board, move)
        triplet_id = _triplet_id(before_keys, action_delta_keys, after_keys)
        triplet = self.triplets.get(triplet_id)
        if triplet is None:
            cell = StemCellTerminal(f"tg26n_triplet_{len(self.triplets):05d}")
            cell.state = StemCellState.TRIAL
            cell.trial_node_id = f"TRIAL_{cell.cell_id}"
            cell.trial_parent_id = "single_graph_triplet_parent"
            cell.metadata = {
                "node_type": "TRIPLET",
                "terminal_kind": "before_action_delta_after",
                "relation_types": ["SUB", "SUR", "POR", "RET"],
                "chooses_move_directly": False,
            }
            triplet = SingleGraphTriplet(
                triplet_id=triplet_id,
                before_keys=before_keys,
                action_delta_keys=action_delta_keys,
                after_keys=after_keys,
                cell=cell,
            )
            self.triplets[triplet_id] = triplet
        return triplet

    def _cached_triplet_keys(
        self,
        board: chess.Board,
        move: chess.Move,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        cache_key = (board.fen(), move.uci())
        cached = self.triplet_key_cache.get(cache_key)
        if cached is None:
            cached = _triplet_keys(board, move)
        self.triplet_key_cache[cache_key] = cached
        return cached

    def _clip_local_weights(self, *, config: SingleGraphCurriculumConfig) -> None:
        max_abs = config.max_abs_local_weight
        for terminal in self.learner.terminals.values():
            terminal.local_weight = max(-max_abs, min(max_abs, terminal.local_weight))
        for triplet in self.triplets.values():
            triplet.local_weight = max(-max_abs, min(max_abs, triplet.local_weight))

    def mature_existing_graph(self, *, config: SingleGraphCurriculumConfig) -> dict[str, Any]:
        matured_terminals = 0
        for terminal in self.learner.terminals.values():
            if abs(terminal.local_weight) >= config.triplet_mature_min_abs_weight or terminal.confirm_count > 0:
                terminal.cell.state = StemCellState.MATURE
                terminal.cell.metadata["tier"] = "mature"
                terminal.cell.metadata["mature_reason"] = "single_graph_curriculum_stage_completion"
                matured_terminals += 1
        matured_triplets = 0
        for triplet in self.triplets.values():
            if abs(triplet.local_weight) >= config.triplet_mature_min_abs_weight or triplet.confirm_count > 0:
                triplet.mature()
                matured_triplets += 1
        return {
            "matured_terminal_count": matured_terminals,
            "matured_triplet_count": matured_triplets,
            "total_terminal_count": len(self.learner.terminals),
            "total_triplet_count": len(self.triplets),
        }

    def to_dict(self, *, max_triplets: int = 24) -> dict[str, Any]:
        triplets = sorted(self.triplets.values(), key=lambda item: item.local_weight, reverse=True)
        return {
            "single_persistent_graph": True,
            "separate_stage_networks": False,
            "hardcoded_mate1_handoff": False,
            "terminal_substrate": self.learner.to_dict(max_terminals=12),
            "triplet_count": len(self.triplets),
            "mature_triplet_count": sum(1 for item in self.triplets.values() if item.cell.state == StemCellState.MATURE),
            "triplet_key_cache_size": len(self.triplet_key_cache),
            "top_positive_triplets": [item.to_dict() for item in triplets[:max_triplets]],
            "top_negative_triplets": [
                item.to_dict()
                for item in sorted(triplets, key=lambda item: item.local_weight)[:max_triplets]
            ],
        }


@dataclass(frozen=True)
class SingleGraphCurriculumResult:
    config: SingleGraphCurriculumConfig
    dataset: dict[str, Any]
    mate1: dict[str, Any]
    maturation: dict[str, Any]
    mate2: dict[str, Any]
    graph: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg26n_single_graph_curriculum.v0",
            "checkpoint": "TG26n_single_graph_curriculum",
            "config": asdict(self.config),
            "purity_boundary": {
                "one_persistent_recon_graph_across_curriculum": True,
                "mate1_graph_matured_before_mate2": True,
                "separate_mate1_or_mate2_networks": False,
                "hardcoded_mate1_handoff": False,
                "stage_labels_learner_visible": False,
                "direct_provider_override": False,
                "runtime_tablebase_or_dtm_move_source": False,
                "curriculum_labels_are_schedule_and_diagnostics_only": True,
            },
            "dataset": self.dataset,
            "mate1": self.mate1,
            "maturation": self.maturation,
            "mate2": self.mate2,
            "graph": self.graph,
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_single_graph_curriculum(
    *,
    config: SingleGraphCurriculumConfig | None = None,
) -> SingleGraphCurriculumResult:
    cfg = config or SingleGraphCurriculumConfig()
    entries = curated_stage_entries(include_symmetries=cfg.include_symmetries)
    mate1_fens = _unique(
        entry.fen
        for entry in entries
        if entry.stage_name == "Mate_In_1" and entry.mate_in_one_moves
    )
    buckets = _mate2_buckets(entries)
    mate2_fens = _unique(fen for bucket in buckets for fen in bucket["fens"])
    graph = SingleGraphKRKNetwork.create(config=cfg)

    mate1_training = _train_mate1_stage(graph, mate1_fens, config=cfg)
    mate1_eval = _evaluate_mate1_stage(graph, mate1_fens, config=cfg)
    maturation = graph.mature_existing_graph(config=cfg)
    mate2_training = _train_mate2_stage(graph, mate2_fens, config=cfg)
    mate2_eval = _evaluate_mate2_stage(graph, mate2_fens, config=cfg)
    decision = {
        "checkpoint_pass": (
            mate1_eval["accuracy"] >= cfg.mate1_threshold
            and mate2_eval["conversion_rate"] >= cfg.mate2_threshold
            and mate2_eval["same_graph_second_move_count"] > 0
        ),
        "mate1_threshold": cfg.mate1_threshold,
        "mate2_threshold": cfg.mate2_threshold,
        "m4_mate1_maturation_event_count": int(maturation["matured_terminal_count"] > 0 or maturation["matured_triplet_count"] > 0),
        "m4_mate2_consolidation_event_count": int(mate2_eval["conversion_rate"] >= cfg.mate2_threshold),
        "single_graph_chain_demonstrated": mate2_eval["same_graph_second_move_count"] > 0,
        "next_step": (
            "use single-graph triplet chain as the only foundation before edge/fence"
            if mate2_eval["conversion_rate"] >= cfg.mate2_threshold
            else "tighten single-graph triplet chain before edge/fence"
        ),
    }
    return SingleGraphCurriculumResult(
        config=cfg,
        dataset={
            "source": "src/recon_lite_chess/training/krk_curriculum.py::KRK_STAGES",
            "include_symmetries": cfg.include_symmetries,
            "mate1_position_count": len(mate1_fens),
            "mate2_bucket_count": len(buckets),
            "mate2_position_count": len(mate2_fens),
            "raw_mate2_bucket_entry_count": sum(len(bucket["fens"]) for bucket in buckets),
        },
        mate1={
            "training": mate1_training,
            "evaluation": mate1_eval,
        },
        maturation=maturation,
        mate2={
            "training": mate2_training,
            "evaluation": mate2_eval,
        },
        graph=graph.to_dict(max_triplets=24),
        decision=decision,
    )


def _train_mate1_stage(
    graph: SingleGraphKRKNetwork,
    fens: Iterable[str],
    *,
    config: SingleGraphCurriculumConfig,
) -> dict[str, Any]:
    totals = {"positive": 0, "negative": 0, "neutral": 0}
    records = 0
    for fen in tuple(fens):
        for _ in range(config.train_repetitions):
            board = chess.Board(fen)
            positives = {move.uci() for move in _mate_moves(board)}
            rewards = {
                move.uci(): _move_reward(board, move, positive_moves=positives)
                for move in board.legal_moves
            }
            updates = graph.train_action_rewards(board, rewards=rewards, stage="Mate_In_1", config=config)
            records += 1
            for key in totals:
                totals[key] += updates[key]
    return {
        "train_records": records,
        "positive_updates": totals["positive"],
        "negative_updates": totals["negative"],
        "neutral_updates": totals["neutral"],
        "m3_update_count": graph.learner.m3_update_count,
        "terminal_count": len(graph.learner.terminals),
        "triplet_count": len(graph.triplets),
    }


def _train_mate2_stage(
    graph: SingleGraphKRKNetwork,
    fens: Iterable[str],
    *,
    config: SingleGraphCurriculumConfig,
) -> dict[str, Any]:
    totals = {"positive": 0, "negative": 0, "neutral": 0}
    continuation_records = 0
    first_records = 0
    chain_positive_total = 0
    no_chain_positive = 0
    for fen in tuple(fens):
        board = chess.Board(fen)
        forced = tuple(_forced_mate_in_two_first_moves(board))
        for _ in range(config.continuation_repetitions):
            for first in forced:
                after_first = board.copy(stack=False)
                after_first.push(first)
                for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                    before_mate = after_first.copy(stack=False)
                    before_mate.push(reply)
                    positives = {move.uci() for move in _mate_moves(before_mate)}
                    rewards = {
                        move.uci(): _move_reward(before_mate, move, positive_moves=positives)
                        for move in before_mate.legal_moves
                    }
                    graph.train_action_rewards(
                        before_mate,
                        rewards=rewards,
                        stage="Mate_In_2_continuation_experience",
                        config=config,
                    )
                    continuation_records += 1
        for _ in range(config.train_repetitions):
            chain_positives = _same_graph_chain_positive_first_moves(graph, board, config=config)
            chain_positive_total += len(chain_positives)
            no_chain_positive += int(not chain_positives)
            rewards = {
                move.uci(): _move_reward(board, move, positive_moves=chain_positives)
                for move in board.legal_moves
            }
            updates = graph.train_action_rewards(board, rewards=rewards, stage="Mate_In_2_first_move", config=config)
            first_records += 1
            for key in totals:
                totals[key] += updates[key]
    return {
        "first_move_train_records": first_records,
        "continuation_experience_records": continuation_records,
        "chain_positive_total": chain_positive_total,
        "no_chain_positive_record_count": no_chain_positive,
        "positive_updates": totals["positive"],
        "negative_updates": totals["negative"],
        "neutral_updates": totals["neutral"],
        "m3_update_count": graph.learner.m3_update_count,
        "terminal_count": len(graph.learner.terminals),
        "triplet_count": len(graph.triplets),
        "continuation_experience_uses_same_graph": True,
        "external_labels_are_training_rewards_only": True,
    }


def _evaluate_mate1_stage(
    graph: SingleGraphKRKNetwork,
    fens: Iterable[str],
    *,
    config: SingleGraphCurriculumConfig,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    correct = 0
    for fen in tuple(fens):
        board = chess.Board(fen)
        move = graph.choose(board, config=config)
        mates = {item.uci() for item in _mate_moves(board)}
        ok = move is not None and move.uci() in mates
        correct += int(ok)
        rows.append({
            "fen": fen,
            "selected": None if move is None else move.uci(),
            "correct_mates": sorted(mates),
            "correct": ok,
        })
    total = len(rows)
    return {
        "position_count": total,
        "correct_count": correct,
        "accuracy": 0.0 if total == 0 else correct / total,
        "samples": rows[:config.max_samples],
    }


def _evaluate_mate2_stage(
    graph: SingleGraphKRKNetwork,
    fens: Iterable[str],
    *,
    config: SingleGraphCurriculumConfig,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    first_success = 0
    converted = 0
    reply_total = 0
    reply_mated = 0
    same_graph_second_move_count = 0
    for fen in tuple(fens):
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        first = graph.choose(board, config=config)
        first_ok = first is not None and first.uci() in forced
        first_success += int(first_ok)
        all_replies_mated = False
        reply_rows: list[dict[str, Any]] = []
        if first is not None:
            after_first = board.copy(stack=False)
            after_first.push(first)
            all_replies_mated = True
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                second = graph.choose(before_mate, config=config)
                mates = {move.uci() for move in _mate_moves(before_mate)}
                ok = second is not None and second.uci() in mates
                reply_total += 1
                reply_mated += int(ok)
                same_graph_second_move_count += int(second is not None)
                all_replies_mated = all_replies_mated and ok
                reply_rows.append({
                    "black_reply": reply.uci(),
                    "same_graph_selected_second": None if second is None else second.uci(),
                    "correct_mates": sorted(mates),
                    "mated": ok,
                })
        converted += int(first_ok and all_replies_mated)
        rows.append({
            "fen": fen,
            "same_graph_selected_first": None if first is None else first.uci(),
            "forced_first_moves": sorted(forced),
            "first_move_success": first_ok,
            "all_replies_mated_by_same_graph": all_replies_mated,
            "reply_checks": reply_rows[:8],
        })
    total = len(rows)
    return {
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "same_graph_reply_mate_rate": 0.0 if reply_total == 0 else reply_mated / reply_total,
        "same_graph_second_move_count": same_graph_second_move_count,
        "hardcoded_mate1_handoff": False,
        "samples": rows[:config.max_samples],
    }


def _same_graph_chain_positive_first_moves(
    graph: SingleGraphKRKNetwork,
    board: chess.Board,
    *,
    config: SingleGraphCurriculumConfig,
) -> set[str]:
    positives: set[str] = set()
    for first in sorted(board.legal_moves, key=lambda item: item.uci()):
        if _mate_moves(board):
            continue
        after_first = board.copy(stack=False)
        after_first.push(first)
        replies = list(after_first.legal_moves)
        if not replies:
            continue
        all_replies_mated = True
        for reply in replies:
            before_mate = after_first.copy(stack=False)
            before_mate.push(reply)
            second = graph.choose(before_mate, config=config)
            mates = {move.uci() for move in _mate_moves(before_mate)}
            if second is None or second.uci() not in mates:
                all_replies_mated = False
                break
        if all_replies_mated:
            positives.add(first.uci())
    return positives


def _triplet_keys(board: chess.Board, move: chess.Move) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    after = board.copy(stack=False)
    after.push(move)
    before_features = extract_terminal_feature_vector(board)
    after_features = extract_terminal_feature_vector(after)
    before_keys = tuple(
        f"before_terminal:{key}={_bucket(value)}"
        for key, value in sorted(before_features.items())
    )
    after_keys = tuple(
        f"after_terminal:{key}={_bucket(value)}"
        for key, value in sorted(after_features.items())
    )
    action_delta_keys = [
        key
        for key, _scale in terminal_action_feature_keys(board, move)
        if key.startswith("action_pattern:")
    ]
    for key in sorted(before_features.keys() & after_features.keys()):
        action_delta_keys.append(
            f"delta_terminal:{key}={_delta_bucket(after_features[key] - before_features[key])}"
        )
    validate_learner_visible_keys(
        [*before_keys, *action_delta_keys, *after_keys],
        builder="single_graph_curriculum._triplet_keys",
    )
    return before_keys, tuple(action_delta_keys), after_keys


def _triplet_overlap(triplet: SingleGraphTriplet, board: chess.Board, move: chess.Move) -> float:
    before_keys, action_delta_keys, after_keys = _triplet_keys(board, move)
    hits = (
        len(set(triplet.before_keys) & set(before_keys))
        + len(set(triplet.action_delta_keys) & set(action_delta_keys))
        + len(set(triplet.after_keys) & set(after_keys))
    )
    total = max(1, len(triplet.before_keys) + len(triplet.action_delta_keys) + len(triplet.after_keys))
    return hits / total


def _triplet_id(before_keys: tuple[str, ...], action_delta_keys: tuple[str, ...], after_keys: tuple[str, ...]) -> str:
    digest = hashlib.sha1(
        "\n".join([*before_keys, *action_delta_keys, *after_keys]).encode("utf-8")
    ).hexdigest()[:16]
    return f"tg26n_triplet_{digest}"


def _unique(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))
