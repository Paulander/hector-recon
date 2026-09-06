"""Mechanism fixtures may supply truth tables; chess learning receives no answers."""
from dataclasses import asdict
import inspect
import itertools
import pickle

import chess
import pytest

from recon_lite.graph import NodeState, NodeType
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.interface import Feedback
from recon_lite_chess.coach.terminal import ChessFeaturePort, TerminalOrganism
from recon_lite_hector.learning.terminal_development import Coordinate, DevelopmentConfig, TerminalDevelopment
from recon_lite_hector.learning.residual_shadow import (
    Definition, ResidualEvidence, ShadowConfig, ShadowDevelopment, random_definitions,
)

BOOL = (False, True)


class Port:
    schema = tuple(Coordinate(name, BOOL) for name in ("x", "y", "action"))

    def __init__(self, x=False, y=False, names=("a", "b")):
        self.values = (x, y)
        self.names = names
        self.executed = None
        self.reads = []

    def bindings(self):
        assert inspect.currentframe().f_back.f_code.co_name == "_catalog"
        return self.names

    def measure(self, index, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        assert self.executed is None
        self.reads.append((index, binding))
        return (*self.values, binding == self.names[1])[index]

    def execute(self, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_actuator"
        assert self.executed is None
        self.executed = binding


def actor_state(o):
    return (asdict(o.config), asdict(o.bias), [asdict(c) for c in o.conditions.values()],
            o.completed, o.last_event, o.pending, o.next_condition, o.pruned,
            o.rng.getstate(), o.retired_conditions)


def make(seed=1):
    return ShadowDevelopment(seed=seed, config=DevelopmentConfig(max_conditions=6),
                             shadow_config=ShadowConfig(candidates=12, discovery_episodes=16, min_support=2))


def step(o, event, reward=1, port=None):
    action = o.act(port or Port(bool(event % 2), bool(event % 3)), event_id=event, learn=True)
    o.observe(Feedback(event, action, reward))
    return action


def test_generic_random_pool_is_deterministic_finite_and_canonical():
    plan = random_definitions(Port.schema, seed=1, count=12)
    assert plan == random_definitions(Port.schema, seed=1, count=12)
    assert len(set(plan)) == 12
    for d in plan:
        d.validate(Port.schema)
    assert any(len(d.atoms) > 1 for d in plan)
    with pytest.raises(ValueError, match="no silent truncation"):
        random_definitions((Coordinate("x", BOOL),), seed=1, count=3)
    with pytest.raises(ValueError, match="active and inactive"):
        ShadowConfig(discovery_episodes=2)
    with pytest.raises(ValueError, match="typed domain"):
        Definition("and", ((0, 1),)).validate(Port.schema)


def test_isolated_shadows_leave_actions_actor_learning_and_rng_identical():
    shadow = make()
    plain = TerminalDevelopment(seed=1, config=shadow.config)
    for event in range(40):
        actions = [step(o, event, 1 if event % 3 else -1) for o in (plain, shadow)]
        assert actions[0] == actions[1]
        assert actor_state(plain) == actor_state(shadow)
    assert shadow.shadow.observations == 40
    for edge in shadow.graph.edges:
        assert edge.src.startswith("shadow:") == edge.dst.startswith("shadow:")
    assert all(not shadow.graph.children(nid) for nid, n in shadow.graph.nodes.items()
               if n.ntype == NodeType.TERMINAL)
    shadow.graph.validate_formal_pairs()


@pytest.mark.parametrize("operator,truth", [
    ("and", (False, False, False, True)), ("or", (False, True, True, True)),
    ("xor", (False, True, True, False)),
])
def test_shadow_boolean_values_come_from_formal_composition(operator, truth):
    o = ShadowDevelopment(shadow_config=ShadowConfig(candidates=1, discovery_episodes=8, min_support=2),
                          definitions=(Definition(operator, ((0, True), (1, True))),))
    for event, ((x, y), expected) in enumerate(zip(itertools.product(BOOL, repeat=2), truth)):
        port = Port(x, y)
        action = o.act(port, event_id=event, learn=True)
        assert o.shadow_pending.active == (expected,)
        assert (o.graph.nodes["shadow:gate:0"].state == NodeState.CONFIRMED) == expected
        o.observe(Feedback(event, action, 1))


def test_joint_nomination_needs_no_marginal_atom_usefulness():
    definitions = (Definition("and", ((0, True),)), Definition("and", ((1, True),)),
                   Definition("xor", ((0, True), (1, True))),
                   Definition("xor", ((0, True), (2, True))))
    book = ResidualEvidence(definitions, seed=1,
                            config=ShadowConfig(candidates=4, discovery_episodes=16, min_support=2))
    for event, (x, y, z) in enumerate(list(itertools.product(BOOL, repeat=3)) * 2):
        ticket = book.commit(event, "opaque", 0.0, (x, y, x != y, x != z))
        book.observe(ticket, 1 if x != y else -1, live=set())
    assert book.evidence[0].residual_sum == book.evidence[1].residual_sum == 0
    assert book.nomination["ranked"] == 2
    assert book.nomination["random_pool"] == (2, 3)
    assert book.nomination["ranked_support"] == book.nomination["random_support"] == 8
    assert book.prospective["count"] == 0  # Discovery outcomes never counted again.
    decision = dict(book.nomination)
    ticket = book.commit(16, "opaque", 0.0, (False, True, True, False))
    old_weight = book.evidence[2].weight
    book.observe(ticket, -1, live=set())
    assert book.prospective["ranked_squared_error"] == pytest.approx((-1 - old_weight) ** 2)
    assert book.evidence[2].weight != old_weight
    assert book.prospective["ranked_squared_error"] > book.prospective["base_squared_error"]
    assert book.nomination == decision  # A bad future outcome cannot rewrite nomination.


def test_sparse_or_live_candidates_cannot_fake_a_matched_pair():
    defs = (Definition("and", ((0, True),)), Definition("and", ((1, True),)))
    for live in (set(), set(defs)):
        book = ResidualEvidence(defs, seed=1,
                                config=ShadowConfig(candidates=2, discovery_episodes=8, min_support=2))
        for event in range(8):
            # First case is constant and unsupported off-state; second excludes live definitions.
            bits = (True, True) if not live else (bool(event % 2), bool(event % 2))
            book.observe(book.commit(event, "a", 0, bits), 1, live=live)
        assert book.nomination_status == "no_matched_pair"
        assert book.nomination is None and book.prospective["count"] == 0


def test_random_control_can_select_winner_and_does_not_depend_on_reward():
    defs = (Definition("and", ((0, True),)), Definition("and", ((1, True),)))
    selected = set()
    for seed in range(12):
        books = [ResidualEvidence(defs, seed=seed,
                  config=ShadowConfig(candidates=2, discovery_episodes=8, min_support=2)) for _ in range(2)]
        for event in range(8):
            bits = (bool(event % 2), bool((event // 2) % 2))
            for book, direction in zip(books, (1, -1)):
                book.observe(book.commit(event, "a", 0, bits), direction * (1 if bits[0] else -1), live=set())
        assert books[0].nomination["random"] == books[1].nomination["random"]
        selected.add(books[0].nomination["random"])
    assert selected == {0, 1}


def test_same_terminal_history_different_outcomes_changes_ranked_nomination():
    defs = (Definition("and", ((0, True),)), Definition("and", ((1, True),)))
    books = [ResidualEvidence(defs, seed=1,
             config=ShadowConfig(candidates=2, discovery_episodes=8, min_support=2)) for _ in range(2)]
    for event in range(8):
        bits = (bool(event % 2), bool((event // 2) % 2))
        for target, book in enumerate(books):
            book.observe(book.commit(event, "a", 0, bits), 1 if bits[target] else -1, live=set())
    assert [book.nomination["ranked"] for book in books] == [0, 1]
    assert books[0].nomination["random"] == books[1].nomination["random"]


def test_stale_invalid_early_and_delayed_feedback_cannot_mutate_evidence():
    o = make()
    with pytest.raises(RuntimeError, match="awaiting"):
        o.observe(Feedback(0, "a", 1))
    action = o.act(Port(), event_id=0, learn=True)
    before = o.shadow.report(), actor_state(o)
    for feedback in (Feedback(1, action, 1), Feedback(0, "wrong", 1), Feedback(0, action, float("nan"))):
        with pytest.raises(ValueError):
            o.observe(feedback)
        assert (o.shadow.report(), actor_state(o)) == before
    with pytest.raises(RuntimeError, match="each actual action"):
        o.act(Port(), event_id=1, learn=True)
    with pytest.raises(RuntimeError, match="outcome"):
        pickle.dumps(o)
    o.observe(Feedback(0, action, 1))
    with pytest.raises(RuntimeError):
        o.observe(Feedback(0, action, 1))


def test_pickle_before_and_after_nomination_preserves_future_evidence():
    o = make()
    for event in range(12):
        step(o, event)
    restored = pickle.loads(pickle.dumps(o))
    for event in range(12, 36):
        if event == 20:
            restored = pickle.loads(pickle.dumps(restored))
        assert step(o, event, -1) == step(restored, event, -1)
        assert o.shadow.report() == restored.shadow.report()
        assert actor_state(o) == actor_state(restored)


def test_evaluation_never_creates_or_updates_shadow_learning():
    o = make()
    o.act(Port(), event_id=0, learn=False)
    assert o.shadow is None
    for event in range(20):
        step(o, event)
    before = o.shadow.report(), actor_state(o)
    for event in range(5):
        o.act(Port(), event_id=event, learn=False)
    assert (o.shadow.report(), actor_state(o)) == before


def test_chess_shadow_reads_only_selected_binding_before_one_real_actuator(monkeypatch):
    class Organism(ShadowDevelopment):
        embodiment = "typed_feature_terminals_v1"
    o = Organism(config=DevelopmentConfig(max_conditions=6),
                 shadow_config=ShadowConfig(candidates=12, discovery_episodes=8, min_support=2))
    plain = TerminalOrganism(config=o.config)
    original_measure = ChessFeaturePort.measure
    reads, pushes = [], []
    def measure(port, index, binding):
        frame = inspect.currentframe().f_back
        assert frame.f_code.co_name == "_reader"
        if frame.f_locals["node"].nid.startswith("shadow:"):
            reads.append(binding)
        return original_measure(port, index, binding)
    original_push = chess.Board.push
    def push(board, move):
        pushes.append(move.uci())
        return original_push(board, move)
    monkeypatch.setattr(ChessFeaturePort, "measure", measure)
    monkeypatch.setattr(chess.Board, "push", push)
    fen = "k7/8/1K6/8/8/8/8/7R w - - 0 1"
    for event in range(10):
        reads.clear()
        a = play_mate_one(o, fen, event_id=event, learn=True)
        assert reads and set(reads) == {a.action}
        b = play_mate_one(plain, fen, event_id=event, learn=True)
        assert a.action == b.action and a.reward == b.reward
        assert actor_state(o) == actor_state(plain)
    assert len(pushes) == 20
