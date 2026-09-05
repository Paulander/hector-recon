"""Mechanism tests: test-side labels never become organism inputs."""
from dataclasses import asdict
import inspect
import itertools
import pickle
import random

import chess
import pytest

from recon_lite.graph import LinkType, NodeState, NodeType
from recon_lite_chess.coach.interface import Feedback
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.terminal import ChessFeaturePort, TerminalOrganism
from recon_lite_hector.learning.terminal_development import (
    Condition, Coordinate, DevelopmentConfig, PlasticWeight, TerminalDevelopment,
)

BOOL = (False, True)
M1 = "k7/8/1K6/8/8/8/8/7R w - - 0 1"


class BooleanPort:
    schema = tuple(Coordinate(name, BOOL) for name in ("x", "y", "action"))

    def __init__(self, x=False, y=False, *, names=("left", "right")):
        self.values = (x, y)
        self.names = names
        self.executed = None
        self.reads = []

    def bindings(self):
        assert inspect.currentframe().f_back.f_code.co_name == "_catalog"
        return self.names

    def measure(self, coordinate, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        self.reads.append((coordinate, binding))
        return (*self.values, binding == self.names[1])[coordinate]

    def execute(self, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_actuator"
        assert self.executed is None
        assert binding in self.names
        self.executed = binding


# Tests may plant topology to isolate a primitive. The XOR learning test below
# deliberately does not use this helper or plant readers/weights/structures.
def attach(organism, atoms, *, weight=0.0, operator="and"):
    cid = organism.next_condition
    organism.next_condition += 1
    c = Condition(cid, tuple(atoms), operator, organism.completed,
                  weight=PlasticWeight(fast=weight))
    organism.conditions[cid] = c
    for slot in range(organism.slots):
        organism._add_condition_slot(c, slot)
    return c


def learned_state(organism):
    return {
        "schema": organism.schema,
        "config": asdict(organism.config),
        "bias": asdict(organism.bias),
        "conditions": [(cid, asdict(c)) for cid, c in organism.conditions.items()],
        "completed": organism.completed,
        "next_condition": organism.next_condition,
        "pruned": organism.pruned,
        "pending": organism.pending,
        "last_event": organism.last_event,
        "rng": organism.rng.getstate(),
    }


def test_heterogeneous_domains_and_sparse_reading_boundary():
    schema = (Coordinate("flag", BOOL), Coordinate("even", (0, 2, 4, 6)), Coordinate("unused", BOOL))
    class Port(BooleanPort):
        def measure(self, coordinate, binding):
            assert inspect.currentframe().f_back.f_code.co_name == "_reader"
            assert coordinate == 1  # An unread coordinate cannot influence policy.
            return 2 if binding == "left" else 4
    Port.schema = schema
    organism = TerminalDevelopment(config=DevelopmentConfig(exploration=0))
    organism.schema = schema
    attach(organism, ((1, 2),), weight=1)
    before_rng = organism.rng.getstate()
    for irrelevant in (False, True):
        port = Port(y=irrelevant)
        assert organism.act(port, event_id=0, learn=False) == "left"
    assert organism.rng.getstate() == before_rng
    with pytest.raises(ValueError, match="typed domain"):
        schema[1].validate(3)
    with pytest.raises(ValueError, match="typed domain"):
        schema[0].validate(1)


@pytest.mark.parametrize("operator,truth", [
    ("and", (False, False, False, True)),
    ("or", (False, True, True, True)),
    ("xor", (False, True, True, False)),
])
def test_formal_boolean_compositions_and_negated_readers(operator, truth):
    organism = TerminalDevelopment(config=DevelopmentConfig(exploration=0))
    organism.schema = BooleanPort.schema
    c = attach(organism, ((0, False), (1, False)), operator=operator)
    for i, (x, y) in enumerate(itertools.product(BOOL, repeat=2)):
        # Input equality to False is a learned terminal's Boolean negation.
        organism.act(BooleanPort(not x, not y), event_id=0, learn=False)
        assert (organism.graph.nodes[f"gate:0:{c.identity}"].state == NodeState.CONFIRMED) == truth[i]
    organism.graph.validate_formal_pairs()
    assert all(not organism.graph.children(nid) for nid, n in organism.graph.nodes.items()
               if n.ntype == NodeType.TERMINAL)


def test_graph_edges_drive_choice_and_failed_conditions_do_not_contribute():
    organism = TerminalDevelopment(config=DevelopmentConfig(exploration=0))
    organism.schema = BooleanPort.schema
    c = attach(organism, ((2, False),), weight=2)
    attach(organism, ((0, True),), weight=1000)  # Inactive, regardless of weight.
    assert organism.act(BooleanPort(), event_id=0, learn=False) == "left"
    # Removing the actual evidence edge weight must remove its policy effect.
    for slot in range(organism.slots):
        organism.graph.edge_by_key[(f"gate:{slot}:{c.identity}", f"option:{slot}", LinkType.SUR)].w = -2
    assert organism.act(BooleanPort(), event_id=1, learn=False) == "right"


def test_zero_marginal_xor_is_learned_from_actions_and_scalar_outcomes():
    # Every individual input coordinate is exactly uncorrelated with the target.
    rows = tuple(itertools.product(BOOL, repeat=2))
    for coordinate in (0, 1):
        for value in BOOL:
            assert sum((x != y) for x, y in rows if (x, y)[coordinate] == value) == 1
    organism = TerminalDevelopment(seed=1)
    assert not organism.conditions and float(organism.bias) == 0
    schedule = random.Random(17)
    for event in range(1200):
        x, y = schedule.choice(rows)
        port = BooleanPort(x, y)
        action = organism.act(port, event_id=event, learn=True)
        reward = 1.0 if (action == "right") == (x != y) else -1.0
        organism.observe(Feedback(event, action, reward))
    state = learned_state(organism)
    for x, y in rows:
        # Opaque action identifiers were never features: rename them on reuse.
        port = BooleanPort(x, y, names=("new-a", "new-b"))
        assert (organism.act(port, event_id=0, learn=False) == "new-b") == (x != y)
    assert learned_state(organism) == state
    assert any(len(c.atoms) > 1 and abs(float(c.weight)) > 0.05 for c in organism.conditions.values())
    assert any(c.weight.slow != 0 for c in organism.conditions.values())
    assert all(not c.stats.has_causal_intervention for c in organism.conditions.values())


def test_delayed_credit_updates_only_participants_and_rejects_stale_feedback():
    organism = TerminalDevelopment(config=DevelopmentConfig(exploration=0))
    organism.schema = BooleanPort.schema
    first = attach(organism, ((0, False),))
    second = attach(organism, ((0, True),))
    unselected = attach(organism, ((2, False),), weight=-1)
    a0 = organism.act(BooleanPort(False), event_id=3, learn=True)
    a1 = organism.act(BooleanPort(True), event_id=4, learn=True)
    assert a0 == a1 == "right"
    assert float(first.weight) == float(second.weight) == 0  # No intermediate reward.
    with pytest.raises(RuntimeError, match="outcome"):
        pickle.dumps(organism)
    with pytest.raises(ValueError, match="latest"):
        organism.observe(Feedback(3, a0, 1))
    with pytest.raises(ValueError, match="finite"):
        organism.observe(Feedback(4, a1, float("nan")))
    organism.observe(Feedback(4, a1, 1))
    assert float(first.weight) == pytest.approx(0.3 * 0.8 / 2)
    assert float(second.weight) == pytest.approx(0.3 / 2)
    assert float(unselected.weight) == -1
    assert unselected.stats.credit_stats.total_correlations == 0
    with pytest.raises(RuntimeError, match="awaiting"):
        organism.observe(Feedback(4, a1, 1))
    with pytest.raises(ValueError, match="increase"):
        organism.act(BooleanPort(), event_id=4, learn=True)


def test_pruning_preserves_readers_needed_by_a_joint_condition():
    organism = TerminalDevelopment()
    organism.schema = BooleanPort.schema
    organism._ensure_slots(2)
    marginal = attach(organism, ((0, True),), weight=0)
    joint = attach(organism, ((0, True), (1, True)), weight=0.5)
    doomed = attach(organism, ((1, False),), weight=0)
    organism.completed = 300
    graph_id = id(organism.graph)
    organism._prune()
    assert id(organism.graph) == graph_id
    assert marginal.identity not in organism.conditions and doomed.identity not in organism.conditions
    assert joint.identity in organism.conditions
    assert "read:0:0:1" in organism.graph.nodes
    assert "read:0:1:0" not in organism.graph.nodes
    for slot in range(organism.slots):
        assert organism.graph.edge_by_key[(f"gate:{slot}:{joint.identity}", f"option:{slot}", LinkType.SUR)].w is joint.weight
    organism.graph.validate_formal_pairs()


def test_consolidation_preserves_effective_value_and_keeps_fast_plasticity():
    weight = PlasticWeight(fast=0.75, slow=-0.1)
    old = float(weight)
    weight.consolidate(0.1)
    assert float(weight) == pytest.approx(old)
    assert weight.slow == pytest.approx(-0.025)
    weight.fast += 0.2
    assert float(weight) == pytest.approx(old + 0.2)


def test_checkpoint_continuation_preserves_rng_topology_credit_and_weight_aliases():
    organism = TerminalDevelopment(seed=11)
    for event in range(20):
        action = organism.act(BooleanPort(bool(event % 2), bool(event % 3)), event_id=event, learn=True)
        organism.observe(Feedback(event, action, 1 if event % 3 else -1))
    restored = pickle.loads(pickle.dumps(organism))
    for event in range(20, 35):
        actions = [o.act(BooleanPort(bool(event % 2), bool(event % 3)), event_id=event, learn=True)
                   for o in (organism, restored)]
        assert actions[0] == actions[1]
        for o, action in zip((organism, restored), actions):
            o.observe(Feedback(event, action, 1 if event % 3 else -1))
        assert learned_state(organism) == learned_state(restored)
    for c in restored.conditions.values():
        for slot in range(restored.slots):
            assert restored.graph.edge_by_key[(f"gate:{slot}:{c.identity}", f"option:{slot}", LinkType.SUR)].w is c.weight
    assert list(restored.graph.nodes) == list(organism.graph.nodes)
    assert [(e.src, e.dst, e.ltype, float(e.w)) for e in restored.graph.edges] == [
        (e.src, e.dst, e.ltype, float(e.w)) for e in organism.graph.edges]


def test_chess_uses_only_real_actuator_push_and_terminal_measurements(monkeypatch):
    original = chess.Board.push
    pushes = []
    def counted(board, move):
        pushes.append(move.uci())
        return original(board, move)
    monkeypatch.setattr(chess.Board, "push", counted)
    original_measure = ChessFeaturePort.measure
    def measure(self, coordinate, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        return original_measure(self, coordinate, binding)
    monkeypatch.setattr(ChessFeaturePort, "measure", measure)
    # Fail if either legacy board reconstruction or anonymous host-score builder
    # is accidentally reintroduced into the new path.
    from recon_lite_chess.coach.native import NativeOrganism
    from recon_lite.choice_genome import AnonymousChoiceGenome
    def forbidden(*args, **kwargs):
        raise AssertionError("legacy scoring path was called")
    monkeypatch.setattr(NativeOrganism, "act", forbidden)
    monkeypatch.setattr(AnonymousChoiceGenome, "emit", forbidden)
    organism = TerminalOrganism(seed=1)
    for event in range(4):
        attempt = play_mate_one(organism, M1, event_id=event, learn=True)
        assert attempt.real_moves == 1 and attempt.reason != "illegal_action"
        assert pushes[-1] == attempt.action
    assert len(pushes) == 4
    organism.graph.validate_formal_pairs()


def test_trial_grace_and_noise_have_a_finite_structural_budget():
    organism = TerminalDevelopment(seed=7, config=DevelopmentConfig(max_conditions=8))
    noise = random.Random(99)
    for event in range(80):
        action = organism.act(BooleanPort(bool(event % 2), bool(event % 3)), event_id=event, learn=True)
        organism.observe(Feedback(event, action, noise.choice((-1, 1))))
        assert len(organism.conditions) <= 8
    assert len(organism.conditions) == 8
    assert organism.pruned == 0
    # A candidate is protected throughout its complete grace period.
    candidate = next(iter(organism.conditions.values()))
    candidate.weight.fast = candidate.weight.slow = 0.0
    organism.completed = candidate.born + organism.config.grace_episodes - 1
    organism._prune()
    assert candidate.identity in organism.conditions
    organism.completed += 1
    organism._prune()
    assert candidate.identity not in organism.conditions


def test_changing_unexposed_board_clocks_cannot_change_a_decision():
    organism = TerminalOrganism(config=DevelopmentConfig(exploration=0))
    for event in range(6):
        play_mate_one(organism, M1, event_id=event, learn=True)
    restored = pickle.loads(pickle.dumps(organism))
    a = play_mate_one(organism, M1, event_id=0, learn=False)
    b = play_mate_one(restored, M1.replace("0 1", "12 40"), event_id=0, learn=False)
    assert a.action == b.action
    assert {nid: n.meta.get("reading") for nid, n in organism.graph.nodes.items()} == {
        nid: n.meta.get("reading") for nid, n in restored.graph.nodes.items()}


def test_schema_and_invalid_measurements_fail_before_any_actuator_effect():
    organism = TerminalDevelopment()
    organism.schema = BooleanPort.schema
    attach(organism, ((0, False),), weight=1)
    class Broken(BooleanPort):
        def measure(self, coordinate, binding):
            return 1  # An integer cannot masquerade as a Boolean.
    port = Broken()
    with pytest.raises(ValueError, match="typed domain"):
        organism.act(port, event_id=0, learn=True)
    assert port.executed is None
    class Changed(BooleanPort):
        schema = (Coordinate("different", BOOL),)
    with pytest.raises(ValueError, match="schema changed"):
        organism.act(Changed(), event_id=0, learn=True)
