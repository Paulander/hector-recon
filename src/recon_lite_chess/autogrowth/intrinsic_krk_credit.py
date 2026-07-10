"""KRK adapter for graph-native, outcome-grounded competence credit.

This module does not decide whether a chess position is objectively winning. It
asks the already-promoted TG46d graph whether its Mate-in-1/Mate-in-2 competence
responds, then exposes the competence's consolidated empirical value. Exact
validators remain evaluation-only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import gzip
import json
from typing import Any, Mapping

import chess

from recon_lite_hector.learning import (
    CompetenceGateConfig,
    CompetenceGateExample,
    IntrinsicCreditConfig,
    IntrinsicCreditEngine,
    OutcomeCalibratedCompetenceGate,
)

from .terminal_substrate import TerminalAffordanceLearner


MATE1_COMPETENCE_ID = "tg46d:mate1"
MATE2_COMPETENCE_ID = "tg46d:mate2"
TG46D_POLICY_FEATURE_NAMES = (
    "selected_weight",
    "active_terminal_count",
    "runner_up_margin",
    "weight_per_active_terminal",
)


@dataclass(frozen=True)
class KRKIntrinsicCreditConfig:
    gamma: float = 0.97
    real_move_cost: float = 0.01
    terminal_failure_value: float = -1.0
    terminal_draw_value: float = -0.25
    min_grounding_evidence: int = 3


def native_foundation_response(
    board: chess.Board,
    parent: Mapping[str, TerminalAffordanceLearner] | None,
    *,
    mate2_gate: OutcomeCalibratedCompetenceGate | None = None,
) -> dict[str, Any]:
    """Return TG46d response without consulting mate validators or stage labels."""

    if parent is None:
        return _empty_native_response()
    if board.turn == chess.WHITE:
        detail = _native_response_at_white_turn(board, parent, mate2_gate=mate2_gate)
        provider_ids = _providers_for_types((detail["graph_response_type"],))
        return {
            "graph_positive": detail["graph_positive"],
            "graph_all_reply": detail["graph_positive"],
            "graph_partial_reply": False,
            "graph_positive_reply_count": int(detail["graph_positive"]),
            "reply_total": 1,
            "graph_response_types": [detail["graph_response_type"]],
            "provider_ids": list(provider_ids),
            "selected_mate1_move": detail["selected_mate1_move"],
            "selected_mate2_first_move": detail["selected_mate2_first_move"],
            "validator_consulted": False,
            "competence_gate_probability": detail["competence_gate_probability"],
            "competence_gate_confirmed": detail["competence_gate_confirmed"],
        }

    replies = list(board.legal_moves)
    details = []
    for reply in replies:
        after = board.copy(stack=False)
        after.push(reply)
        details.append(_native_response_at_white_turn(after, parent, mate2_gate=mate2_gate))
    positive_count = sum(int(detail["graph_positive"]) for detail in details)
    response_types = tuple(detail["graph_response_type"] for detail in details)
    graph_all = bool(replies and positive_count == len(replies))
    return {
        "graph_positive": bool(positive_count),
        "graph_all_reply": graph_all,
        "graph_partial_reply": bool(positive_count and not graph_all),
        "graph_positive_reply_count": positive_count,
        "reply_total": len(replies),
        "graph_response_types": list(response_types),
        "provider_ids": list(_providers_for_types(response_types)) if graph_all else [],
        "selected_mate1_move": next(
            (detail["selected_mate1_move"] for detail in details if detail["selected_mate1_move"]),
            None,
        ),
        "selected_mate2_first_move": next(
            (
                detail["selected_mate2_first_move"]
                for detail in details
                if detail["selected_mate2_first_move"]
            ),
            None,
        ),
        "validator_consulted": False,
        "competence_gate_probability": min(
            (float(detail["competence_gate_probability"]) for detail in details),
            default=0.0,
        ),
        "competence_gate_confirmed": graph_all,
    }


def _native_response_at_white_turn(
    board: chess.Board,
    parent: Mapping[str, TerminalAffordanceLearner],
    *,
    mate2_gate: OutcomeCalibratedCompetenceGate | None,
) -> dict[str, Any]:
    mate = parent["mate1"].choose(board)
    mate_positive = False
    if mate is not None and parent["mate1"].weight_for_move(board, mate) > 0.0:
        after_mate = board.copy(stack=False)
        after_mate.push(mate)
        mate_positive = after_mate.is_checkmate()
    first = parent["mate2_first"].choose(board)
    gate_probability = 0.0
    first_positive = False
    if first is not None and parent["mate2_first"].weight_for_move(board, first) > 0.0:
        features = policy_response_features(parent["mate2_first"], board)
        if mate2_gate is not None:
            gate_probability = mate2_gate.probability(features)
            first_positive = mate2_gate.confirms(features)
    if mate_positive and first_positive:
        response_type = "mate1_and_mate2_graph_positive"
    elif mate_positive:
        response_type = "mate1_graph_positive"
    elif first_positive:
        response_type = "mate2_first_graph_positive"
    else:
        response_type = "no_graph_positive_response"
    return {
        "graph_positive": bool(mate_positive or first_positive),
        "graph_response_type": response_type,
        "selected_mate1_move": None if mate is None else mate.uci(),
        "selected_mate2_first_move": None if first is None else first.uci(),
        "competence_gate_probability": gate_probability,
        "competence_gate_confirmed": first_positive,
    }


def _providers_for_types(response_types: tuple[str, ...]) -> tuple[str, ...]:
    useful = tuple(item for item in response_types if item != "no_graph_positive_response")
    if not useful:
        return ()
    # Any reply requiring Mate-in-2 makes Mate-in-2 the conservative provider.
    if any("mate2" in item for item in useful):
        return (MATE2_COMPETENCE_ID,)
    return (MATE1_COMPETENCE_ID,)


def _empty_native_response() -> dict[str, Any]:
    return {
        "graph_positive": False,
        "graph_all_reply": False,
        "graph_partial_reply": False,
        "graph_positive_reply_count": 0,
        "reply_total": 0,
        "graph_response_types": [],
        "provider_ids": [],
        "selected_mate1_move": None,
        "selected_mate2_first_move": None,
        "validator_consulted": False,
        "competence_gate_probability": 0.0,
        "competence_gate_confirmed": False,
    }


def policy_response_features(
    learner: TerminalAffordanceLearner,
    board: chess.Board,
) -> tuple[float, ...]:
    """Content-blind graph-response statistics consumed by the learned gate."""

    options = sorted(
        (
            learner.weight_for_move(board, move),
            move.uci(),
            learner.active_terminal_count(board, move),
        )
        for move in board.legal_moves
    )
    if not options:
        return (0.0, 0.0, 0.0, 0.0)
    selected_weight, _uci, active_count = options[-1]
    runner_up = options[-2][0] if len(options) > 1 else 0.0
    return (
        float(selected_weight),
        float(active_count),
        float(selected_weight - runner_up),
        float(selected_weight) / max(1.0, float(active_count)),
    )


def rollout_foundation_policy(
    start: chess.Board,
    parent: Mapping[str, TerminalAffordanceLearner],
    *,
    max_plies: int = 4,
) -> dict[str, Any]:
    """Observe the mature foundation's real bounded outcome without an oracle."""

    board = start.copy(stack=False)
    moves: list[str] = []
    for _ply in range(max(0, int(max_plies))):
        terminal = _raw_terminal_kind(board)
        if terminal is not None:
            return {"outcome": terminal, "success": terminal == "mate", "moves": moves}
        if board.turn == chess.WHITE:
            move = _foundation_policy_move(board, parent)
        else:
            move = _deterministic_black_reply(board)
        if move is None or move not in board.legal_moves:
            return {"outcome": "illegal", "success": False, "moves": moves}
        moves.append(move.uci())
        board.push(move)
    terminal = _raw_terminal_kind(board)
    outcome = terminal or "horizon"
    return {"outcome": outcome, "success": outcome == "mate", "moves": moves}


def _foundation_policy_move(
    board: chess.Board,
    parent: Mapping[str, TerminalAffordanceLearner],
) -> chess.Move | None:
    mate = parent["mate1"].choose(board)
    if mate is not None and mate in board.legal_moves:
        after = board.copy(stack=False)
        after.push(mate)
        if after.is_checkmate():
            return mate
    first = parent["mate2_first"].choose(board)
    return first if first is not None and first in board.legal_moves else None


def _deterministic_black_reply(board: chess.Board) -> chess.Move | None:
    replies = list(board.legal_moves)
    if not replies:
        return None
    ranked = []
    for move in replies:
        after = board.copy(stack=False)
        after.push(move)
        rook_missing = not bool(after.pieces(chess.ROOK, chess.WHITE))
        reply_mobility = after.legal_moves.count()
        ranked.append((int(rook_missing), reply_mobility, move.uci(), move))
    ranked.sort(reverse=True)
    return ranked[0][-1]


def _raw_terminal_kind(board: chess.Board) -> str | None:
    if board.is_checkmate():
        return "mate"
    if board.is_stalemate():
        return "stalemate"
    if not bool(board.pieces(chess.ROOK, chess.WHITE)):
        return "rook_loss"
    if board.is_insufficient_material():
        return "draw"
    return None


def fit_tg46d_mate2_competence_gate(
    m4_eval_path: str,
) -> OutcomeCalibratedCompetenceGate:
    """Fit on the old heldout split and validate once on old regression rows."""

    with gzip.open(m4_eval_path, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]
    train = [
        CompetenceGateExample(_eval_row_policy_features(row), bool(row["conversion"]))
        for row in rows
        if row.get("trace_type") == "m4_only_mate2_heldout"
    ]
    validation = [
        CompetenceGateExample(_eval_row_policy_features(row), bool(row["conversion"]))
        for row in rows
        if row.get("trace_type") == "m4_only_mate2_regression"
    ]
    return OutcomeCalibratedCompetenceGate.fit(
        TG46D_POLICY_FEATURE_NAMES,
        train,
        validation,
        CompetenceGateConfig(
            threshold=0.50,
            min_validation_true_positives=50,
            max_validation_false_positives=0,
            min_validation_precision=0.99,
        ),
    )


def _eval_row_policy_features(row: Mapping[str, Any]) -> tuple[float, ...]:
    candidates = list(row.get("top_competing_graph_candidates", ()))
    if not candidates:
        return (0.0, 0.0, 0.0, 0.0)
    selected = candidates[0]
    weight = float(selected["weight"])
    active = float(selected["active_terminal_count"])
    runner_up = float(candidates[1]["weight"]) if len(candidates) > 1 else 0.0
    return (weight, active, weight - runner_up, weight / max(1.0, active))


class KRKIntrinsicCredit:
    """Read-only restored TG46d value plus local episode-return calculation."""

    def __init__(
        self,
        artifact: Mapping[str, Any],
        config: KRKIntrinsicCreditConfig | None = None,
        *,
        mate2_gate: OutcomeCalibratedCompetenceGate | None = None,
    ) -> None:
        self.config = config or KRKIntrinsicCreditConfig()
        self.mate2_gate = mate2_gate
        self._native_response_cache: dict[str, dict[str, Any]] = {}
        self.artifact_provenance = {
            "schema_version": artifact.get("schema_version"),
            "config_hash": artifact.get("config_hash"),
            "graph_summary_hash": artifact.get("graph_summary_hash"),
        }
        intrinsic = IntrinsicCreditConfig(
            gamma=self.config.gamma,
            real_move_cost=self.config.real_move_cost,
            terminal_failure_value=self.config.terminal_failure_value,
            terminal_draw_value=self.config.terminal_draw_value,
            min_grounding_evidence=self.config.min_grounding_evidence,
            min_causal_confirmations=1,
        )
        self.engine = IntrinsicCreditEngine(intrinsic)
        mate1_rate = float(artifact["m4_only_mate1_regression_accuracy"])
        mate2_rate = min(
            float(artifact["m4_only_mate2_heldout_conversion"]),
            float(artifact["m4_only_mate2_regression_conversion"]),
        )
        self._restore_competence(
            MATE1_COMPETENCE_ID,
            expected_value=_expected_return(mate1_rate, intrinsic.terminal_failure_value),
            grounding_level=0,
            ancestors=set(),
        )
        self._restore_competence(
            MATE2_COMPETENCE_ID,
            expected_value=_expected_return(mate2_rate, intrinsic.terminal_failure_value),
            grounding_level=1,
            ancestors={MATE1_COMPETENCE_ID},
        )

    @classmethod
    def from_artifacts(
        cls,
        artifact: Mapping[str, Any],
        *,
        m4_eval_path: str,
        config: KRKIntrinsicCreditConfig | None = None,
    ) -> "KRKIntrinsicCredit":
        return cls(
            artifact,
            config,
            mate2_gate=fit_tg46d_mate2_competence_gate(m4_eval_path),
        )

    def native_response(
        self,
        board: chess.Board,
        parent: Mapping[str, TerminalAffordanceLearner] | None,
    ) -> dict[str, Any]:
        if parent is None:
            return _empty_native_response()
        key = board.fen()
        cached = self._native_response_cache.get(key)
        if cached is not None:
            return cached
        response = native_foundation_response(board, parent, mate2_gate=self.mate2_gate)
        self._native_response_cache[key] = response
        return response

    def _restore_competence(
        self,
        cell_id: str,
        *,
        expected_value: float,
        grounding_level: int,
        ancestors: set[str],
    ) -> None:
        state = self.engine.register(
            cell_id,
            mature=True,
            initial_fast_value=expected_value,
            initial_slow_value=expected_value,
        )
        if grounding_level == 0:
            state.terminal_evidence = self.config.min_grounding_evidence
        else:
            state.handoff_evidence = self.config.min_grounding_evidence
        state.causal_confirmations = 1
        state.grounding_level = grounding_level
        state.grounding_ancestors = set(ancestors)

    def episode_return(
        self,
        native_response: Mapping[str, Any],
        *,
        real_white_moves: int,
        terminal_kind: str | None = None,
    ) -> tuple[dict[str, float], float, dict[str, Any]]:
        """Return raw outcome + metabolic cost + mature-child bootstrap only."""

        moves = max(0, int(real_white_moves))
        move_cost = -self.config.real_move_cost * moves
        world_terminal = 0.0
        provider_ids: tuple[str, ...] = ()
        child_bootstrap = 0.0
        if terminal_kind is not None:
            world_terminal = self.engine.terminal_value(terminal_kind)
        elif bool(native_response.get("graph_all_reply")):
            provider_ids = tuple(map(str, native_response.get("provider_ids", ())))
            signal, _rejected = self.engine.successor_signal(provider_ids)
            if signal is not None:
                child_bootstrap = (self.config.gamma ** max(1, moves)) * signal.value
        total = max(-1.0, min(1.0, world_terminal + move_cost + child_bootstrap))
        channels = {
            "world_terminal": round(world_terminal, 6),
            "mature_child_bootstrap": round(child_bootstrap, 6),
            "real_move_metabolic_cost": round(move_cost, 6),
        }
        audit = {
            "provider_ids": list(provider_ids),
            "native_graph_response_used": bool(provider_ids),
            "validator_used_for_reward": False,
            "authored_geometry_shaping_used": False,
            "artifact_provenance": self.artifact_provenance,
        }
        return channels, round(total, 6), audit

    def snapshot(self) -> dict[str, Any]:
        return {
            "config": asdict(self.config),
            "artifact_provenance": self.artifact_provenance,
            "engine": self.engine.snapshot(),
            "mate2_competence_gate": None if self.mate2_gate is None else self.mate2_gate.to_dict(),
            "native_response_cache_entries": len(self._native_response_cache),
        }


def _expected_return(success_rate: float, failure_value: float) -> float:
    probability = max(0.0, min(1.0, float(success_rate)))
    return probability + (1.0 - probability) * float(failure_value)
