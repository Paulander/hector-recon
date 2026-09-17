"""Data-free mechanical checks for action-sensitive budding."""
from dataclasses import replace
import copy
import pickle

import pytest

from recon_lite.graph import NodeState
from recon_lite_chess.coach.interface import Feedback
from recon_lite_hector.learning.route_action_bud import (
    RouteActionBudDevelopment, RouteActionEvidence)
from recon_lite_hector.learning.recursive_context import Expression
from selective_boolean_fixture import BooleanEnvironment, ROWS, create_actor


def actor(seed=41):
    baseline = create_actor(seed, 'current')
    return RouteActionBudDevelopment.create(
        schema=BooleanEnvironment.schema, state_coordinates=(0, 1, 2, 3),
        seed=seed, config=replace(baseline.config, exploration=0),
        search=baseline.birth_search_config, development=baseline.development_config,
        limits=baseline.ownership_limits)


def scores(learner, row):
    learner.act(BooleanEnvironment(row), event_id=0, learn=False)
    return tuple(learner.graph.nodes[f'option:{slot}'].activation.value
                 for slot in range(2))


def plant_supported_interaction(learner):
    route = next(i for i, expression in enumerate(learner.owner_candidates)
                 if expression == Expression('read', atom=(0, True)))
    reader = next(i for i, expression in enumerate(learner.action_readers)
                  if expression == Expression('read', atom=(4, True)))
    evidence = RouteActionEvidence()
    for side in (False, True):
        for active in (False, True):
            for _ in range(4):
                evidence.add(side, active, True, 1 if side and active else 0)
    learner.action_bud_evidence[0][(route, reader)] = evidence
    return route, reader


def test_bud_is_zero_weight_action_feature_in_same_owner():
    learner = actor()
    before = {row: scores(learner, row) for row in ROWS}
    route, reader = plant_supported_interaction(learner)
    learner._run_development(0)
    assert learner.development_history[-1]['bud'] is not None
    assert learner.development_history[-1]['split'] is None
    assert len(learner.leaves) == 1
    cid = learner.development_history[-1]['birth']
    assert learner.base_expressions[cid].children == tuple(sorted((
        learner.owner_candidates[route], learner.action_readers[reader]), key=repr))
    assert float(learner.conditions[cid].weight) == 0
    assert {row: scores(learner, row) for row in ROWS} == before
    learner.validate_ownership()


def test_actual_action_credit_changes_only_matching_route_and_action():
    learner = actor()
    plant_supported_interaction(learner)
    learner._run_development(0)
    cid = learner.development_history[-1]['birth']
    row = next(row for row in ROWS if row[0])
    env = BooleanEnvironment(row)
    action = learner.act(env, event_id=0, learn=True)
    assert action == 'act-b'
    assert cid in learner.pending[-1][3]
    with pytest.raises(ValueError):
        learner.observe(Feedback(0, 'act-a', 1))
    with pytest.raises(RuntimeError):
        pickle.dumps(learner)
    learner.observe(Feedback(0, action, 1))
    assert learner.conditions[cid].weight.fast > 0
    assert learner.action_bud_pending is None
    assert pickle.loads(pickle.dumps(learner)).conditions == learner.conditions
    active_margin = scores(learner, row)[1] - scores(learner, row)[0]
    inactive_margin = scores(learner, next(r for r in ROWS if not r[0]))[1] - scores(
        learner, next(r for r in ROWS if not r[0]))[0]
    assert active_margin > 0
    assert inactive_margin == 0


def test_formal_observations_and_impossible_child_exclusion():
    learner = actor()
    env = BooleanEnvironment(next(row for row in ROWS if row[0]))
    action = learner.act(env, event_id=0, learn=True)
    pending = learner.action_bud_pending
    assert pending[0:2] == (0, action)
    assert all(pending[5])  # Action reader differs between legal bindings.
    for slot in range(2):
        assert all(learner.graph.nodes[nid].state in (NodeState.CONFIRMED, NodeState.FAILED)
                   for nid in learner.action_probe_nodes[slot])
    learner.observe(Feedback(0, action, env.outcome()))
    assert sum(e.counts.get((True, True), 0) for e in learner.action_bud_evidence[0].values()) <= (
        len(learner.owner_candidates) * len(learner.action_readers))
    children = learner.split_decision(0, Expression('read', atom=(0, True)))
    opposite = Expression('read', atom=(0, False))
    assert learner._compatibility(children[1], opposite)[0].status == 'impossible'
    assert all(learner.action_bud_evidence[child] == {} for child in children)


def test_interaction_needs_all_four_cells_and_action_variation():
    evidence = RouteActionEvidence()
    for side in (False, True):
        for active in (False, True):
            for _ in range(4):
                evidence.add(side, active, False, 1 if side and active else 0)
    assert evidence.score(4) is None
    for side in (False, True):
        for active in (False, True):
            for _ in range(4):
                evidence.add(side, active, True, 1 if side and active else 0)
    assert evidence.score(4) > 0
