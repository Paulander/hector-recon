"""Planted mechanism fixtures are tests, never inputs to chess training."""
import copy
from dataclasses import asdict, replace
import inspect
import pickle

import chess
import pytest

from recon_lite.graph import LinkType, NodeType
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.interface import Feedback
from recon_lite_chess.experiments.live_trial import TrialOrganism, learned_digest
from recon_lite_hector.learning.live_trial import TrialConfig, TrialDevelopment
from recon_lite_hector.learning.residual_shadow import Definition, ShadowConfig
from recon_lite_hector.learning.terminal_development import Coordinate, DevelopmentConfig
from recon_lite_hector.nodes.stem_cell import CandidateLocalStats, StemCellState


class Port:
    schema = tuple(Coordinate(n, (False, True)) for n in ("x", "y", "action"))

    def __init__(self, x=True, y=False, names=("a", "b")):
        self.values, self.names, self.executed = (x, y), names, None

    def bindings(self):
        assert inspect.currentframe().f_back.f_code.co_name == "_catalog"
        return self.names

    def measure(self, index, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        assert self.executed is None
        return (*self.values, binding == "b")[index]

    def execute(self, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_actuator"
        assert self.executed is None
        self.executed = binding


def make(role="ranked"):
    return TrialDevelopment(config=DevelopmentConfig(max_conditions=1, exploration=0.5),
        shadow_config=ShadowConfig(candidates=2, discovery_episodes=4, min_support=1),
        trial_config=TrialConfig(role, 8),
        definitions=(Definition("and", ((0, True), (2, True))),
                     Definition("and", ((1, True), (2, True)))))


def step(o, event, reward=-1):
    action = o.act(Port(bool(event % 2), bool(event % 3)), event_id=event, learn=True)
    o.observe(Feedback(event, action, reward))
    return action


def before_attachment(role="ranked"):
    o = make(role)
    for event in range(7):
        step(o, event)
    # A planted nomination isolates the handoff mechanics from ranking quality.
    # Production and experiment coaches have no nomination-setting interface.
    o.shadow.nomination = {"ranked": 0, "random": 1}
    return o


def attached(role="ranked"):
    o = before_attachment(role)
    step(o, 7)
    assert o.trial_decision["status"] == ("no_addition" if role == "none" else "attached")
    return o


def test_attachment_after_valid_feedback_preserves_signed_history_and_trial_state():
    o = before_attachment()
    source = o.shadow.evidence[0]
    source.weight = -0.75
    action = o.act(Port(), event_id=7, learn=True)
    assert o.trial_condition is None
    with pytest.raises(ValueError):
        o.observe(Feedback(7, "wrong", -1))
    assert o.trial_condition is None
    o.observe(Feedback(7, action, -1))
    c = o.trial_condition
    assert c.source_index == 0 and c.source_evidence is source
    assert c.atoms == o.shadow.definitions[0].atoms
    assert c.operator == o.shadow.definitions[0].operator
    assert float(c.weight) == source.weight < 0
    assert c.born == 8 and c.state == StemCellState.TRIAL
    assert c.stats == CandidateLocalStats()
    assert o.live_counts["episodes"] == 0 and len(o.conditions) == 2
    with pytest.raises(RuntimeError, match="one attachment"):
        o._begin_trial()


def test_live_composition_changes_actual_action_with_one_shared_weight():
    o = attached()
    o.config = replace(o.config, exploration=0)
    for c in o.conditions.values():
        c.weight.fast = c.weight.slow = 0.0
    o.bias.fast = o.bias.slow = 0.0
    c = o.trial_condition
    c.weight.fast = 0.8
    masked = copy.deepcopy(o)
    masked.trial_condition.weight.fast = 0.0
    assert o.act(Port(names=("a", "b", "c")), event_id=8, learn=False) == "b"
    assert masked.act(Port(names=("a", "b", "c")), event_id=8, learn=False) == "c"
    # AND requires both readings; neither the host nor one literal selects b.
    assert o.act(Port(x=False, names=("a", "b", "c")), event_id=8, learn=False) == "c"
    o.act(Port(names=("a", "b", "c", "d")), event_id=8, learn=False)
    for slot in range(4):
        assert o.graph.edge_by_key[(f"gate:{slot}:{c.identity}", f"option:{slot}", LinkType.SUR)].w is c.weight
    assert all(not o.graph.children(nid) for nid, n in o.graph.nodes.items() if n.ntype == NodeType.TERMINAL)
    o.graph.validate_formal_pairs()


def test_live_credit_updates_once_and_shadow_evidence_stops():
    o = attached()
    o.config = replace(o.config, exploration=0)
    for c in o.conditions.values():
        c.weight.fast = c.weight.slow = 0.0
    c = o.trial_condition
    c.weight.fast = 0.8
    book = copy.deepcopy(o.shadow.report())
    source = copy.deepcopy(asdict(c.source_evidence))
    action = o.act(Port(), event_id=8, learn=True)
    _, _, prediction, active = o.pending[0]
    assert c.identity in active
    old = float(c.weight)
    before = learned_digest(o)
    for feedback in (Feedback(9, action, 1), Feedback(8, "wrong", 1), Feedback(8, action, float("nan"))):
        with pytest.raises(ValueError):
            o.observe(feedback)
        assert learned_digest(o) == before
    with pytest.raises(RuntimeError):
        pickle.dumps(o)
    o.observe(Feedback(8, action, -1))
    assert float(c.weight) == pytest.approx(old + o.config.learning_rate * (-1 - prediction) / (1 + len(active)))
    assert o.shadow.report() == book and asdict(c.source_evidence) == source
    assert o.shadow_pending is None
    assert o.live_counts == {"episodes": 1, "active": 1, "positive_active": 0,
                             "negative_active": 1, "reward_sum_active": -1.0}
    before = learned_digest(o)
    with pytest.raises(RuntimeError):
        o.observe(Feedback(8, action, -1))
    assert learned_digest(o) == before
    action = o.act(Port(x=False), event_id=9, learn=True)
    old = float(c.weight)
    o.observe(Feedback(9, action, 1))
    assert float(c.weight) == old and o.live_counts["active"] == 1


def test_roles_have_identical_prefix_and_equal_nominees_have_equal_live_behavior():
    organisms = [make(role) for role in ("none", "ranked", "random")]
    for event in range(8):
        if event == 7:
            for o in organisms:
                o.shadow.nomination = {"ranked": 0, "random": 0}
        assert len({step(o, event) for o in organisms}) == 1
        assert all(o.shadow.report() == organisms[0].shadow.report() for o in organisms)
        assert all(o.rng.getstate() == organisms[0].rng.getstate() for o in organisms)
        assert all(o.bias == organisms[0].bias for o in organisms)
        for o in organisms:
            for cid, c in organisms[0].conditions.items():
                assert o.conditions[cid] == c
    for event in range(8, 20):
        a, b = organisms[1:]
        assert step(a, event) == step(b, event)
        assert a.conditions == b.conditions and a.bias == b.bias


@pytest.mark.parametrize("status", ["no_addition", "no_nomination", "already_live", "already_retired"])
def test_unavailable_nominees_are_not_substituted_or_reborn(status):
    o = before_attachment("none" if status == "no_addition" else "ranked")
    if status == "no_nomination":
        o.shadow.nomination = None
    if status in ("already_live", "already_retired"):
        c = next(iter(o.conditions.values()))
        # Test fixture places this exact definition into the historical pool.
        o.shadow.definitions = (Definition(c.operator, c.atoms), o.shadow.definitions[1])
        if status == "already_retired":
            o.retired_conditions[(c.operator, c.atoms)] = o.conditions.pop(c.identity)
    step(o, 7)
    assert o.trial_decision["status"] == status
    assert o.trial_condition is None
    for event in range(8, 12):
        step(o, event)
    assert o.trial_condition is None and o.shadow.observations == 8


def test_checkpoint_continuity_across_attachment_and_live_learning():
    o = before_attachment()
    restored = pickle.loads(pickle.dumps(o))
    for event in range(7, 20):
        if event == 9:
            restored = pickle.loads(pickle.dumps(restored))
        assert step(o, event) == step(restored, event)
        assert learned_digest(o) == learned_digest(restored)
        if restored.trial_condition:
            c = restored.trial_condition
            assert c.source_evidence is restored.shadow.evidence[c.source_index]
    before = learned_digest(o)
    o.act(Port(), event_id=0, learn=False)
    assert learned_digest(o) == before


def test_pruning_retains_trial_evidence_and_prevents_exact_rebirth():
    o = attached()
    c = o.trial_condition
    book = copy.deepcopy(o.shadow.report())
    o.completed = c.born + o.config.grace_episodes
    c.weight.fast = c.weight.slow = 0.0
    o._prune()
    assert c.state == StemCellState.PRUNED
    assert o.retired_conditions[(c.operator, c.atoms)] is c
    assert c.source_evidence is o.shadow.evidence[c.source_index]
    assert o.shadow.report() == book
    for _ in range(100):
        o._birth()
    assert all((x.operator, x.atoms) != (c.operator, c.atoms) for x in o.conditions.values())
    restored = pickle.loads(pickle.dumps(o))
    assert restored.trial_condition.source_evidence is restored.shadow.evidence[c.source_index]


def test_actual_chess_uses_one_push_and_terminal_reads_after_attachment(monkeypatch):
    o = TrialOrganism(config=DevelopmentConfig(max_conditions=1),
                      shadow_config=ShadowConfig(candidates=2, discovery_episodes=4, min_support=1),
                      trial_config=TrialConfig("ranked", 8),
                      definitions=(Definition("and", ((1, True), (12, False))),
                                   Definition("and", ((1, False), (12, True)))))
    pushes = []
    original = chess.Board.push
    def push(board, move):
        pushes.append(move.uci())
        return original(board, move)
    monkeypatch.setattr(chess.Board, "push", push)
    from recon_lite_chess.coach.terminal import ChessFeaturePort
    original_measure = ChessFeaturePort.measure
    def measure(port, index, binding):
        frame = inspect.currentframe().f_back
        assert frame.f_code.co_name == "_reader"
        if o.completed >= 8:
            assert not frame.f_locals["node"].nid.startswith("shadow:")
        return original_measure(port, index, binding)
    monkeypatch.setattr(ChessFeaturePort, "measure", measure)
    for event in range(10):
        if event == 7:
            o.shadow.nomination = {"ranked": 0, "random": 1}
        result = play_mate_one(o, "k7/8/1K6/8/8/8/8/7R w - - 0 1", event_id=event, learn=True)
        assert result.real_moves == 1
    assert o.trial_decision["status"] == "attached" and len(pushes) == 10


def test_invalid_trial_configuration():
    with pytest.raises(ValueError):
        TrialConfig("oracle")
    with pytest.raises(ValueError):
        TrialConfig(after_episode=0)
    with pytest.raises(ValueError, match="prospective interval"):
        TrialDevelopment(trial_config=TrialConfig(after_episode=64))
