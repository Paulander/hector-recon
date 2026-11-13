"""A supplied Setup then M1 exercise for training one owned chess skill."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass

import chess

from recon_lite_chess.autogrowth.mate_horizon_opponent import choose_mate_horizon_reply
from recon_lite_hector.learning.context_decision import OwnershipLimits
from recon_lite_hector.learning.owner_birth_search import BirthSearchConfig
from recon_lite_hector.learning.owner_development import OwnerDevelopmentConfig
from recon_lite_hector.learning.refining_route_action import (
    ProspectiveRefiningRouteActionDevelopment,
)
from recon_lite_hector.learning.terminal_development import DevelopmentConfig

from .interface import Feedback
from .m2_schema import (
    M1_SCHEMA_VERSION, M2_SCHEMA, M2_SCHEMA_VERSION, M2ChessFeaturePort, schema_version,
)
from .selective import STATE_COORDINATES
from .terminal import ChessFeaturePort


@dataclass(frozen=True)
class PracticeMove:
    role: str
    action: str
    before_fen: str
    after_fen: str


@dataclass(frozen=True)
class SetupFrame:
    event_id: int
    action: str
    owner: int
    prediction: float
    active: tuple[int, ...]
    candidate_observations: tuple[bool, ...]
    action_reader_observations: tuple[bool, ...]
    action_reader_variable: tuple[bool, ...]
    refinement_active: tuple[int, ...]
    birth_observations: tuple[bool, ...]


@dataclass(frozen=True)
class SetupMenu:
    """Logged scores after subtracting the exploration boost, with float roundoff."""

    bindings: int
    boost_subtracted_min: float
    boost_subtracted_max: float

    @property
    def score_spread(self):
        return self.boost_subtracted_max - self.boost_subtracted_min


# Condition identity, fast weight, slow weight. Active identities include bias.
WeightSnapshot = tuple[tuple[int, float, float], ...]


@dataclass(frozen=True)
class SetupCredit:
    feedback: Feedback
    multiplier: float
    residual: float
    weights_before: WeightSnapshot
    weights_after: WeightSnapshot


@dataclass(frozen=True)
class SetupDevelopment:
    owner: int
    visit: int
    retired: tuple[int, ...]
    born: int | None
    bud: int | None
    refined: tuple[int, tuple[int, ...]] | None
    prospective_reviews: tuple[tuple[int, str], ...]
    prospective_nominations: tuple[int, ...]


@dataclass(frozen=True)
class SetupPracticeEpisode:
    event_id: int
    moves: tuple[PracticeMove, ...]
    outcome: str
    reward: float
    menu: SetupMenu
    frame: SetupFrame | None
    credit: SetupCredit | None
    completed_before: int
    completed_after: int
    development: tuple[SetupDevelopment, ...]


class SetupPracticeError(RuntimeError):
    """Execution stopped before an outcome receipt, with the committed prefix."""

    def __init__(self, event_id, stage, moves, board, cause):
        super().__init__(f"{stage} failed during Setup practice event {event_id}: {cause}")
        self.event_id = event_id
        self.stage = stage
        self.moves = tuple(moves)
        self.last_fen = board.fen()


@dataclass
class _CreditCapture:
    feedback: Feedback
    multiplier: float
    weights_before: WeightSnapshot
    result: SetupCredit | None = None


class _PracticeSetupPort(M2ChessFeaturePort):
    menu: SetupMenu


class SetupPracticeActor(ProspectiveRefiningRouteActionDevelopment):
    """The existing owner learner with a weight multiplier for its actual finish."""

    def _weight_credit_multiplier(self):
        capture = getattr(self, "_practice_capture", None)
        return 1.0 if capture is None else capture.multiplier

    def _before_execute(self, engine, env, *, event_id, slot, prediction, learn):
        port = env["port"]
        if isinstance(port, _PracticeSetupPort):
            count = len(env["bindings"])
            exploration = env["exploration"]
            scores = tuple(self.graph.nodes[f"option:{i}"].activation.value
                           - exploration.get(i, 0.0) for i in range(count))
            port.menu = SetupMenu(count, min(scores), max(scores))
        super()._before_execute(engine, env, event_id=event_id, slot=slot,
                                prediction=prediction, learn=learn)

    def _record_nomination_outcome(self, owner, action, residual, observations):
        capture = getattr(self, "_practice_capture", None)
        if capture is not None:
            # The owner has applied credit and any scheduled bias consolidation.
            # Development still waits for the selected-action evidence to close.
            active = (cid for cid, _, _ in capture.weights_before)
            capture.result = SetupCredit(capture.feedback, capture.multiplier, residual,
                                         capture.weights_before, self._weights(active))
        super()._record_nomination_outcome(owner, action, residual, observations)

    def _weights(self, active):
        return tuple((cid, self.conditions[cid].weight.fast,
                      self.conditions[cid].weight.slow) for cid in active)

    def _credit_practice(self, feedback, *, finisher_committed):
        if (type(feedback) is not Feedback or type(feedback.event_id) is not int
                or type(feedback.action) is not str or type(feedback.reward) is not float
                or feedback.reward not in (-1.0, 1.0)):
            raise ValueError("practice requires a bound event, action and signed outcome")
        if len(self.pending) != 1 or self.pending[0][:2] != (feedback.event_id, feedback.action):
            raise ValueError("practice outcome does not bind to the pending Setup action")
        if type(finisher_committed) is not bool:
            raise ValueError("finisher commit must be explicit")
        multiplier = self.config.eligibility_decay if finisher_committed else 1.0
        capture = _CreditCapture(feedback, multiplier, self._weights(self.pending[0][3]))
        self._practice_capture = capture
        try:
            self.observe(feedback)
        finally:
            self.__dict__.pop("_practice_capture", None)
        if capture.result is None:
            raise RuntimeError("Setup credit did not close through the owner learner")
        return capture.result


def create_setup_actor(*, seed):
    """Create a fresh Setup owner with the October modular pilot's parameters."""
    return SetupPracticeActor.create(
        schema=M2_SCHEMA, state_coordinates=STATE_COORDINATES, seed=seed,
        config=DevelopmentConfig(),
        limits=OwnershipLimits(max_leaves=1, max_parameters=96, max_definitions=512,
                               max_physical_nodes=32768),
        search=BirthSearchConfig(mode="residual", candidates=64),
        development=OwnerDevelopmentConfig(split_enabled=False, candidates=42,
                                           develop_every=64, min_support=4),
        reclosure_enabled=False, prospective_resource_cost=.25,
    )


def _start(fen):
    board = chess.Board(fen)
    if (len(board.piece_map()) != 3 or not board.is_valid() or board.turn != chess.WHITE
            or len(board.pieces(chess.ROOK, chess.WHITE)) != 1
            or board.is_game_over(claim_draw=True)):
        raise ValueError("Setup practice requires a live legal White-to-move KRK position")
    return board


def _terminal(board):
    if board.is_checkmate():
        return "checkmate" if board.turn == chess.BLACK else "lost"
    if not board.pieces(chess.ROOK, chess.WHITE):
        return "rook_captured"
    if board.is_stalemate():
        return "stalemate"
    if board.is_game_over(claim_draw=True):
        return "draw"
    return None


def _white_move(actor, board, port, role, *, event_id, learn):
    before = board.fen()
    ply = len(board.move_stack)
    action = actor.act(port, event_id=event_id, learn=learn)
    if (action is None or action != port.executed or len(board.move_stack) != ply + 1
            or board.peek().uci() != action):
        raise RuntimeError(f"{role} must commit one selected move through its actuator")
    return PracticeMove(role, action, before, board.fen())


def _setup_frame(actor):
    event_id, action, prediction, active = actor.pending[0]
    owner = actor.owner_pending[2]
    bud = actor.action_bud_pending
    return SetupFrame(event_id, action, owner, prediction, active,
                      actor.candidate_pending[4], bud[4], bud[5], bud[6],
                      actor.birth_search_pending[4])


def _development(record):
    refinement = record["refinement"]
    bud = record["bud"]
    return SetupDevelopment(
        record["owner"], record["local_visit"], tuple(record["retired"]),
        record["birth"] if bud is None else None, bud["condition"] if bud is not None else None,
        (refinement["parent"], tuple(refinement["children"])) if refinement else None,
        tuple((review["condition"], review["decision"])
              for review in record["prospective_reviews"]),
        tuple(nomination["condition"] for nomination in record["prospective_nominations"]),
    )


def play_setup_practice(setup, finisher, fen, *, event_id, learn,
                        opponent=choose_mate_horizon_reply):
    """Play one supplied exercise using a live Setup actor and a frozen M1 copy.

    The environment chooses one legal reply after the actual first move. The
    outcome is actual mate (+1) or a terminal stop or two-move timeout (-1).
    An execution error raises before issuing a receipt. A failed episode may
    leave an unresolved action and requires recovery from a completed state.
    Evaluation is greedy and uses disposable copies of both actors.
    """
    if type(event_id) is not int or event_id < 0 or type(learn) is not bool:
        raise ValueError("practice requires a nonnegative event ID and explicit learning mode")
    if not isinstance(setup, SetupPracticeActor) or schema_version(setup.schema) != M2_SCHEMA_VERSION:
        raise ValueError("practice requires a Setup actor with the declared M2 port")
    if (not isinstance(finisher, ProspectiveRefiningRouteActionDevelopment)
            or schema_version(finisher.schema) != M1_SCHEMA_VERSION):
        raise ValueError("practice requires a finisher with the declared M1 port")
    # Existing checkpoint guards also reject unresolved local evidence frames.
    setup.__getstate__()
    finisher.__getstate__()
    if learn and event_id <= setup.last_event:
        raise ValueError("Setup action event must increase")
    board = _start(fen)
    if not learn:
        setup = deepcopy(setup)
    completed = setup.completed
    development_count = len(setup.development_history)

    stage = "setup"
    moves = []
    try:
        setup_port = _PracticeSetupPort(board)
        first = _white_move(setup, board, setup_port, "setup",
                            event_id=event_id, learn=learn)
        moves.append(first)
        frame = _setup_frame(setup) if learn else None
        outcome = _terminal(board)
        finisher_committed = False
        if outcome is None:
            stage = "black"
            reply = opponent(board.copy(stack=True))
            if not isinstance(reply, chess.Move) or reply not in board.legal_moves:
                raise ValueError("opponent must return one legal Black move")
            before = board.fen()
            board.push(reply)
            moves.append(PracticeMove("black", reply.uci(), before, board.fen()))
            outcome = _terminal(board)
            if outcome is None:
                stage = "m1"
                moves.append(_white_move(deepcopy(finisher), board, ChessFeaturePort(board), "m1",
                                         event_id=event_id, learn=False))
                finisher_committed = True
                outcome = _terminal(board) or "exercise_timeout"
    except Exception as error:
        raise SetupPracticeError(event_id, stage, moves, board, error) from error
    reward = 1.0 if outcome == "checkmate" else -1.0
    credit = (setup._credit_practice(Feedback(event_id, first.action, reward),
                                    finisher_committed=finisher_committed)
              if learn else None)
    return SetupPracticeEpisode(
        event_id, tuple(moves), outcome, reward, setup_port.menu, frame, credit, completed,
        setup.completed, tuple(map(_development, setup.development_history[development_count:])),
    )
