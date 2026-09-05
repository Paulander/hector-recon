"""Opaque adapter around the existing native ReCoN learner.

The coach never sees the native decision, its graph, or its imagined states.
This adapter deliberately does not claim to replace the legacy score-construction
path with a fully persistent in-graph selector. It keeps the existing feature
vocabulary and known chess transition model explicit (see MATE_ONE_COACH.md).
"""

from dataclasses import dataclass
import math

import chess

from recon_lite_chess.autogrowth.native_single_graph_curriculum import (
    LOCAL_EXPLORATION_FINITE_UCB, NativeReConKRKGraph, NativeSingleGraphConfig,
)
from recon_lite_hector.learning.intrinsic_credit import (
    IntrinsicCreditConfig, IntrinsicCreditEngine, Responsibility,
)

from .interface import BoardSensor, Feedback


@dataclass(frozen=True)
class NativeConfig:
    consolidation_every: int = 256

    def __post_init__(self) -> None:
        if self.consolidation_every < 1:
            raise ValueError("consolidation_every must be positive")


class NativeOrganism:
    """Own action choice, generated triplets, M3, and local slow-value memory."""

    def __init__(self, config: NativeConfig | None = None):
        self.config = config or NativeConfig()
        self._graph = NativeReConKRKGraph(config=NativeSingleGraphConfig(
            include_symmetries=False, max_ticks=32, key_mode="canonical",
            shared_feature_atoms=True, shared_projection_atoms=False,
            include_grouped_cache_terminals=False,
            score_action_pattern_atoms=False, score_hierarchy_edge_weights=False,
            terminal_score_normalization="mean",
            local_exploration_mode=LOCAL_EXPLORATION_FINITE_UCB,
        ))
        self._credit = IntrinsicCreditEngine(IntrinsicCreditConfig(
            eta_fast=self._graph.config.eta_m3,
            real_move_cost=0.0,  # The exercise already ends after one own move.
        ))
        self._pending = None
        self._last_event_id = -1
        self._observations = 0
        self._consolidations = 0

    def __getstate__(self):
        if self._pending is not None:
            raise RuntimeError("cannot checkpoint between action and feedback")
        return self.__dict__

    def act(self, sensor: BoardSensor, *, event_id: int, learn: bool) -> str | None:
        if self._pending is not None:
            raise RuntimeError("previous action has no committed real feedback")
        if learn and event_id <= self._last_event_id:
            raise ValueError("training event IDs must be strictly increasing")
        measured = sensor.measure()
        # This is the organism's private rules-model state, not the live board.
        board = chess.Board(None)
        for square, piece_type, color in measured.pieces:
            board.set_piece_at(square, chess.Piece(piece_type, color))
        board.turn = measured.white_to_move
        board.halfmove_clock = measured.halfmove_clock
        # Fullmove numbering is diagnostic, not a learned feature or a new event.
        board.fullmove_number = 1
        if not board.is_valid():
            raise ValueError("invalid measured board")
        if learn:
            decision = self._graph.choose_local_training_action(board, "real")
            self._pending = (event_id, board, decision)
        else:
            decision = self._graph.choose_local_policy_action(board)
        return None if decision is None else decision.move_uci

    def observe(self, feedback: Feedback) -> None:
        if self._pending is None:
            raise RuntimeError("feedback has no pending selected action")
        event_id, board, decision = self._pending
        if feedback.event_id != event_id or feedback.action != decision.move_uci:
            raise ValueError("feedback does not match the selected action")
        if not math.isfinite(feedback.reward) or feedback.reward not in (-1.0, 1.0):
            raise ValueError("mate-one exercise reward must be -1 or +1")
        # Pattern aliases can represent multiple actuators. Their evidence must
        # remain separate, just like NativeReConKRKGraph's per-actuator Q maps.
        identity = decision.triplet_id + ":" + decision.move_uci
        state = self._credit.register(identity, hierarchy_depth=0)
        self._credit.begin_episode()
        # The graph owns Q. Initialize the credit mirror from that same Q so
        # consolidation cannot mistake a sum of TD corrections for a value.
        state.fast_value = decision.prediction
        event = self._credit.transition(
            identity, responsibilities=(Responsibility(identity),),
            terminal_value=feedback.reward, prediction_override=decision.prediction,
        )
        self._graph.apply_intrinsic_td(
            board, decision.move, td_error=event.td_error,
            prediction_value=decision.prediction, stage_diagnostic="real",
        )
        self._observations += 1
        if self._observations % self.config.consolidation_every == 0:
            # Local REAL evidence, no validation score and no coach approval.
            # This prepares slow child-value memory; it does not freeze policy,
            # assert dataset mastery, or causally promote a structural candidate.
            self._credit.consolidate_direct_outcome_providers(tuple(self._credit.states))
            self._consolidations += 1
        self._last_event_id = event_id
        self._pending = None
