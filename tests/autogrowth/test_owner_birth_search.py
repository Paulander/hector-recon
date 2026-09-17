import copy
from dataclasses import replace
import pickle

import pytest

from recon_lite_chess.coach.interface import Feedback
from recon_lite_hector.learning.compatible_owner import CompatibleOwnerDevelopment
from recon_lite_hector.learning.context_decision import OwnershipLimits
from recon_lite_hector.learning.owner_development import OwnerDevelopmentConfig
from recon_lite_hector.learning.owner_birth_search import BirthSearchConfig, BirthSearchOwnerDevelopment
from recon_lite_hector.learning.recursive_context import Expression, SplitEvidence
from test_context_decision import Port, ROWS, planted, scores, weight_snapshot
from test_owner_development import step


def learner(*, mode="random", extra=False, every=1000, source=None):
    return BirthSearchOwnerDevelopment.from_actor(source or planted(),
        state_coordinates=(0, 1, 2), search_seed=12,
        search=BirthSearchConfig(mode=mode, extra_after_split=extra),
        development=OwnerDevelopmentConfig(develop_every=every, min_support=2),
        limits=OwnershipLimits(max_parameters=64, max_definitions=256, max_physical_nodes=2048))


def test_observers_preserve_real_choices_credit_and_source():
    source = planted()
    original = pickle.dumps(source)
    control = CompatibleOwnerDevelopment.from_actor(source, state_coordinates=(0, 1, 2),
        development=OwnerDevelopmentConfig(develop_every=1000),
        limits=OwnershipLimits(max_parameters=64, max_definitions=256, max_physical_nodes=2048))
    actor = learner(source=source)
    assert pickle.dumps(source) == original
    assert len(actor.graph.nodes) > len(control.graph.nodes)
    for event in range(16):
        assert step(actor, event, ROWS[event % 8]) == step(control, event, ROWS[event % 8])
        assert actor.conditions == control.conditions
        assert actor.exploration_rng.getstate() == control.exploration_rng.getstate()
    assert all(e.n0+e.n1 == 16 for e in actor.birth_evidence[0])


def test_feedback_validation_and_preupdate_residual():
    actor = learner()
    port = Port(ROWS[1]); action = actor.act(port, event_id=9, learn=True)
    pending = actor.birth_search_pending
    before = copy.deepcopy(actor.conditions)
    for feedback in (Feedback(8, action, 1), Feedback(9, 'wrong', 1), Feedback(9, action, float('nan'))):
        with pytest.raises(ValueError): actor.observe(feedback)
        assert actor.conditions == before
        assert actor.birth_search_pending == pending
        assert all(e.n0+e.n1 == 0 for e in actor.birth_evidence[0])
    with pytest.raises(RuntimeError): pickle.dumps(actor)
    actor.observe(Feedback(9, action, port.outcome()))
    for e, flag in zip(actor.birth_evidence[0], pending[4]):
        assert (e.n0, e.n1) == ((0, 1) if flag else (1, 0))
        assert e.sum0+e.sum1 == port.outcome()-pending[3]


def test_unvisited_sibling_keeps_weights_and_evidence():
    actor = learner()
    left, right = actor.split_decision(0, Expression('read', atom=(0, True)))
    before = weight_snapshot(actor, left)
    for event in range(8): step(actor, event, (True, bool(event%2), False))
    assert weight_snapshot(actor, left) == before
    assert all(e.n0+e.n1 == 0 for e in actor.birth_evidence[left])
    assert all(e.n0+e.n1 == 8 for e in actor.birth_evidence[right])
    assert 0 in actor.birth_evidence


@pytest.mark.parametrize('extra', [False, True])
def test_split_schedule_targets_only_observed_child_without_inventing_visits(extra):
    actor = learner(extra=extra, every=8)
    for event in range(8): step(actor, event, ROWS[event])
    event = actor.development_history[0]
    assert event['split'] is not None
    children = event['split']['children']
    assert all(actor.owner_visits[c] == 0 for c in children)
    assert all(e.n0+e.n1 == 8 for e in actor.birth_evidence[0])
    assert all(e.n0+e.n1 == 0 for c in children for e in actor.birth_evidence[c])
    if extra:
        active = actor.last_route_observations[0][event['split']['candidate']]
        target = event['extra_birth']['owner']
        assert target == children[int(active)]
        assert len(actor.birth_nominations) == 1
        assert actor.birth_nominations[0]['owner'] == target
    else:
        assert not actor.birth_nominations and 'extra_birth' not in event


def test_unobserved_state_only_structure_remains_eligible_and_starts_untrained():
    actor = learner(mode='residual')
    selected = None
    for i, expression in enumerate(actor.birth_expressions):
        if expression in actor.owner_seen[0]: continue
        try: actor._check_route(expression)
        except ValueError: continue
        selected = i; break
    assert selected is not None
    actor.owner_seen[0].update(e for i,e in enumerate(actor.birth_expressions) if i != selected)
    cid = actor._birth_local(0)
    assert cid is not None and actor.base_expressions[cid] == actor.birth_expressions[selected]
    assert float(actor.conditions[cid].weight) == 0
    assert actor.birth_nominations[-1]['selection'] == 'random'
    assert actor.birth_nominations[-1]['evidence'].n0 == 0


def test_ranker_uses_local_evidence_without_importing_fitted_weights():
    actor = learner(mode='residual')
    eligible = [i for i,e in enumerate(actor.birth_expressions) if e not in actor.owner_seen[0]]
    target = eligible[-1]
    actor.birth_evidence[0][target] = SplitEvidence(8, 8, -8, 8)
    actor.birth_search_config = replace(actor.birth_search_config, random_fraction=1e-12)
    cid = actor._birth_local(0)
    record = actor.birth_nominations[-1]
    assert record['selected'] == target and record['selection'] == 'residual'
    assert float(actor.conditions[cid].weight) == 0
    assert actor.birth_evidence[0][target] == SplitEvidence(8, 8, -8, 8)


def test_checkpoint_continuation_preserves_both_search_and_action_histories():
    actor = learner(mode='residual', extra=True, every=8)
    for event in range(8): step(actor, event, ROWS[event])
    restored = pickle.loads(pickle.dumps(actor))
    for event in range(8, 24):
        assert step(actor, event, ROWS[event%8]) == step(restored, event, ROWS[event%8])
        for name in ('conditions', 'leaves', 'birth_evidence', 'birth_nominations', 'development_history'):
            assert getattr(actor,name) == getattr(restored,name)
        assert actor.birth_selection_rng.getstate() == restored.birth_selection_rng.getstate()
    assert [scores(actor,row) for row in ROWS] == [scores(restored,row) for row in ROWS]


@pytest.mark.parametrize('kwargs', [{'mode':'bad'}, {'candidates':0}, {'extra_after_split':1},
                                   {'random_fraction':0}, {'random_fraction':float('nan')}])
def test_invalid_configuration(kwargs):
    with pytest.raises(ValueError): BirthSearchConfig(**kwargs)
