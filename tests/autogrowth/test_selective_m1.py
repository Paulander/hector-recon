"""Chess integration checks; planted expressions below are mechanical fixtures."""
import ast
import copy
from dataclasses import asdict, replace
import inspect
import pickle

import chess
import pytest

from recon_lite.graph import NodeState
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.interface import Feedback
from recon_lite_chess.coach.selective import STATE_COORDINATES, create_actor
from recon_lite_chess.coach.terminal import ChessFeaturePort, SCHEMA, TerminalOrganism
from recon_lite_hector.learning.owner_birth_search import BirthSearchConfig
from recon_lite_hector.learning.owner_development import OwnerDevelopmentConfig
from recon_lite_hector.learning.recursive_context import Expression, TRUE, combine
from recon_lite_hector.learning.terminal_development import Condition, DevelopmentConfig, PlasticWeight


M1 = "k7/8/1K6/8/8/8/8/7R w - - 0 1"
WIDE = "k7/8/8/8/3K4/8/4R3/8 w - - 0 1"


def small_actor(**kwargs):
    return create_actor(seed=71, search=BirthSearchConfig(mode="residual", candidates=4),
                        **kwargs)


@pytest.mark.parametrize("role", ("selective", "refining"))
def test_fresh_defaults_and_complete_declared_reader_pools(role):
    actor = create_actor(seed=71, role=role)
    assert actor.completed == actor.owner_visits[0] == 0
    assert actor.schema == SCHEMA and actor.state_coordinates == frozenset(STATE_COORDINATES)
    assert actor.slots == 1 and len(actor.leaves) == 1
    assert len(actor.conditions) == 1
    assert actor.base_expressions == {actor.leaves[0].bias_id: TRUE}
    assert all(float(condition.weight) == 0 for condition in actor.conditions.values())
    assert actor.graph.nodes["option:0"].meta["actuator_identity"] == "unbound"
    assert len(actor.owner_candidates) == 42 and len(actor.action_readers) == 38
    assert len(actor.birth_definitions) == 64
    assert {reader.atom for reader in actor.owner_candidates} == {
        (index, value) for index in STATE_COORDINATES for value in SCHEMA[index].values
    }
    assert all(reader.atom[0] not in STATE_COORDINATES for reader in actor.action_readers)
    assert actor.refinable == set() and not actor.refinement_history
    assert not actor.development_history and not actor.action_bud_history
    assert actor.reclosure_enabled is False and not actor.reclosure_history
    assert actor.development_config.split_enabled is False
    if role == "selective":
        assert actor.prospective_resource_cost == .25 and not actor.prospective_history
    actor._ensure_slots(22)  # KRK has at most eight king plus fourteen rook moves.
    actor.validate_ownership()
    assert len(actor.graph.nodes) < actor.ownership_limits.max_physical_nodes


def test_existing_knobs_and_ordinary_reference():
    config = DevelopmentConfig(learning_rate=.1, exploration=.4, max_conditions=64)
    actor = small_actor(config=config, development=OwnerDevelopmentConfig(develop_every=32))
    assert actor.config == config and actor.development_config.develop_every == 32
    assert actor.development_config.split_enabled is False
    reference = create_actor(role="ordinary", config=config)
    assert type(reference) is TerminalOrganism and reference.config is config
    assert reference.completed == 0 and not reference.conditions
    with pytest.raises(ValueError, match="role"):
        create_actor(role="unrecognized")
    with pytest.raises(ValueError, match="DevelopmentConfig only"):
        create_actor(role="ordinary", search=BirthSearchConfig())
    with pytest.raises(ValueError, match="resource cost"):
        small_actor(prospective_resource_cost=0)


def test_declared_state_measurements_are_binding_invariant():
    for fen in (M1, WIDE):
        port = ChessFeaturePort(chess.Board(fen))
        for index in STATE_COORDINATES:
            assert len({port.measure(index, binding) for binding in port.bindings()}) == 1


def test_chess_terminal_path_executes_and_grades_only_the_selected_move(monkeypatch):
    actor = small_actor(config=DevelopmentConfig(exploration=0))
    pushes, measurements, executions, receipts = [], [], [], []
    push, measure, execute = chess.Board.push, ChessFeaturePort.measure, ChessFeaturePort.execute
    observe = type(actor).observe

    def recorded_push(board, move):
        pushes.append(move.uci())
        return push(board, move)

    def recorded_measure(port, coordinate, binding):
        assert not executions
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        measurements.append((coordinate, binding))
        return measure(port, coordinate, binding)

    def recorded_execute(port, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_actuator"
        executions.append(binding)
        return execute(port, binding)

    def recorded_observe(learner, feedback):
        receipts.append(feedback)
        return observe(learner, feedback)

    monkeypatch.setattr(chess.Board, "push", recorded_push)
    monkeypatch.setattr(ChessFeaturePort, "measure", recorded_measure)
    monkeypatch.setattr(ChessFeaturePort, "execute", recorded_execute)
    monkeypatch.setattr(type(actor), "observe", recorded_observe)
    attempt = play_mate_one(actor, M1, event_id=8, learn=True)
    assert measurements and pushes == executions == [attempt.action]
    assert receipts == [Feedback(8, attempt.action, attempt.reward)]
    assert set(asdict(receipts[0])) == {"event_id", "action", "reward"}
    assert attempt.reward == (1 if chess.Board(attempt.after_fen).is_checkmate() else -1)
    assert actor.completed == 1 and not actor.pending and actor.action_bud_pending is None


def test_dynamic_bindings_disable_unused_slots_without_learning():
    actor = small_actor()
    original = copy.deepcopy(actor.conditions)
    counts = []
    for fen in (M1, WIDE, M1):
        board = chess.Board(fen)
        legal = {move.uci() for move in board.legal_moves}
        port = ChessFeaturePort(board)
        counts.append(len(legal))
        action = actor.act(port, event_id=0, learn=False)
        assert action in legal and action == port.executed
        for slot in range(len(legal), actor.slots):
            assert actor.graph.nodes[f"option:{slot}"].state == NodeState.FAILED
    assert counts[0] < counts[1] and counts[2] == counts[0]
    assert actor.slots == max(counts) and actor.conditions == original and actor.completed == 0


def test_feedback_binding_and_checkpoint_preserve_subsequent_credit_and_growth():
    actor = small_actor(development=OwnerDevelopmentConfig(develop_every=2))
    port = ChessFeaturePort(chess.Board(M1))
    action = actor.act(port, event_id=0, learn=True)
    with pytest.raises(ValueError, match="matching actual action"):
        actor.observe(Feedback(0, "wrong-binding", -1))
    with pytest.raises(RuntimeError, match="checkpoint"):
        pickle.dumps(actor)
    actor.observe(Feedback(0, action, 1. if port._board.is_checkmate() else -1.))
    restored = pickle.loads(pickle.dumps(actor))
    for event, fen in enumerate((WIDE, M1, WIDE), start=1):
        first = play_mate_one(actor, fen, event_id=event, learn=True)
        second = play_mate_one(restored, fen, event_id=event, learn=True)
        assert first == second
        assert actor.conditions == restored.conditions
        assert actor.development_history == restored.development_history
        assert actor.action_bud_evidence == restored.action_bud_evidence
        assert actor.prospective_discovery == restored.prospective_discovery
        assert actor.exploration_rng.getstate() == restored.exploration_rng.getstate()
    assert len(actor.development_history) == 2 and len(actor.conditions) > 1
    assert not actor.reclosure_history


def test_test_planted_refinement_preserves_every_chess_option_score():
    actor = small_actor()
    expression = combine("and", (Expression("read", atom=(0, True)),
                                 Expression("read", atom=(1, True))))
    cid = actor.next_condition
    actor.next_condition += 1
    actor.conditions[cid] = Condition(cid, (), "and", 0, weight=PlasticWeight(fast=.7))
    actor.base_expressions[cid] = expression
    actor.birth_visits[cid] = 0
    actor.owner_seen[0].add(expression)
    actor.leaves[0] = replace(actor.leaves[0], contributions=(*actor.leaves[0].contributions, cid))
    actor.refinable.add(cid)
    actor.refinement_evidence[cid] = {}
    actor._rebuild(actor.slots)

    def scores(learner):
        result = []
        for fen in (M1, WIDE):
            clone = copy.deepcopy(learner)
            port = ChessFeaturePort(chess.Board(fen))
            bindings = port.bindings()
            clone.act(port, event_id=0, learn=False)
            result.append(tuple(clone.graph.nodes[f"option:{slot}"].activation.value
                                for slot in range(len(bindings))))
        return result

    before = scores(actor)
    event = actor._refine_local(0, cid, Expression("read", atom=(2, 1)))
    assert scores(actor) == before and len(actor.leaves) == 1
    assert cid not in actor.conditions
    assert all(float(actor.conditions[child].weight) == .7 for child in event["children"])
    assert len({id(actor.conditions[child].weight) for child in event["children"]}) == 2
    assert not actor.reclosure_history
    actor.validate_ownership()


def test_generic_learner_inheritance_has_no_chess_import():
    actor = small_actor()
    modules = {inspect.getmodule(cls) for cls in type(actor).__mro__
               if cls.__module__.startswith("recon_lite_hector.learning")}
    assert modules
    for module in modules:
        for node in ast.walk(ast.parse(inspect.getsource(module))):
            names = ([alias.name for alias in node.names] if isinstance(node, ast.Import)
                     else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            assert all(name != "chess" and not name.startswith("chess.")
                       and not name.startswith("recon_lite_chess") for name in names)
