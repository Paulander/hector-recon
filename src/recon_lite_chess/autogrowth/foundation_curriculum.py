"""TG25 foundation curriculum re-entry for dense KRK learning."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import random
from typing import Any, Iterable

import chess

from recon_lite_hector.nodes.stem_cell import StemCellState, StemCellTerminal

from .features import extract_learner_features, validate_learner_record


@dataclass(frozen=True)
class FoundationCurriculumConfig:
    seed: int = 20260612
    mate1_train_count: int = 1000
    mate1_heldout_count: int = 300
    mate1_mirror_count: int = 120
    mate2_train_count: int = 300
    mate2_heldout_count: int = 100
    mate2_enabled: bool = True
    max_generation_attempts: int = 500_000
    eta_m3: float = 0.10
    mate1_pass_threshold: float = 0.95
    mate2_pass_threshold: float = 0.80
    max_samples: int = 12


@dataclass
class ActionNode:
    action_key: str
    cell: StemCellTerminal
    local_weight: float = 0.0
    positive_credit: int = 0
    negative_credit: int = 0
    neutral_credit: int = 0

    def update(self, reward: float, eta: float) -> None:
        self.local_weight += eta * reward
        if reward > 0.0:
            self.positive_credit += 1
        elif reward < 0.0:
            self.negative_credit += 1
        else:
            self.neutral_credit += 1
        self.cell.xp += 1

    def to_dict(self) -> dict[str, Any]:
        learner_visible = {
            "node_type": "ACTION",
            "action_key": self.action_key,
            "local_weight": round(self.local_weight, 6),
            "positive_credit": self.positive_credit,
            "negative_credit": self.negative_credit,
            "neutral_credit": self.neutral_credit,
            "chooses_move_directly": False,
        }
        validate_learner_record(learner_visible)
        return {
            "cell": self.cell.to_dict(),
            "learner_visible": learner_visible,
            "diagnostics": {
                "m3_local_weight": round(self.local_weight, 6),
                "positive_credit": self.positive_credit,
                "negative_credit": self.negative_credit,
                "neutral_credit": self.neutral_credit,
            },
        }


@dataclass
class ActionRanker:
    nodes: dict[str, ActionNode]
    eta_m3: float
    m3_update_count: int = 0

    @classmethod
    def create(cls, *, eta_m3: float) -> "ActionRanker":
        return cls(nodes={}, eta_m3=eta_m3)

    def get_node(self, action_key: str) -> ActionNode:
        node = self.nodes.get(action_key)
        if node is None:
            cell = StemCellTerminal(f"foundation_action_{len(self.nodes):05d}")
            cell.state = StemCellState.TRIAL
            cell.trial_node_id = f"TRIAL_{cell.cell_id}"
            cell.trial_parent_id = "foundation_local_action_parent"
            node = ActionNode(action_key=action_key, cell=cell)
            self.nodes[action_key] = node
        return node

    def train_position(self, board: chess.Board, *, positive_moves: set[str]) -> dict[str, int]:
        updates = {"positive": 0, "negative": 0, "neutral": 0}
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            reward = _move_reward(board, move, positive_moves=positive_moves)
            for key in _action_feature_keys(board, move):
                node = self.get_node(key)
                node.update(reward, self.eta_m3)
                self.m3_update_count += 1
            if reward > 0:
                updates["positive"] += 1
            elif reward < 0:
                updates["negative"] += 1
            else:
                updates["neutral"] += 1
        return updates

    def choose(self, board: chess.Board) -> chess.Move | None:
        options: list[tuple[float, str, chess.Move]] = []
        for move in sorted(board.legal_moves, key=lambda item: item.uci()):
            options.append((self.weight_for_move(board, move), move.uci(), move))
        if not options:
            return None
        options.sort(reverse=True)
        return options[0][-1]

    def weight_for_move(self, board: chess.Board, move: chess.Move) -> float:
        return sum(
            0.0 if self.nodes.get(key) is None else self.nodes[key].local_weight
            for key in _action_feature_keys(board, move)
        )

    def to_dict(self, *, max_nodes: int = 24) -> dict[str, Any]:
        nodes = sorted(self.nodes.values(), key=lambda item: item.local_weight, reverse=True)
        return {
            "node_count": len(nodes),
            "m3_update_count": self.m3_update_count,
            "top_nodes": [node.to_dict() for node in nodes[:max_nodes]],
        }


@dataclass(frozen=True)
class FoundationCurriculumResult:
    config: FoundationCurriculumConfig
    mate1_train: tuple[str, ...]
    mate1_heldout: tuple[str, ...]
    mate1_mirror: tuple[str, ...]
    mate2_train: tuple[str, ...]
    mate2_heldout: tuple[str, ...]
    mate1_ranker: ActionRanker
    mate2_first_ranker: ActionRanker | None
    mate1_metrics: dict[str, Any]
    mate2_metrics: dict[str, Any]
    decision: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "krk_autogrowth_tg25_foundation_curriculum.v0",
            "checkpoint": "TG25_foundation_curriculum",
            "config": asdict(self.config),
            "dataset": {
                "mate1_train_count": len(self.mate1_train),
                "mate1_heldout_count": len(self.mate1_heldout),
                "mate1_mirror_count": len(self.mate1_mirror),
                "mate2_train_count": len(self.mate2_train),
                "mate2_heldout_count": len(self.mate2_heldout),
            },
            "training_runway": {
                "uses_curriculum_as_experience_distribution": True,
                "mate1_source": "generated legal KRK mate-in-1 variants",
                "mate2_source": "generated legal KRK forced mate-in-2 variants",
                "curriculum_labels_learner_visible": False,
                "stage_labels_diagnostics_only": True,
                "runtime_tablebase_or_dtm_move_source": False,
                "direct_provider_override": False,
            },
            "local_recon_structure": {
                "parent_node_type": "SCRIPT",
                "candidate_node_type": "ACTION",
                "relation_types": ["SUB", "POR", "SUR"],
                "move_choice_mediated_by_local_action_nodes": True,
                "action_nodes_receive_m3_credit": True,
                "direct_move_override": False,
            },
            "mate1": self.mate1_metrics,
            "mate2": self.mate2_metrics,
            "mate1_ranker": self.mate1_ranker.to_dict(),
            "mate2_first_ranker": None if self.mate2_first_ranker is None else self.mate2_first_ranker.to_dict(),
            "decision": self.decision,
        }

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return output


def run_foundation_curriculum(
    *,
    config: FoundationCurriculumConfig,
) -> FoundationCurriculumResult:
    mate1_train = tuple(_generate_mate_in_one_positions(
        count=config.mate1_train_count,
        seed=config.seed,
        max_attempts=config.max_generation_attempts,
    ))
    used = set(mate1_train)
    mate1_heldout = tuple(_generate_mate_in_one_positions(
        count=config.mate1_heldout_count,
        seed=config.seed + 1,
        excluded=used,
        max_attempts=config.max_generation_attempts,
    ))
    mate1_mirror = tuple(_mirrored_positions(mate1_heldout, limit=config.mate1_mirror_count))

    mate1_ranker = ActionRanker.create(eta_m3=config.eta_m3)
    mate1_pre = _evaluate_mate_in_one(mate1_heldout, ranker=ActionRanker.create(eta_m3=config.eta_m3), max_samples=config.max_samples)
    mate1_train_metrics = _train_mate_in_one(mate1_train, ranker=mate1_ranker)
    mate1_heldout_metrics = _evaluate_mate_in_one(mate1_heldout, ranker=mate1_ranker, max_samples=config.max_samples)
    mate1_mirror_metrics = _evaluate_mate_in_one(mate1_mirror, ranker=mate1_ranker, max_samples=config.max_samples)
    mate1_pass = mate1_heldout_metrics["accuracy"] >= config.mate1_pass_threshold
    mate1_m4 = int(mate1_pass and mate1_ranker.m3_update_count > 0)

    mate2_train: tuple[str, ...] = ()
    mate2_heldout: tuple[str, ...] = ()
    mate2_first_ranker: ActionRanker | None = None
    mate2_metrics: dict[str, Any] = {
        "enabled": False,
        "reason": "disabled_or_mate1_not_passed",
        "m4_consolidation_event_count": 0,
    }
    if config.mate2_enabled and mate1_pass:
        mate2_train = tuple(_generate_forced_mate_in_two_positions(
            count=config.mate2_train_count,
            seed=config.seed + 2,
            max_attempts=config.max_generation_attempts,
        ))
        mate2_heldout = tuple(_generate_forced_mate_in_two_positions(
            count=config.mate2_heldout_count,
            seed=config.seed + 3,
            excluded=set(mate2_train),
            max_attempts=config.max_generation_attempts,
        ))
        mate2_first_ranker = ActionRanker.create(eta_m3=config.eta_m3)
        mate2_train_metrics = _train_mate_in_two(mate2_train, first_ranker=mate2_first_ranker, mate_ranker=mate1_ranker)
        mate2_eval = _evaluate_mate_in_two(
            mate2_heldout,
            first_ranker=mate2_first_ranker,
            mate_ranker=mate1_ranker,
            max_samples=config.max_samples,
        )
        mate2_pass = mate2_eval["conversion_rate"] >= config.mate2_pass_threshold
        mate2_metrics = {
            "enabled": True,
            "stage_diagnostic": "Mate_In_2",
            "curriculum_labels_learner_visible": False,
            "training": mate2_train_metrics,
            "heldout": mate2_eval,
            "m4_consolidation_event_count": int(mate2_pass and mate2_first_ranker.m3_update_count > 0),
        }

    mate1_metrics = {
        "stage_diagnostic": "Mate_In_1",
        "curriculum_labels_learner_visible": False,
        "pre_training_heldout": mate1_pre,
        "training": mate1_train_metrics,
        "heldout": mate1_heldout_metrics,
        "mirror_generalization": mate1_mirror_metrics,
        "m3_update_count": mate1_ranker.m3_update_count,
        "m3_effect_on_accuracy": round(mate1_heldout_metrics["accuracy"] - mate1_pre["accuracy"], 6),
        "m4_consolidation_event_count": mate1_m4,
    }
    decision = _decision(
        config=config,
        mate1_pass=mate1_pass,
        mate1_metrics=mate1_metrics,
        mate2_metrics=mate2_metrics,
    )
    return FoundationCurriculumResult(
        config=config,
        mate1_train=mate1_train,
        mate1_heldout=mate1_heldout,
        mate1_mirror=mate1_mirror,
        mate2_train=mate2_train,
        mate2_heldout=mate2_heldout,
        mate1_ranker=mate1_ranker,
        mate2_first_ranker=mate2_first_ranker,
        mate1_metrics=mate1_metrics,
        mate2_metrics=mate2_metrics,
        decision=decision,
    )


def _train_mate_in_one(fens: Iterable[str], *, ranker: ActionRanker) -> dict[str, Any]:
    fen_list = tuple(fens)
    totals = {"positive": 0, "negative": 0, "neutral": 0}
    for fen in fen_list:
        board = chess.Board(fen)
        positives = {move.uci() for move in _mate_moves(board)}
        updates = ranker.train_position(board, positive_moves=positives)
        for key in totals:
            totals[key] += updates[key]
    return {
        "position_count": len(fen_list),
        "positive_updates": totals["positive"],
        "negative_updates": totals["negative"],
        "neutral_updates": totals["neutral"],
        "m3_update_count": ranker.m3_update_count,
    }


def _train_mate_in_two(
    fens: Iterable[str],
    *,
    first_ranker: ActionRanker,
    mate_ranker: ActionRanker,
) -> dict[str, Any]:
    fen_list = tuple(fens)
    first_totals = {"positive": 0, "negative": 0, "neutral": 0}
    second_updates = 0
    for fen in fen_list:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        updates = first_ranker.train_position(board, positive_moves=forced)
        for key in first_totals:
            first_totals[key] += updates[key]
        for first in _forced_mate_in_two_first_moves(board):
            after_first = board.copy(stack=False)
            after_first.push(first)
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                positives = {move.uci() for move in _mate_moves(before_mate)}
                before = mate_ranker.m3_update_count
                mate_ranker.train_position(before_mate, positive_moves=positives)
                second_updates += mate_ranker.m3_update_count - before
    return {
        "position_count": len(fen_list),
        "first_move_positive_updates": first_totals["positive"],
        "first_move_negative_updates": first_totals["negative"],
        "first_ranker_m3_update_count": first_ranker.m3_update_count,
        "second_mate_ranker_extra_m3_updates": second_updates,
    }


def _evaluate_mate_in_one(
    fens: Iterable[str],
    *,
    ranker: ActionRanker,
    max_samples: int,
) -> dict[str, Any]:
    fen_list = tuple(fens)
    rows = []
    correct = 0
    legal_moves = 0
    matched_positions = 0
    wrong_actions = 0
    suppressed_wrong_actions = 0
    for fen in fen_list:
        board = chess.Board(fen)
        move = ranker.choose(board)
        positives = {item.uci() for item in _mate_moves(board)}
        is_correct = move is not None and move.uci() in positives
        correct += int(is_correct)
        legal_moves += board.legal_moves.count()
        matched_positions += int(any(
            any(key in ranker.nodes for key in _action_feature_keys(board, item))
            for item in board.legal_moves
        ))
        for legal in board.legal_moves:
            if legal.uci() in positives:
                continue
            wrong_actions += 1
            suppressed_wrong_actions += int(ranker.weight_for_move(board, legal) < 0.0)
        rows.append({
            "fen": fen,
            "selected": None if move is None else move.uci(),
            "correct_moves": sorted(positives),
            "correct": is_correct,
            "legal_move_count": board.legal_moves.count(),
        })
    total = len(rows)
    return {
        "position_count": total,
        "correct_count": correct,
        "accuracy": 0.0 if total == 0 else correct / total,
        "top_ranked_action_correctness": 0.0 if total == 0 else correct / total,
        "avg_legal_move_count": 0.0 if total == 0 else round(legal_moves / total, 6),
        "candidate_activation_rate": 0.0 if total == 0 else matched_positions / total,
        "wrong_action_suppression_rate": (
            0.0 if wrong_actions == 0 else suppressed_wrong_actions / wrong_actions
        ),
        "wrong_action_suppressed_count": suppressed_wrong_actions,
        "wrong_action_available_count": wrong_actions,
        "wrong_action_count": total - correct,
        "samples": rows[:max_samples],
    }


def _evaluate_mate_in_two(
    fens: Iterable[str],
    *,
    first_ranker: ActionRanker,
    mate_ranker: ActionRanker,
    max_samples: int,
) -> dict[str, Any]:
    fen_list = tuple(fens)
    rows = []
    converted = 0
    first_success = 0
    chain_steps = 0
    replied_mated = 0
    replied_total = 0
    for fen in fen_list:
        board = chess.Board(fen)
        forced = {move.uci() for move in _forced_mate_in_two_first_moves(board)}
        first = first_ranker.choose(board)
        first_ok = first is not None and first.uci() in forced
        first_success += int(first_ok)
        all_replies_mated = False
        reply_rows = []
        if first is not None:
            after_first = board.copy(stack=False)
            after_first.push(first)
            all_replies_mated = True
            for reply in sorted(after_first.legal_moves, key=lambda item: item.uci()):
                before_mate = after_first.copy(stack=False)
                before_mate.push(reply)
                mate_move = mate_ranker.choose(before_mate)
                mates = {move.uci() for move in _mate_moves(before_mate)}
                ok = mate_move is not None and mate_move.uci() in mates
                chain_steps += 1
                replied_total += 1
                replied_mated += int(ok)
                all_replies_mated = all_replies_mated and ok
                reply_rows.append({
                    "black_reply": reply.uci(),
                    "selected_mate": None if mate_move is None else mate_move.uci(),
                    "correct_mates": sorted(mates),
                    "mated": ok,
                })
        converted += int(first_ok and all_replies_mated)
        rows.append({
            "fen": fen,
            "selected_first": None if first is None else first.uci(),
            "forced_first_moves": sorted(forced),
            "first_move_success": first_ok,
            "all_replies_mated": all_replies_mated,
            "reply_checks": reply_rows[:8],
        })
    total = len(rows)
    return {
        "position_count": total,
        "first_move_success_count": first_success,
        "first_move_success_rate": 0.0 if total == 0 else first_success / total,
        "conversion_count": converted,
        "conversion_rate": 0.0 if total == 0 else converted / total,
        "forced_mate_reply_coverage": 0.0 if replied_total == 0 else replied_mated / replied_total,
        "chain_request_count": total,
        "chain_step_count": chain_steps,
        "chain_completion_count": converted,
        "wrong_first_move_count": total - first_success,
        "samples": rows[:max_samples],
    }


def _move_reward(board: chess.Board, move: chess.Move, *, positive_moves: set[str]) -> float:
    if move.uci() in positive_moves:
        return 1.0
    after = board.copy(stack=False)
    after.push(move)
    if after.is_stalemate():
        return -1.0
    if _rook_missing_or_attacked(after):
        return -0.50
    return -0.05


def _action_feature_keys(board: chess.Board, move: chess.Move) -> tuple[str, ...]:
    features = _action_features(board, move)
    keys = [f"{name}={value}" for name, value in sorted(features.items())]
    keys.extend((
        "pair:gives_check:black_reply_mobility_after="
        f"{features['gives_check']}:{features['black_reply_mobility_after']}",
        "pair:gives_check:black_king_edge_after="
        f"{features['gives_check']}:{features['black_king_edge_after']}",
        "pair:piece:gives_check="
        f"{features['piece_type']}:{features['gives_check']}",
        "pair:piece:file_rank_delta="
        f"{features['piece_type']}:{features['file_delta_sign']}:{features['rank_delta_sign']}",
        "pair:rook_safety:gives_check="
        f"{features['rook_attacked_after']}:{features['gives_check']}",
    ))
    validate_learner_record(keys)
    return tuple(keys)


def _action_features(board: chess.Board, move: chess.Move) -> dict[str, int]:
    piece = board.piece_at(move.from_square)
    after = board.copy(stack=False)
    after.push(move)
    features = extract_learner_features(after)
    file_delta = chess.square_file(move.to_square) - chess.square_file(move.from_square)
    rank_delta = chess.square_rank(move.to_square) - chess.square_rank(move.from_square)
    payload = {
        "piece_type": 0 if piece is None else int(piece.piece_type),
        "file_delta_sign": _sign(file_delta),
        "rank_delta_sign": _sign(rank_delta),
        "file_delta_magnitude": min(abs(file_delta), 3),
        "rank_delta_magnitude": min(abs(rank_delta), 3),
        "from_file_edge_distance": _edge_distance(move.from_square),
        "from_rank_edge_distance": _rank_edge_distance(move.from_square),
        "to_file_edge_distance": _edge_distance(move.to_square),
        "to_rank_edge_distance": _rank_edge_distance(move.to_square),
        "gives_check": int(board.gives_check(move)),
        "is_capture": int(board.is_capture(move)),
        "black_reply_mobility_after": int(features["black_reply_mobility"]),
        "black_king_edge_after": int(features["black_king_nearest_edge_distance"]),
        "white_king_to_black_king_after": int(features["white_king_to_black_king_distance"]),
        "white_rook_to_black_king_after": int(features["white_rook_to_black_king_distance"]),
        "white_king_to_rook_after": int(features["white_king_to_rook_distance"]),
        "rook_attacked_after": int(features["rook_attacked_by_black"]),
        "is_stalemate_after": int(features["is_stalemate"]),
    }
    validate_learner_record(payload)
    return payload


def _generate_mate_in_one_positions(
    *,
    count: int,
    seed: int,
    excluded: set[str] | None = None,
    max_attempts: int,
) -> list[str]:
    rng = random.Random(seed)
    used = set(excluded or set())
    positions: list[str] = []
    for _ in range(max_attempts):
        if len(positions) >= count:
            break
        board = _random_krk_board(rng)
        if not _valid_foundation_board(board):
            continue
        mates = _mate_moves(board)
        if 1 <= len(mates) <= 3 and board.fen() not in used:
            used.add(board.fen())
            positions.append(board.fen())
    if len(positions) < count:
        raise RuntimeError(f"generated {len(positions)} mate-in-1 positions, needed {count}")
    return positions


def _generate_forced_mate_in_two_positions(
    *,
    count: int,
    seed: int,
    excluded: set[str] | None = None,
    max_attempts: int,
) -> list[str]:
    rng = random.Random(seed)
    used = set(excluded or set())
    positions: list[str] = []
    for _ in range(max_attempts):
        if len(positions) >= count:
            break
        board = _random_krk_board(rng)
        if not _valid_foundation_board(board):
            continue
        forced = _forced_mate_in_two_first_moves(board)
        if 1 <= len(forced) <= 5 and board.fen() not in used:
            used.add(board.fen())
            positions.append(board.fen())
    if len(positions) < count:
        raise RuntimeError(f"generated {len(positions)} mate-in-2 positions, needed {count}")
    return positions


def _random_krk_board(rng: random.Random) -> chess.Board:
    wk, wr, bk = rng.sample(list(chess.SQUARES), 3)
    board = chess.Board(None)
    board.clear_board()
    board.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(wr, chess.Piece(chess.ROOK, chess.WHITE))
    board.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    board.turn = chess.WHITE
    board.castling_rights = 0
    board.ep_square = None
    board.halfmove_clock = 0
    board.fullmove_number = 1
    return board


def _valid_foundation_board(board: chess.Board) -> bool:
    return (
        board.turn == chess.WHITE
        and board.is_valid()
        and not board.is_game_over(claim_draw=False)
        and not board.is_checkmate()
        and not board.is_stalemate()
    )


def _mate_moves(board: chess.Board) -> list[chess.Move]:
    mates: list[chess.Move] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        after = board.copy(stack=False)
        after.push(move)
        if after.is_checkmate():
            mates.append(move)
    return mates


def _forced_mate_in_two_first_moves(board: chess.Board) -> list[chess.Move]:
    if _mate_moves(board):
        return []
    forced: list[chess.Move] = []
    for move in sorted(board.legal_moves, key=lambda item: item.uci()):
        after_first = board.copy(stack=False)
        after_first.push(move)
        replies = list(after_first.legal_moves)
        if not replies:
            continue
        if all(_mate_moves(_after_reply(after_first, reply)) for reply in replies):
            forced.append(move)
    return forced


def _after_reply(board: chess.Board, reply: chess.Move) -> chess.Board:
    after = board.copy(stack=False)
    after.push(reply)
    return after


def _mirrored_positions(fens: Iterable[str], *, limit: int) -> list[str]:
    transforms = (chess.flip_horizontal, chess.flip_vertical, chess.flip_diagonal, chess.flip_anti_diagonal)
    positions: list[str] = []
    used: set[str] = set()
    for fen in fens:
        board = chess.Board(fen)
        for transform in transforms:
            mirrored = board.transform(transform)
            mirrored.turn = chess.WHITE
            fen_out = mirrored.fen()
            if fen_out in used or not _valid_foundation_board(mirrored):
                continue
            if not _mate_moves(mirrored):
                continue
            used.add(fen_out)
            positions.append(fen_out)
            if len(positions) >= limit:
                return positions
    return positions


def _rook_missing_or_attacked(board: chess.Board) -> bool:
    rook = _white_rook_square(board)
    return rook is None or board.is_attacked_by(chess.BLACK, rook)


def _white_rook_square(board: chess.Board) -> int | None:
    rooks = sorted(board.pieces(chess.ROOK, chess.WHITE))
    return rooks[0] if rooks else None


def _sign(value: int) -> int:
    return int(value > 0) - int(value < 0)


def _edge_distance(square: int) -> int:
    return min(chess.square_file(square), 7 - chess.square_file(square))


def _rank_edge_distance(square: int) -> int:
    return min(chess.square_rank(square), 7 - chess.square_rank(square))


def _decision(
    *,
    config: FoundationCurriculumConfig,
    mate1_pass: bool,
    mate1_metrics: dict[str, Any],
    mate2_metrics: dict[str, Any],
) -> dict[str, Any]:
    mate2_pass = bool(
        mate2_metrics.get("enabled")
        and mate2_metrics["heldout"]["conversion_rate"] >= config.mate2_pass_threshold
    )
    return {
        "status": (
            "tg25_foundation_mate1_mate2_passed"
            if mate1_pass and mate2_pass
            else "tg25_foundation_mate1_passed"
            if mate1_pass
            else "tg25_foundation_failed"
        ),
        "mate1_passed": mate1_pass,
        "mate1_heldout_accuracy": mate1_metrics["heldout"]["accuracy"],
        "mate1_mirror_accuracy": mate1_metrics["mirror_generalization"]["accuracy"],
        "mate1_m3_update_count": mate1_metrics["m3_update_count"],
        "mate1_m4_consolidation_event_count": mate1_metrics["m4_consolidation_event_count"],
        "mate2_enabled": bool(mate2_metrics.get("enabled")),
        "mate2_passed": mate2_pass,
        "mate2_conversion_rate": None if not mate2_metrics.get("enabled") else mate2_metrics["heldout"]["conversion_rate"],
        "mate2_m4_consolidation_event_count": int(mate2_metrics.get("m4_consolidation_event_count", 0)),
        "curriculum_labels_learner_visible": False,
        "direct_provider_override": False,
        "runtime_tablebase_or_dtm_move_source": False,
        "next_recommended_checkpoint": (
            "Continue foundation curriculum into edge-trap/fence small slices"
            if mate1_pass and mate2_pass
            else "Inspect Mate_In_2 first-move features and chain dynamics before edge-trap/fence"
            if mate1_pass
            else "Fix Mate_In_1 action-node substrate before any broader KRK autogrowth"
        ),
    }
