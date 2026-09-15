"""Planted graphs isolate primitives; the separate learning run starts empty."""
from dataclasses import replace
import inspect
import itertools
import pickle
import random

import pytest

from recon_lite.graph import LinkType, NodeState, NodeType
from recon_lite_chess.coach.interface import Feedback
from recon_lite_hector.learning.terminal_development import (
    Condition, Coordinate, DevelopmentConfig, PlasticWeight, TerminalDevelopment,
)
from recon_lite_hector.learning.recursive_context import (
    Expression, RecursiveConfig, RecursiveDevelopment, combine,
)

BOOL = (False, True)


class Port:
    schema = tuple(Coordinate(name, BOOL) for name in ("x", "y", "a"))

    def __init__(self, x=False, y=False, names=("a", "b")):
        self.values = (x, y)
        self.names = names
        self.executed = None

    def bindings(self):
        assert inspect.currentframe().f_back.f_code.co_name == "_catalog"
        return self.names

    def measure(self, coordinate, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        return (*self.values, binding == self.names[1])[coordinate]

    def execute(self, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_actuator"
        assert self.executed is None and binding in self.names
        self.executed = binding


def planted():
    actor = RecursiveDevelopment(config=DevelopmentConfig(max_conditions=12, exploration=0))
    actor.schema = Port.schema
    c = Condition(0, ((2, True),), "and", 0,
                  weight=PlasticWeight(fast=.6, slow=.2))
    c.stats.record_correlation("positive")
    actor.conditions[0] = c
    actor.next_condition = 1
    actor._ensure_slots(2)
    return actor


def scores(actor, x, y):
    action = actor.act(Port(x, y), event_id=0, learn=False)
    return action, tuple(actor.graph.nodes[f"option:{i}"].activation.value for i in range(2))


def test_split_inherits_every_score_and_recursively_reuses_actual_scripts():
    actor = planted()
    rows = tuple(itertools.product(BOOL, repeat=2))
    before = [scores(actor, *r) for r in rows]
    source = actor.expressions[0]
    left, right = actor.refine(0, Expression("read", atom=(0, True)))
    assert [scores(actor, *r) for r in rows] == before
    a, b = actor.refine(right, Expression("read", atom=(1, True)))
    assert [scores(actor, *r) for r in rows] == before
    assert actor.generation[a] == actor.generation[b] == 2
    weights = [actor.conditions[cid].weight for cid in (left, a, b)]
    assert len({id(w) for w in weights}) == 3
    assert all(float(w) == .8 for w in weights)
    assert actor.history[0]["condition"].stats.credit_stats.total_correlations == 1
    assert actor.history[0]["condition"].weight is not weights[0]
    assert f"gate:0:0" not in actor.graph.nodes
    source_nid = actor._expression_node(source, 0)
    assert len(actor.graph.all_parents(source_nid)) >= 2
    for cid in actor.conditions:
        for slot in range(2):
            assert actor.graph.edge_by_key[(f"gate:{slot}:{cid}", f"option:{slot}", LinkType.SUR)].w is actor.conditions[cid].weight
    actor.graph.validate_formal_pairs()
    assert all(not actor.graph.children(nid) for nid, n in actor.graph.nodes.items()
               if n.ntype == NodeType.TERMINAL)


def test_reward_changes_only_the_selected_context_leaf_without_erasing_ancestry():
    actor = planted()
    left, right = actor.refine(0, Expression("read", atom=(0, True)))
    actor.completed = actor.recursive_config.prefix
    action = actor.act(Port(True, False), event_id=20, learn=True)
    assert action == "b"
    with pytest.raises(RuntimeError, match="feedback"):
        actor.refine(right, Expression("read", atom=(1, True)))
    with pytest.raises(RuntimeError, match="feedback"):
        pickle.dumps(actor)
    snapshot = (actor.completed, float(actor.bias), dict(actor.evidence))
    with pytest.raises(ValueError, match="bind"):
        actor.observe(Feedback(21, action, -1))
    with pytest.raises(ValueError, match="finite"):
        actor.observe(Feedback(20, action, float("nan")))
    assert (actor.completed, float(actor.bias), actor.evidence) == snapshot
    actor.observe(Feedback(20, action, -1))
    assert float(actor.conditions[left].weight) == .8
    assert float(actor.conditions[right].weight) == pytest.approx(.8 + .3 * (-1 - .8) / 2)
    assert float(actor.history[0]["condition"].weight) == .8
    assert actor.conditions[left].stats.credit_stats.total_correlations == 0
    assert actor.conditions[right].stats.credit_stats.total_correlations == 1


def test_nested_and_or_truth_is_computed_by_the_formal_graph():
    actor = planted()
    actor._remove_contributions({0}, "test")
    expression = combine("and", (
        Expression("read", atom=(2, True)),
        combine("or", (Expression("read", atom=(0, True)), Expression("read", atom=(1, True)))),
    ))
    c = Condition(1, ((2, True),), "and", 0, weight=PlasticWeight(fast=1))
    actor.conditions[1] = c
    actor.expressions[1] = expression
    actor.next_condition = 2
    for slot in range(2):
        actor._add_condition_slot(c, slot)
    for x, y in itertools.product(BOOL, repeat=2):
        _, support = scores(actor, x, y)
        assert support == (0, float(x or y))


def test_no_split_prefix_matches_the_original_learner_not_just_another_clone():
    config = DevelopmentConfig(max_conditions=12)
    old = TerminalDevelopment(seed=3, config=config)
    new = RecursiveDevelopment(seed=3, config=config)
    schedule = random.Random(17)
    for event in range(64):
        x, y = (schedule.choice(BOOL) for _ in range(2))
        actions = [a.act(Port(x, y), event_id=event, learn=True) for a in (old, new)]
        assert actions[0] == actions[1]
        for a, action in zip((old, new), actions):
            a.observe(Feedback(event, action, 1 if (action == "b") == (x != y) else -1))
        assert old.rng.getstate() == new.rng.getstate()
        assert float(old.bias) == float(new.bias)
        assert {k: float(v.weight) for k, v in old.conditions.items()} == {k: float(v.weight) for k, v in new.conditions.items()}


def test_checkpoint_preserves_nested_shared_definitions_and_independent_learning():
    actor = planted()
    children = actor.refine(0, Expression("read", atom=(0, True)))
    actor.refine(children[1], Expression("read", atom=(1, True)))
    actor.completed = 256
    restored = pickle.loads(pickle.dumps(actor))
    for event in range(20):
        actions = [a.act(Port(bool(event % 2), bool(event % 3)), event_id=event, learn=True)
                   for a in (actor, restored)]
        assert actions[0] == actions[1]
        for a, action in zip((actor, restored), actions):
            a.observe(Feedback(event, action, 1 if event % 2 else -1))
        # Pickle memo sharing/interned strings are not semantic state. Compare
        # continuation, parameters, histories and physical graph explicitly.
        for name in ("conditions", "bias", "completed", "next_condition", "pruned",
                     "pending", "last_event", "expressions", "expression_ids", "seen",
                     "history", "splits", "contexts", "evidence", "generation"):
            assert getattr(actor, name) == getattr(restored, name), name
        for name in ("rng", "proposal_rng", "exploration_rng"):
            assert getattr(actor, name).getstate() == getattr(restored, name).getstate()
        assert [(e.src, e.dst, e.ltype, float(e.w)) for e in actor.graph.edges] == [
            (e.src, e.dst, e.ltype, float(e.w)) for e in restored.graph.edges]
        assert [(nid, n.state, n.activation.value, n.meta) for nid, n in actor.graph.nodes.items()] == [
            (nid, n.state, n.activation.value, n.meta) for nid, n in restored.graph.nodes.items()]
    for x, y in itertools.product(BOOL, repeat=2):
        before = (actor.rng.getstate(), actor.proposal_rng.getstate(), dict(actor.evidence))
        assert (actor.act(Port(x, y, names=("new-a", "new-b")), event_id=0, learn=False) == "new-b") == (scores(actor, x, y)[0] == "b")
        assert before == (actor.rng.getstate(), actor.proposal_rng.getstate(), actor.evidence)


def test_shared_script_definition_has_separate_parent_request_instances():
    actor = planted()
    actor._remove_contributions({0}, "test")
    source = combine("or", (Expression("read", atom=(0, True)), Expression("read", atom=(2, True))))
    c = Condition(1, ((0, True), (2, True)), "or", 0, weight=PlasticWeight(fast=.8))
    actor.conditions[1] = c
    actor.expressions[1] = source
    actor.next_condition = 2
    for slot in range(2):
        actor._add_condition_slot(c, slot)
    actor.refine(1, Expression("read", atom=(1, True)))
    instances = [nid for nid, n in actor.graph.nodes.items()
                 if n.meta.get("definition_id") == actor.expression_ids[source]]
    assert len(instances) == 4  # Two branches times two action bindings.
    assert all(len(actor.graph.all_parents(nid)) == 1 for nid in instances)
    assert len({actor.graph.parent[nid] for nid in instances}) == 4
    actor.graph.validate_formal_pairs()


def test_bounds_and_retirement_do_not_delete_shared_structure_or_reset_history():
    with pytest.raises(ValueError, match="depth"):
        RecursiveConfig(max_depth=5)
    with pytest.raises(ValueError, match="positive"):
        RecursiveConfig(candidates=0)
    with pytest.raises(ValueError, match="distinct"):
        combine("xor", (Expression("read", atom=(0, True)),) * 2)
    actor = planted()
    children = actor.refine(0, Expression("read", atom=(0, True)))
    actor.conditions[children[0]].weight.fast = -.2
    actor.completed = 300
    actor._prune()
    assert children[0] not in actor.conditions
    assert children[1] in actor.conditions
    assert actor.history[-1]["reason"] == "weak"
    assert scores(actor, True, False)[1] == (0, .8)
    actor.recursive_config = replace(actor.recursive_config, max_splits=1)
    with pytest.raises(ValueError, match="budget"):
        actor.refine(children[1], Expression("read", atom=(1, True)))
