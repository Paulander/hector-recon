"""Planted mechanical fixtures, not results of autonomous growth or chess play."""
from dataclasses import replace
import copy
import inspect
import itertools
import pickle

import pytest

from recon_lite.graph import LinkType
from recon_lite_chess.coach.interface import Feedback
from recon_lite_hector.learning.terminal_development import Condition, Coordinate, DevelopmentConfig, PlasticWeight
from recon_lite_hector.learning.recursive_context import Expression, RecursiveConfig, RecursiveDevelopment, combine
from recon_lite_hector.learning.context_decision import ContextDecisionDevelopment, OwnershipLimits


BOOL = (False, True)
ROWS = tuple(itertools.product(BOOL, repeat=3))


class Port:
    schema = tuple(Coordinate(f"measurement-{i}", BOOL) for i in range(4))

    def __init__(self, row, names=("a", "b")):
        self.row, self.names, self.executed = row, names, None

    def bindings(self):
        assert inspect.currentframe().f_back.f_code.co_name == "_catalog"
        return self.names

    def measure(self, coordinate, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_reader"
        return (*self.row, binding == self.names[-1])[coordinate]

    def execute(self, binding):
        assert inspect.currentframe().f_back.f_code.co_name == "_actuator"
        assert self.executed is None and binding in self.names
        self.executed = binding

    def outcome(self):
        assert self.executed is not None
        return 1 if (self.executed == self.names[-1]) == self.row[0] else -1


def planted():
    # Broad a, broad b and a composed contributor, with nonzero signed/bias terms.
    actor = RecursiveDevelopment(
        seed=11, config=DevelopmentConfig(exploration=0, max_conditions=16,
                                          consolidate_every=4, grace_episodes=10000),
        recursive_config=RecursiveConfig(prefix=1024))
    actor.schema = Port.schema
    for cid, (atoms, operator, fast, slow) in enumerate((
        (((3, False),), "and", .2, .1),
        (((3, True),), "and", -.1, .05),
        (((1, True), (2, False)), "or", .4, -.15),
    )):
        actor.conditions[cid] = Condition(cid, atoms, operator, 0,
                                           PlasticWeight(fast=fast, slow=slow))
        actor.conditions[cid].stats.record_correlation("positive")
    actor.bias = PlasticWeight(fast=.125, slow=-.0625)
    actor.next_condition = 3
    actor._ensure_slots(2)
    return actor


def owned(source=None, **kwargs):
    return ContextDecisionDevelopment.from_actor(
        source or planted(), state_coordinates=(0, 1, 2), **kwargs)


def scores(actor, row, names=("a", "b")):
    action = actor.act(Port(row, names), event_id=-1, learn=False)
    return names.index(action), tuple(actor.graph.nodes[f"option:{i}"].activation.value
                                     for i in range(len(names)))


def weight_snapshot(actor, owner):
    return {cid: copy.deepcopy(actor.conditions[cid])
            for cid in actor.leaves[owner].contributions}


def test_conversion_and_nested_forks_preserve_all_scores_and_source_state():
    source = planted()
    before = [scores(source, row) for row in ROWS]
    original = pickle.dumps(source)
    actor = owned(source)
    assert pickle.dumps(source) == original
    left, right = actor.split_decision(0, Expression("read", atom=(0, True)))
    actor.split_decision(right, Expression("read", atom=(1, True)))
    assert [scores(actor, row) for row in ROWS] == before
    actor.validate_ownership()
    # Shared immutable base definitions, separate trainable weights and histories.
    copies = [actor.base_expressions[cid] for leaf in actor.leaves.values()
              for cid in leaf.contributions if actor.base_expressions[cid].operator == "or"]
    assert len(copies) == 3 and len({id(x) for x in copies}) == 1
    ancestor = actor.ownership_history[0]["conditions"]
    assert ancestor[0].stats.credit_stats.total_correlations == 1
    assert all(c.stats.credit_stats.total_correlations == 0 for c in actor.conditions.values())
    assert len(actor.conditions) == 12  # Three owners, three contributions + bias each.
    assert pickle.dumps(source) == original


def test_learning_in_one_context_changes_all_its_competitors_but_not_other_scores():
    actor = owned()
    left, right = actor.split_decision(0, Expression("read", atom=(0, True)))
    inactive_rows = [row for row in ROWS if not row[0]]
    inactive_scores = [scores(actor, row) for row in inactive_rows]
    inactive_weights = weight_snapshot(actor, left)
    right_before = weight_snapshot(actor, right)
    before = scores(actor, (True, False, False))
    actual = []
    for event in range(24):
        port = Port((True, bool(event % 2), bool(event % 3)))
        action = actor.act(port, event_id=event, learn=True)
        actual.append(action)
        actor.observe(Feedback(event, action, port.outcome()))
        assert [scores(actor, row) for row in inactive_rows] == inactive_scores
        assert weight_snapshot(actor, left) == inactive_weights
    assert set(actual) == {"a", "b"}  # Both competing choices got real outcome credit.
    assert weight_snapshot(actor, right) != right_before
    assert scores(actor, (True, False, False)) != before
    assert scores(actor, (True, False, False))[0] == 1
    assert float(actor.bias) == 0


def test_nested_update_also_preserves_the_other_child_of_the_same_parent():
    actor = owned()
    a, b = actor.split_decision(0, Expression("read", atom=(0, True)))
    b0, b1 = actor.split_decision(b, Expression("read", atom=(1, True)))
    protected = {owner: weight_snapshot(actor, owner) for owner in (a, b0)}
    rows = [row for row in ROWS if not (row[0] and row[1])]
    before = [scores(actor, row) for row in rows]
    for event in range(8):
        port = Port((True, True, bool(event % 2)))
        action = actor.act(port, event_id=event, learn=True)
        actor.observe(Feedback(event, action, port.outcome()))
    assert protected == {owner: weight_snapshot(actor, owner) for owner in (a, b0)}
    assert [scores(actor, row) for row in rows] == before


def test_credit_keeps_the_original_normalization_and_uses_the_graph_prediction():
    actor = owned()
    _, right = actor.split_decision(0, Expression("read", atom=(0, True)))
    port = Port((True, True, False))
    action = actor.act(port, event_id=0, learn=True)
    _, _, prediction, active = actor.pending[-1]
    before = {cid: float(c.weight) for cid, c in actor.conditions.items()}
    expected = .3 * (port.outcome() - prediction) / len(active)
    assert actor.leaves[right].bias_id in active
    actor.observe(Feedback(0, action, port.outcome()))
    for cid, c in actor.conditions.items():
        assert float(c.weight) == pytest.approx(before[cid] + (expected if cid in active else 0))


def test_graph_continuation_restores_ownership_rng_and_observation_history():
    actor = owned()
    actor.config = replace(actor.config, exploration=.25)
    actor.split_decision(0, Expression("read", atom=(0, True)))
    for event in range(3):
        port = Port(ROWS[event])
        action = actor.act(port, event_id=event, learn=True)
        actor.observe(Feedback(event, action, port.outcome()))
    restored = pickle.loads(pickle.dumps(actor))
    restored.validate_ownership()
    for event in range(3, 19):
        actions = []
        for learner in (actor, restored):
            port = Port(ROWS[event % len(ROWS)], names=("left-token", "right-token"))
            action = learner.act(port, event_id=event, learn=True)
            actions.append(action)
            learner.observe(Feedback(event, action, port.outcome()))
        assert actions[0] == actions[1]
        for name in ("conditions", "leaves", "ownership_history", "completed", "last_event"):
            assert getattr(actor, name) == getattr(restored, name)
        assert actor.rng.getstate() == restored.rng.getstate()
        assert actor.exploration_rng.getstate() == restored.exploration_rng.getstate()
        restored.validate_ownership()
    assert [scores(actor, row) for row in ROWS] == [scores(restored, row) for row in ROWS]


def test_feedback_failures_and_pending_mutations_do_not_apply_credit():
    actor = owned()
    action = actor.act(Port((True, False, True)), event_id=4, learn=True)
    conditions = copy.deepcopy(actor.conditions)
    for feedback in (Feedback(5, action, 1), Feedback(4, "other", 1),
                     Feedback(4, action, float("nan"))):
        with pytest.raises(ValueError):
            actor.observe(feedback)
        assert actor.conditions == conditions
    with pytest.raises(RuntimeError, match="feedback"):
        actor.split_decision(0, Expression("read", atom=(0, True)))
    with pytest.raises(RuntimeError, match="feedback"):
        pickle.dumps(actor)
    actor.observe(Feedback(4, action, -1))
    with pytest.raises(ValueError):
        actor.observe(Feedback(4, action, -1))
    with pytest.raises(ValueError, match="increase"):
        actor.act(Port(ROWS[0]), event_id=4, learn=True)


@pytest.mark.parametrize("limits", [
    OwnershipLimits(max_leaves=1), OwnershipLimits(max_parameters=7),
    OwnershipLimits(max_depth=1), OwnershipLimits(max_physical_nodes=50),
])
def test_exhausted_split_budget_does_not_partly_mutate_the_actor(limits):
    actor = owned(limits=limits)
    before = pickle.dumps(actor)
    route = combine("or", (Expression("read", atom=(0, True)), Expression("read", atom=(1, True))))
    with pytest.raises(ValueError, match="budget"):
        actor.split_decision(0, route)
    assert pickle.dumps(actor) == before


def test_action_dependent_routes_are_rejected_without_executing_an_action():
    actor = owned()
    with pytest.raises(ValueError, match="state coordinates"):
        actor.split_decision(0, Expression("read", atom=(3, True)))
    # Even a falsely declared coordinate is checked against formal observations.
    actor = ContextDecisionDevelopment.from_actor(planted(), state_coordinates=(0, 1, 2, 3))
    actor.split_decision(0, Expression("read", atom=(3, True)))
    port = Port(ROWS[0])
    with pytest.raises(RuntimeError, match="differs"):
        actor.act(port, event_id=0, learn=True)
    assert port.executed is None and not actor.pending and actor.owner_pending is None


def test_more_bindings_keep_existing_engine_graph_and_scoring_weight_aliases():
    actor = owned()
    actor.split_decision(0, Expression("read", atom=(0, True)))
    action, values = scores(actor, ROWS[0], names=("first", "second", "third"))
    assert len(values) == 3 and values[0] == values[1]
    actor.validate_ownership()
    assert scores(actor, ROWS[0], names=("renamed-a", "renamed-b"))[1] == (values[0], values[2])


def test_no_split_conversion_matches_original_weight_updates_without_lifecycle():
    source = planted()
    # Neither side reaches a lifecycle event in this three-action check.
    source.config = replace(source.config, max_conditions=3)
    actor = owned(source)
    for event in range(3):
        choices = []
        for learner in (source, actor):
            port = Port(ROWS[event])
            action = learner.act(port, event_id=event, learn=True)
            choices.append(action)
            learner.observe(Feedback(event, action, port.outcome()))
        assert choices[0] == choices[1]
        for cid in source.conditions:
            assert float(source.conditions[cid].weight) == float(actor.conditions[cid].weight)
        bias_id = actor.leaves[0].bias_id
        assert float(source.bias) == float(actor.conditions[bias_id].weight)


def test_alias_corruption_is_detected_before_claiming_isolation():
    actor = owned()
    left, right = actor.split_decision(0, Expression("read", atom=(0, True)))
    actor.conditions[actor.leaves[right].bias_id].weight = actor.conditions[actor.leaves[left].bias_id].weight
    with pytest.raises(ValueError, match="alias"):
        actor.validate_ownership()


def test_composed_route_settles_at_the_supported_depth_limit():
    actor = owned()
    route = combine("and", (
        combine("or", (Expression("read", atom=(0, True)), Expression("read", atom=(1, True)))),
        Expression("read", atom=(2, True)),
    ))
    before = [scores(actor, row) for row in ROWS]
    actor.split_decision(0, route)
    assert max(actor.expressions[cid].depth for cid in actor.conditions) == 4
    assert [scores(actor, row) for row in ROWS] == before
