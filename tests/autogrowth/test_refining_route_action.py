"""Synthetic exact checks; planted expressions are test fixtures, not training."""
import copy
from dataclasses import replace
import pickle

import pytest

from recon_lite.graph import LinkType
from recon_lite_chess.coach.interface import Feedback
from recon_lite_hector.learning.context_decision import OwnershipLimits
from recon_lite_hector.learning.recursive_context import Expression, combine
from recon_lite_hector.learning.recursive_context import SplitEvidence
from recon_lite_hector.learning.refining_route_action import (
    ProspectiveRefinementNomination, ProspectiveRefiningRouteActionDevelopment,
    RefiningRouteActionDevelopment,
)
from recon_lite_hector.learning.route_action_bud import RouteActionEvidence
from recon_lite_hector.learning.terminal_development import Condition, PlasticWeight
from selective_boolean_fixture import BooleanEnvironment, ROWS, create_actor


def actor(seed=43, *, max_parameters=64, minimum_refinement_score=0.0,
          reclosure_enabled=False):
    baseline = create_actor(seed, 'current')
    return RefiningRouteActionDevelopment.create(
        schema=BooleanEnvironment.schema, state_coordinates=(0, 1, 2, 3),
        seed=seed, config=replace(baseline.config, exploration=0),
        search=baseline.birth_search_config, development=baseline.development_config,
        limits=replace(baseline.ownership_limits, max_parameters=max_parameters),
        minimum_refinement_score=minimum_refinement_score,
        reclosure_enabled=reclosure_enabled)


def prospective_actor(seed=43, *, resource_cost=1.0):
    baseline = create_actor(seed, 'current')
    return ProspectiveRefiningRouteActionDevelopment.create(
        schema=BooleanEnvironment.schema, state_coordinates=(0, 1, 2, 3),
        seed=seed, config=replace(baseline.config, exploration=0),
        search=baseline.birth_search_config, development=baseline.development_config,
        limits=baseline.ownership_limits,
        prospective_resource_cost=resource_cost)


def read(index, value=True):
    return Expression('read', atom=(index, value))


def add(learner, expression, weight, *, refinable=False):
    cid = learner.next_condition
    learner.next_condition += 1
    learner.conditions[cid] = Condition(cid, (), 'and', learner.completed,
                                        weight=PlasticWeight(fast=weight))
    learner.base_expressions[cid] = expression
    learner.birth_visits[cid] = learner.owner_visits[0]
    learner.owner_seen[0].add(expression)
    learner.leaves[0] = replace(learner.leaves[0], contributions=(
        *learner.leaves[0].contributions, cid))
    if refinable:
        learner.refinable.add(cid)
        learner.refinement_evidence[cid] = {}
    learner._rebuild(learner.slots)
    return cid


def scores(learner):
    result = []
    for row in ROWS:
        clone = copy.deepcopy(learner)
        clone.act(BooleanEnvironment(row), event_id=0, learn=False)
        result.append(tuple(clone.graph.nodes[f'option:{slot}'].activation.value
                            for slot in range(2)))
    return result


def test_refinement_preserves_all_action_scores_and_owner():
    learner = actor()
    parent = add(learner, combine('and', (read(0), read(4))), .7, refinable=True)
    before = scores(learner)
    event = learner._refine_local(0, parent, read(2))
    assert scores(learner) == before
    assert len(learner.leaves) == 1 and parent not in learner.conditions
    assert len(event['children']) == 2
    assert all(float(learner.conditions[c].weight) == .7 for c in event['children'])
    assert len({id(learner.conditions[c].weight) for c in event['children']}) == 2
    assert pickle.loads(pickle.dumps(learner)).conditions == learner.conditions
    learner.validate_ownership()


def test_refined_grammar_can_represent_full_conditional_switch():
    learner = actor()
    add(learner, read(4), -.5)
    x = add(learner, combine('and', (read(0), read(4))), 1., refinable=True)
    y = add(learner, combine('and', (read(1), read(4))), 1., refinable=True)
    x_low, x_high = learner._refine_local(0, x, read(2))['children']
    y_low, y_high = learner._refine_local(0, y, read(2))['children']
    learner.conditions[x_high].weight.fast = 0.
    learner.conditions[y_low].weight.fast = 0.
    for row in ROWS:
        env = BooleanEnvironment(row)
        action = learner.act(env, event_id=0, learn=False)
        assert env.outcome() == 1, (row, action)
    assert learner.base_expressions[x_low] != learner.base_expressions[x_high]
    assert learner.base_expressions[y_low] != learner.base_expressions[y_high]


def test_real_credit_and_local_evidence_follow_only_active_contribution():
    learner = actor()
    cid = add(learner, combine('and', (read(0), read(4))), .7, refinable=True)
    row = next(r for r in ROWS if r[0])
    env = BooleanEnvironment(row)
    action = learner.act(env, event_id=0, learn=True)
    assert action == 'act-b' and cid in learner.action_bud_pending[6]
    with pytest.raises(ValueError):
        learner.observe(Feedback(0, 'act-a', 1))
    before = float(learner.conditions[cid].weight)
    learner.observe(Feedback(0, action, -1))
    assert float(learner.conditions[cid].weight) < before
    assert all(e.n0 + e.n1 == 1 for e in learner.refinement_evidence[cid].values())
    assert learner.action_bud_pending is None
    env = BooleanEnvironment(next(r for r in ROWS if not r[0]))
    action = learner.act(env, event_id=1, learn=True)
    assert cid not in learner.action_bud_pending[6]
    learner.observe(Feedback(1, action, env.outcome()))
    assert all(e.n0 + e.n1 == 1 for e in learner.refinement_evidence[cid].values())


def test_impossible_or_over_budget_refinement_is_atomic():
    learner = actor(max_parameters=2)
    cid = add(learner, combine('and', (read(0), read(4))), .7, refinable=True)
    initial = (copy.deepcopy(learner.conditions), copy.deepcopy(learner.leaves),
               scores(learner), len(learner.graph.nodes), learner.next_condition)
    with pytest.raises(ValueError, match='impossible'):
        learner._refine_local(0, cid, read(0))
    assert (learner.conditions, learner.leaves, scores(learner),
            len(learner.graph.nodes), learner.next_condition) == initial
    with pytest.raises(ValueError, match='budget'):
        learner._refine_local(0, cid, read(2))
    assert (learner.conditions, learner.leaves, scores(learner),
            len(learner.graph.nodes), learner.next_condition) == initial


def test_nonzero_score_floor_avoids_weak_refinement():
    weak = actor(minimum_refinement_score=1.0)
    cid = add(weak, combine('and', (read(0), read(4))), .7, refinable=True)
    route = next(i for i, predicate in enumerate(weak.owner_candidates)
                 if predicate == read(2))
    weak.refinement_evidence[cid][route] = SplitEvidence(4, 4, 0., 2.)
    assert weak.refinement_evidence[cid][route].score(4) == .5
    weak._run_development(0)
    assert not weak.refinement_history
    strong = actor(minimum_refinement_score=0.0)
    cid = add(strong, combine('and', (read(0), read(4))), .7, refinable=True)
    strong.refinement_evidence[cid][route] = SplitEvidence(4, 4, 0., 2.)
    strong._run_development(0)
    assert len(strong.refinement_history) == 1


def _supported_siblings(*, low_residual=0., high_residual=0., weight=.7):
    learner = actor(reclosure_enabled=True)
    parent = add(learner, combine('and', (read(0), read(4))), weight,
                 refinable=True)
    split = learner._refine_local(0, parent, read(2))
    low, high = split['children']
    learner.owner_visits[0] = learner.config.grace_episodes
    count = learner.development_config.min_support
    for cid in (low, high):
        for episode in range(count):
            learner.conditions[cid].stats.record_confirm(episode, 'action_choice')
    index = learner.owner_candidates.index(read(2))
    learner.refinement_evidence[low][index] = SplitEvidence(
        count, 0, count * low_residual, 0.)
    learner.refinement_evidence[high][index] = SplitEvidence(
        0, count, 0., count * high_residual)
    return learner, split


def test_reclosure_vetoes_equal_weights_with_opposite_post_birth_residuals():
    learner, split = _supported_siblings(low_residual=-1., high_residual=1.)
    assert learner._eligible_reclosure(0, split) is None
    with pytest.raises(ValueError, match='locally redundant'):
        learner._reclose_local(0, split)
    assert not learner.reclosure_history
    assert all(cid in learner.conditions for cid in split['children'])
    # No support from an unchosen action may be supplied through feedback.
    row = next(row for row in ROWS if row[0] and not row[2])
    action = learner.act(BooleanEnvironment(row), event_id=88, learn=True)
    before = copy.deepcopy(learner.refinement_evidence)
    wrong = 'act-a' if action == 'act-b' else 'act-b'
    with pytest.raises(ValueError):
        learner.observe(Feedback(88, wrong, 1.))
    assert learner.refinement_evidence == before
    learner.observe(Feedback(88, action, 1.))
    assert learner.refinement_evidence != before


def test_reclosure_accepts_redundant_siblings_with_exact_scores_and_tombstones():
    learner, split = _supported_siblings()
    # Suppress the unrelated random-birth fallback in this exact merge fixture.
    learner.ownership_limits = replace(learner.ownership_limits,
                                       max_parameters=len(learner.conditions))
    before_scores = scores(learner)
    old_ids = set(learner.conditions)
    old_next = learner.next_condition
    old_count = len(learner.conditions)
    assert learner._eligible_reclosure(0, split) == (0., 0., (4, 4))
    learner._run_development(0)
    event = learner.development_history[-1]['reclosure']
    cid = event['condition']
    assert learner.development_history[-1]['refinement'] is None
    assert event['maximum_option_score_change'] == 0.
    assert scores(learner) == before_scores
    assert len(learner.conditions) == old_count - 1
    assert cid == old_next and cid not in old_ids
    assert set(split['children']).isdisjoint(learner.conditions)
    assert all(child not in learner.refinable for child in split['children'])
    assert learner.base_expressions[cid] == learner.base_expressions[split['parent']]
    assert learner.conditions[cid].stats.relevance_stats.confirm_count == 0
    tombstone = learner.reclosure_history[-1]
    assert tuple(c.identity for c in tombstone['retired_conditions']) == split['children']
    assert all(tombstone['retired_evidence'])
    assert len(learner.leaves) == 1 and cid in learner.refinable
    assert len({id(c.weight) for c in learner.conditions.values()}) == len(learner.conditions)
    learner.validate_ownership()
    restored = pickle.loads(pickle.dumps(learner, protocol=5))
    assert restored.conditions == learner.conditions
    assert scores(restored) == before_scores
    for slot in range(restored.slots):
        assert (restored.graph.edge_by_key[(f'gate:{slot}:{cid}',
                                           f'option:{slot}', LinkType.SUR)].w
                is restored.conditions[cid].weight)


def test_reclosure_does_not_preempt_supported_refinement_and_replays():
    learner, split = _supported_siblings()
    parent = add(learner, combine('and', (read(1), read(4))), .7,
                 refinable=True)
    index = learner.owner_candidates.index(read(2))
    learner.refinement_evidence[parent][index] = SplitEvidence(4, 4, -4., 4.)
    before = scores(learner)
    learner._run_development(0)
    event = learner.development_history[-1]
    assert event['refinement']['parent'] == parent
    assert event['reclosure']['children'] == split['children']
    assert event['refinement']['episode'] == event['reclosure']['episode']
    assert len(learner.refinement_history) == 2
    assert len(learner.reclosure_history) == 1
    assert scores(learner) == before
    restored = pickle.loads(pickle.dumps(learner, protocol=5))
    assert restored.development_history == learner.development_history
    assert restored.reclosure_history == learner.reclosure_history
    assert scores(restored) == before


def test_reclosure_does_not_preempt_supported_action_bud():
    learner, split = _supported_siblings()
    route = learner.owner_candidates.index(read(1, False))
    reader = learner.action_readers.index(read(4))
    keys = ((False, False), (False, True), (True, False), (True, True))
    learner.action_bud_evidence[0][(route, reader)] = RouteActionEvidence(
        counts={key: 4 for key in keys},
        sums={key: (4. if key[0] == key[1] else -4.) for key in keys},
        variable=16)
    before = scores(learner)
    learner._run_development(0)
    event = learner.development_history[-1]
    assert event['bud'] is not None
    assert event['bud']['expression'] == combine('and', (read(1, False), read(4)))
    assert event['reclosure']['children'] == split['children']
    assert scores(learner) == before


def test_reclosure_midpoint_bounds_every_option_score():
    learner, split = _supported_siblings()
    low, high = split['children']
    learner.conditions[low].weight.fast = .5
    learner.conditions[low].weight.slow = .2
    learner.conditions[high].weight.fast = .51
    learner.conditions[high].weight.slow = .2
    prior = scores(learner)
    event = learner._reclose_local(0, split)
    after = scores(learner)
    assert event['gap'] == pytest.approx(.01)
    assert event['maximum_option_score_change'] == pytest.approx(.005)
    assert learner.conditions[event['condition']].weight.fast == pytest.approx(.505)
    assert learner.conditions[event['condition']].weight.slow == pytest.approx(.2)
    assert max(abs(a - b) for row_before, row_after in zip(prior, after)
               for a, b in zip(row_before, row_after)) <= event['gap'] / 2 + 1e-12


def test_reclosure_chooses_smallest_gap_and_default_stays_off():
    baseline = actor()
    assert baseline.reclosure_enabled is False and baseline.reclosure_history == []
    learner, first = _supported_siblings()
    first_low, first_high = first['children']
    learner.conditions[first_high].weight.fast += .01
    parent = add(learner, combine('and', (read(1), read(4))), .7,
                 refinable=True)
    second = learner._refine_local(0, parent, read(2))
    low, high = second['children']
    learner.owner_visits[0] += learner.config.grace_episodes
    count = learner.development_config.min_support
    index = learner.owner_candidates.index(read(2))
    for cid in (low, high):
        for episode in range(count):
            learner.conditions[cid].stats.record_confirm(episode, 'action_choice')
    learner.refinement_evidence[low][index] = SplitEvidence(count, 0, 0., 0.)
    learner.refinement_evidence[high][index] = SplitEvidence(0, count, 0., 0.)
    learner.conditions[high].weight.fast += .005
    learner._run_development(0)
    assert learner.development_history[-1]['reclosure']['children'] == (low, high)
    assert first_low in learner.conditions and first_high in learner.conditions


def test_reclosure_rejects_missing_or_inconsistent_evidence_and_pending_feedback(monkeypatch):
    learner, split = _supported_siblings()
    low, _ = split['children']
    index = learner.owner_candidates.index(read(2))
    learner.refinement_evidence[low][index].n0 -= 1
    assert learner._eligible_reclosure(0, split) is None
    learner.refinement_evidence[low][index].n0 += 1
    assert learner._eligible_reclosure(0, split) is not None
    for pending_name in ('candidate_pending', 'action_bud_pending',
                         'birth_search_pending'):
        setattr(learner, pending_name, ('partial actual-action frame',))
        with pytest.raises(RuntimeError, match='completed actual feedback'):
            learner._reclose_local(0, split)
        setattr(learner, pending_name, None)
    action = learner.act(BooleanEnvironment(next(r for r in ROWS if r[0])),
                         event_id=99, learn=True)
    with pytest.raises(RuntimeError, match='completed actual feedback'):
        learner._reclose_local(0, split)
    learner.observe(Feedback(99, action, 1.))
    learner, split = _supported_siblings()
    # A failed compile must not commit any part of the proposed mutation.
    before = (copy.deepcopy(learner.conditions), copy.deepcopy(learner.leaves),
              copy.deepcopy(learner.refinement_evidence),
              learner.next_condition, len(learner.reclosure_history))
    with monkeypatch.context() as patcher:
        def fail_rebuild(_self, _slots):
            raise RuntimeError('synthetic compile failure')
        patcher.setattr(RefiningRouteActionDevelopment, '_rebuild', fail_rebuild)
        with pytest.raises(RuntimeError, match='synthetic compile failure'):
            learner._reclose_local(0, split)
    assert (learner.conditions, learner.leaves, learner.refinement_evidence,
            learner.next_condition, len(learner.reclosure_history)) == before


def _nominate(learner):
    cid = add(learner, combine('and', (read(0), read(4))), .7, refinable=True)
    index = next(i for i, candidate in enumerate(learner.owner_candidates)
                 if candidate == read(2))
    learner.prospective_discovery[cid] = {index: SplitEvidence(4, 4, -4., 4.)}
    learner.prospective_started[cid] = 0
    learner.owner_visits[0] = learner.development_config.develop_every
    learner._run_development(0)
    assert not learner.refinement_history
    nomination = learner.prospective_nominations[cid]
    assert nomination.index == index and nomination.validation == SplitEvidence()
    return cid, index


def test_prospective_gate_freezes_discovery_and_accepts_later_gain():
    learner = prospective_actor()
    cid, index = _nominate(learner)
    discovery = copy.deepcopy(learner.prospective_nominations[cid].discovery)
    learner.prospective_nominations[cid].validation = SplitEvidence(4, 4, -4., 4.)
    assert learner.prospective_nominations[cid].validation_gain(4) == 8.
    before = scores(learner)
    learner.owner_visits[0] += learner.development_config.develop_every
    learner._run_development(0)
    assert scores(learner) == before
    assert len(learner.refinement_history) == 1
    assert learner.refinement_history[0]['parent'] == cid
    assert learner.development_history[-1]['refinement'] is not None
    review = learner.prospective_history[-1]
    assert review['candidate'] == index and review['decision'] == 'approved'
    assert review['discovery'] == discovery and review['prospective_gain'] == 8.
    assert cid not in learner.prospective_nominations


def _two_approved_nominations():
    learner = prospective_actor()
    first, index = _nominate(learner)
    second = add(learner, combine('and', (read(1), read(4))), .7,
                 refinable=True)
    discovery = SplitEvidence(4, 4, -4., 4.)
    learner.prospective_nominations[first].validation = SplitEvidence(4, 4, -4., 4.)
    learner.prospective_nominations[second] = ProspectiveRefinementNomination(
        index, copy.deepcopy(discovery), discovery.score(4),
        learner.owner_visits[0], SplitEvidence(4, 4, -3.75, 3.75))
    assert learner._eligible_refinement(0, second, read(2)) is not None
    return learner, first, second, discovery


def test_only_one_simultaneous_approval_commits_and_other_revalidates():
    learner, first, second, discovery = _two_approved_nominations()
    before = scores(learner)
    learner.owner_visits[0] += learner.development_config.develop_every
    learner._run_development(0)
    assert scores(learner) == before
    assert len(learner.refinement_history) == 1
    assert learner.refinement_history[0]['parent'] == first
    assert first not in learner.prospective_nominations
    remaining = learner.prospective_nominations[second]
    assert remaining.index == next(i for i, p in enumerate(learner.owner_candidates)
                                   if p == read(2))
    assert remaining.discovery == discovery
    assert remaining.validation == SplitEvidence()
    assert remaining.nominated_visit == learner.owner_visits[0]
    deferred = learner.refinement_history[0]['deferred_revalidation']
    assert len(deferred) == 1
    assert deferred[0]['condition'] == second
    assert deferred[0]['prior_gain'] == 7.
    assert deferred[0]['reset_visit'] == learner.owner_visits[0]
    assert len(learner.development_history[-1]['prospective_reviews']) == 2
    assert all(item['decision'] == 'approved' for item in
               learner.development_history[-1]['prospective_reviews'])
    # Passing the next safe point without any post-mutation receipt cannot
    # spend the earlier approval a second time.
    learner.owner_visits[0] += learner.development_config.develop_every
    learner._run_development(0)
    assert len(learner.refinement_history) == 1
    assert learner.prospective_nominations[second].validation == SplitEvidence()


def test_deferred_nomination_needs_new_real_receipts_and_replays():
    learner, _, second, discovery = _two_approved_nominations()
    learner.owner_visits[0] += learner.development_config.develop_every
    learner._run_development(0)
    learner.config = replace(learner.config, learning_rate=.01)
    clone = pickle.loads(pickle.dumps(learner))
    assert clone.prospective_nominations == learner.prospective_nominations
    for organism in (learner, clone):
        for event in range(8):
            row = (False, True, bool(event % 2), False)
            env = BooleanEnvironment(row)
            action = organism.act(env, event_id=event, learn=True)
            assert action == 'act-b'
            organism.observe(Feedback(event, action, env.outcome()))
        remaining = organism.prospective_nominations[second]
        assert remaining.discovery == discovery
        assert (remaining.validation.n0, remaining.validation.n1) == (4, 4)
        assert remaining.validation_gain(4) > organism.prospective_resource_cost
        organism.owner_visits[0] = 2 * organism.development_config.develop_every + 64
        organism._run_development(0)
        assert len(organism.refinement_history) == 2
        assert organism.refinement_history[-1]['parent'] == second
    assert learner.conditions == clone.conditions
    assert learner.prospective_history == clone.prospective_history
    assert scores(learner) == scores(clone)


def test_prospective_gate_rejects_reversed_later_evidence():
    learner = prospective_actor()
    cid, _ = _nominate(learner)
    learner.prospective_nominations[cid].validation = SplitEvidence(4, 4, 4., -4.)
    assert learner.prospective_nominations[cid].validation_gain(4) == -24.
    learner.owner_visits[0] += learner.development_config.develop_every
    learner._run_development(0)
    assert not learner.refinement_history
    assert learner.prospective_history[-1]['decision'] == 'rejected'
    assert cid not in learner.prospective_nominations
    assert learner.development_history[-1]['refinement'] is None


def test_prospective_resource_cost_rejects_small_positive_gain():
    learner = prospective_actor(resource_cost=1.0)
    cid, _ = _nominate(learner)
    learner.prospective_nominations[cid].validation = SplitEvidence(4, 4, -2.25, 2.25)
    assert learner.prospective_nominations[cid].validation_gain(4) == 1.
    learner.owner_visits[0] += learner.development_config.develop_every
    learner._run_development(0)
    assert not learner.refinement_history
    assert learner.prospective_history[-1]['decision'] == 'rejected'


def test_prospective_gate_expires_unsupported_validation():
    learner = prospective_actor()
    cid, _ = _nominate(learner)
    learner.prospective_nominations[cid].validation = SplitEvidence(3, 6, -3., 6.)
    learner.owner_visits[0] += 4 * learner.development_config.develop_every
    learner._run_development(0)
    assert not learner.refinement_history
    assert learner.prospective_history[-1]['decision'] == 'unsupported'
    assert cid not in learner.prospective_nominations


def test_prospective_discovery_window_expires_without_two_sided_support():
    learner = prospective_actor()
    cid = add(learner, combine('and', (read(0), read(4))), .7, refinable=True)
    index = next(i for i, candidate in enumerate(learner.owner_candidates)
                 if candidate == read(2))
    learner.prospective_discovery[cid] = {index: SplitEvidence(0, 12, 0., 6.)}
    learner.prospective_started[cid] = 0
    learner.owner_visits[0] = 4 * learner.development_config.develop_every
    learner._run_development(0)
    assert cid not in learner.prospective_nominations
    assert learner.prospective_discovery[cid] == {}
    assert learner.prospective_started[cid] == learner.owner_visits[0]


def test_prospective_evidence_uses_only_confirmed_actual_action_and_replays():
    learner = prospective_actor()
    cid = add(learner, combine('and', (read(0), read(4))), .7, refinable=True)
    row = next(r for r in ROWS if r[0])
    env = BooleanEnvironment(row)
    action = learner.act(env, event_id=0, learn=True)
    assert action == 'act-b' and cid in learner.action_bud_pending[6]
    with pytest.raises(ValueError):
        learner.observe(Feedback(0, 'act-a', 1))
    assert learner.prospective_discovery == {}
    learner.observe(Feedback(0, action, env.outcome()))
    assert all(e.n0 + e.n1 == 1 for e in learner.prospective_discovery[cid].values())
    clone = pickle.loads(pickle.dumps(learner))
    assert clone.prospective_discovery == learner.prospective_discovery
    second = next(r for r in ROWS if not r[0])
    for organism in (learner, clone):
        env = BooleanEnvironment(second)
        action = organism.act(env, event_id=1, learn=True)
        organism.observe(Feedback(1, action, env.outcome()))
    assert clone.prospective_discovery == learner.prospective_discovery
    assert all(e.n0 + e.n1 == 1 for e in learner.prospective_discovery[cid].values())
    assert scores(clone) == scores(learner)


def test_real_receipt_after_nomination_enters_validation_not_discovery():
    learner = prospective_actor()
    cid, _ = _nominate(learner)
    frozen = copy.deepcopy(learner.prospective_nominations[cid].discovery)
    env = BooleanEnvironment(next(r for r in ROWS if r[0]))
    action = learner.act(env, event_id=0, learn=True)
    with pytest.raises(ValueError):
        learner.observe(Feedback(0, 'act-a' if action == 'act-b' else 'act-b', 1))
    assert learner.prospective_nominations[cid].validation == SplitEvidence()
    learner.observe(Feedback(0, action, env.outcome()))
    nomination = learner.prospective_nominations[cid]
    assert nomination.discovery == frozen
    assert nomination.validation.n0 + nomination.validation.n1 == int(action == 'act-b')
    assert learner.prospective_discovery[cid] == {}
    clone = pickle.loads(pickle.dumps(learner))
    assert clone.prospective_nominations == learner.prospective_nominations


def test_prospective_gain_matches_direct_squared_error_difference():
    first = SplitEvidence(4, 4, -2., 2.)
    validation = SplitEvidence(4, 4, -1., 3.)
    nomination = ProspectiveRefinementNomination(0, first, first.score(4), 64,
                                                  validation)
    gain = nomination.validation_gain(4)
    residuals = ((-1., 0., 0., 0.), (0., 1., 1., 1.))
    means = (-.5, .5)
    direct = sum(sum(value * value - (value - means[side]) ** 2
                     for value in residuals[side]) for side in (0, 1))
    assert gain == direct
