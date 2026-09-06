"""Generic planted fixtures test access value, not chess discovery quality."""
import copy
from dataclasses import asdict
import pickle

import chess
import pytest

from recon_lite.graph import LinkType, NodeState, NodeType
from recon_lite_chess.coach.exercise import play_mate_one
from recon_lite_chess.coach.interface import Feedback
from recon_lite_chess.experiments.trial_usefulness import UsefulnessOrganism, use_digest
from recon_lite_chess.experiments.live_trial import TrialOrganism, learned_digest
from recon_lite_hector.learning.live_trial import TrialConfig
from recon_lite_hector.learning.residual_shadow import Definition, ShadowConfig
from recon_lite_hector.learning.terminal_development import Condition, DevelopmentConfig
from recon_lite_hector.learning.trial_usefulness import UsefulnessConfig, UsefulnessDevelopment, _permission
from recon_lite_hector.nodes.stem_cell import StemCellState
from test_live_trial import Port


def make(*, kind="useful", window=64, plain=False, role="ranked"):
    definition = (Definition("and", ((0, True), (2, True))) if kind == "useful"
                  else Definition("and", ((0, True), (1, False))))
    kwargs = dict(seed=1, config=DevelopmentConfig(max_conditions=1, exploration=0),
                  shadow_config=ShadowConfig(candidates=2, discovery_episodes=4, min_support=1),
                  trial_config=TrialConfig(role, 8),
                  definitions=(definition, Definition("and", ((1, False), (2, True)))))
    o = (TrialOrganism(**kwargs) if plain else
         UsefulnessDevelopment(**kwargs, usefulness_config=UsefulnessConfig(window)))
    # A fixed, inactive baseline keeps this fixture about the trial's effect.
    # The ordinary bias and candidate weights still learn from every real outcome.
    o.schema = Port.schema
    o.conditions[0] = Condition(0, ((1, True),), "and", 0)
    o.next_condition = 1
    return o


def step(o, event, reward=-1):
    a = o.act(Port(names=("a", "b", "c")), event_id=event, learn=True)
    o.observe(Feedback(event, a, reward))
    return a


def attach(o):
    for event in range(8):
        if event == 7:
            o.shadow.nomination = {"ranked": 0, "random": 0}
        step(o, event)
    assert o.trial_decision["status"] == "attached"
    o.trial_condition.weight.fast, o.trial_condition.weight.slow = 0.8, 0.0
    return o


def identity(o):
    return learned_digest(o), use_digest(o)


def test_real_use_distinguishes_useful_and_from_success_correlation():
    useful, irrelevant = attach(make()), attach(make(kind="irrelevant"))
    for o in (useful, irrelevant):
        initial_bias = float(o.bias)
        for event in range(8, 72):
            a = o.act(Port(names=("a", "b", "c")), event_id=event, learn=True)
            reward = 1 if a == ("b" if o is useful else "c") else -1
            o.observe(Feedback(event, a, reward))
        report = o.usefulness_report()
        assert report["assigned_episodes"] == 64 and report["window_elapsed"]
        assert report["groups"]["disabled"]["participations"] == 0
        assert all(report["groups"][g]["count"] > 0 for g in ("enabled", "disabled"))
        assert float(o.bias) != initial_bias  # Actor not frozen to manufacture effect.
        assert o.trial_condition.state == StemCellState.TRIAL
        assert report["groups"]["enabled"]["positive"] > 0
    assert useful.usefulness_report()["mean_reward_difference"] == 2.0
    assert useful.usefulness_report()["randomized_reward_contrast"] == 2.0
    assert irrelevant.usefulness_report()["mean_reward_difference"] == 0.0


def test_disabled_trial_has_no_credit_but_all_assigned_rewards_enter_evidence(monkeypatch):
    o = attach(make())
    c = o.trial_condition
    for event, draw, x in ((8, 0.9, True), (9, 0.1, False), (10, 0.1, True)):
        monkeypatch.setattr(o.use_rng, "random", lambda: draw)
        old_weight, old_bias = float(c.weight), float(o.bias)
        a = o.act(Port(x=x, names=("a", "b", "c")), event_id=event, learn=True)
        active = c.identity in o.pending[0][3]
        assert active == (draw < 0.5 and x)
        o.observe(Feedback(event, a, 1))
        if not active:
            assert float(c.weight) == old_weight
        assert float(o.bias) != old_bias
    r = o.usefulness_report()
    assert r["assigned_episodes"] == 3
    assert r["groups"]["enabled"]["count"] == 2  # Includes enabled-but-inactive.
    assert r["groups"]["enabled"]["participations"] == 1
    assert r["groups"]["disabled"]["count"] == 1
    assert r["groups"]["disabled"]["participations"] == 0


@pytest.mark.parametrize("operator,bits,expected", [
    ("and", (True, False), False), ("and", (True, True), True),
    ("or", (True, False), True), ("or", (False, False), False),
    ("xor", (True, True), False), ("xor", (True, False), True),
])
def test_permission_wrapper_preserves_boolean_semantics(operator, bits, expected, monkeypatch):
    o = make()
    o.shadow_definitions = (Definition(operator, ((0, True), (1, True))),
                            Definition("and", ((1, False), (2, True))))
    attach(o)
    for event, enabled in ((8, True), (9, False)):
        monkeypatch.setattr(o.use_rng, "random", lambda: 0.1 if enabled else 0.9)
        a = o.act(Port(*bits, names=("a", "b", "c", "d")), event_id=event, learn=True)
        c = o.trial_condition
        for slot in range(4):
            assert (o.graph.nodes[f"gate:{slot}:{c.identity}"].state == NodeState.CONFIRMED) == (enabled and expected)
            assert o.graph.edge_by_key[(f"gate:{slot}:{c.identity}", f"option:{slot}", LinkType.SUR)].w is c.weight
        assert all(not o.graph.children(nid) for nid, n in o.graph.nodes.items() if n.ntype == NodeType.TERMINAL)
        o.observe(Feedback(event, a, -1))
        o.graph.validate_formal_pairs()


def test_invalid_duplicate_feedback_and_pending_actions_preserve_evidence_and_rng():
    o = attach(make())
    a = o.act(Port(), event_id=8, learn=True)
    before = identity(o)
    for feedback in (Feedback(9, a, 1), Feedback(8, "wrong", 1), Feedback(8, a, float("nan"))):
        with pytest.raises(ValueError):
            o.observe(feedback)
        assert identity(o) == before
    with pytest.raises(RuntimeError):
        o.act(Port(), event_id=9, learn=True)
    assert identity(o) == before
    with pytest.raises(RuntimeError):
        pickle.dumps(o)
    o.observe(Feedback(8, a, 1))
    before = identity(o)
    with pytest.raises(RuntimeError):
        o.observe(Feedback(8, a, 1))
    with pytest.raises(ValueError):
        o.act(Port(), event_id=8, learn=True)
    assert identity(o) == before


def test_checkpoint_before_attachment_and_during_probe_preserves_future():
    o = make()
    for event in range(7):
        step(o, event)
    o.shadow.nomination = {"ranked": 0, "random": 0}
    restored = pickle.loads(pickle.dumps(o))
    for event in range(7, 30):
        if event == 14:
            restored = pickle.loads(pickle.dumps(restored))
        assert step(o, event) == step(restored, event)
        assert identity(o) == identity(restored)
        c = restored.trial_condition
        assert c.source_evidence is restored.shadow.evidence[c.source_index]


def test_prefix_and_completed_window_preserve_old_actor_and_evaluation_is_frozen():
    a, b = make(window=2), make(plain=True)
    for event in range(8):
        if event == 7:
            for o in (a, b):
                o.shadow.nomination = {"ranked": 0, "random": 0}
        assert step(a, event) == step(b, event)
        assert learned_digest(a) == learned_digest(b)
        assert a.use_outcomes == []
    rng = a.use_rng.getstate()
    before = identity(a)
    assert a.act(Port(), event_id=0, learn=False) == b.act(Port(), event_id=0, learn=False)
    assert identity(a) == before and a.use_rng.getstate() == rng
    for event in (8, 9):
        step(a, event)
    history, rng = copy.deepcopy(a.use_outcomes), a.use_rng.getstate()
    for event in range(10, 14):
        step(a, event)
        assert a.use_enabled
    assert a.use_outcomes == history and a.use_rng.getstate() == rng


def test_pruning_removes_wrappers_but_preserves_history_and_shared_weights():
    o = attach(make())
    for event in range(8, 16):
        step(o, event)
    c = o.trial_condition
    history, source = copy.deepcopy(o.use_outcomes), c.source_evidence
    o.completed = c.born + o.config.grace_episodes
    c.weight.fast = c.weight.slow = 0.0
    o._prune()
    assert c.state == StemCellState.PRUNED
    assert o.retired_conditions[(c.operator, c.atoms)] is c
    assert c.source_evidence is source and o.use_outcomes == history
    assert not any(nid.startswith("use:") for nid in o.graph.nodes)
    assert all(n.predicate is not _permission for n in o.graph.nodes.values())
    assert all(o.graph.all_parents(nid) for nid, n in o.graph.nodes.items() if n.ntype == NodeType.TERMINAL)
    restored = pickle.loads(pickle.dumps(o))
    assert restored.use_outcomes == history
    assert restored.trial_condition.source_evidence is restored.shadow.evidence[c.source_index]
    o.graph.validate_formal_pairs()


def test_no_addition_never_draws_or_fakes_use_evidence():
    o = make(role="none")
    rng = o.use_rng.getstate()
    for event in range(20):
        step(o, event)
    assert o.trial_condition is None
    assert o.use_rng.getstate() == rng
    assert o.usefulness_report()["assigned_episodes"] == 0
    assert o.usefulness_report()["mean_reward_difference"] is None


def test_chess_probe_executes_one_actual_move_per_outcome(monkeypatch):
    o = UsefulnessOrganism(config=DevelopmentConfig(max_conditions=1),
        shadow_config=ShadowConfig(candidates=2, discovery_episodes=4, min_support=1),
        trial_config=TrialConfig("ranked", 8), usefulness_config=UsefulnessConfig(8),
        definitions=(Definition("and", ((1, True), (12, False))),
                     Definition("and", ((1, False), (12, True)))))
    pushes, original = [], chess.Board.push
    def push(board, move):
        pushes.append(move.uci())
        return original(board, move)
    monkeypatch.setattr(chess.Board, "push", push)
    for event in range(16):
        if event == 7:
            o.shadow.nomination = {"ranked": 0, "random": 1}
        r = play_mate_one(o, "k7/8/1K6/8/8/8/8/7R w - - 0 1", event_id=event, learn=True)
        assert r.real_moves == 1
    assert len(pushes) == 16 and len(o.use_outcomes) == 8
    assert o.usefulness_report()["groups"]["disabled"]["participations"] == 0


@pytest.mark.parametrize("window,p", [(0, 0.5), (1, 0), (1, 1), (1, float("nan"))])
def test_invalid_config(window, p):
    with pytest.raises(ValueError):
        UsefulnessConfig(window, p)
